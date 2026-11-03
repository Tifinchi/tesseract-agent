#!/usr/bin/env python3
"""Process memory (PRF section 12): the engine's own history, readable by the engine.

Reads every run log, debrief and chat in logs/, and builds:
  logs/memory.json  — per claim (matched across runs by wording), the history of verdicts with reasons
  logs/memory.md    — the digest the engine, the chat and the debrief load: positions held, changes of mind,
                      failures kept, and what the model said about itself in debriefs and chats

A change of mind is a claim whose verdict differs between two runs. It is never hidden: the old reason and
the new one are printed together, with the run ids, so the engine can say "I previously held X because A;
I now hold Y because B" instead of silently overwriting (PRF 1.3, 12.1, 12.3).

    python3 memory.py            # rebuild and print the digest
    python3 memory.py --json     # print the json
"""
import difflib, glob, json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
LOGS = os.path.join(HERE, "logs")
WORD = re.compile(r"[a-z0-9√π]{3,}")

def norm(t):
    return " ".join(WORD.findall((t or "").lower()))

def similar(a, b):
    na, nb = norm(a), norm(b)
    if not na or not nb:
        return 0.0
    sa, sb = set(na.split()), set(nb.split())
    jac = len(sa & sb) / len(sa | sb)
    return max(jac, difflib.SequenceMatcher(None, na, nb).ratio())

def load_runs():
    runs = []
    for p in sorted(glob.glob(os.path.join(LOGS, "run-*.jsonl")), key=os.path.getmtime):
        rid = re.sub(r"^run-|\.jsonl$", "", os.path.basename(p))
        claims, verdicts, whys, routes = {}, {}, {}, {}
        for line in open(p, encoding="utf-8"):
            try:
                r = json.loads(line)
            except json.JSONDecodeError:
                continue
            ps = r.get("pass_")
            if ps == "RECOGNITION_STATE":
                for c in r.get("claims", []):
                    cid = c.get("id")
                    claims[cid] = c.get("text", "")
                    for i, rd in enumerate(c.get("readings") or []):
                        claims[f"{cid}r{i+1}"] = rd.get("reading") or c.get("text", "")
            elif ps == "EVALUATION_STATE":
                e = r.get("output") or {}
                verdicts[r.get("claim")] = e.get("synthesis")
                qc = e.get("quad_core") or {}
                routes[r.get("claim")] = (qc.get("outcome") or {}).get("reason", "")
            elif ps == "REVISION_STATE":
                o = r.get("output") or {}
                whys[r.get("claim")] = o.get("why") or (o.get("final") or {}).get("statement") or ""
        for cid, v in verdicts.items():
            text = claims.get(cid) or claims.get(re.sub(r"r\d+$", "", cid)) or ""
            runs.append({"run": rid, "cid": cid, "text": text, "verdict": v, "reason": routes.get(cid, ""), "why": whys.get(cid, "")})
    return runs

def group_claims(entries, threshold=0.6):
    """Cluster entries across runs by wording similarity."""
    groups = []
    for e in entries:
        best, score = None, 0.0
        for g in groups:
            s = max(similar(e["text"], x["text"]) for x in g)
            if s > score:
                best, score = g, s
        if best is not None and score >= threshold:
            best.append(e)
        else:
            groups.append([e])
    return groups

def self_reports():
    """What the model said about itself: debrief answers and chat replies, newest last, trimmed."""
    out = []
    for p in sorted(glob.glob(os.path.join(LOGS, "run-*-debrief.md")) + glob.glob(os.path.join(LOGS, "chat-*.md")), key=os.path.getmtime):
        t = open(p, encoding="utf-8").read()
        out.append((os.path.basename(p), t))
    return out

def build():
    entries = load_runs()
    groups = group_claims(entries)
    memory = {"claims": [], "changes": [], "runs": sorted(set(e["run"] for e in entries))}
    for g in groups:
        g = sorted(g, key=lambda e: e["run"])
        hist = [{"run": e["run"], "cid": e["cid"], "verdict": e["verdict"], "reason": e["reason"][:300], "why": e["why"][:300]} for e in g]
        item = {"text": g[-1]["text"], "history": hist, "current": hist[-1]["verdict"]}
        memory["claims"].append(item)
        for a, b in zip(hist, hist[1:]):
            if a["verdict"] != b["verdict"]:
                memory["changes"].append({"text": item["text"], "from": a, "to": b})
    os.makedirs(LOGS, exist_ok=True)
    json.dump(memory, open(os.path.join(LOGS, "memory.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    open(os.path.join(LOGS, "memory.md"), "w", encoding="utf-8").write(digest(memory))
    return memory

def digest(memory=None, max_chars=9000):
    if memory is None:
        p = os.path.join(LOGS, "memory.json")
        memory = json.load(open(p, encoding="utf-8")) if os.path.exists(p) else build()
    L = [f"# Process memory — {len(memory['runs'])} run(s): {', '.join(memory['runs'][-6:])}", ""]
    L.append("## Changes of mind (verdict differed between runs; old and new reasons kept)")
    if not memory["changes"]:
        L.append("- none recorded")
    for ch in memory["changes"][-12:]:
        L.append(f"- {ch['text'][:140]}")
        L.append(f"    was {ch['from']['verdict']} in {ch['from']['run']}: {ch['from']['reason'] or ch['from']['why'] or '(no reason logged)'}")
        L.append(f"    now {ch['to']['verdict']} in {ch['to']['run']}: {ch['to']['reason'] or ch['to']['why'] or '(no reason logged)'}")
    L.append("")
    L.append("## Positions held (latest verdict per claim, with how many runs saw it)")
    for c in sorted(memory["claims"], key=lambda c: -len(c["history"]))[:30]:
        runs_seen = len(set(h["run"] for h in c["history"]))
        verdict_hist = "→".join(h["verdict"] or "?" for h in c["history"][-5:])
        L.append(f"- [{c['current']}] ({runs_seen} run(s): {verdict_hist}) {c['text'][:140]}")
    L.append("")
    reports = self_reports()
    if reports:
        L.append("## What I said about myself (debriefs and chats, newest last; self-report, not evidence)")
        budget = max_chars - sum(len(x) for x in L) - 200
        for name, t in reports[-4:]:
            snippet = re.sub(r"\s+", " ", t)[: max(300, budget // 4)]
            L.append(f"- {name}: {snippet}")
    text = "\n".join(L)
    return text[:max_chars] + ("\n…(memory digest truncated)" if len(text) > max_chars else "")

def previous_on(text, memory=None, threshold=0.6):
    """Earlier verdicts on a claim like this one (for the engine to see before it judges again)."""
    if memory is None:
        p = os.path.join(LOGS, "memory.json")
        memory = json.load(open(p, encoding="utf-8")) if os.path.exists(p) else {"claims": []}
    best, score = None, 0.0
    for c in memory["claims"]:
        s = similar(text, c["text"])
        if s > score:
            best, score = c, s
    return best if score >= threshold else None

if __name__ == "__main__":
    m = build()
    print(json.dumps(m, ensure_ascii=False, indent=1) if "--json" in sys.argv else digest(m))
