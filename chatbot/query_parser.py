"""Understands the question *before* retrieval.

Pure vector search is bad at three things users ask all the time:
  * exact names   -> "Tata Power" and "Tata Steel" embed almost identically
  * dates         -> "yesterday" has no meaning to an embedding
  * categories    -> "all buybacks this week" needs every buyback, not the 8 closest chunks
So we pull those out with rules and turn them into hard metadata filters.
"""
import datetime as dt
import re
from dataclasses import dataclass, field

from rapidfuzz import fuzz

WEEKDAYS = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
MONTHS = {m: i for i, m in enumerate(
    ["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"], 1)}

# keyword (regex) -> dataset tags
TAG_WORDS = [
    (r"\bdividends?\b", ["Dividend"]),
    (r"\bbuy ?backs?\b", ["Buyback"]),
    (r"\bbonus\b", ["Bonus"]),
    (r"\b(stock )?splits?\b|sub-?division", ["Split"]),
    (r"\b(results?|earnings|quarterly|q[1-4]|profit|revenue|financials?)\b", ["Results"]),
    (r"\b(orders?|contracts?|order wins?|awarded|work orders?)\b", ["Order"]),
    (r"\b(acquisitions?|acquires?|acquired|takeovers?|mergers?|amalgamation)\b", ["Acquisition", "Scheme Of Arrangement"]),
    (r"\b(fund ?rais\w*|qip|preferential|warrants?|rights issue|raise capital|capital raising)\b",
     ["Fund Raising", "Qip", "Pref", "Warrants", "Rights Issue"]),
    (r"\b(credit )?ratings?\b", ["Ratings Update"]),
    (r"\b(ceo|cfo|md|director|resign\w*|appoint\w*|management change|key managerial|kmp)\b", ["Change In Management"]),
    (r"\b(con ?calls?|conference calls?|earnings calls?|transcripts?)\b", ["Concall"]),
    (r"\b(investor meet\w*|analyst meet\w*|investor conference)\b", ["Investor Meet"]),
    (r"\b(investor presentations?)\b", ["Investor Presentation"]),
    (r"\b(open offers?)\b", ["Open Offer"]),
    (r"\b(nclt|insolvency|ibc)\b", ["Nclt"]),
    (r"\b(legal|court|penalt\w*|sebi order|regulatory|show cause)\b", ["Legal/Reg"]),
    (r"\b(subsidiar\w*)\b", ["New Subsidiary"]),
    (r"\b(capacity|new plant|expansion|commission\w*)\b", ["Capacity Increase"]),
    (r"\b(partnerships?|tie-?ups?|collaborat\w*|mou|joint venture)\b", ["Partnership"]),
    (r"\b(promoters? (buy|sell|bought|sold)\w*|insider|promoter (selling|buying))\b",
     ["Promoter Buy/Sell", "Inter-se Transfer", "Stake Change"]),
    (r"\b(stake)\b", ["Stake Change", "Acquisition"]),
    (r"\b(usfda|fda|drug approval|product approval)\b", ["Product Approval"]),
    (r"\b(clinical trials?)\b", ["Clinical Trial"]),
]

ADVICE = re.compile(r"\b(should i (buy|sell|invest|hold)|is it (a )?good (time|stock)|(buy|sell) or (hold|sell|buy)|"
                    r"target price|price target|will .* (go up|rise|fall|crash)|recommend\w* (a |me )?stock|"
                    r"which stock (to|should)|best stocks?|multibagger)\b", re.I)
LIVE_PRICE = re.compile(r"\b(share price|stock price|current price|ltp|market cap(italisation)?|52[- ]week|"
                        r"price today|trading at)\b", re.I)
LIST_Q = re.compile(r"\b(which|list|all|how many|number of|count|every|companies that|companies who|any company|"
                    r"show me (all|the)|what companies)\b", re.I)
TOP_Q = re.compile(r"\b(top|most important|biggest|major|key|highlights?|summar(y|ise|ize)|what happened)\b", re.I)
COMPARE_Q = re.compile(r"\b(compare|comparison|versus|vs\.?|difference between|better than)\b", re.I)
GREETING = re.compile(r"^\s*(hi|hello|hey|namaste|good (morning|evening|afternoon)|thanks|thank you)\W*$", re.I)
HELP_Q = re.compile(r"\b(what can you do|help me|how (do|can) i use|who are you|what (data|do you know))\b", re.I)
FOLLOWUP = re.compile(r"\b(they|their|them|it|its|this company|that company|the company|same company)\b", re.I)

COMMON_WORDS = set("""a an and are as at be by for from has have in is it its of on or the to was were will with
all any are can get one two new out see top how why who what when which this that best good last next week day
days today yesterday results result order orders bank india share shares stock stocks company limited ltd group
news about tell me give show list buy sell hold price data more info filing filings nse bse sme ipo board meeting
power steel energy capital finance financial services motors auto tech
value total global first prime future smart great super united national general standard premier modern quality
golden royal supreme ideal select universal popular active dynamic perfect sterling latest recent details update
updates announced announcement amount record interim final approval approved plant battery agreement project
contract received declared issue market money credit rating growth income profit revenue bonus split merger
mobile digital green solar health care life wealth trust unique alpha star indian bharat hindustan""".split())


@dataclass
class ParsedQuery:
    text: str
    date_from: str | None = None
    date_to: str | None = None
    date_label: str = ""
    out_of_window: bool = False
    companies: list = field(default_factory=list)      # list of (company, ticker)
    tags: list = field(default_factory=list)
    intent: str = "lookup"     # lookup | list | top | compare | advice | live_price | greeting | help
    notes: list = field(default_factory=list)


def _norm(s):
    s = s.lower().replace("&", " and ")
    s = re.sub(r"\b(limited|ltd|pvt|private|the|inc|corporation|corp|co)\b\.?", " ", s)
    s = re.sub(r"[^a-z0-9 ]", " ", s)
    return re.sub(r"\s+", " ", s).strip()


class CompanyIndex:
    """Finds companies in free text: exact name, ticker, unique first word, or a typo."""

    def __init__(self, filings):
        self.by_alias = {}
        first_word = {}
        seen = {}
        for f in filings:
            key = (f["company"], f["ticker"])
            if key in seen:
                continue
            seen[key] = True
            n = _norm(f["company"])
            if n:
                self.by_alias[n] = key
                w = n.split()[0]
                first_word.setdefault(w, set()).add(key)
        # Unique leading word-prefixes: "zee entertainment" -> Zee Entertainment Enterprises Ltd
        prefix = {}
        for key in seen:
            words = _norm(key[0]).split()
            for n in range(2, len(words)):
                prefix.setdefault(" ".join(words[:n]), set()).add(key)
        for pfx, keys in prefix.items():
            if len(keys) == 1 and pfx not in self.by_alias:
                self.by_alias[pfx] = next(iter(keys))
        for w, keys in first_word.items():
            if len(keys) == 1 and len(w) >= 5 and w not in COMMON_WORDS and w not in self.by_alias:
                self.by_alias[w] = next(iter(keys))
        self.tickers = {}
        for (c, t) in seen:
            if t and len(t) >= 3 and t.lower() not in COMMON_WORDS:
                self.tickers[t.upper()] = (c, t)
        self.aliases = sorted(self.by_alias, key=len, reverse=True)

    def find(self, text):
        found, taken = [], []
        q = " " + _norm(text) + " "
        # 1) exact alias, longest first, so "tata motors" wins over "tata"
        for a in self.aliases:
            i = q.find(" " + a + " ")
            if i >= 0 and not any(s <= i < e for s, e in taken):
                taken.append((i, i + len(a) + 1))
                found.append(self.by_alias[a])
        # 2) tickers written in capitals (or long enough to be unambiguous)
        for tok in re.findall(r"[A-Za-z0-9&\-]{3,}", text):
            up = tok.upper()
            if up in self.tickers and (tok.isupper() or len(tok) >= 6):
                found.append(self.tickers[up])
        # 3) typo tolerance on 1-3 word windows ("infosis", "bajaj finserve")
        if not found:
            words = _norm(text).split()
            grams = {" ".join(words[i:i + n]) for n in (1, 2, 3) for i in range(len(words) - n + 1)}
            grams = {g for g in grams if len(g) >= 6 and g not in COMMON_WORDS}
            best = None
            for g in grams:
                for a in self.aliases:
                    if abs(len(a) - len(g)) > 3:
                        continue
                    s = fuzz.ratio(g, a)
                    if s >= 90 and (best is None or s > best[0]):
                        best = (s, a)
            if best:
                found.append(self.by_alias[best[1]])
        out = []
        for k in found:
            if k not in out:
                out.append(k)
        return out[:5]


def _d(x):
    return x.isoformat()


def parse_dates(text, anchor, first):
    """Returns (from, to, label, out_of_window). anchor = latest date in the data."""
    t = text.lower()
    if re.search(r"\b(last|previous|past) (month|year|quarter)\b", t):
        return None, None, "outside the 7-day window", True
    # "in 2021" / "during 2023" - a year said as a time period, not "2000 crore"
    years = re.findall(r"\b(?:in|of|year|during|since|from)\s+((?:19|20)\d\d)\b(?!\s*(?:crore|cr|lakh|shares|mn|%))", t)
    if any(int(y) != anchor.year for y in years):
        return None, None, "outside the 7-day window", True
    if re.search(r"\bday before yesterday\b", t):
        d = anchor - dt.timedelta(days=2)
        return _d(d), _d(d), d.strftime("%d %b"), False
    if re.search(r"\byesterday\b", t):
        d = anchor - dt.timedelta(days=1)
        return _d(d), _d(d), d.strftime("%d %b"), False
    if re.search(r"\btoday\b|\blatest day\b", t):
        return _d(anchor), _d(anchor), anchor.strftime("%d %b"), False
    m = re.search(r"\b(?:last|past|previous) (\d+) days?\b", t)
    if m:
        n = int(m.group(1))
        d = anchor - dt.timedelta(days=n - 1)
        label = f"last {n} days" if d >= first else f"last {n} days (I only have data from {first:%d %b})"
        return _d(max(d, first)), _d(anchor), label, False
    for i, w in enumerate(WEEKDAYS):
        if re.search(rf"\b(on |last )?{w}\b", t):
            back = (anchor.weekday() - i) % 7
            d = anchor - dt.timedelta(days=back)
            return _d(d), _d(d), d.strftime("%A %d %b"), d < first
    m = (re.search(r"\b(\d{1,2})(?:st|nd|rd|th)?\s*(?:of\s+)?(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\b", t)
         or re.search(r"\b(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\s+(\d{1,2})(?:st|nd|rd|th)?\b", t))
    if m:
        a, b = m.groups()
        day, mon = (int(a), MONTHS[b]) if a.isdigit() else (int(b), MONTHS[a])
        try:
            d = dt.date(anchor.year, mon, day)
            return _d(d), _d(d), d.strftime("%d %b"), not (first <= d <= anchor)
        except ValueError:
            pass
    m = re.search(r"\b(\d{4})-(\d{2})-(\d{2})\b", t)
    if m:
        d = dt.date(*map(int, m.groups()))
        return _d(d), _d(d), d.strftime("%d %b"), not (first <= d <= anchor)
    if re.search(r"\b(this|last|past) week\b|\b(7|seven) days\b", t):
        return _d(first), _d(anchor), "this week", False
    return None, None, "", False


def detect_tags(text):
    tags = []
    for pat, ts in TAG_WORDS:
        if re.search(pat, text, re.I):
            tags += [x for x in ts if x not in tags]
    return tags


def parse(text, companies: CompanyIndex, anchor: dt.date, first: dt.date) -> ParsedQuery:
    p = ParsedQuery(text=text)
    if GREETING.match(text):
        p.intent = "greeting"
        return p
    if HELP_Q.search(text):
        p.intent = "help"
        return p
    p.date_from, p.date_to, p.date_label, p.out_of_window = parse_dates(text, anchor, first)
    p.companies = companies.find(text)
    p.tags = detect_tags(text)
    if ADVICE.search(text):
        p.intent = "advice"
    elif LIVE_PRICE.search(text) and not p.tags:
        p.intent = "live_price"
    elif COMPARE_Q.search(text) or len(p.companies) >= 2:
        p.intent = "compare"
    elif LIST_Q.search(text) and not p.companies:
        p.intent = "list"
    elif TOP_Q.search(text) and not p.companies:
        p.intent = "top"
    return p
