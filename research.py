#!/usr/bin/env python3
"""Research: find data online and put it in the evidence store with its provenance, so it can be cited verbatim.

    python3 research.py "Great Pyramid base length Cole 1925"            # search, fetch the top pages, store them
    python3 research.py --url https://en.wikipedia.org/wiki/Great_Pyramid_of_Giza
    python3 research.py --echo                                            # re-run the echo-chamber check on evidence/

What goes in evidence/web-<host>-<slug>.md:
    source: <page title>
    url: <url>
    retrieved: <local date-time with zone>      ← the chronological reference point for everything in the file
    published: <date if the page states one>     ← else "not stated"
    group: web:<registered domain>
    status: web, secondary unless the page is the primary record; verify against the primary before quoting results
    derives_from: web:<other domain>             ← added by the echo check when this page copies another's text

The engine then treats the file like any other evidence: a citation must be verbatim in it, values are compared
by process, and independence is counted by group root. Two rules keep the web from becoming an echo chamber:
  1. Pages that share long verbatim passages are the same source: the echo check marks the copy as deriving
     from the earlier-published (or first-stored) one, so they count once (same root). Agreement among copies
     is cyclical agreement, not independence.
  2. Web files are provisional by status: they can stabilize a claim but cannot lock it until a primary record
     is on file. An average of what the web says is not a measurement.

Search uses DuckDuckGo's HTML endpoint (no key). Pages are fetched with a plain GET and reduced to text; if a
page needs a browser (scripts, consent walls, bot checks) it is rendered in headless Chrome on this machine
(google-chrome --headless --dump-dom) and the rendered DOM is reduced instead. Nothing here calls the model: this is retrieval, logged, with timestamps.
"""
import argparse, datetime, glob, html, os, re, sys, time, urllib.parse
import requests

HERE = os.path.dirname(os.path.abspath(__file__))
UA = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) tesseract-agent research/1.0"}
WORD = re.compile(r"[A-Za-z0-9]+")

def now():
    return datetime.datetime.now().astimezone().strftime("%Y-%m-%d %H:%M %Z (UTC%z)")

def domain(url):
    host = urllib.parse.urlparse(url).netloc.lower().split(":")[0]
    parts = host.split(".")
    return ".".join(parts[-2:]) if len(parts) >= 2 else host

def search(query, n=5):
    """DuckDuckGo HTML results: [(title, url)], best first."""
    r = requests.post("https://html.duckduckgo.com/html/", data={"q": query}, headers=UA, timeout=30)
    r.raise_for_status()
    out = []
    for m in re.finditer(r'<a[^>]+class="result__a"[^>]+href="([^"]+)"[^>]*>(.*?)</a>', r.text, re.S):
        href, title = m.group(1), re.sub(r"<[^>]+>", "", m.group(2))
        if "uddg=" in href:  # DDG redirect wrapper
            href = urllib.parse.unquote(re.search(r"uddg=([^&]+)", href).group(1))
        if href.startswith("http") and not any(href.startswith(b) for b in ("https://duckduckgo.com",)):
            out.append((html.unescape(title).strip(), href))
        if len(out) >= n:
            break
    return out

def to_text(page):
    page = re.sub(r"(?is)<(script|style|noscript|nav|footer|header|aside)[^>]*>.*?</\1>", " ", page)
    page = re.sub(r"(?i)<br\s*/?>|</p>|</div>|</li>|</h\d>|</tr>", "\n", page)
    page = re.sub(r"<[^>]+>", " ", page)
    page = html.unescape(page)
    page = re.sub(r"[ \t\r\f\v]+", " ", page)
    page = re.sub(r"\n\s*\n+", "\n\n", page)
    return page.strip()

def published_date(page):
    for pat in (r'(?i)(?:article:published_time|datePublished|publishdate|date)["\']?\s*(?:content|:)\s*["\']?(\d{4}-\d{2}-\d{2})',
                r'(?i)<time[^>]+datetime="(\d{4}-\d{2}-\d{2})'):
        m = re.search(pat, page)
        if m:
            return m.group(1)
    return "not stated"

def title_of(page, url):
    m = re.search(r"(?is)<title[^>]*>(.*?)</title>", page)
    return html.unescape(re.sub(r"\s+", " ", m.group(1))).strip()[:160] if m else url

def slug(s):
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")[:48] or "page"

def store(url, folder, max_chars=40000):
    """Fetch one page into evidence/. Returns the filename, or None if it was already stored or could not be read."""
    os.makedirs(folder, exist_ok=True)
    for p in glob.glob(os.path.join(folder, "web-*.md")):
        head = open(p, encoding="utf-8", errors="replace").read(600)
        if f"url: {url}" in head:
            return None
    page, text = "", ""
    try:
        r = requests.get(url, headers=UA, timeout=45)
        r.raise_for_status()
        if "html" in r.headers.get("content-type", "") or "text" in r.headers.get("content-type", ""):
            page = r.text; text = to_text(page)
    except Exception as ex:
        print(f"  plain GET failed ({str(ex)[:60]}); trying Chrome")
    if len(WORD.findall(text)) < 80:
        page2 = chrome_dom(url)   # pages that need a browser (scripts, consent walls, bot checks)
        if page2:
            page = page2; text = to_text(page)
    if len(WORD.findall(text)) < 80:
        return None
    title = title_of(page, url)
    fn = f"web-{slug(domain(url))}-{slug(title)}.md"
    body = (f"source: {title}\nurl: {url}\nretrieved: {now()}\npublished: {published_date(page)}\n"
            f"group: web:{domain(url)}\nstatus: web, secondary unless the page is the primary record; verify against the primary before quoting results\n\n"
            + text[:max_chars] + ("\n\n[truncated by research.py]" if len(text) > max_chars else "") + "\n")
    open(os.path.join(folder, fn), "w", encoding="utf-8").write(body)
    return fn

def chrome_dom(url, timeout=60):
    """Render the page in headless Chrome on this machine and return the DOM, or '' if Chrome is not here."""
    import shutil, subprocess
    exe = next((shutil.which(x) for x in ("google-chrome", "google-chrome-stable", "chromium", "chromium-browser", "chrome") if shutil.which(x)), None)
    if not exe:
        return ""
    try:
        out = subprocess.run([exe, "--headless=new", "--disable-gpu", "--no-sandbox", "--virtual-time-budget=8000", "--dump-dom", url],
                             capture_output=True, text=True, timeout=timeout)
        return out.stdout if out.returncode == 0 else ""
    except Exception:
        return ""

def shingles(text, k=12):
    w = [x.lower() for x in WORD.findall(text)]
    return set(" ".join(w[i:i + k]) for i in range(0, max(0, len(w) - k), 3))

def echo_check(folder, min_shared=6):
    """Pages that share ≥ min_shared 12-word passages are one source: the later-published (or later-stored) one
       gets derives_from: the other's group. Returns [(copy, original, shared)]."""
    files = sorted(glob.glob(os.path.join(folder, "web-*.md")))
    docs = []
    for p in files:
        t = open(p, encoding="utf-8", errors="replace").read()
        head = t[:800]
        grp = re.search(r"(?m)^group:\s*(.+)$", head); pub = re.search(r"(?m)^published:\s*(.+)$", head)
        docs.append({"path": p, "group": grp.group(1).strip() if grp else os.path.basename(p), "published": (pub.group(1).strip() if pub else "not stated"),
                     "shingles": shingles(t.split("\n\n", 1)[1] if "\n\n" in t else t), "text": t, "stored": os.path.getmtime(p)})
    found = []
    for i in range(len(docs)):
        for j in range(i + 1, len(docs)):
            a, b = docs[i], docs[j]
            if a["group"] == b["group"]:
                continue
            shared = len(a["shingles"] & b["shingles"])
            if shared < min_shared:
                continue
            # the original is the earlier-published; if neither states a date, the earlier-stored
            def key(d): return (d["published"] == "not stated", d["published"], d["stored"])
            orig, copy = (a, b) if key(a) <= key(b) else (b, a)
            if "derives_from:" not in copy["text"][:800]:
                copy["text"] = re.sub(r"(?m)^(group:.*)$", rf"\1\nderives_from: {orig['group']}", copy["text"], count=1)
                open(copy["path"], "w", encoding="utf-8").write(copy["text"])
            found.append((os.path.basename(copy["path"]), os.path.basename(orig["path"]), shared))
    return found

def search_and_store(query, folder, max_pages=3, n_results=6):
    """Search, fetch the first max_pages readable results into evidence/, run the echo check. Returns the new filenames."""
    added = []
    for title, url in search(query, n=n_results):
        try:
            fn = store(url, folder)
        except Exception as ex:
            print(f"  skip {url}: {str(ex)[:80]}"); continue
        if fn:
            added.append(fn); print(f"  stored {fn}  ← {url}")
        if len(added) >= max_pages:
            break
        time.sleep(1.0)
    if added:
        for copy, orig, shared in echo_check(folder):
            print(f"  echo: {copy} copies {orig} ({shared} shared passages) → counted once")
    return added

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("query", nargs="?", default="")
    ap.add_argument("--url", default=None)
    ap.add_argument("--echo", action="store_true")
    ap.add_argument("--pages", type=int, default=3)
    ap.add_argument("--evidence", default=os.path.join(HERE, "evidence"))
    a = ap.parse_args()
    if a.url:
        print(store(a.url, a.evidence) or "already stored / unreadable")
    elif a.echo:
        for c, o, s in echo_check(a.evidence):
            print(f"{c} derives from {o} ({s} shared passages)")
    elif a.query:
        print(f"[{now()}] research: {a.query}")
        print(search_and_store(a.query, a.evidence, max_pages=a.pages) or "nothing stored")
    else:
        ap.print_help()
