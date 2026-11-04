#!/usr/bin/env python3
"""NFPA LiNK free access → dated evidence, through your own Chrome, with your own login.

NFPA LiNK (https://link.nfpa.org) is a JavaScript viewer behind a sign-in; a plain fetch returns "Loading...".
This script drives the Chrome already installed on this machine (via Playwright) with YOUR NFPA account, opens
the free-access edition you point it at, and saves the text it shows as evidence with the edition year, the url
and the retrieval time — so the engine can cite the 2026 code verbatim and the chronology rule can see 2026.

One-time:
    pip3 install --break-system-packages playwright      # uses your installed Chrome; no browser download
    export NFPA_USER='you@example.com'  NFPA_PASS='…'     # in the shell, never in a file in the repo

Use:
    python3 nfpa.py https://link.nfpa.org/free-access/publications/70/2026
        → signs in, opens the page, saves what the viewer shows to evidence-private/nfpa-70-2026-<slug>.md
    python3 nfpa.py <url> --manual
        → opens a visible Chrome window; YOU sign in and navigate to the section you want (e.g. Table 430.250),
          then press Enter in this terminal and the script saves what is on screen. Use this if the automatic
          sign-in does not find the form (the site's layout is not known to this script).
    python3 nfpa.py <url> --path "Chapter 4" "430" "Table 430.250"
        → navigates by the words on screen: clicks each text in turn in the viewer (the chapter, then the
          article, then the table), scrolls the content so lazy sections render, then saves. If a step is not
          found it saves a screenshot in evidence-private/ so you can see what it saw.
    python3 nfpa.py <url> --path "Chapter 4" "430 Motors" --ocr
        → the viewer draws the code pages as IMAGES, so there is no text to save: --ocr collects every page
          image in the article (the <img>/<canvas> elements, at their own resolution; screenshots as fallback),
          saves them to evidence-private/nfpa-70-2026-pages/, runs Tesseract over each, and writes the text as
          the evidence file with the image filename marked beside each page. OCR can misread a digit, so the
          file's status says "OCR, unverified" (provisional: it can stabilize, not lock) until you check the
          rows you rely on against the page image and change the status line to say so.
          Needs: sudo apt install -y tesseract-ocr && pip3 install --break-system-packages pytesseract pillow
    python3 nfpa.py <url> --find "430.250"
        → after opening, types the term into the viewer's search box if one is found, then saves.

The saved files go in evidence-private/, which .gitignore keeps out of the public repository: the NEC text is
NFPA's copyright and free access is for your own viewing. Point a run at it with
    python3 trial.py claims/motor-m1.md --evidence evidence-private
(copy the other motor evidence files in beside it, or symlink them).
"""
import argparse, datetime, os, re, sys, time

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "evidence-private")

def now():
    return datetime.datetime.now().astimezone().strftime("%Y-%m-%d %H:%M %Z (UTC%z)")

def slug(s):
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")[:48] or "page"

STATUS_NOTE = "text as shown by the NFPA LiNK viewer on the retrieval date; personal-use excerpt, not for redistribution"

def save(url, title, text, edition, find=None):
    os.makedirs(OUT, exist_ok=True)
    fn = f"nfpa-70-{edition}-{slug(find or title)}.md"
    body = (f"source: NFPA 70, National Electrical Code, {edition} edition — NFPA LiNK free access ({title})\n"
            f"edition: {edition}\nurl: {url}\nretrieved: {now()}\ngroup: nec\nwatch: NFPA 70 National Electrical Code current edition\nsafety: yes\n"
            f"status: {STATUS_NOTE}; personal-use excerpt, not for redistribution\n\n"
            + text.strip() + "\n")
    p = os.path.join(OUT, fn)
    open(p, "w", encoding="utf-8").write(body)
    return p

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("url")
    ap.add_argument("--manual", action="store_true", help="you sign in and navigate; the script saves what is on screen when you press Enter")
    ap.add_argument("--find", default=None, help="a term to type into the viewer's search box after opening (e.g. 430.250)")
    ap.add_argument("--path", nargs="+", default=None, help="texts to click in order, e.g. --path 'Chapter 4' '430' 'Table 430.250'")
    ap.add_argument("--show", action="store_true", help="run with a visible Chrome window (watch it navigate)")
    ap.add_argument("--ocr", action="store_true", help="the pages are images: save them and OCR them (tesseract)")
    ap.add_argument("--edition", default=None, help="edition year (default: the last number in the url)")
    ap.add_argument("--wait", type=int, default=20, help="seconds to let the viewer load")
    a = ap.parse_args()
    edition = a.edition or (re.findall(r"\b(20\d{2})\b", a.url) or ["unknown"])[-1]
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        sys.exit("playwright is not installed: pip3 install --break-system-packages playwright")
    user, pw = os.environ.get("NFPA_USER"), os.environ.get("NFPA_PASS")
    if not a.manual and not (user and pw):
        sys.exit("set NFPA_USER and NFPA_PASS in the environment, or use --manual")
    with sync_playwright() as p:
        browser = p.chromium.launch(channel="chrome", headless=not (a.manual or a.show))
        ctx = browser.new_context(viewport={"width": 1400, "height": 1000})
        page = ctx.new_page()
        page.goto(a.url, wait_until="domcontentloaded", timeout=90000)
        time.sleep(5)
        if a.manual:
            print("Chrome is open. Sign in and navigate to the section you want. When the text you need is on screen, press Enter here.")
            try:
                input()
            except EOFError:
                pass
        else:
            # try the common sign-in shapes; the site's exact layout is not known to this script
            signed = False
            for sel_user, sel_pass in (("input[type=email]", "input[type=password]"), ("input[name*=user i]", "input[type=password]"),
                                       ("input[name*=email i]", "input[type=password]"), ("#username", "#password")):
                try:
                    if page.locator(sel_user).count() == 0:
                        # a sign-in link may need clicking first
                        for link in ("text=Sign in", "text=Log in", "text=Sign In", "text=Login"):
                            if page.locator(link).count():
                                page.locator(link).first.click(); time.sleep(3); break
                    if page.locator(sel_user).count():
                        page.locator(sel_user).first.fill(user); page.locator(sel_pass).first.fill(pw)
                        page.keyboard.press("Enter"); time.sleep(8); signed = True; break
                except Exception:
                    continue
            if not signed:
                print("could not find a sign-in form automatically; re-run with --manual")
            if "free-access" in a.url and page.url != a.url:
                page.goto(a.url, wait_until="domcontentloaded", timeout=90000)
            time.sleep(a.wait)
            def dismiss_popups():
                for sel in ("[aria-label*=lose i]", "button:has-text('×')", "button:has-text('Close')", "text=×", ".close", "[class*=close i]"):
                    try:
                        loc = page.locator(sel)
                        if loc.count():
                            loc.first.click(timeout=2000); time.sleep(1)
                    except Exception:
                        pass
            dismiss_popups()
            if a.path:
                os.makedirs(OUT, exist_ok=True)
                for step in a.path:
                    dismiss_popups()
                    clicked = False
                    for loc in (page.get_by_role("link", name=re.compile(re.escape(step), re.I)),
                                page.get_by_role("button", name=re.compile(re.escape(step), re.I)),
                                page.get_by_text(re.compile(re.escape(step), re.I))):
                        try:
                            if loc.count():
                                loc.first.scroll_into_view_if_needed(timeout=5000); loc.first.click(timeout=8000); clicked = True
                                print(f"  clicked '{step}'"); time.sleep(6); break
                        except Exception:
                            continue
                    if not clicked:
                        shot = os.path.join(OUT, f"nfpa-lost-at-{slug(step)}.png")
                        page.screenshot(path=shot, full_page=False)
                        print(f"  could not find '{step}' on the page; screenshot saved: {shot} — send it and the step can be named by what is there")
                        break
                # scroll the content until it stops growing, so sections that render on demand are all loaded
                last, same = -1, 0
                for _ in range(400):
                    page.mouse.wheel(0, 1800); time.sleep(0.5)
                    h = page.evaluate("() => Math.max(document.body.scrollHeight, ...[...document.querySelectorAll('*')].slice(0,400).map(e => e.scrollHeight||0))")
                    same = same + 1 if h == last else 0; last = h
                    if same >= 6:
                        break
                time.sleep(3)
            if a.find:
                for sel in ("input[type=search]", "input[placeholder*=earch]", "input[aria-label*=earch]"):
                    try:
                        if page.locator(sel).count():
                            page.locator(sel).first.fill(a.find); page.keyboard.press("Enter"); time.sleep(8); break
                    except Exception:
                        continue
        title = page.title() or "NFPA LiNK"
        text = page.evaluate("() => document.body.innerText") or ""
        url_now = page.url
        images = []
        if a.ocr:
            import base64
            pages_dir = os.path.join(OUT, f"nfpa-70-{edition}-pages"); os.makedirs(pages_dir, exist_ok=True)
            # 1. image elements at their own resolution (data: or http src), 2. canvases, 3. screenshots of the content
            srcs = page.evaluate("""() => [...document.querySelectorAll('img')].map(i => ({src: i.currentSrc || i.src, w: i.naturalWidth, h: i.naturalHeight}))
                                           .filter(i => i.w >= 400 && i.h >= 400)""")
            n = 0
            for it in srcs:
                src = it["src"]
                try:
                    if src.startswith("data:"):
                        data = base64.b64decode(src.split(",", 1)[1])
                    else:
                        resp = page.request.get(src); data = resp.body()
                    n += 1; fn = os.path.join(pages_dir, f"page-{n:03d}.png"); open(fn, "wb").write(data); images.append(fn)
                except Exception:
                    continue
            if not images:
                canv = page.evaluate("""() => [...document.querySelectorAll('canvas')].filter(c => c.width >= 400).map(c => { try { return c.toDataURL('image/png') } catch (e) { return null } }).filter(Boolean)""")
                for d in canv:
                    n += 1; fn = os.path.join(pages_dir, f"page-{n:03d}.png"); open(fn, "wb").write(base64.b64decode(d.split(",", 1)[1])); images.append(fn)
            if not images:
                # screenshots: scroll the content from the top, one viewport at a time
                page.evaluate("() => window.scrollTo(0, 0)"); time.sleep(1)
                last = -1
                for i in range(300):
                    n += 1; fn = os.path.join(pages_dir, f"shot-{n:03d}.png"); page.screenshot(path=fn, full_page=False); images.append(fn)
                    y = page.evaluate("() => window.scrollY"); page.mouse.wheel(0, 900); time.sleep(0.8)
                    if page.evaluate("() => window.scrollY") == y:
                        break
            print(f"  {len(images)} page image(s) saved in {pages_dir}")
        browser.close()
    if a.ocr and images:
        try:
            import pytesseract
            from PIL import Image
        except ImportError:
            sys.exit("OCR needs: sudo apt install -y tesseract-ocr && pip3 install --break-system-packages pytesseract pillow")
        parts = []
        for fn in images:
            try:
                t = pytesseract.image_to_string(Image.open(fn), config="--psm 6")
            except Exception as ex:
                t = f"(OCR failed: {ex})"
            parts.append(f"[page image {os.path.basename(fn)}]\n{t.strip()}")
        text = "\n\n".join(parts)
        global STATUS_NOTE
        STATUS_NOTE = ("OCR of the viewer's page images (Tesseract), UNVERIFIED transcription — a digit can be misread; the page images are "
                       f"in {os.path.basename(os.path.dirname(images[0]))}/; check each row you rely on against its image, then edit this line to "
                       "'OCR, verified by hand against the page images on <date>' so the engine may count it fully")
    words = len(re.findall(r"[A-Za-z0-9]+", text))
    if (words < 80 or text.strip().lower() in ("loading...", "loading…")) and not (a.ocr and images):
        print("hint: if the viewer draws the pages as images, run again with --ocr")
    if words < 80 or text.strip().lower() in ("loading...", "loading…"):
        sys.exit(f"the viewer did not show readable text ({words} words). Try --manual, a longer --wait, or navigate to the section first.")
    if a.path and not re.search(re.escape(a.path[-1].split()[-1]), text):
        print(f"note: the text saved does not contain '{a.path[-1]}' — the viewer may render that part as an image, or the step landed elsewhere; check the file")
    path = save(url_now, title, text, edition, a.find or (a.path[-1] if a.path else None))
    print(f"saved {path}  ({words} words; edition {edition}; retrieved {now()})")
    print("check it: open the file and confirm the section you need is there and verbatim; the engine cites only what is in it.")

if __name__ == "__main__":
    main()
