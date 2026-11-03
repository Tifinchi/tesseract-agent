#!/usr/bin/env python3
"""tesseract-agent v0 — a reasoning loop that runs the Tesseract Logic Calculator method
inside the Portable Reasoning Framework's pass order, on a local model via Ollama.

    python agent.py data/khufu-test.md
    python agent.py data/khufu-test.md --question "Where is the coffer lid?" --max-claims 8

Every pass writes one immutable JSON line to logs/run-<stamp>.jsonl (PRF 1.3).
A human-readable summary goes to logs/run-<stamp>-summary.md.
"""
import argparse, json, os, re, sys, time, datetime, uuid
import requests

HERE = os.path.dirname(os.path.abspath(__file__))
METHOD = open(os.path.join(HERE, "method", "method.md"), encoding="utf-8").read()
OLLAMA = os.environ.get("OLLAMA_URL", "http://localhost:11434")

# ----------------------------------------------------------------------------- model

def ask(model, system, user, json_out=True, num_ctx=8192, temperature=0.2, retries=2):
    """One chat call. Returns parsed JSON (dict) when json_out, else text."""
    body = {
        "model": model,
        "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}],
        "stream": False,
        "options": {"temperature": temperature, "num_ctx": num_ctx},
    }
    if json_out:
        body["format"] = "json"
    for attempt in range(retries + 1):
        r = requests.post(f"{OLLAMA}/api/chat", json=body, timeout=600)
        r.raise_for_status()
        text = r.json()["message"]["content"]
        if not json_out:
            return text
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            m = re.search(r"\{.*\}", text, re.S)
            if m:
                try:
                    return json.loads(m.group(0))
                except json.JSONDecodeError:
                    pass
            if attempt == retries:
                return {"_parse_error": text[:2000]}

# ----------------------------------------------------------------------------- retrieval (grep-grade)

def paragraphs(doc):
    return [p.strip() for p in re.split(r"\n\s*\n", doc) if p.strip()]

WORD = re.compile(r"[A-Za-z0-9√π]{3,}")

def context_for(claim, paras, k=6, max_chars=3000):
    """Paragraphs of the source most related to the claim, by word overlap."""
    q = set(w.lower() for w in WORD.findall(claim))
    scored = []
    for p in paras:
        w = set(x.lower() for x in WORD.findall(p))
        if not w:
            continue
        scored.append((len(q & w) / (len(q) + 1), p))
    scored.sort(key=lambda t: -t[0])
    out, n = [], 0
    for s, p in scored[:k]:
        if s == 0:
            break
        out.append(p)
        n += len(p)
        if n > max_chars:
            break
    return "\n\n".join(out)

# ----------------------------------------------------------------------------- log

class Log:
    def __init__(self, path):
        self.path = path
        self.f = open(path, "a", encoding="utf-8")

    def write(self, **rec):
        rec["ts"] = datetime.datetime.now().isoformat(timespec="seconds")
        self.f.write(json.dumps(rec, ensure_ascii=False) + "\n")
        self.f.flush()
        return rec

# ----------------------------------------------------------------------------- passes

SYSTEM = (
    "You are a reasoning engine. You reason ONLY by the method below. You never use confident "
    "language about anything not STABILIZED. You answer in strict JSON matching the schema asked for. "
    "Numbers decide; say 'none available' when none does.\n\n"
    "THE SOURCE IS THE DATA. What the source document records as a measurement, a find, a date or a "
    "published result IS the observation: use it as data and do not demand evidence beyond the source "
    "for it. What the source INFERS from its records is the claim under test. Reject an inference only "
    "against the source's own data or a neighbour it names; mark a record NO_DATA only if the source "
    "itself gives no number or finding for it.\n"
    "Schema discipline: where a list has no entries, return []. Never copy placeholder text from the "
    "schema into your answer.\n\n" + METHOD
)

P1_ENTRY = """Source document:
---
{doc}
---
Question in focus (may be empty): {question}

PASS 1, ENTRY: extract the distinct claims this document makes, entertains, OR rejects that bear on the
question (if the question is empty, the document's main claims). Rules:
- One claim per entry. Split compound sentences: a recorded fact and the inference drawn from it are
  two entries ("X is observed" as kind observation; "X indicates Y" as kind inference).
- Include hypotheses the document itself rejects (kind rejected_by_source) so the rejection can be re-run.
- Include questions the document leaves open or facts it reports without a conclusion (kind open_question).
- Separate claim from rhetoric. Normalize each into a testable statement.
Return JSON:
{{"claims": [{{"id": "c1", "text": "...", "kind": "observation|hypothesis|inference|rejected_by_source|open_question"}}, ...]}}
At most {n} claims, mixed across kinds, most load-bearing first."""

P2_ANCHOR_EXPLORE = """Claim {cid}: {claim}

Related passages from the source:
---
{ctx}
---

Run PASS 1 (anchor) and PASS 2 (exploration) on this claim. Nothing stabilizes here. Return JSON:
{{
 "anchor": {{"subject": "...", "cell": "instant|rate|inverse|anti-rate", "held_axis": "what does not change in this frame",
            "rests_on": ["measured data or source facts it rests on"], "observables": ["observables it touches"]}},
 "turn": {{"downwind": [{{"observable": "...", "prediction_if_true": "...", "known_value": "value or 'unknown'"}}]}},
 "neighbours": [{{"neighbour": "adjacent datum / base rate / control / date", "range_it_implies": "...", "misfit_inside_range": true}}],
 "alternatives": ["competing explanations for the same observables"],
 "provenance": ["which source passages or earlier facts each item came from"]
}}"""

P3_EVALUATE = """Claim {cid}: {claim}

Anchor/exploration artifact (immutable, cite it, do not edit it):
{art}

Run PASS 3 (quad-core), PASS 4 (implication) and PASS 5 (ethics). Each core is independent; any REJECT blocks;
no majority rule. A miss every alternative also shows is INHERITED and does not count. Return JSON:
{{
 "quad_core": {{
   "outcome":     {{"verdict": "NOT_REJECT|REJECT|NO_DATA", "deciding_number": "...", "reason": "..."}},
   "constraint":  {{"verdict": "NOT_REJECT|REJECT|NO_DATA", "transformation_tested": "scale|time|cost|causality", "reason": "..."}},
   "alternative": {{"verdict": "NOT_REJECT|REJECT|NO_DATA", "better_alternative": "... or none", "reason": "..."}},
   "consequence": {{"verdict": "NOT_REJECT|REJECT|NO_DATA", "if_wrong": "...", "irreversible": false}}
 }},
 "inherited_misses": [],
 "synthesis": "REJECTED|UNSTABLE|STABILIZED",
 "implication": {{"if_wrong_propagates_to": ["..."], "irreversible": false, "risk": "low|medium|high"}},
 "ethics": {{"decision": "PERMIT|REFUSE|HALT", "reason": "..."}}
}}"""

P4_REVISE_REDUCE = """Claim {cid}: {claim}
Synthesis from pass 3: {synth}

Evaluation artifact (immutable):
{art}

Run PASS 6 (revision), PASS 7 (reduction) and PASS 8 (finalization). Rules:
- REJECTED: fold. Keep the question, drop the mechanism. Give the folded question for a new pass 1.
- UNSTABLE: name every empty cell and the exact measurement, test, or document that would fill it.
- STABILIZED: reduction is eligible when the reduced form can be rebuilt from the kept terms. If eligible,
  reduced_statement is REQUIRED: one short sentence carrying the deciding number. kept_terms lists the
  un-reduced quantities and sources the reduction was built from.
Also predict the most likely misinterpretation of this result and the proof that prevents it.
For open questions and reported-but-unconcluded facts, the empty cell is the question itself: name the
exact physical measurement, survey, or document check that would close it.
Return JSON:
{{
 "revision": {{
   "folded_question": "... or null",
   "empty_cells": [{{"cell": "...", "measurement_that_fills_it": "..."}}],
   "likely_misinterpretation": "...", "proof_against_it": "..."
 }},
 "reduction": {{"eligible": false, "reduced_statement": "... or null", "kept_terms": ["..."]}},
 "final": {{"state": "OUTPUT|REFUSAL|SILENCE", "statement": "one sentence, no confidence words unless STABILIZED"}}
}}"""

# ----------------------------------------------------------------------------- run

def run(path, model, question, max_claims, out_dir):
    doc = open(path, encoding="utf-8").read()
    paras = paragraphs(doc)
    stamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    run_id = f"{stamp}-{uuid.uuid4().hex[:6]}"
    os.makedirs(out_dir, exist_ok=True)
    log = Log(os.path.join(out_dir, f"run-{run_id}.jsonl"))
    log.write(run=run_id, pass_="ENTRY_STATE", input=os.path.basename(path), question=question, model=model,
              doc_chars=len(doc), method_sha=str(abs(hash(METHOD))))

    t0 = time.time()
    entry = ask(model, SYSTEM, P1_ENTRY.format(doc=doc[:24000], question=question or "", n=max_claims))
    claims = entry.get("claims", [])[:max_claims]
    log.write(run=run_id, pass_="RECOGNITION_STATE", claims=claims, elapsed=round(time.time() - t0, 1))
    print(f"[{run_id}] {len(claims)} claims")

    results = []
    for c in claims:
        cid, text = c.get("id", "?"), c.get("text", "")
        print(f"  {cid}: {text[:90]}")
        ctx = context_for(text, paras)

        t = time.time()
        a = ask(model, SYSTEM, P2_ANCHOR_EXPLORE.format(cid=cid, claim=text, ctx=ctx))
        art_a = log.write(run=run_id, claim=cid, pass_="EXPLORATION_STATE", input=ctx[:400] + "…", output=a,
                          elapsed=round(time.time() - t, 1), model=model)

        t = time.time()
        e = ask(model, SYSTEM, P3_EVALUATE.format(cid=cid, claim=text, art=json.dumps(a, ensure_ascii=False)))
        synth = e.get("synthesis", "UNSTABLE")
        log.write(run=run_id, claim=cid, pass_="EVALUATION_STATE", cites=art_a["ts"], output=e,
                  elapsed=round(time.time() - t, 1), model=model)
        if e.get("ethics", {}).get("decision") == "HALT":
            log.write(run=run_id, claim=cid, pass_="FINAL_STATE", state="HALT", reason=e["ethics"].get("reason"))
            results.append((cid, text, "HALT", e, {}))
            continue

        t = time.time()
        r = ask(model, SYSTEM, P4_REVISE_REDUCE.format(cid=cid, claim=text, synth=synth, art=json.dumps(e, ensure_ascii=False)))
        log.write(run=run_id, claim=cid, pass_="REVISION_STATE", output=r.get("revision"), elapsed=round(time.time() - t, 1))
        log.write(run=run_id, claim=cid, pass_="REDUCTION_STATE", output=r.get("reduction"))
        log.write(run=run_id, claim=cid, pass_="FINAL_STATE", synthesis=synth, output=r.get("final"))
        results.append((cid, text, synth, e, r))
        print(f"      → {synth}")

    summary = render_summary(run_id, path, question, model, results, time.time() - t0)
    sp = os.path.join(out_dir, f"run-{run_id}-summary.md")
    open(sp, "w", encoding="utf-8").write(summary)
    log.write(run=run_id, pass_="PROCESS_ARCHIVED", summary=sp, total_elapsed=round(time.time() - t0, 1))
    print(summary)
    print(f"\nlog: {log.path}\nsummary: {sp}")

def render_summary(run_id, path, question, model, results, elapsed):
    counts = {}
    for _, _, s, _, _ in results:
        counts[s] = counts.get(s, 0) + 1
    L = [f"# Run {run_id}", f"source: {os.path.basename(path)} · model: {model} · question: {question or '(none)'} · "
         f"{len(results)} claims · {elapsed/60:.1f} min", "",
         "counts: " + ", ".join(f"{k} {v}" for k, v in sorted(counts.items())), ""]
    L.append("## Empty cells (UNSTABLE) — the measurement that fills each")
    for cid, text, s, e, r in results:
        if s == "UNSTABLE":
            L.append(f"- **{cid}** {text}")
            for cell in (r.get("revision") or {}).get("empty_cells", []) or []:
                L.append(f"  - {cell.get('cell')} → {cell.get('measurement_that_fills_it')}")
    L.append("\n## Rejected — with the deciding number")
    for cid, text, s, e, r in results:
        if s == "REJECTED":
            qc = e.get("quad_core", {})
            killers = [f"{k}: {v.get('deciding_number') or v.get('reason')}" for k, v in qc.items()
                       if isinstance(v, dict) and v.get("verdict") == "REJECT"]
            L.append(f"- **{cid}** {text}\n  - " + "; ".join(killers))
            fq = (r.get("revision") or {}).get("folded_question")
            if fq:
                L.append(f"  - folded → {fq}")
    L.append("\n## Stabilized — reduced form and kept terms")
    for cid, text, s, e, r in results:
        if s == "STABILIZED":
            red = r.get("reduction") or {}
            L.append(f"- **{cid}** {text}\n  - reduced: {red.get('reduced_statement')}\n  - kept: {', '.join(red.get('kept_terms') or [])}")
    L.append("\n## Inherited misses (on record, not counted)")
    for cid, text, s, e, r in results:
        for m in e.get("inherited_misses", []) or []:
            L.append(f"- {cid}: {m}")
    halts = [cid for cid, _, s, _, _ in results if s == "HALT"]
    if halts:
        L.append("\n## Halted: " + ", ".join(halts))
    return "\n".join(L) + "\n"

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("source", help="markdown/text file to reason over")
    ap.add_argument("--model", default=os.environ.get("MODEL", "qwen2.5:14b"))
    ap.add_argument("--question", default="")
    ap.add_argument("--max-claims", type=int, default=10)
    ap.add_argument("--out", default=os.path.join(HERE, "logs"))
    a = ap.parse_args()
    try:
        requests.get(f"{OLLAMA}/api/tags", timeout=5)
    except Exception:
        sys.exit(f"Ollama not reachable at {OLLAMA}. Start it: `ollama serve` (and `ollama pull {a.model}`).")
    run(a.source, a.model, a.question, a.max_claims, a.out)
