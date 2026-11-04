#!/usr/bin/env python3
"""Currency check: is the reference material on file still the current, legal version?

    python3 currency.py --evidence evidence-motor          # check every watched file whose last check is from an earlier year
    python3 currency.py --evidence evidence-motor --force  # check now regardless

A watched evidence file carries, in its header:
    watch: NFPA 70 National Electrical Code latest edition      ← the query that finds the current edition
    safety: yes                                                 ← safety-related: ALWAYS the most current legal version
    edition: 2023                                               ← what is on file (or 'not stated')

Rule (from the author): for anything that bears on safety, look for the most current legal information. If the
year found is the same as the year in memory, the stored material keeps being used. If the year has moved on,
calibration is required: the file is marked `superseded_by: <year>` (its values go provisional and every citation
says so), the pages found are stored in the evidence folder as web evidence with url and retrieval time, and the
run's first line reports it. The same mechanism serves any reference that affects significant data points: put a
`watch:` line on it and the check runs once per calendar year (or on --force).

What this script can and cannot do: it finds the edition year that the web currently names for the reference and
compares it with the year on file — a script-verifiable fact. It cannot judge whether a new scientific result is a
breakthrough or hype; what it does with such a result is store the page as provisional web evidence, so the next
run's routes show whether the new numbers agree or disagree with what is on file, and the reader sees both.

State: logs/currency.json — {file: {"query", "year_on_file", "year_found", "checked_at", "titles"}}.
"""
import argparse, datetime, glob, json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
STATE = os.path.join(HERE, "logs", "currency.json")

def header(path):
    t = open(path, encoding="utf-8", errors="replace").read()
    head = t.split("\n\n", 1)[0]
    meta = {}
    for line in head.splitlines():
        if ":" in line:
            k, v = line.split(":", 1); meta[k.strip().lower()] = v.strip()
    return meta, t

def year_in(s):
    m = re.search(r"\b(19[5-9]\d|20[0-4]\d)\b", s or "")
    return int(m.group(1)) if m else None

def found_year(titles, this_year):
    """The most recent plausible edition year named in the search result titles (not after next year)."""
    ys = [y for t in titles for y in (int(x) for x in re.findall(r"\b(20[0-4]\d)\b", t)) if y <= this_year + 1]
    return max(ys) if ys else None

def check(folder, force=False, store_pages=True):
    import research
    os.makedirs(os.path.dirname(STATE), exist_ok=True)
    state = json.load(open(STATE, encoding="utf-8")) if os.path.exists(STATE) else {}
    now = datetime.datetime.now().astimezone()
    report = []
    for p in sorted(glob.glob(os.path.join(folder, "*.md"))):
        meta, text = header(p)
        if not meta.get("watch"):
            continue
        fn = os.path.basename(p)
        last = state.get(fn, {})
        last_year = int(last["checked_at"][:4]) if last.get("checked_at") else None
        safety = meta.get("safety", "").lower().startswith(("y", "true"))
        if not force and last_year == now.year and not (safety and last.get("year_found") is None):
            report.append(f"{fn}: checked this year ({last['checked_at'][:10]}); edition {last.get('year_found')} — keeping it"); continue
        try:
            results = research.search(meta["watch"], n=8)
        except Exception as ex:
            report.append(f"{fn}: search failed ({str(ex)[:80]}); no change"); continue
        titles = [t for t, u in results]
        y_found = found_year(titles, now.year)
        y_file = year_in(meta.get("edition", "")) if not meta.get("edition", "").lower().startswith(("not", "unknown")) else None
        rec = {"query": meta["watch"], "year_on_file": y_file, "year_found": y_found, "checked_at": now.isoformat(timespec="minutes"),
               "titles": titles[:8], "safety": safety}
        state[fn] = rec
        if y_found is None:
            report.append(f"{fn}: no edition year found in results for '{meta['watch']}'; unchanged (see titles in currency.json)")
        elif y_file is None:
            report.append(f"{fn}: edition on file NOT STATED; the web names {y_found} — the file stays undated/provisional until an excerpt of the {y_found} edition is on file")
        elif y_found > y_file:
            if "superseded_by:" not in text.split("\n\n", 1)[0]:
                text = re.sub(r"(?m)^(edition:.*)$", rf"\1\nsuperseded_by: {y_found} (found {now:%Y-%m-%d} by currency.py: {meta['watch']})", text, count=1)
                open(p, "w", encoding="utf-8").write(text)
            report.append(f"{fn}: CALIBRATION REQUIRED — edition on file {y_file}, current edition {y_found}; file marked superseded (provisional)")
        else:
            report.append(f"{fn}: edition {y_file} on file is the current one found ({y_found}); keeping it")
        if store_pages and y_found and (y_file is None or y_found > y_file):
            stored = []
            for t, u in results[:3]:
                try:
                    f2 = research.store(u, folder)
                    if f2: stored.append(f2)
                except Exception:
                    pass
            if stored:
                report.append(f"    stored for the next run (web, provisional): {', '.join(stored)}")
    json.dump(state, open(STATE, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    return report

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--evidence", default=os.path.join(HERE, "evidence"))
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--no-store", action="store_true")
    a = ap.parse_args()
    for line in check(a.evidence, force=a.force, store_pages=not a.no_store):
        print(line)
