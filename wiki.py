#!/usr/bin/env python3
"""Wikipedia as a dated, verifiable source — through its own API, which does not refuse, rate-limit bursts, or
need a browser. Replaces the Wayback Machine for "what did the page say on a date": MediaWiki keeps every revision,
so the article as it stood on any date is one API call, with the revision id and timestamp as the chronological
reference point.

    python3 wiki.py "National Electrical Code"                  # the article now → evidence/wiki-<title>.md
    python3 wiki.py "National Electrical Code" --at 2016-01-01  # the article as it stood on that date
    python3 wiki.py --search "NEMA Design B locked rotor"       # Wikipedia's own search: titles to fetch

Files carry: url (the permanent revision link), revision id, `published:` (the revision's timestamp = the date
the text speaks for), `retrieved:`, group wiki:<title> (two dates of one article are one root, never two votes),
status: encyclopedia (secondary; can stabilize, cannot lock) — and Wikipedia's citations are in the text, so the
model can be sent to the primary from there.
"""
import argparse, datetime, os, re, sys, time
import requests

HERE = os.path.dirname(os.path.abspath(__file__))
API = "https://en.wikipedia.org/w/api.php"
UA = {"User-Agent": "tesseract-agent/1.0 (research tool; contact: repository owner)"}

def now():
    return datetime.datetime.now().astimezone().strftime("%Y-%m-%d %H:%M %Z (UTC%z)")

def slug(s):
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")[:48] or "page"

_last = [0.0]

def _get(params):
    """One API call, paced (≥ 2 s apart) with backoff on 429/503: Wikipedia asks for politeness, not a key."""
    params = dict(params, format="json", formatversion=2, maxlag=5)
    for attempt in range(5):
        gap = time.time() - _last[0]
        if gap < 2:
            time.sleep(2 - gap)
        _last[0] = time.time()
        r = requests.get(API, params=params, headers=UA, timeout=45)
        if r.status_code in (429, 503):
            time.sleep(5 * (attempt + 1)); continue
        r.raise_for_status()
        return r.json()
    r.raise_for_status()

def search(query, n=5):
    j = _get({"action": "query", "list": "search", "srsearch": query, "srlimit": n})
    return [(hit["title"], f"https://en.wikipedia.org/wiki/{hit['title'].replace(' ', '_')}") for hit in j.get("query", {}).get("search", [])]

def wikitext_to_text(wt):
    t = re.sub(r"<ref[^>]*/>", "", wt); t = re.sub(r"(?s)<ref[^>]*>.*?</ref>", "", t)
    t = re.sub(r"(?s)\{\{[^{}]*\}\}", "", t); t = re.sub(r"(?s)\{\{[^{}]*\}\}", "", t)   # templates, two levels
    t = re.sub(r"\[\[(?:[^|\]]*\|)?([^\]]*)\]\]", r"\1", t)                               # [[link|text]] -> text
    t = re.sub(r"\[https?://[^\s\]]+\s*([^\]]*)\]", r"\1", t)
    t = re.sub(r"'{2,}", "", t); t = re.sub(r"<[^>]+>", " ", t)
    t = re.sub(r"(?m)^=+\s*(.*?)\s*=+$", r"\n\1\n", t)
    t = re.sub(r"[ \t]+", " ", t); t = re.sub(r"\n{3,}", "\n\n", t)
    return t.strip()

def revision_at(title, date_iso):
    """The newest revision at or before the date (ISO YYYY-MM-DD): (revid, timestamp)."""
    j = _get({"action": "query", "prop": "revisions", "titles": title, "rvlimit": 1, "rvdir": "older",
              "rvstart": f"{date_iso}T23:59:59Z", "rvprop": "ids|timestamp"})
    pages = j.get("query", {}).get("pages", [])
    revs = pages[0].get("revisions", []) if pages else []
    if not revs:
        return None, None
    return revs[0]["revid"], revs[0]["timestamp"]

def fetch(title, folder, at=None, max_chars=60000):
    """Store the article (now, or as it stood on `at`) as evidence. Returns (filename, note)."""
    os.makedirs(folder, exist_ok=True)
    if at:
        revid, ts = revision_at(title, at)
        if not revid:
            return None, f"no revision of '{title}' at or before {at}"
        j = _get({"action": "query", "prop": "revisions", "revids": revid, "rvprop": "ids|timestamp|content", "rvslots": "main"})
        pages = j.get("query", {}).get("pages", [])
        rev = (pages[0].get("revisions") or [{}])[0] if pages else {}
        content = ((rev.get("slots") or {}).get("main") or {}).get("content") or ""
        text = wikitext_to_text(content)
        real_title = pages[0].get("title", title) if pages else title
    else:
        j = _get({"action": "query", "prop": "revisions|extracts", "titles": title, "rvprop": "ids|timestamp", "explaintext": 1, "redirects": 1})
        pages = j.get("query", {}).get("pages", [])
        if not pages or pages[0].get("missing"):
            return None, f"no article '{title}'"
        rev = (pages[0].get("revisions") or [{}])[0]
        revid, ts = rev.get("revid"), rev.get("timestamp")
        text = pages[0].get("extract") or ""
        real_title = pages[0].get("title", title)
    if len(re.findall(r"[A-Za-z0-9]+", text)) < 60:
        return None, "article text too short to use"
    url = f"https://en.wikipedia.org/w/index.php?title={real_title.replace(' ', '_')}&oldid={revid}"
    fn = f"wiki-{slug(real_title)}" + (f"-{str(ts)[:10]}" if at else "") + ".md"
    body = (f"source: Wikipedia, \"{real_title}\" — revision {revid} of {str(ts)[:16].replace('T', ' ')} UTC"
            + (f" (the article as it stood on {at})" if at else " (the article now)") + "\n"
            f"url: {url}\nrevision: {revid}\npublished: {str(ts)[:10]}\nretrieved: {now()}\ngroup: wiki:{slug(real_title)}\n"
            f"status: encyclopedia article, secondary (its own citations name the primary sources); dated by its revision\n\n"
            + text[:max_chars] + ("\n\n[truncated by wiki.py]" if len(text) > max_chars else "") + "\n")
    open(os.path.join(folder, fn), "w", encoding="utf-8").write(body)
    return fn, f"revision {revid} of {str(ts)[:10]}"

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("title", nargs="?", default="")
    ap.add_argument("--at", default=None, help="YYYY-MM-DD: the article as it stood on that date")
    ap.add_argument("--search", default=None)
    ap.add_argument("--evidence", default=os.path.join(HERE, "evidence"))
    a = ap.parse_args()
    if a.search:
        for t, u in search(a.search):
            print(t, "—", u)
    elif a.title:
        fn, note = fetch(a.title, a.evidence, a.at)
        print(f"{fn or 'not stored'}: {note}")
    else:
        ap.print_help()
