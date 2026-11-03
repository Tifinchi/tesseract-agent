#!/usr/bin/env python3
"""Debrief: talk with the model about a run it just did.

The model is given the same standing orders it ran under, the run's summary, and a condensed trace of what
the script did with its proposals (verdicts, routes, discards, overrides). Then it is asked how it understood
the task, how it went about it, and what we were doing — the self-reported reasoning-process interview from
the author's research proposal. Its answers are SELF-REPORT: they are logged beside the trace so they can be
checked against it, and they are not evidence of anything by themselves (method, multimodal rule 6).

    python3 debrief.py                 # latest run, the fixed question set, then your own questions
    python3 debrief.py --run <id>      # a specific run id (the stamp in logs/run-<id>.jsonl)
    python3 debrief.py --no-interactive

Answers are written to logs/run-<id>-debrief.md.
"""
import argparse, glob, json, os, re, sys
import requests

HERE = os.path.dirname(os.path.abspath(__file__))
OLLAMA = os.environ.get("OLLAMA_URL", "http://localhost:11434")
METHOD = "\n\n".join(open(os.path.join(HERE, "method", f), encoding="utf-8").read()
                     for f in ("method.md", "cube.md", "multimodal.md"))

QUESTIONS = [
    "In your own words: what was the task, and what were we (the author and the script) trying to find out?",
    "How did you understand the method you were running under? Describe it as structure, not as steps.",
    "Walk through one claim from this run: how you anchored it, which readings you saw in it, how you looked for routes, and what the script then did with what you proposed.",
    "Where did the script discard something you proposed, or override a verdict? Say why that happened, honestly, and whether the script was right.",
    "Which claims could not stabilize, and what is the single measurement that would change that for each?",
    "What did you find hardest: telling a record from an estimate, finding a relation through neighbours, keeping a quote verbatim, or something else?",
    "Did you at any point reason in a sequence and then report it as structure, or the reverse? How would you tell?",
    "If the author ran this again tomorrow with the same evidence, what would come out the same and what would come out different, and why?",
    "What should change in the standing orders, the evidence, or the script before the next run? One thing each.",
]

def ask(model, messages, temperature=0.3):
    r = requests.post(f"{OLLAMA}/api/chat", json={"model": model, "stream": False, "messages": messages,
                                                   "options": {"temperature": temperature, "num_ctx": 16384, "num_predict": 1200}}, timeout=900)
    r.raise_for_status()
    return r.json()["message"]["content"]

def latest_run(run_id=None):
    logs = sorted(glob.glob(os.path.join(HERE, "logs", "run-*.jsonl")), key=os.path.getmtime)
    if not logs:
        sys.exit("no runs in logs/")
    if run_id:
        logs = [p for p in logs if run_id in os.path.basename(p)] or sys.exit(f"no run matching {run_id}")
    return logs[-1]

def condensed_trace(jsonl, max_chars=14000):
    """What the script did: claims, readings, routes kept/discarded, cores, synthesis, revision. Compact."""
    out, claims = [], {}
    for line in open(jsonl, encoding="utf-8"):
        r = json.loads(line)
        p = r.get("pass_")
        if p == "ENTRY_STATE":
            out.append(f"RUN {r.get('run')}: source {r.get('input')}; evidence groups {', '.join(r.get('evidence_groups') or [])}")
        elif p == "RECOGNITION_STATE":
            for c in r.get("claims", []):
                claims[c.get("id")] = c
                rd = c.get("readings") or []
                out.append(f"CLAIM {c.get('id')} [{c.get('section')}] ({c.get('kind')}): {c.get('text')}")
                a = c.get("anchor") or {}
                if a:
                    out.append(f"  anchor: corner {a.get('corner')}, cell {a.get('cell')}, held {a.get('held_axis')}")
                for i, x in enumerate(rd):
                    out.append(f"  reading {i+1}: {x.get('reading')}  observables: " +
                               "; ".join(f"{o.get('name')} = {o.get('claimed_value')}" for o in (x.get('observables') or [])))
        elif p == "ROUTE_STATE":
            rep = r.get("report") or {}
            out.append(f"  ROUTES {r.get('claim')} / {rep.get('observable')}: {rep.get('independent_routes')} independent, "
                       f"{rep.get('agree')} agree, {rep.get('disagree')} disagree, {len(rep.get('discarded') or [])} discarded")
            for rt in (rep.get("independent") or [])[:4]:
                out.append(f"    kept: {rt.get('process')}")
            for d in (rep.get("discarded") or [])[:3]:
                out.append(f"    discarded: {d.get('what')}: {d.get('why')}")
        elif p == "EVALUATION_STATE":
            e = r.get("output") or {}
            qc = e.get("quad_core") or {}
            out.append(f"  VERDICT {r.get('claim')}: {e.get('synthesis')} (lock {e.get('lock_level')}); " +
                       "; ".join(f"{k}={v.get('verdict')}" + (f" [{v.get('recorded_not_counted') or v.get('downgraded')}]" if (v.get('recorded_not_counted') or v.get('downgraded')) else "")
                                 for k, v in qc.items() if isinstance(v, dict)))
        elif p == "REVISION_STATE":
            o = r.get("output") or {}
            if o.get("why"):
                out.append(f"  why: {o.get('why')}")
            for cell in o.get("empty_cells") or []:
                out.append(f"  next route: {cell.get('observable')} → {cell.get('next_route')}")
            if o.get("folded_question"):
                out.append(f"  folded: {o.get('folded_question')}")
    text = "\n".join(out)
    return text[:max_chars] + ("\n…(trace truncated)" if len(text) > max_chars else "")

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", default=None)
    ap.add_argument("--model", default=os.environ.get("MODEL", "qwen2.5:14b"))
    ap.add_argument("--no-interactive", action="store_true")
    a = ap.parse_args()
    jsonl = latest_run(a.run)
    run_id = re.sub(r"^run-|\.jsonl$", "", os.path.basename(jsonl))
    summary_path = jsonl.replace(".jsonl", "-summary.md")
    summary = open(summary_path, encoding="utf-8").read() if os.path.exists(summary_path) else "(no summary file)"
    trace = condensed_trace(jsonl)

    system = ("You are the reasoning engine that just ran the method below on a document. You are now being interviewed "
              "about that run by the author of the method. Answer plainly and in the first person. Everything you say is "
              "self-report: say what you did and why, and where you are unsure whether your account matches the trace, say so. "
              "Do not use confident language about claims the trace shows as UNSTABLE or REJECTED.\n\n" + METHOD)
    context = (f"RUN SUMMARY (written by the script):\n{summary[:9000]}\n\nCONDENSED TRACE (what the script did with your proposals):\n{trace}")
    messages = [{"role": "system", "content": system}, {"role": "user", "content": context + "\n\nAcknowledge in one line that you have read the run."}]
    out_path = os.path.join(HERE, "logs", f"run-{run_id}-debrief.md")
    with open(out_path, "a", encoding="utf-8") as f:
        f.write(f"# Debrief of run {run_id} (model: {a.model}) — self-report, check against the trace\n\n")
        ack = ask(a.model, messages); messages.append({"role": "assistant", "content": ack})
        print(ack, "\n")
        for q in QUESTIONS:
            print(f"Q: {q}")
            messages.append({"role": "user", "content": q})
            ans = ask(a.model, messages); messages.append({"role": "assistant", "content": ans})
            print(f"A: {ans}\n"); f.write(f"**Q: {q}**\n\n{ans}\n\n"); f.flush()
        if not a.no_interactive and sys.stdin.isatty():
            print("Your questions now (empty line to finish):")
            while True:
                try:
                    q = input("> ").strip()
                except EOFError:
                    break
                if not q:
                    break
                messages.append({"role": "user", "content": q})
                ans = ask(a.model, messages); messages.append({"role": "assistant", "content": ans})
                print(f"A: {ans}\n"); f.write(f"**Q (author): {q}**\n\n{ans}\n\n"); f.flush()
    print(f"debrief saved: {out_path}")

if __name__ == "__main__":
    main()
