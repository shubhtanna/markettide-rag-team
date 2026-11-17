"""
agent.py - Conversational Agent Core for Market Tide
Implements state management, intent classification, entity extraction,
tool execution, strict zero-hallucination relevance gates, and real-time streaming.
"""

import os
import re
from typing import Generator
from dotenv import load_dotenv

try:
    from .tools import MarketTools, STOPWORDS, DISALLOWED_SINGLE_WORDS, CORPORATE_INDICATORS
    from . import grounding
except ImportError:
    from tools import MarketTools, STOPWORDS, DISALLOWED_SINGLE_WORDS, CORPORATE_INDICATORS
    import grounding

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(BASE_DIR, ".env"))
load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# Foreign / non-NSE companies to catch proactively
FOREIGN_OR_NON_NSE = {
    "google": "Alphabet Inc. (Google) is listed on NASDAQ (USA) and does not file disclosures with the National Stock Exchange of India (NSE).",
    "alphabet": "Alphabet Inc. is listed on NASDAQ (USA) and does not file disclosures with the National Stock Exchange of India (NSE).",
    "apple": "Apple Inc. is listed on NASDAQ (USA) and does not file disclosures with the National Stock Exchange of India (NSE).",
    "microsoft": "Microsoft Corporation is listed on NASDAQ (USA) and does not file disclosures with the National Stock Exchange of India (NSE).",
    "amazon": "Amazon.com Inc. is listed on NASDAQ (USA) and does not file disclosures with the National Stock Exchange of India (NSE).",
    "tesla": "Tesla Inc. is listed on NASDAQ (USA) and does not file disclosures with the National Stock Exchange of India (NSE).",
    "meta": "Meta Platforms Inc. is listed on NASDAQ (USA) and does not file disclosures with the National Stock Exchange of India (NSE).",
    "facebook": "Meta Platforms Inc. (Facebook) is listed on NASDAQ (USA) and does not file disclosures with the National Stock Exchange of India (NSE).",
    "nvidia": "NVIDIA Corporation is listed on NASDAQ (USA) and does not file disclosures with the National Stock Exchange of India (NSE)."
}

# Major Benchmark NSE companies for deterministic zero-filing recognition
BENCHMARK_NSE_COMPANIES = {
    # IT & Tech
    "infosys": {"company": "Infosys Limited", "ticker": "INFY"},
    "infy": {"company": "Infosys Limited", "ticker": "INFY"},
    "tcs": {"company": "Tata Consultancy Services Limited", "ticker": "TCS"},
    "wipro": {"company": "Wipro Limited", "ticker": "WIPRO"},
    "hcl tech": {"company": "HCL Technologies Limited", "ticker": "HCLTECH"},
    "tech mahindra": {"company": "Tech Mahindra Limited", "ticker": "TECHM"},
    "zomato": {"company": "Zomato Limited", "ticker": "ZOMATO"},
    "swiggy": {"company": "Swiggy Limited", "ticker": "SWIGGY"},
    "paytm": {"company": "One97 Communications Limited", "ticker": "PAYTM"},
    "one97": {"company": "One97 Communications Limited", "ticker": "PAYTM"},
    "nykaa": {"company": "FSN E-Commerce Ventures Limited", "ticker": "NYKAA"},
    "ola electric": {"company": "Ola Electric Mobility Limited", "ticker": "OLAELEC"},
    
    # Banking & Financial Services
    "hdfc bank": {"company": "HDFC Bank Limited", "ticker": "HDFCBANK"},
    "icici bank": {"company": "ICICI Bank Limited", "ticker": "ICICIBANK"},
    "state bank of india": {"company": "State Bank of India", "ticker": "SBIN"},
    "sbin": {"company": "State Bank of India", "ticker": "SBIN"},
    "sbi": {"company": "State Bank of India", "ticker": "SBIN"},
    "kotak": {"company": "Kotak Mahindra Bank Limited", "ticker": "KOTAKBANK"},
    "axis bank": {"company": "Axis Bank Limited", "ticker": "AXISBANK"},
    "indusind": {"company": "IndusInd Bank Limited", "ticker": "INDUSINDBK"},
    "bajaj finance": {"company": "Bajaj Finance Limited", "ticker": "BAJFINANCE"},
    "bajaj finserv": {"company": "Bajaj Finserv Limited", "ticker": "BAJAJFINSV"},
    
    # FMCG, Retail, Auto, Pharma, Industrials, Energy, Metals
    "itc": {"company": "ITC Limited", "ticker": "ITC"},
    "hindustan unilever": {"company": "Hindustan Unilever Limited", "ticker": "HINDUNILVR"},
    "hul": {"company": "Hindustan Unilever Limited", "ticker": "HINDUNILVR"},
    "maruti": {"company": "Maruti Suzuki India Limited", "ticker": "MARUTI"},
    "l&t": {"company": "Larsen & Toubro Limited", "ticker": "LT"},
    "larsen": {"company": "Larsen & Toubro Limited", "ticker": "LT"},
    "bharti airtel": {"company": "Bharti Airtel Limited", "ticker": "BHARTIARTL"},
    "airtel": {"company": "Bharti Airtel Limited", "ticker": "BHARTIARTL"},
    "sun pharma": {"company": "Sun Pharmaceutical Industries Limited", "ticker": "SUNPHARMA"},
    "cipla": {"company": "Cipla Limited", "ticker": "CIPLA"},
    "dr reddy": {"company": "Dr. Reddy's Laboratories Limited", "ticker": "DRREDDY"},
    "titan": {"company": "Titan Company Limited", "ticker": "TITAN"},
    "asian paints": {"company": "Asian Paints Limited", "ticker": "ASIANPAINT"},
    "tata steel": {"company": "Tata Steel Limited", "ticker": "TATASTEEL"},
    "jsw steel": {"company": "JSW Steel Limited", "ticker": "JSWSTEEL"},
    "hindalco": {"company": "Hindalco Industries Limited", "ticker": "HINDALCO"},
    "ntpc": {"company": "NTPC Limited", "ticker": "NTPC"},
    "power grid": {"company": "Power Grid Corporation of India Limited", "ticker": "POWERGRID"},
    "coal india": {"company": "Coal India Limited", "ticker": "COALINDIA"},
    "ongc": {"company": "Oil and Natural Gas Corporation Limited", "ticker": "ONGC"},
    "adani enterprises": {"company": "Adani Enterprises Limited", "ticker": "ADANIENT"},
    "adani power": {"company": "Adani Power Limited", "ticker": "ADANIPOWER"},
    "adani green": {"company": "Adani Green Energy Limited", "ticker": "ADANIGREEN"},
    "adani ports": {"company": "Adani Ports and Special Economic Zone Limited", "ticker": "ADANIPORTS"},
    "dlf": {"company": "DLF Limited", "ticker": "DLF"}
}

# Major Conglomerate / Business House Groups for multi-organization resolution
CONGLOMERATE_GROUPS = {
    "tata": {
        "group_name": "Tata Group",
        "pattern": r'\b(tata\s+group|tata\s+companies|all\s+tata|tata)\b',
        "tickers": ['TATAPOWER', 'TMPV', 'TATASTEEL', 'TATACHEM', 'TATACOMM', 'TCS', 'TMCV', 'TTML']
    },
    "adani": {
        "group_name": "Adani Group",
        "pattern": r'\b(adani\s+group|adani\s+companies|all\s+adani|adani)\b',
        "tickers": ['ADANIENT', 'ADANIENSOL', 'ADANIPOWER']
    },
    "reliance": {
        "group_name": "Reliance Group",
        "pattern": r'\b(reliance\s+group|reliance\s+companies|all\s+reliance|reliance)\b',
        "tickers": ['RELIANCE', 'RELINFRA', 'RPOWER', 'RCOM']
    },
    "birla": {
        "group_name": "Aditya Birla Group",
        "pattern": r'\b(birla\s+group|birla\s+companies|aditya\s+birla|birla)\b',
        "tickers": ['ABCAPITAL', 'ABFRL', 'ABSLAMC', 'BIRLACORPN', 'BIRLAMONEY', 'BIRLANU']
    },
    "mahindra": {
        "group_name": "Mahindra Group",
        "pattern": r'\b(mahindra\s+group|mahindra\s+companies|all\s+mahindra|mahindra)\b',
        "tickers": ['M&M', 'TECHM', 'MAHLOG', 'M&MFIN', 'MHRIL', 'SMLMAH']
    },
    "godrej": {
        "group_name": "Godrej Group",
        "pattern": r'\b(godrej\s+group|godrej\s+companies|all\s+godrej|godrej)\b',
        "tickers": ['GODREJIND', 'GODREJPROP', 'GODREJAGRO']
    },
    "bajaj": {
        "group_name": "Bajaj Group",
        "pattern": r'\b(bajaj\s+group|bajaj\s+companies|all\s+bajaj|bajaj)\b',
        "tickers": ['BAJFINANCE', 'BAJAJFINSV', 'BAJAJHIND']
    }
}

# Subjective / Opinion Query Patterns (Strict Zero-Hallucination & Refusal)
SUBJECTIVE_OPINION_PATTERNS = [
    # is/are/was/were ... (good|bad|reliable|terrible|...)
    r'\b(is|are|was|were)\s+.*?\b(bad|good|evil|corrupt|fraud|scam|better|worse|best|worst|safe|risky|reliable|ethical|unethical|trustworthy|overvalued|undervalued|overpriced|underpriced|terrible|horrible|poor|solid|shady|going\s+to\s+crash|worth\s+(?:it|buying|investing))\b',
    # is [entity] a (good|bad|...) company/stock
    r'\b(is|are)\s+.*?\b(good|bad|great|terrible|horrible|poor|solid|shady|best|worst)\s+(company|stock|business|firm|group|investment)\b',
    # good or bad / bad or good / true or false / fraud rumors
    r'\b(good\s+or\s+bad|bad\s+or\s+good|good\s+company|bad\s+company|good\s+stock|bad\s+stock|worst\s+company|best\s+company|true\s+or\s+false|fraud\s+rumors?|rumors?|worst\s+investment)\b',
    # opinion / view / sentiment / think of / recommendation
    r'\b(?:personal\s+)?(?:opinion|view|views|take|sentiment)\s+on\b',
    r'\bwhat\s+(?:is\s+your|do\s+you)\s+(?:personal\s+)?(?:opinion|think|view|views|take)\b',
    r'\bdo\s+you\s+like\b',
    r'\b(?:personal\s+)?recommendation\b',
    r'\bdo\s+you\s+recommend\b',
    # why is ... (bad|good|failing|crashing|dropping|falling)
    r'\bwhy\s+is\s+.*?\b(bad|good|evil|corrupt|falling|dropping|crashing|failing)\b',
    # should i buy / should i sell / should i invest / best stock to buy
    r'\b(?:should\s+i|shall\s+i|can\s+i)\s+(?:buy|sell|invest)\b',
    r'\b(?:best|worst)\s+stock\s+to\s+buy\b',
    r'\b(should\s+i\s+trust|reputation\s+of|is\s+it\s+worth\s+buying|is\s+it\s+worth\s+investing|would\s+you\s+recommend)\b',
]

# Out-of-Domain and Greeting Patterns for strict domain boundary enforcement
OUT_OF_DOMAIN_PATTERNS = [
    # Non-filing market data: stock quotes, prices, market hours, demat / trading tutorials
    r'\b(stock\s+price|share\s+price|current\s+price|trading\s+price|market\s+price|target\s+price|live\s+quote|52\s+week\s+high|52\s+week\s+low|pe\s+ratio|market\s+cap\s+of)\b',
    r'\b(is\s+the\s+market\s+open|market\s+hours|trading\s+hours|market\s+timing|market\s+holiday|trading\s+holiday|open\s+today|closed\s+today)\b',
    r'\b(how\s+do\s+i\s+buy\s+shares|how\s+to\s+buy\s+stocks|how\s+to\s+invest|open\s+demat|demat\s+account|brokerage|zerodha|groww|upstox|angel\s+one)\b',
    r'\b(gold\s+price|silver\s+price|crude\s+oil|brent\s+crude|forex|usdinr|inrusd|currency\s+exchange)\b',
    r'\b(nifty\s+today|sensex\s+today|market\s+crash|recession|inflation\s+rate|interest\s+rate\s+in\s+india)\b',

    # Sports: cricket, athletes, coaches, tennis, football, Olympics
    r'\b(cricket|ipl(?!\s+pesticides)|fifa|world\s*cup|football|soccer|tennis|wimbledon|badminton|olympics?|premier\s+league|champions\s+league)\b',
    r'\b(virat\s+kohli|rohit\s+sharma|ms\s+dhoni|sachin\s+tendulkar|messi|ronaldo|le\s*bron|federer|nadal|djokovic|babar\s+azam|gavaskar|gambhir|neeraj\s+chopra|javelin|athlete|coach)\b',
    r'\b(live\s+score|match\s+score|batting|bowling|wicket|goal\s+scorer|tournament|grand\s+slam|commentary)\b',
    
    # Celebrities / Entertainment (Negative lookahead prevents hijacking legitimate NSE companies)
    r'\b(taylor\s+swift|shah\s*rukh\s*khan|deepika\s+padukone|salman\s+khan|aamir\s+khan|amitabh\s+bachchan|ranbir\s+kapoor|alia\s+bhatt|katrina\s+kaif|beyonce|drake|eminem|justin\s+bieber|tom\s+cruise|leonardo\s+dicaprio|zuckerberg|mark\s+zuckerberg|elon\s+musk|jeff\s+bezos|bill\s+gates)\b',
    r'\b(movie|movies|film(?!\s+(?:international|limited|ltd))|films(?!\s+(?:limited|ltd|filings|announcements))|cinema|box\s*office|bollywood|hollywood|actor|actress|celebrity(?!\s+fashions)|celebrities|album|singer(?!\s+india)|song|songs|grammy|oscar|oscars|emmy)\b',
    
    # Non-NSE Crypto & Foreign Macroeconomics
    r'\b(bitcoin|ethereum|crypto|cryptocurrency|blockchain|proof\s+of\s+stake|halving)\b',
    r'\b(bretton\s+woods|federal\s+reserve|bank\s+of\s+england|monetary\s+policy)\b',

    # General world trivia / weather / science / politics
    r'\b(weather|temperature|forecast|rain\s+in|humidity|climate)\b',
    r'\b(capital\s+of|president\s+of|presidential\s+address|prime\s+minister|narendra\s+modi|joe\s+biden|donald\s+trump|kamala\s+harris|vladimir\s+putin|british\s+monarchy|wears\s+the\s+crown)\b',
    r'\b(how\s+many\s+continents|tallest\s+mountain|mount\s+everest|longest\s+river|population\s+of|gdp\s+of|prime\s+meridian|equator|latitude|longitude|geography|map\s+of)\b',
    r'\b(photosynthesis|quantum\s+computing|quantum\s+physics|speed\s+of\s+light|theory\s+of\s+relativity|black\s*holes?|dna|mitochondria|solar\s+system|planet|mars|moon|gravity|gravitational\s+force|thermodynamics|astronomy|astrophysics|telescope|galaxy(?!\s+(?:medicare|infotech))|galaxies|universe|hardness\s+of\s+diamond|boiling\s+point|why\s+is\s+the\s+sky)\b',
    
    # Recipes / cooking / everyday tasks / creative writing / chitchat
    r'\b(how\s+to\s+(?:make|bake|cook|prepare|boil|clean|drive)|recipe|bake\s+a\s+cake|chocolate\s+chip|cookies|make\s+tea|brew\s+coffee|ingredients\s+for|butter\s+chicken|pizza|dough|pasta|burger|samosa|biryani|boil\s+eggs?|clean\s+a\s+greasy\s+oven|birthday\s+gift|bicycle\s+chain|submarine\s+expedition)\b',
    r'\b(tell\s+(me\s+)?a\s+joke|joke|funny|riddle|pun)\b',
    r'\b(write\s+(me\s+)?a\s+(poem|story|song|essay|haiku|script))\b',
    r'\b(who\s+are\s+you|who\s+made\s+you|what\s+is\s+your\s+name|are\s+you\s+an\s+ai|are\s+you\s+human|tell\s+me\s+about\s+yourself|what\s+time\s+is\s+it)\b',
    
    # Coding / computer science
    r'\b(python\s+(code|function|script|program)|write\s+(a\s+)?(?:python\s+)?(?:function|code|script)|quicksort|quick\s*sort|merge\s*sort|bubble\s*sort|sorting\s+algorithm|binary\s+tree|binary\s*search|reverse\s+a\s+linked\s+list|leetcode|javascript|typescript|c\+\+|java\s+code|html|css|sql\s+query|regex\s+pattern|debug\s+this\s+code|quadratic\s+equation|in\s+python)\b',
    r'\b(what\s+is\s+machine\s+learning|what\s+is\s+deep\s+learning|what\s+is\s+artificial\s+intelligence|how\s+does\s+neural\s+network\s+work|backpropagation)\b'
]

GREETING_PATTERNS = [
    r'^(hi|hello|hey|good\s+(morning|afternoon|evening)|namaste|greetings|howdy|what\'?s\s+up|sup|hola)[\s!.,?]*$',
    r'^(hi|hello|hey|good\s+(morning|afternoon|evening)|namaste)[\s!.,?]+(how\s+are\s+you|how\s+are\s+you\s+today|how\'?re\s+you)[\s!.,?]*$',
    r'^(how\s+are\s+you|how\s+are\s+you\s+today|how\s+do\s+you\s+do)[\s!.,?]*$'
]


class MarketTideAgent:
    def __init__(self):
        self.tools = MarketTools()
        self.client = None
        self.last_result = None          # grounding.Result of the latest answered question (for the UI trace)
        if GROQ_API_KEY:
            try:
                from groq import Groq
                self.client = Groq(api_key=GROQ_API_KEY)
            except Exception as e:
                print(f"Groq initialization notice: {e}")

    def resolve_high_confidence_company(self, query: str) -> list[dict]:
        """
        Stage 1 Entity Resolution (Evaluated BEFORE Out-of-Domain Guardrails):
        Only resolves when there is unambiguous, high-confidence evidence of an NSE entity:
        1. Query matches a recognized benchmark NSE company (e.g. Infosys, TCS, SBIN).
        2. Query matches 2 or more distinct significant words of a company name in the dataset
           (e.g., 'Celebrity Fashions', 'Singer India', 'Inspire Films', 'Galaxy Medicare').
        3. Query contains an exact ticker WITH an explicit corporate indicator (or is strictly the ticker).
        4. Query contains a single distinctive company name WITH an explicit corporate indicator.
        Suppresses loose single-word matches for ordinary words without corporate context.
        """
        q_lower = query.lower().strip()
        raw_words = re.findall(r'[a-zA-Z0-9]+', q_lower)
        words = [w for w in raw_words if w not in STOPWORDS and len(w) >= 3]
        if not words:
            return []

        has_corp_indicator = (
            any(w in CORPORATE_INDICATORS for w in raw_words) or
            ("nse:" in q_lower or "bse:" in q_lower)
        )

        # 1. Benchmark NSE company check
        for benchmark_key, meta in BENCHMARK_NSE_COMPANIES.items():
            if re.search(r'\b' + re.escape(benchmark_key) + r'\b', q_lower):
                exact_in_df = self.tools.df[self.tools.df['ticker'].str.upper() == meta['ticker']]
                count = len(exact_in_df)
                comp_name = exact_in_df.iloc[0]['company'] if count > 0 else meta["company"]
                return [{
                    "ticker": meta["ticker"],
                    "company": comp_name,
                    "count": count,
                    "benchmark": True
                }]

        # 2. Multi-word phrase matching against sorted company phrases
        for p in self.tools.sorted_phrases:
            if re.search(r'\b' + re.escape(p) + r'\b', q_lower):
                candidates = self.tools.phrase_to_comps[p]
                summary = []
                for ticker, comp in candidates:
                    count = len(self.tools.df[self.tools.df['ticker'] == ticker])
                    summary.append({"ticker": ticker, "company": comp, "count": count})
                return sorted(summary, key=lambda x: x['count'], reverse=True)

        # 3. Multi-word pair search (requires >= 2 distinct matching words)
        if len(words) >= 2:
            # If the query matches OUT_OF_DOMAIN_PATTERNS without an explicit corporate indicator, DO NOT pair-match!
            if not has_corp_indicator and any(re.search(pat, q_lower) for pat in OUT_OF_DOMAIN_PATTERNS):
                return []
            for i in range(len(words)):
                for j in range(i + 1, len(words)):
                    w1, w2 = words[i], words[j]
                    if w1 in DISALLOWED_SINGLE_WORDS and w2 in DISALLOWED_SINGLE_WORDS and not has_corp_indicator:
                        continue
                    mask = (
                        self.tools.df['company'].str.lower().str.contains(r'\b' + re.escape(w1) + r'\b', regex=True, na=False) &
                        self.tools.df['company'].str.lower().str.contains(r'\b' + re.escape(w2) + r'\b', regex=True, na=False)
                    )
                    m = self.tools.df[mask]
                    if not m.empty:
                        summary = []
                        for ticker, group in m.groupby('ticker'):
                            summary.append({
                                "ticker": ticker,
                                "company": group.iloc[0]['company'],
                                "count": len(group)
                            })
                        return sorted(summary, key=lambda x: x['count'], reverse=True)

        # 4. Exact ticker match (restricted: dictionary/common words REQUIRE corporate indicator)
        for w in words:
            w_upper = w.upper()
            if w in DISALLOWED_SINGLE_WORDS and not (has_corp_indicator or f"nse:{w}" in q_lower or f"bse:{w}" in q_lower):
                continue
            exact_ticker = self.tools.df[self.tools.df['ticker'].str.upper() == w_upper]
            if not exact_ticker.empty:
                if has_corp_indicator or len(words) == 1 or w not in DISALLOWED_SINGLE_WORDS:
                    return [{
                        "ticker": w_upper,
                        "company": exact_ticker.iloc[0]['company'],
                        "count": len(exact_ticker)
                    }]

        # 5. Single company word match ONLY with explicit corporate indicator
        if has_corp_indicator:
            for w in words:
                if len(w) >= 4 and w not in DISALLOWED_SINGLE_WORDS:
                    matches = self.tools.df[
                        self.tools.df['company'].str.lower().str.contains(r'\b' + re.escape(w) + r'\b', regex=True, na=False) |
                        (self.tools.df['ticker'].str.lower() == w)
                    ]
                    if not matches.empty:
                        summary = []
                        for ticker, group in matches.groupby('ticker'):
                            summary.append({
                                "ticker": ticker,
                                "company": group.iloc[0]['company'],
                                "count": len(group)
                            })
                        return sorted(summary, key=lambda x: x['count'], reverse=True)

        return []

    def classify_intent_and_entities(self, query: str) -> dict:
        """Classify user intent and extract key entities using multi-word pattern matching."""
        q = query.strip()
        q_lower = q.lower()
        q_clean = re.sub(r'[^a-zA-Z0-9\s]', ' ', q_lower)
        q_clean = re.sub(r'\s+', ' ', q_clean).strip()

        # 1. Greeting check
        if any(re.match(pat, q_lower) for pat in GREETING_PATTERNS):
            return {"intent": "GREETING", "entities": {}}

        # 1b. Subjective / Opinion Query check (Evaluated BEFORE entity & conglomerate resolution)
        if any(re.search(pat, q_lower) or re.search(pat, q_clean) for pat in SUBJECTIVE_OPINION_PATTERNS):
            return {"intent": "SUBJECTIVE_OPINION", "entities": {}}

        # 2. Non-NSE / Global tech check (Foreign issuers proactively caught before local company searches)
        for foreign_key, explanation in FOREIGN_OR_NON_NSE.items():
            if re.search(r'\b' + re.escape(foreign_key) + r'\b', q_lower):
                return {"intent": "NON_NSE", "entities": {"entity": foreign_key.title(), "explanation": explanation}}

        # 3. Comparison query check (e.g. "compare A and B" or "A vs B")
        comp_match = re.search(r"compare\s+([a-zA-Z0-9\s]+?)\s+(?:and|with|vs)\s+([a-zA-Z0-9\s]+)", q, re.IGNORECASE)
        vs_match = re.search(r"([a-zA-Z0-9\s]+?)\s+vs\s+([a-zA-Z0-9\s]+)", q, re.IGNORECASE)
        if comp_match:
            return {"intent": "COMPARISON", "entities": {"comp_a": comp_match.group(1).strip(), "comp_b": comp_match.group(2).strip()}}
        if vs_match:
            return {"intent": "COMPARISON", "entities": {"comp_a": vs_match.group(1).strip(), "comp_b": vs_match.group(2).strip()}}

        # 3b. Non-filing queries (live quotes, stock price, market hours, how to buy shares)
        # Evaluated BEFORE company search to prevent answering quote questions with filing docs
        live_market_data_patterns = [
            r'\b(stock\s+price|share\s+price|current\s+price|trading\s+price|market\s+price|live\s+quote|52\s+week\s+high|52\s+week\s+low|pe\s+ratio|market\s+cap\s+of)\b',
            r'\b(is\s+the\s+market\s+open|market\s+hours|trading\s+hours|market\s+timing|market\s+holiday|trading\s+holiday|open\s+today|closed\s+today)\b',
            r'\b(how\s+do\s+i\s+buy\s+shares|how\s+to\s+buy\s+stocks|how\s+to\s+invest|open\s+demat|demat\s+account|brokerage|zerodha|groww|upstox|angel\s+one)\b'
        ]
        if any(re.search(pat, q_lower) for pat in live_market_data_patterns):
            return {"intent": "OUT_OF_DOMAIN", "entities": {}}

        # 4. Stage 1: High-Confidence Entity Check (Multi-word company or exact ticker with context)
        # Evaluated BEFORE Out-of-Domain to protect companies like Celebrity Fashions, Singer India, Inspire Films
        stage1_resolved = self.resolve_high_confidence_company(q)
        if stage1_resolved:
            return {"intent": "COMPANY", "entities": {"resolved": stage1_resolved}}

        # 4b. Conglomerate / Group Resolution (e.g. Tata, Adani, Reliance, Birla, Mahindra, Godrej, Bajaj)
        # When user asks about a business house or umbrella name, resolve ALL affiliated organizations!
        for group_key, group_meta in CONGLOMERATE_GROUPS.items():
            if re.search(group_meta["pattern"], q_lower):
                group_resolved = []
                for ticker in group_meta["tickers"]:
                    comp_rows = self.tools.df[self.tools.df['ticker'].str.upper() == ticker]
                    if not comp_rows.empty:
                        comp_name = comp_rows.iloc[0]['company']
                        count = len(comp_rows)
                        group_resolved.append({
                            "ticker": ticker,
                            "company": comp_name,
                            "count": count
                        })
                if group_resolved:
                    return {
                        "intent": "COMPANY",
                        "entities": {
                            "resolved": group_resolved,
                            "group_name": group_meta["group_name"]
                        }
                    }

        # 5. Out-of-domain check (sports, celebrities, weather, science, geography, cooking, coding, chitchat)
        if any(re.search(pat, q_lower) for pat in OUT_OF_DOMAIN_PATTERNS):
            return {"intent": "OUT_OF_DOMAIN", "entities": {}}

        # 6. Financial advice / stock tip check (Compliance)
        advice_triggers = ["should i buy", "should i sell", "target price", "buy or sell", "multibagger", "price forecast", "good time to invest", "invest in"]
        if any(trig in q_lower for trig in advice_triggers):
            return {"intent": "ADVICE", "entities": {}}

        # 7. Out of window check
        years = re.findall(r"\b(20[0-1][0-9]|202[0-5]|202[7-9])\b", q)
        if years or "last year" in q_lower or "2024" in q_lower or "2025" in q_lower or "last month" in q_lower:
            return {"intent": "OUT_OF_WINDOW", "entities": {"years": years}}

        # 8. Top high-impact filings check
        if any(w in q_lower for w in ["top 5", "top filings", "high impact", "high-impact", "biggest news", "most important"]):
            return {"intent": "TOP_FILINGS", "entities": {}}

        # 9. Stage 2: Standard Company Resolution (for single distinctive names without OOD conflict)
        resolved = self.tools.resolve_company(q)
        if resolved:
            return {"intent": "COMPANY", "entities": {"resolved": resolved}}

        # 10. Category filter check
        if any(w in q_lower for w in ["buyback", "buy back", "buy-back"]):
            return {"intent": "CATEGORY", "entities": {"category": "Buyback"}}
        if any(w in q_lower for w in ["dividend", "interim dividend", "bonus"]):
            return {"intent": "CATEGORY", "entities": {"category": "Dividend"}}
        if any(w in q_lower for w in ["order win", "contract", "orders", "won order", "awarded"]):
            return {"intent": "CATEGORY", "entities": {"category": "Order"}}
        if any(w in q_lower for w in ["management", "director", "resignation", "appointment", "ceo", "cfo"]):
            return {"intent": "CATEGORY", "entities": {"category": "Change in Management"}}

        return {"intent": "GENERAL", "entities": {}}

    def is_financial_or_corporate_query(self, query: str, intent_data: dict) -> bool:
        """
        Determines whether a query is financial / corporate in nature.
        Used when documents are empty to distinguish between:
        - Genuinely in-scope company with 0 filings -> emit "No Matching Announcements Found"
        - General trivia / non-financial question -> emit "Domain Scope Refusal"
        """
        if intent_data.get("intent") in {"COMPANY", "CATEGORY", "TOP_FILINGS", "COMPARISON"}:
            return True
        if intent_data.get("entities", {}).get("resolved"):
            return True

        q_lower = query.lower()
        raw_words = re.findall(r'[a-zA-Z0-9]+', q_lower)

        # Check explicit corporate indicators
        if any(w in CORPORATE_INDICATORS for w in raw_words):
            return True

        # Check financial terms
        financial_terms = {
            "quarterly", "annual", "promoter", "stake", "debt", "equity", "revenue",
            "ebitda", "profit", "loss", "pat", "margin", "guidance", "sebi", "exchange",
            "investor", "valuation", "balance", "sheet", "cashflow", "merger", "acquisition"
        }
        if any(w in financial_terms for w in raw_words):
            return True

        # Check recognized company tickers or benchmark keys
        for key in BENCHMARK_NSE_COMPANIES:
            if re.search(r'\b' + re.escape(key) + r'\b', q_lower):
                return True

        return False

    def execute_tools(self, intent_data: dict, query: str, use_hybrid: bool = True) -> tuple[list[dict], str]:
        """Execute tool and enforce strict relevance boundaries."""
        intent = intent_data["intent"]
        entities = intent_data.get("entities", {})

        if intent == "GREETING":
            return [], "greeting"

        if intent == "SUBJECTIVE_OPINION":
            return [], "subjective_opinion"

        if intent == "OUT_OF_DOMAIN":
            return [], "out_of_domain"

        if intent == "NON_NSE":
            return [], f"non_nse:{entities.get('entity')}"

        if intent == "ADVICE":
            resolved = entities.get("resolved") or self.tools.resolve_company(query)
            if resolved:
                docs = self.tools.get_company_filings(resolved[0]["ticker"], top_k=4)
                return docs, f"compliance_advice:{resolved[0]['company']} ({resolved[0]['ticker']})"
            return [], "compliance_advice:general"

        if intent == "OUT_OF_WINDOW":
            return [], "out_of_window"

        if intent == "COMPARISON":
            comp_a = entities.get("comp_a", "")
            comp_b = entities.get("comp_b", "")
            res_comp = self.tools.compare_two_companies(comp_a, comp_b, top_k=3)
            combined_docs = res_comp["company_a"]["filings"] + res_comp["company_b"]["filings"]
            return combined_docs, f"comparison:{comp_a}_vs_{comp_b}"

        if intent == "CATEGORY":
            cat = entities.get("category", "")
            docs = self.tools.filter_by_category(cat, min_score=45, top_k=grounding.MAX_EVIDENCE)
            return docs, f"category:{cat}"

        if intent == "TOP_FILINGS":
            docs = self.tools.get_top_high_impact(top_k=6)
            return docs, "top_filings"

        if intent == "COMPANY":
            resolved = entities.get("resolved", [])
            if not resolved:
                return [], "company:not_found"

            # Multi-organization / Conglomerate group query (e.g. Tata, Adani, Reliance)
            # Retrieve filings across ALL affiliated organizations!
            if len(resolved) > 1:
                all_docs = []
                tickers_included = []
                for comp in resolved:
                    t = comp.get("ticker")
                    if not t:
                        continue
                    # Fetch all filings for each organization in the group (up to 4 per company)
                    comp_filings = self.tools.get_company_filings(t, top_k=4)
                    if comp_filings:
                        all_docs.extend(comp_filings)
                        tickers_included.append(t)

                if all_docs:
                    # Sort combined filings by importance score and date
                    all_docs = sorted(all_docs, key=lambda x: (x.get('importance_score', 0), x.get('date', '')), reverse=True)
                    group_name = entities.get("group_name") or resolved[0]['company'].split()[0]
                    context_label = f"group:{group_name} ({len(tickers_included)} Organizations: {', '.join(tickers_included)})"
                    return all_docs, context_label

            # Single confirmed company
            ticker = resolved[0]["ticker"]
            docs = self.tools.get_company_filings(ticker, top_k=6)
            return docs, f"company:{resolved[0]['company']} ({ticker})"

        # General hybrid search with strict relevance cutoff
        docs = self.tools.hybrid_search(query, top_k=6, use_hybrid=use_hybrid)
        return docs, "general_hybrid"

    def format_prompt(self, query: str, docs: list[dict], tool_context: str, chat_history: list[dict]) -> tuple[str, str]:
        """Construct prompt with system rules, sliding history, and verified context."""
        system_prompt = (
            "You are the Market Tide Financial Intelligence Desk, an institutional research terminal for Indian stock market investors (NSE).\n"
            "DATA COVERAGE: Strictly 7 days of official NSE corporate announcements (Nov 9, 2026 to Nov 15, 2026).\n\n"
            "CRITICAL ACCURACY & DOMAIN BOUNDARY RULES:\n"
            "1. TONE: Direct, authoritative, quantitative, Wall Street / Dalal Street research desk style. Zero AI conversational filler.\n"
            "2. CITATIONS: State exact Company Name, Ticker (e.g. [NSE: ADANIPOWER]), Category, and Date for every claim.\n"
            "3. CONGLOMERATE / GROUP INQUIRIES: When analyzing a business group or conglomerate (e.g. Tata, Adani, Reliance), you MUST present disclosures across ALL affiliated organizations present in the evidence. Organize disclosures clearly by entity in a clean markdown table: [Company (Ticker) | Date | Category | Key Highlight]. Do not omit any organization.\n"
            "4. EARNINGS / RESULTS: Break down into '🟢 Growth & Bull Signals' and '🔴 Risk & Red Flags'.\n"
            "5. STRICT DOMAIN BOUNDARY & ZERO-KNOWLEDGE REFUSAL: Market Tide is strictly restricted to official NSE corporate announcements. Never answer general world knowledge, sports, celebrity, live stock prices, market hours, weather, coding, or trivia questions. If a query is outside the scope of NSE corporate filings, output EXACTLY: 'I don't know. That is not present in the 7-day NSE filings database (Nov 9–15, 2026).' Do NOT apologize, do NOT say 'Refusal:', do NOT explain why, and do NOT provide any world knowledge.\n"
            "6. STRICT EVIDENCE GROUNDING: If the provided documents do not answer the user's specific question, or if no filings match, output EXACTLY: 'I don't know. That is not present in the 7-day NSE filings database (Nov 9–15, 2026).' NEVER invent announcements, hallucinate filings, or discuss unrelated companies."
        )

        context_str = self.tools.retriever.format_context(docs)

        history_str = ""
        recent_history = [m for m in chat_history if m.get("role") in ["user", "assistant"]][-4:]
        if recent_history:
            history_str = "\nRECENT CONVERSATION HISTORY:\n" + "\n".join([f"{m['role'].upper()}: {m['content']}" for m in recent_history]) + "\n"

        user_content = (
            f"{history_str}\n"
            f"TOOL EXECUTION CONTEXT: {tool_context}\n"
            f"VERIFIED NSE FILING EVIDENCE (Nov 9-15, 2026):\n{context_str}\n\n"
            f"USER QUERY: {query}\n\n"
            f"INTELLIGENCE BRIEFING:"
        )

        return system_prompt, user_content

    def stream_response(self, query: str, chat_history: list[dict] = None, use_hybrid: bool = True) -> Generator[str, None, tuple[list[dict], str]]:
        """Stream response tokens in real-time, yielding chunks for st.write_stream."""
        if chat_history is None:
            chat_history = []
        self.last_result = None

        # 1. Intent recognition & entity extraction
        intent_data = self.classify_intent_and_entities(query)

        # Immediate shortcut for GREETING (zero retriever calls)
        if intent_data["intent"] == "GREETING":
            def msg_gen():
                msg = (
                    "Welcome to the Market Tide Institutional Terminal. "
                    "Ask me about any NSE corporate filings, board meeting outcomes, "
                    "quarterly results, dividends, or buybacks filed between Nov 9 and Nov 15, 2026."
                )
                for word in msg.split(" "):
                    yield word + " "
            return msg_gen(), [], "greeting"

        # Immediate shortcut for SUBJECTIVE_OPINION (strict zero-hallucination refusal)
        if intent_data["intent"] == "SUBJECTIVE_OPINION":
            def msg_gen():
                msg = (
                    "I don't know. That is not present in the 7-day NSE filings database (Nov 9–15, 2026).\n\n"
                    "Corporate statutory filings contain factual disclosures rather than subjective opinions."
                )
                for word in msg.split(" "):
                    yield word + " "
            return msg_gen(), [], "subjective_opinion"

        # Immediate shortcut for OUT_OF_DOMAIN (sports, celebrities, trivia, weather, cooking, jokes, coding)
        if intent_data["intent"] == "OUT_OF_DOMAIN":
            def msg_gen():
                msg = (
                    "I don't know. That is not present in the 7-day NSE filings database (Nov 9–15, 2026).\n\n"
                    "Corporate statutory filings contain factual disclosures rather than subjective opinions or queries outside our operational scope."
                )
                for word in msg.split(" "):
                    yield word + " "
            return msg_gen(), [], "out_of_domain"

        # Immediate shortcut for non-NSE / foreign entities (e.g. Google, Apple)
        if intent_data["intent"] == "NON_NSE":
            entity = intent_data["entities"].get("entity", "That company")
            explanation = intent_data["entities"].get("explanation")
            if not explanation:
                explanation = f"{entity} is listed on foreign exchanges (such as NASDAQ/NYSE) and does not file disclosures with the National Stock Exchange of India (NSE)."
            def msg_gen():
                msg = (
                    "I don't know. That is not present in the 7-day NSE filings database (Nov 9–15, 2026).\n\n"
                    f"{explanation}"
                )
                for word in msg.split(" "):
                    yield word + " "
            return msg_gen(), [], "non_nse"

        # Immediate shortcut for out-of-window
        if intent_data["intent"] == "OUT_OF_WINDOW":
            def msg_gen():
                msg = (
                    "I don't know. That is not present in the 7-day NSE filings database (Nov 9–15, 2026).\n\n"
                    "I only have data for the 7-day window from Nov 9 to Nov 15, 2026. "
                    "Filings from other dates are outside our operational scope."
                )
                for word in msg.split(" "):
                    yield word + " "
            return msg_gen(), [], "out_of_window"

        # 2. Execute tools
        docs, tool_context = self.execute_tools(intent_data, query, use_hybrid=use_hybrid)

        # 2b. Semantic Entity Mismatch Gate:
        # If the query inquired about a specific company entity (e.g., Infosys),
        # but NONE of the retrieved documents contain that entity: suppress unrelated docs!
        resolved = intent_data.get("entities", {}).get("resolved", [])
        if resolved:
            target_tickers = {c.get("ticker", "").upper() for c in resolved if c.get("ticker")}
            target_comps = [c.get("company", "").lower() for c in resolved if c.get("company")]
            if docs and not any(
                d.get("ticker", "").upper() in target_tickers or
                any(tc in d.get("company", "").lower() for tc in target_comps)
                for d in docs
            ):
                docs = []
                tool_context = "no_matches"

        # 3. Handle when zero documents match (DO NOT SHOW UNRELATED SOURCES!)
        if not docs:
            resolved = intent_data.get("entities", {}).get("resolved", [])
            comp_name = resolved[0]["company"] if resolved and isinstance(resolved, list) and resolved[0].get("company") else None

            def msg_gen():
                if comp_name:
                    msg = (
                        "I don't know. That is not present in the 7-day NSE filings database (Nov 9–15, 2026).\n\n"
                        f"No announcements were published by {comp_name} during the 7-day reporting window (Nov 9–15, 2026)."
                    )
                else:
                    msg = (
                        "I don't know. That is not present in the 7-day NSE filings database (Nov 9–15, 2026).\n\n"
                        "Corporate statutory filings contain factual disclosures rather than subjective opinions or queries outside our operational scope."
                    )
                for word in msg.split(" "):
                    yield word + " "
            return msg_gen(), [], "no_matches"

        # 4. Handle compliance advice with docs
        if intent_data["intent"] == "ADVICE":
            def msg_gen():
                msg = (
                    "**⚖️ SEBI / Regulatory Compliance Notice**\n\n"
                    "Market Tide is an automated filing intelligence tool, not a registered investment advisor. "
                    "We do not provide buy, sell, or target price recommendations.\n\n"
                    "Here are the objective, verified official disclosures filed for this entity in the 7-day window:"
                )
                for word in msg.split(" "):
                    yield word + " "
            return msg_gen(), docs, tool_context

        # 5. Grounded answer (MedEvolv Mentor pattern): numbered evidence -> temperature-0 draft that must cite
        #    every claim -> deterministic fact check -> one validated rewrite or drop the failing sentences ->
        #    decline if nothing verified remains. The whole answer is checked BEFORE anything is shown.
        facts = []
        if intent_data["intent"] == "CATEGORY":
            cat = intent_data.get("entities", {}).get("category", "")
            total = len(self.tools.filter_by_category(cat, min_score=45, top_k=100000))
            shown = min(len(docs), grounding.MAX_EVIDENCE)
            if total > shown:
                facts.append(f"{total} filings in the database match '{cat}' (importance score 45 or more). "
                             f"Only the {shown} most important are given as passages here, so any list built from "
                             f"them shows {shown} of {total}.")
        # A bare name ("Tata", "Kaynes Tech") is not a question; the strict prompt would rightly call it
        # unanswerable. It means "what did this company/group announce?", so ask exactly that.
        llm_query = query
        if intent_data["intent"] == "COMPANY" and len(query.split()) <= 3 and not query.rstrip().endswith("?"):
            llm_query = f"What did {query.strip()} announce in these filings? Summarise each filing in one bullet."
        result = grounding.answer(self.client, llm_query, docs, chat_history, facts)
        self.last_result = result
        shown_docs = [e.doc for e in result.evidence if e.doc is not None]

        def verified_stream():
            for piece in re.split(r"(\s+)", result.text):
                if piece:
                    yield piece

        return verified_stream(), shown_docs, tool_context
