"""Builds site/index.html: a static, read-only copy of the Market Tide home page.

Numbers on the page come from data/filings_last_7_days.csv, sample cards from
site/_samples.json. Nothing on the page is clickable except the Chatbot buttons.

    python tools/build_home.py
"""
import csv
import html
import json
import pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
rows = list(csv.DictReader(open(ROOT / "data" / "filings_last_7_days.csv", encoding="utf-8")))
samples = json.load(open(ROOT / "site" / "_samples.json", encoding="utf-8"))[:3]
e = html.escape

# Total pulled from NSE before filtering (from the export run) and kept after.
SCANNED = 5399
kept = len(rows)
days = len({r["date"] for r in rows})
cats = len({r["tag"] for r in rows})
start, end = min(r["date"] for r in rows), max(r["date"] for r in rows)

ticker = [r for r in rows if r["tag"] not in ("Results", "Investor Meet", "Concall", "Outcome")][:14]
tick_html = "".join(
    f'<span class="tick"><span class="tk">{e(t["tag"])}</span><b>{e(t["company"])}</b><span>{e(t["date"])}</span></span>'
    for t in ticker + ticker)


def card(s):
    imp = s.get("impact") or ""
    cls = {"Positive": "pos", "Negative": "neg"}.get(imp, "neu")
    nums = "".join(f'<span class="num">{e(n)}</span>' for n in s.get("numbers", []))
    return f"""
          <article class="card">
            <div class="card-top">
              <div>
                <div class="co">{e(s["company"])}</div>
                <div class="meta">{e(s["exchange"])} · {e(s["category"])} · {e(s["time"])}</div>
              </div>
              <div class="badges"><span class="b tag">{e(s["tag"])}</span>{f'<span class="b {cls}">{e(imp)}</span>' if imp else ''}</div>
            </div>
            <p class="summary">{e(s["summary"])}</p>
            {f'<div class="nums">{nums}</div>' if nums else ''}
            {f'<div class="why">{e(s["why"])}</div>' if s.get("why") else ''}
            <div class="card-links"><span class="fake-link">Open the original filing</span><span class="verify">check it yourself</span></div>
          </article>"""


cards = "".join(card(s) for s in samples)
CHAT = "chatbot.html"

page = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<meta name="theme-color" content="#0a0b0d">
<title>Market Tide — the NSE &amp; BSE filings that actually matter</title>
<link rel="icon" href="icon.svg" type="image/svg+xml">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=Instrument+Serif:ital@0;1&display=swap" rel="stylesheet">
<link rel="stylesheet" href="styles.css">
<link rel="stylesheet" href="readonly.css">
</head>
<body>
<nav class="nav">
  <div class="nav-in">
    <span class="nav-brand"><span class="dot"></span><span>Market Tide</span></span>
    <div class="nav-links">
      <span class="fake-link">Dashboard</span>
      <span class="fake-link">Watchlist</span>
      <span class="fake-link">Daily brief</span>
      <span class="fake-link">Insider trading</span>
      <span class="fake-link">Bulk &amp; block</span>
      <a class="nav-cta chat-live" href="{CHAT}">Ask the Chatbot</a>
    </div>
  </div>
</nav>

<main class="mk">
  <section class="mk-hero">
    <h1 class="mk-h1">Every filing read. <br><span class="grad">Only the ones that matter, kept.</span></h1>
    <p class="mk-sub">NSE and BSE publish thousands of company announcements a week. Almost all of it is paperwork.
      <strong>We read every single one</strong> and write a plain-English summary of the handful worth your time — with a
      link to the original PDF, always.</p>
    <div class="mk-ctas">
      <a class="btn-lg btn-grad chat-live" href="{CHAT}">Ask the Chatbot <span aria-hidden="true">→</span></a>
      <span class="btn-lg btn-ghost">Get the free daily brief</span>
    </div>
    <p class="mk-ctanote">Chatbot answers questions from the last 7 days of filings ({start} to {end}).</p>
    <div class="livestrip">
      <div class="livestat"><b>{SCANNED:,}</b><span>filed on NSE</span></div>
      <div class="livestat hi"><b>{kept:,}</b><span>worth reading</span></div>
      <div class="livestat"><b>{days}</b><span>days of data</span></div>
      <div class="livestat"><b>{cats}</b><span>categories to filter</span></div>
    </div>
  </section>

  <div class="ticker" aria-hidden="true"><div class="ticker-track">{tick_html}</div></div>

  <section class="mk-sec">
    <div class="mk-sec-head">
      <p class="mk-kicker">What you actually get</p>
      <h2 class="mk-h2">Not headlines. The answer.</h2>
      <p class="mk-lead">Real summaries of public filings, produced by the Market Tide pipeline.</p>
    </div>
    {cards}
  </section>

  <section class="mk-sec">
    <div class="mk-sec-head"><p class="mk-kicker">How it works</p><h2 class="mk-h2">Three steps, every evening</h2></div>
    <div class="steps">
      <div class="step"><div class="step-n">1</div><h3>We pull everything</h3><p>Every announcement filed with both exchanges, every day — including weekends, when companies still file.</p></div>
      <div class="step"><div class="step-n">2</div><h3>We throw out the noise</h3><p>Trading window notices, newspaper clippings, duplicate share certificates. Roughly nine in ten filings never reach you.</p></div>
      <div class="step"><div class="step-n">3</div><h3>We read the PDF</h3><p>Including scanned ones. You get two or three sentences, the numbers that matter, and the original document to check.</p></div>
    </div>
  </section>

  <section class="mk-sec">
    <div class="mk-sec-head"><p class="mk-kicker">Why it is different</p><h2 class="mk-h2">Built to be checked, not trusted</h2></div>
    <div class="bento">
      <div class="bx wide"><h3>Every card links to the PDF</h3><p>We summarise with AI, and AI gets things wrong. So the original filing is one tap away on every single item. If our summary and the filing disagree, the filing wins.</p></div>
      <div class="bx wide"><h3>Sorted by what it is</h3><p>Buybacks, bonus issues, order wins, schemes of arrangement, QIPs, NCLT matters, rating changes — filter to the one thing you care about instead of scrolling.</p></div>
      <div class="bx"><div class="bx-num">₹0</div><h3>Free newsletter</h3><p>The curated morning email remains free, with no card required.</p></div>
      <div class="bx"><div class="bx-num">7</div><h3>Days of history</h3><p>Catch up on the whole week, not just what landed today.</p></div>
      <div class="bx"><div class="bx-num">XLS</div><h3>Export anything</h3><p>Any filter, straight to Excel — with the PDF link in every row.</p></div>
    </div>
  </section>

  <section class="mk-sec">
    <div class="watchlist-spotlight">
      <div class="watchlist-spotlight-copy">
        <p class="mk-kicker">Your companies, one signal</p>
        <h2 class="mk-h2">Build a watchlist. Let the filings come to you.</h2>
        <p>Follow five companies free, or unlock fifty during your trial and with Premium. Connect Telegram once and important new filings arrive with the summary, key numbers and original PDF.</p>
        <ul><li>One focused feed for the companies you follow</li><li>Instant Telegram alerts during trial and Premium</li><li>No commands to paste and no repeated setup</li></ul>
        <div class="mk-ctas watchlist-spotlight-actions"><span class="btn-lg btn-grad">Build your watchlist</span><span class="btn-lg btn-ghost">See plans</span></div>
      </div>
      <div class="watchlist-preview" aria-label="Preview of the company watchlist">
        <div class="watchlist-preview-head"><span>My watchlist</span><b>3 / 50</b></div>
        <div class="watchlist-preview-company"><i>R</i><span><strong>Reliance Industries</strong><small>New filing · 8 min ago</small></span><b>New</b></div>
        <div class="watchlist-preview-company"><i>F</i><span><strong>Fortis Healthcare</strong><small>Following</small></span><b>✓</b></div>
        <div class="watchlist-preview-company"><i>I</i><span><strong>Infosys</strong><small>Following</small></span><b>✓</b></div>
        <div class="watchlist-preview-telegram"><i>➤</i><span><strong>Telegram connected</strong><small>Important filings arrive automatically</small></span></div>
      </div>
    </div>
  </section>

  <section class="mk-sec home-pricing">
    <div class="mk-sec-head">
      <p class="mk-kicker">Plans for every reader</p>
      <h2 class="mk-h2">Start free. Go deeper when you need it.</h2>
      <p class="mk-lead">The newsletter is free forever. Premium brings the full research dashboard, filing history, filters, original PDFs and exports together.</p>
    </div>
    <div class="plan-grid plan-grid--home">
      <article class="plan-card">
        <div class="plan-card-head"><div><span class="plan-eyebrow">Newsletter only</span><h2>Free</h2></div><div class="plan-price"><b>₹0</b><span>/ forever</span></div></div>
        <p>A focused morning email with the filings worth knowing.</p>
        <ul class="plan-list"><li>Daily email newsletter</li><li>Plain-English market highlights</li><li>Watch up to 5 companies</li><li>Unsubscribe any time</li></ul>
        <span class="btn-lg btn-ghost plan-action">Get the free newsletter</span>
      </article>
      <article class="plan-card plan-card--featured">
        <div class="plan-ribbon">7-day free trial</div>
        <div class="plan-card-head"><div><span class="plan-eyebrow">Complete access</span><h2>Premium</h2></div><div class="plan-price"><b>₹299</b><span>/ 3 months</span></div></div>
        <p>Everything needed to research important NSE and BSE filings efficiently.</p>
        <ul class="plan-list"><li>Full announcement dashboard</li><li>50-company watchlist with Telegram alerts</li><li>Insider trading tracker</li><li>Bulk and block deal tracker</li><li>Summaries, key numbers and original PDFs</li><li>Seven-day history, filters and Excel export</li><li>Private investor community</li><li>Free newsletter included</li></ul>
        <span class="btn-lg btn-grad plan-action">See everything included</span>
      </article>
    </div>
  </section>

  <section class="mk-sec">
    <div class="finale">
      <h2>Ask the week's filings anything.</h2>
      <p>Which companies announced a buyback? What did a company file this week? The chatbot answers only from real filings, and says so when it doesn't know.</p>
      <div class="mk-ctas"><a class="btn-lg btn-grad chat-live" href="{CHAT}">Ask the Chatbot</a></div>
    </div>
  </section>
</main>

<footer class="mk">
  <div class="mk-foot">
    <div class="mk-foot-top"><div class="mk-foot-brand">Market Tide</div></div>
    <p>Market Tide summarises public filings made with NSE and BSE. It is not investment advice. Nothing here is a
      recommendation to buy or sell. Always read the original filing before acting.</p>
    <p>Student RAG assignment demo. This page is a read-only copy; only the chatbot is interactive.</p>
  </div>
</footer>
</body>
</html>
"""
(ROOT / "site" / "index.html").write_text(page, encoding="utf-8")
print(f"index.html written: {kept} filings, {days} days, {cats} categories")
