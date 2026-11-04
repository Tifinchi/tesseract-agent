#!/usr/bin/env python3
"""Ask a question; the engine finds the data online, stores it dated, and verifies the answer by the method.

    python3 ask.py "What is the full-load current of a 10 hp 460 V three-phase motor per the current NEC?"
    python3 ask.py "…" --no-research          # answer from the evidence already on file only
    python3 ask.py "…" --rounds 3             # how many search rounds the model may request (default 2)

What happens, in order, all logged under logs/run-<id>:
  1. RESEARCH. The model turns the question into search phrases and, where a date matters, Wayback requests
     ('wayback <url> <YYYYMMDD>'). The script runs them (DuckDuckGo → pages → evidence/web-*.md with url and
     retrieval time; Wayback snapshots with their archive date), then runs the echo check so copies count once.
     The model sees what was found and may ask for one more round. The model never browses; it asks, the script
     fetches, and only what is on file can be cited.
  2. CLAIM. The model writes the question as a claims document: the answer it expects as a claim with its
     observables (or 'none' if it has no expectation), so the engine evaluates a statement, not a vibe.
  3. EVALUATION. agent.run on that document against EVERY evidence folder (evidence/, evidence-motor/,
     evidence-private/, …): calibration, meaning ladder, routes by independent source, bands, neighbours,
     down-wind, chronology (the edition in force as of today), the locked ledger, the verdict by rule.
  4. ANSWER. The summary's verdicts with their routes and 'where the data lives', plus the self-review.

Nothing useful is withheld: every evidence folder is read, the web is searched, the archive is reachable. What
remains withheld is the one thing the method forbids — a citation that is not verbatim on file.
"""
import argparse, datetime, json, os, re, sys
import requests

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import agent, research, memory, review

P_PLAN = """Question from the author: {question}

Today is {today}. You may ask the script to find data online before answering. Return JSON with:
 "searches": up to 4 web search phrases (3–8 words each) that would find the primary records for this question
             (standards bodies, manufacturers, surveys, papers — not forums), or [] if the evidence on file suffices;
 "wayback": up to 2 items {{"url": "...", "date": "YYYYMMDD"}} when the question is about what a page or an
            edition said AT A DATE (the Wayback Machine holds dated snapshots), else [];
 "needs": one sentence: what datum, from what kind of source, would settle the question.
Already on file (filenames): {files}"""

P_CLAIM = """Question from the author: {question}

Evidence now on file (filenames with their dates): {files}

Write the question as a short claims document the engine can evaluate: a title line '# <question>', the line
'as of: {today}', then ONE paragraph stating the answer you expect as a definite claim with its numbers and units
(the engine will test it against the evidence; if you have no expectation, state the most specific candidate
the evidence suggests and say 'candidate'). Put the paragraph under a heading line '## The answer under test'.
Do not cite files in the paragraph. Return JSON: {{"document": "..."}}"""

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("question")
    ap.add_argument("--model", default=os.environ.get("MODEL", "qwen2.5:14b"))
    ap.add_argument("--no-research", action="store_true")
    ap.add_argument("--rounds", type=int, default=2)
    ap.add_argument("--max-claims", type=int, default=3)
    a = ap.parse_args()
    today = datetime.date.today().isoformat()
    web_dir = os.path.join(HERE, "evidence"); os.makedirs(web_dir, exist_ok=True)
    stamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    qlog = os.path.join(HERE, "logs", f"ask-{stamp}.md"); os.makedirs(os.path.dirname(qlog), exist_ok=True)
    L = [f"# Ask {stamp} — {a.question}", f"clock: {agent.now_line()}", ""]

    ev = agent.Evidence("all")
    files = ", ".join(f"{fn} ({(ev.meta[fn].get('year') or 'undated')})" for fn in sorted(ev.meta))[:3000]
    if not a.no_research:
        for rnd in range(a.rounds):
            plan = agent.ask(a.model, agent.SYSTEM, P_PLAN.format(question=a.question, today=today, files=files))
            searches, wb = (plan.get("searches") or [])[:4], (plan.get("wayback") or [])[:2]
            L.append(f"## research round {rnd + 1}: {len(searches)} search(es), {len(wb)} wayback; needs: {plan.get('needs', '')}")
            if not searches and not wb:
                break
            added = []
            for q in searches:
                try:
                    got = research.search_and_store(str(q), web_dir, max_pages=2); added += got
                    L.append(f"- search '{q}': {', '.join(got) or 'nothing stored'}")
                except Exception as ex:
                    L.append(f"- search '{q}': failed ({str(ex)[:120]})")
            for w in wb:
                try:
                    fn, note = research.wayback_store(str(w.get("url")), web_dir, str(w.get("date") or "") or None)
                    L.append(f"- wayback {w.get('url')} @ {w.get('date')}: {fn or '-'} ({note})"); added += [fn] if fn else []
                except Exception as ex:
                    L.append(f"- wayback {w.get('url')}: failed ({str(ex)[:120]})")
            print("\n".join(L[-(len(searches) + len(wb) + 1):]))
            ev = agent.Evidence("all")
            files = ", ".join(f"{fn} ({(ev.meta[fn].get('year') or 'undated')})" for fn in sorted(ev.meta))[:3000]
            if not added:
                break
    got = agent.ask(a.model, agent.SYSTEM, P_CLAIM.format(question=a.question, today=today, files=files))
    doc = str(got.get("document") or f"# {a.question}\nas of: {today}\n\n{a.question}")
    if not doc.lstrip().startswith("#"):
        doc = f"# {a.question}\nas of: {today}\n\n" + doc
    if not re.search(r"(?m)^##\s", doc):      # the claim paragraph must sit in a section, or extraction skips it as a title
        head, _, body = doc.partition("\n\n")
        doc = head + "\n\n## The answer under test\n\n" + (body or doc)
    qdoc = os.path.join(HERE, "claims", f"ask-{stamp}.md"); open(qdoc, "w", encoding="utf-8").write(doc + "\n")
    L += ["", "## claim document", "```", doc, "```", ""]
    print(f"\nclaim document: {qdoc}\n{doc}\n")
    run_id = agent.run(qdoc, a.model, a.question, a.max_claims, os.path.join(HERE, "logs"), "all", research_on=False)
    memory.build()
    rev = review.report([os.path.join(HERE, "logs", f"run-{run_id}.jsonl")])
    summary = open(os.path.join(HERE, "logs", f"run-{run_id}-summary.md"), encoding="utf-8").read()
    L += ["## answer (the run summary)", summary, "", "## self-review", rev]
    open(qlog, "w", encoding="utf-8").write("\n".join(L))
    print(f"\nask log: {qlog}")

if __name__ == "__main__":
    main()
