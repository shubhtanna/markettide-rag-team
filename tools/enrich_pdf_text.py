"""Download each filing's public PDF and add its text to the dataset.

Why: NSE headlines are short and generic ("has submitted financial results").
The real facts (revenue, order value, dividend per share, record date) are inside
the PDF. Putting that text in the dataset is what lets the chatbot answer
real questions instead of repeating headlines.

    python tools/enrich_pdf_text.py            # resumes; already-fetched rows are skipped

Input : data/filings_last_7_days.csv
Output: data/filings_enriched.csv   (adds `body` and `body_chars`)
"""
import concurrent.futures as cf
import csv
import io
import pathlib
import re
import sys
import threading
import zipfile

import requests
from pypdf import PdfReader

ROOT = pathlib.Path(__file__).resolve().parent.parent
SRC = ROOT / "data" / "filings_last_7_days.csv"
OUT = ROOT / "data" / "filings_enriched.csv"

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0 Safari/537.36")
MAX_BYTES = 8_000_000      # skip giant annual-report style attachments
MAX_PAGES = 6              # the facts are almost always on the first pages
MAX_CHARS = 9000           # keeps the index small enough for a free server

_local = threading.local()


def session():
    s = getattr(_local, "s", None)
    if s is None:
        s = requests.Session()
        s.headers["User-Agent"] = UA
        _local.s = s
    return s


def download(url):
    r = session().get(url, timeout=(5, 25), stream=True,
                      headers={"Referer": "https://www.nseindia.com/"})
    try:
        if r.status_code != 200 or int(r.headers.get("Content-Length") or 0) > MAX_BYTES:
            return None
        buf = bytearray()
        for chunk in r.iter_content(65536):
            buf += chunk
            if len(buf) > MAX_BYTES:
                return None
        blob = bytes(buf)
    finally:
        r.close()
    if blob[:2] == b"PK":                            # NSE sometimes zips the PDF
        try:
            zf = zipfile.ZipFile(io.BytesIO(blob))
            for n in zf.namelist():
                if n.lower().endswith(".pdf"):
                    return zf.read(n)
        except Exception:
            return None
    return blob if blob[:4] == b"%PDF" else None


def clean(text):
    text = text.replace("\x00", " ")
    text = re.sub(r"[ \t ]+", " ", text)
    text = re.sub(r"\n\s*\n+", "\n", text)
    # Drop boilerplate address / contact lines that add noise to retrieval.
    lines = [l.strip() for l in text.split("\n")]
    junk = re.compile(r"(cin\s*[:\-]|e-?mail|website|tel\.?|phone|fax|regd\.? office|www\.)", re.I)
    lines = [l for l in lines if l and not junk.search(l) and len(l) > 2]
    return "\n".join(lines)[:MAX_CHARS]


def text_for(row):
    url = row.get("pdf_url") or ""
    if not url.lower().startswith("http"):
        return ""
    try:
        blob = download(url)
        if not blob:
            return ""
        pages = PdfReader(io.BytesIO(blob)).pages[:MAX_PAGES]
        return clean("\n".join((p.extract_text() or "") for p in pages))
    except Exception:
        return ""


def main():
    rows = list(csv.DictReader(open(SRC, encoding="utf-8")))
    done = {}
    if OUT.exists():
        for r in csv.DictReader(open(OUT, encoding="utf-8")):
            if r.get("body"):
                done[r["id"]] = r["body"]
    todo = [r for r in rows if r["id"] not in done]
    print(f"{len(rows)} filings, {len(done)} already have text, fetching {len(todo)}")

    results = dict(done)
    with cf.ThreadPoolExecutor(max_workers=8) as pool:
        futs = {pool.submit(text_for, r): r["id"] for r in todo}
        for i, f in enumerate(cf.as_completed(futs), 1):
            results[futs[f]] = f.result()
            if i % 200 == 0:
                print(f"  {i}/{len(todo)}", flush=True)

    fields = list(rows[0].keys()) + ["body", "body_chars"]
    with open(OUT, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for r in rows:
            body = results.get(r["id"], "")
            w.writerow({**r, "body": body, "body_chars": len(body)})
    got = sum(1 for r in rows if results.get(r["id"]))
    print(f"done: {got}/{len(rows)} filings have PDF text -> {OUT.name}")


if __name__ == "__main__":
    sys.exit(main())
