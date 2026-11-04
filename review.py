#!/usr/bin/env python3
"""Self-review: the checks a reviewer did by hand after each trial, run by script after every pass.

    python3 review.py                 # latest run
    python3 review.py --run <id>      # one run
    python3 review.py --last 3        # the last three runs together

It reads the run logs and counts, by kind, everything the script had to throw out, could not check, or
reversed — the places where the model, the parser, the prompts or the evidence fell short — and names the
component each kind points at. It does not call the model. Findings are ranked by count, each with examples
copied from the log, and the report ends with the model's own 'would change' answers from its reflection,
marked as self-report. The output is the agenda for the next revision; a human (or the author's reviewer)
reads the agenda, not the whole log.
"""
import argparse, collections, glob, json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
LOGS = os.path.join(HERE, "logs")
sys.path.insert(0, HERE)
import memory

# what each kind of failure points at (the component to fix), learned from trials 1–4
POINTS_AT = [
    (r"cannot evaluate", "parser/prompt: the relation form the model writes is not one the evaluator accepts"),
    (r"unit mismatch", "cross-field matching: the model offered a value in other units or for another quantity; the unit check caught it"),
    (r"not in evidence|file .* not in evidence", "hallucinated citation: the model named a file that does not exist; caught"),
    (r"not verbatim|paraphras", "hallucinated or paraphrased quote: the model reworded the source; caught"),
    (r"number .* not in|does not appear in", "hallucinated value: the number is not in the file cited; caught"),
    (r"delimiter only", "extraction prompt: a neighbour named by its corner symbol with no datum to look up"),
    (r"not a single number", "neighbour check: the model's implied value was a sentence, not a value"),
    (r"does not bear on", "relevance: a verbatim quote that is about something else; recorded, not counted"),
    (r"without a verbatim quote", "rejection discipline: a REJECT with no quote; recorded, not counted"),
    (r"no reference in evidence", "evidence gap: an ambiguous term the evidence cannot calibrate (empty cell)"),
    (r"reference quote not verbatim", "hallucinated reference in calibration; caught"),
    (r"unknown variable|name .* is not defined", "parser: a variable in the relation that was never given a value"),
    (r"result does not depend", "definition route: an identity, not a measurement; counted as definition only"),
    (r"shares? (an? )?(input|root)|share ancestry", "cyclical agreement: routes with a common upstream; counted once"),
    (r"inverse turn does not return", "relation check: the relation the model wrote does not return the cited inputs — a wrong relation or a wrong input (read the relation in the example)"),
    (r"down-wind (weak|asserted)_mismatch", "down-wind: the model asserted a consequence mismatch without a quote that bears on it; held the reading, not rejected"),
    (r"no route reached", "evidence or relation gap: no cited value and no evaluable relation reached this observable (empty cell)"),
    (r"neighbour contradicts", "vertex misfit: a neighbour disagrees; resolve the datum's corner/cell/sign before it can stand"),
    (r"different kind of quantity", "dimension discipline: implied and reported values are different kinds of quantity; not compared"),
    (r"relation conflict", "relation check: the model wrote two relations that cannot both be right; the disagreeing one is suspect, not the reading"),
    (r"not found in FILE|value/quote not found", "hallucinated neighbour citation: the quote is not in the file named; caught"),
]

def points_at(text):
    for pat, what in POINTS_AT:
        if re.search(pat, text, re.I):
            return what
    return "unclassified (read the example)"

def norm_reason(t):
    """Collapse specifics so the same kind of failure counts together."""
    t = re.sub(r"'[^']*'", "'…'", t); t = re.sub(r"\"[^\"]*\"", "\"…\"", t)
    t = re.sub(r"\d+(?:\.\d+)?", "N", t); t = re.sub(r"[\w\-]+\.md", "FILE", t)
    return re.sub(r"\s+", " ", t).strip()[:110]

def load(jsonl):
    items = collections.defaultdict(list)   # kind -> [example]
    meta = {"run": None, "claims": 0, "readings": 0, "elapsed": None, "verdicts": collections.Counter(), "changes": [], "reflection": None,
            "ledger": [], "research": []}
    for line in open(jsonl, encoding="utf-8"):
        try:
            r = json.loads(line)
        except json.JSONDecodeError:
            continue
        p = r.get("pass_"); meta["run"] = meta["run"] or r.get("run")
        if p == "RECOGNITION_STATE":
            meta["claims"] = len(r.get("claims") or []); meta["readings"] = sum(len(c.get("readings") or []) for c in r.get("claims") or [])
            for c in r.get("claims") or []:
                for n in ((c.get("anchor") or {}).get("neighbours_to_check") or []):
                    if not isinstance(n, dict):
                        items["neighbour named as a delimiter only"].append(f"{c.get('id')}: {n}")
        elif p == "ROUTE_STATE":
            rep = r.get("report") or {}
            for d in rep.get("discarded") or []:
                items["discard: " + norm_reason(str(d.get("why")))].append(f"{r.get('claim')}/{rep.get('observable')}: {str(d.get('why'))[:160]}")
            if not rep.get("text") and rep.get("independent_routes", 0) == 0:
                items["no route reached the observable"].append(f"{r.get('claim')}: {rep.get('observable')} = {rep.get('claimed')}")
            for rc in rep.get("relation_conflicts") or []:
                items["relation conflict: two relations for one observable disagree"].append(f"{r.get('claim')}/{rep.get('observable')}: {rc[:150]}")
            if rep.get("cyclical"):
                items["cyclical agreement: routes share " + (", ".join(rep.get("shared") or []) or "ancestry/inputs")].append(f"{r.get('claim')}/{rep.get('observable')}")
            if rep.get("from_ledger"):
                meta["ledger"].append(f"{r.get('claim')}: {rep.get('observable')} held")
        elif p == "EVALUATION_STATE":
            e = r.get("output") or {}
            meta["verdicts"][e.get("synthesis")] += 1
            for n in e.get("neighbours") or []:
                if n.get("status") == "unchecked":
                    items["neighbour unchecked: " + norm_reason(str(n.get("note")))].append(f"{r.get('claim')}: {n.get('neighbour')} — {str(n.get('note'))[:140]}")
                if n.get("status") == "contradicts":
                    items["neighbour contradicts (confidently-wrong candidate)"].append(f"{r.get('claim')}: {n.get('neighbour')} — {str(n.get('note'))[:140]}")
            for d in e.get("downwind") or []:
                if d.get("status") in ("weak_mismatch", "asserted_mismatch"):
                    items[f"down-wind {d['status']} (held the reading from standing)"].append(f"{r.get('claim')}: {str(d.get('if_true'))[:120]}")
            qc = e.get("quad_core") or {}
            for k in ("constraint", "alternative", "consequence"):
                v = qc.get(k) or {}
                note = v.get("recorded_not_counted") or v.get("downgraded")
                if note:
                    items[f"{k} core: " + norm_reason(note)].append(f"{r.get('claim')}: {str(v.get('quote') or v.get('reason'))[:140]}")
            for t in e.get("turns") or []:
                if t.get("status") == "does_not_return":
                    items["inverse turn does not return"].append(f"{r.get('claim')}: {str(t.get('note'))[:140]}")
            cal = e.get("calibration") or {}
            for cp in cal.get("components") or []:
                if not cp["status"].startswith("replaced"):
                    items["calibration: " + norm_reason(cp["status"])].append(f"{r.get('claim')}: '{cp['term']}' needs {cp.get('needs')}")
            if e.get("inherited_misses"):
                items["inherited miss (every reading shows it)"].append(f"{r.get('claim')}: {'; '.join(e['inherited_misses'])[:140]}")
        elif p == "REGRESSION_STATE":
            meta["changes"].append(f"{r.get('claim')}: {(r.get('previous') or {}).get('verdict')} (run {(r.get('previous') or {}).get('run')}) → {r.get('now')}; "
                                   f"explanation: {str(r.get('explanation') or '(none)')[:160]}")
        elif p == "LEDGER_STATE" and r.get("reopened"):
            meta["ledger"].append(f"{r.get('claim')}: {r.get('observable')} REOPENED by {r.get('conflict')}")
        elif p == "RESEARCH_STATE":
            meta["research"].append(f"{r.get('claim')}: {r.get('query')} → {r.get('added') or r.get('error')}")
        elif p == "REFLECTION_STATE":
            meta["reflection"] = r.get("output")
        elif p == "PROCESS_ARCHIVED":
            meta["elapsed"] = r.get("total_elapsed")
    return items, meta

def report(jsonls):
    all_items, metas = collections.defaultdict(list), []
    for j in jsonls:
        it, m = load(j); metas.append(m)
        for k, v in it.items():
            all_items[k].extend(v)
    L = [f"# Review of {len(jsonls)} run(s): {', '.join(m['run'] for m in metas)}", ""]
    for m in metas:
        L.append(f"- {m['run']}: {m['claims']} claims, {m['readings']} base readings, {(m['elapsed'] or 0)/60:.1f} min; verdicts " +
                 ", ".join(f"{k} {v}" for k, v in sorted(m["verdicts"].items(), key=lambda kv: str(kv[0]))))
    L.append("\n## Findings, ranked by count (what the script threw out, could not check, or reversed) → the component it points at")
    ranked = sorted(all_items.items(), key=lambda kv: -len(kv[1]))
    if not ranked:
        L.append("- none: every proposal was verifiable and every check ran")
    for kind, exs in ranked:
        L.append(f"- ×{len(exs)}  {kind}\n    → {points_at(kind)}")
        for ex in exs[:2]:
            L.append(f"    e.g. {ex}")
    changes = [c for m in metas for c in m["changes"]]
    L.append(f"\n## Changes of mind against process memory: {len(changes)}")
    for c in changes[:12]:
        L.append(f"- {c}")
    led = [c for m in metas for c in m["ledger"]]
    if led:
        L.append(f"\n## Locked ledger: {len(led)} event(s)")
        L += [f"- {x}" for x in led[:12]]
    res = [c for m in metas for c in m["research"]]
    if res:
        L.append(f"\n## Research (web evidence added during the run): {len(res)}")
        L += [f"- {x}" for x in res[:12]]
    L.append("\n## Suggested agenda (by rule: the top finding first; a kind seen once is noted, not acted on)")
    for kind, exs in ranked[:5]:
        L.append(f"- {'ACT' if len(exs) >= 2 else 'note'}: {points_at(kind)}  [{kind}, ×{len(exs)}]")
    refl = [m["reflection"] for m in metas if m.get("reflection")]
    if refl:
        L.append("\n## What the model said it would change (self-report, not evidence)")
        for r in refl[-2:]:
            wc = r.get("would_change") if isinstance(r, dict) else None
            if isinstance(wc, dict):
                for k, v in wc.items():
                    L.append(f"- {k}: {str(v)[:200]}")
    return "\n".join(L) + "\n"

def latest(n=1, run_id=None):
    logs = sorted(glob.glob(os.path.join(LOGS, "run-*.jsonl")), key=os.path.getmtime)
    if run_id:
        logs = [p for p in logs if run_id in os.path.basename(p)]
    return logs[-n:]

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", default=None)
    ap.add_argument("--last", type=int, default=1)
    a = ap.parse_args()
    js = latest(a.last, a.run)
    if not js:
        sys.exit("no runs in logs/")
    memory.build()
    text = report(js)
    out = os.path.join(LOGS, f"review-{os.path.basename(js[-1])[4:-6]}.md")
    open(out, "w", encoding="utf-8").write(text)
    print(text + f"\nreview: {out}")
