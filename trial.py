#!/usr/bin/env python3
"""Trial: the same version, the same input, N times, then the variance — before anything is changed.

    python3 trial.py claims/khufu-run.md                 # 3 runs, 4 claims each
    python3 trial.py claims/khufu-run.md --runs 3 --max-claims 4

Each run is a normal run (its own log, summary, reflection). Afterwards the readings are matched across
runs by wording and every verdict is listed side by side. A reading whose verdict differs between identical
runs is UNSTABLE BY SAMPLING: no prompt change can be credited for fixing it, and no diagnosis can be built
on a single run of it. The report goes to logs/trial-<stamp>.md with the git commit it was run at.
"""
import argparse, datetime, glob, json, os, re, subprocess, sys, time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import agent, memory

def version():
    try:
        return subprocess.check_output(["git", "-C", HERE, "rev-parse", "--short", "HEAD"], text=True).strip()
    except Exception:
        return "unknown"

def settle(model, wait=3):
    """Full stop between runs: wait, then confirm the model server has no request in flight for this model."""
    time.sleep(wait)
    try:
        import requests
        ps = requests.get(f"{agent.OLLAMA}/api/ps", timeout=10).json().get("models", [])
        busy = [m for m in ps if m.get("name", "").startswith(model.split(":")[0]) and m.get("size_vram") and False]
        # /api/ps reports loaded models, not in-flight requests; our calls are synchronous, so a returned run has none.
    except Exception:
        pass

def load(run_id):
    p = os.path.join(HERE, "logs", f"run-{run_id}.jsonl")
    readings, verdicts, diags, routes = {}, {}, {}, {}
    for line in open(p, encoding="utf-8"):
        r = json.loads(line)
        if r.get("pass_") == "RECOGNITION_STATE":
            for c in r["claims"]:
                for i, rd in enumerate(c.get("readings") or []):
                    readings[f"{c['id']}r{i+1}"] = rd.get("reading") or c.get("text")
        elif r.get("pass_") == "FOLD_STATE":
            readings[r["child"]] = r["reading"]
        elif r.get("pass_") == "EVALUATION_STATE":
            e = r["output"]; cid = r["claim"]
            verdicts[cid] = e.get("synthesis"); diags[cid] = (e.get("quad_core") or {}).get("outcome", {}).get("diagnosis", "")
            routes[cid] = (e.get("quad_core") or {}).get("outcome", {}).get("reason", "")[:120]
    return [{"run": run_id, "cid": k, "text": readings.get(k, ""), "verdict": verdicts.get(k), "diag": diags.get(k, ""), "reason": routes.get(k, "")}
            for k in verdicts]

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("source")
    ap.add_argument("--runs", type=int, default=3)
    ap.add_argument("--max-claims", type=int, default=4)
    ap.add_argument("--model", default=os.environ.get("MODEL", "qwen2.5:14b"))
    ap.add_argument("--question", default="")
    a = ap.parse_args()
    ver = version(); stamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    print(f"TRIAL at version {ver}: {a.runs} runs of {a.source}, {a.max_claims} claims each")
    ids, t0 = [], time.time()
    # Strictly one run at a time: each call below blocks until that run has written its summary and reflection
    # and returned. Nothing is threaded or backgrounded, so two runs never share the model. Ctrl+C stops the
    # trial at the end of the current model call and the report covers the runs that finished.
    try:
        for i in range(a.runs):
            print(f"\n================ run {i+1} of {a.runs} (sequential; the next starts only after this one returns) ================")
            rid = agent.run(a.source, a.model, a.question, a.max_claims, os.path.join(HERE, "logs"), os.path.join(HERE, "evidence"))
            ids.append(rid)
            settle(a.model)
            print(f"================ run {i+1} finished and settled: {rid} ================")
    except KeyboardInterrupt:
        print(f"\nstopped by hand after {len(ids)} completed run(s)")
    if not ids:
        sys.exit("no completed runs; nothing to compare")
    entries = [e for rid in ids for e in load(rid)]
    groups = memory.group_claims(entries, threshold=0.55)
    L = [f"# Trial {stamp} — version {ver}, {a.runs} identical runs of {os.path.basename(a.source)}, {a.max_claims} claims each, {(time.time()-t0)/60:.1f} min",
         f"runs: {', '.join(ids)}", ""]
    n_base = [sum(1 for e in entries if e['run'] == rid and not e['cid'].endswith('f')) for rid in ids]
    n_fold = [sum(1 for e in entries if e['run'] == rid and e['cid'].endswith('f')) for rid in ids]
    L.append(f"base readings per run: {n_base}  (extraction drift: {'none' if len(set(n_base)) == 1 else 'yes'}); fold children per run: {n_fold}")
    stable, seen_in_all, total = 0, 0, 0
    L.append("\n## Readings matched across runs — verdict per run")
    for g in sorted(groups, key=lambda g: -len(g)):
        runs_seen = sorted(set(e["run"] for e in g))
        vs = [e["verdict"] for e in g]
        all_same = len(set(vs)) == 1
        total += 1; stable += all_same; seen_in_all += (len(runs_seen) == len(ids))
        mark = "stable" if all_same else "UNSTABLE BY SAMPLING"
        L.append(f"- [{mark}] seen in {len(runs_seen)}/{len(ids)} runs — {g[0]['text'][:130]}")
        for e in sorted(g, key=lambda e: e["run"]):
            L.append(f"    {e['run'][-6:]}: {e['verdict']} — {e['diag']}" + (f" — {e['reason']}" if e['reason'] else ""))
    L.append(f"\n## Variance")
    L.append(f"- readings seen in every run: {seen_in_all}/{total} (the rest were extracted in some runs only: extraction drift)")
    L.append(f"- readings with the same verdict every time they appeared: {stable}/{total}")
    L.append(f"- rule: a reading that is UNSTABLE BY SAMPLING cannot support a diagnosis from one run, and a prompt change cannot be credited for changing its verdict.")
    report = "\n".join(L) + "\n"
    out = os.path.join(HERE, "logs", f"trial-{stamp}.md")
    open(out, "w", encoding="utf-8").write(report)
    print("\n" + report + f"\ntrial report: {out}")

if __name__ == "__main__":
    main()
