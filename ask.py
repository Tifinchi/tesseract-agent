#!/usr/bin/env python3
"""Ask a question; the engine finds the data online, stores it dated, and verifies the answer by the method.

    python3 ask.py "What is the full-load current of a 10 hp 460 V three-phase motor per the current NEC?"
    python3 ask.py "…" --no-research          # answer from the evidence already on file only
    python3 ask.py "…" --rounds 3             # how many search rounds the model may request (default 2)

What happens, in order, all logged under logs/run-<id>:
  1. RESEARCH. The model names the Wikipedia articles that bear on the question (with a date when the question is
     about what was true or said at a date: the article as it stood then is fetched, by revision) and search
     phrases; the script fetches through Wikipedia's API (never refused; every file dated by its revision) and
     the web (DuckDuckGo/Bing → pages → evidence/web-*.md with url and retrieval time), then runs the echo check.
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
import agent, research, memory, review, wiki

P_PLAN = """Question from the author: {question}

Today is {today}. You may ask the script to find data online before answering. Return JSON with:
 "searches": up to 4 web search phrases (3–8 words each) that would find the primary records for this question
             (standards bodies, manufacturers, surveys, papers — not forums), or [] if the evidence on file suffices;
 "wikipedia": up to 3 items {{"title": "<exact article title>", "date": "YYYY-MM-DD" or null}} — the Wikipedia
            articles whose text (or whose cited primary sources) would bear on the question; give a date when the
            question is about what was true or was said AT A DATE (the article as it stood then is fetched);
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
    ap.add_argument("--web", action="store_true", help="also try the web search engines (refused on every box so far; Wikipedia and direct urls are the default)")
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
            searches, wk = (plan.get("searches") or [])[:4], (plan.get("wikipedia") or [])[:3]
            L.append(f"## research round {rnd + 1}: {len(searches)} search(es), {len(wk)} wikipedia; needs: {plan.get('needs', '')}")
            if not searches and not wk:
                break
            added = []
            for w in wk:
                try:
                    fn, note = wiki.fetch(str(w.get("title")), web_dir, (str(w.get("date"))[:10] if w.get("date") and str(w.get("date")).lower() != "null" else None))
                    L.append(f"- wikipedia '{w.get('title')}'{' @ ' + str(w.get('date')) if w.get('date') and str(w.get('date')).lower() != 'null' else ''}: {fn or '-'} ({note})"); added += [fn] if fn else []
                except Exception as ex:
                    L.append(f"- wikipedia '{w.get('title')}': failed ({str(ex)[:120]})")
            # Wikipedia's own search, on the question itself; a hit is kept only if its title shares a content word
            # with the question (a search for "NEC …" otherwise returns NEC Corporation, the NEC supertower, …)
            qwords = set(w.lower() for w in re.findall(r"[A-Za-z]{4,}", a.question))
            if rnd == 0:
                try:
                    hits = [(t, u) for t, u in wiki.search(a.question, n=5) if set(w.lower() for w in re.findall(r"[A-Za-z]{4,}", t)) & qwords][:2]
                    for t, u in hits:
                        fn, note = wiki.fetch(t, web_dir); added += [fn] if fn else []
                    L.append(f"- wikipedia search on the question: {', '.join(t for t, _ in hits) or 'no relevant title'}")
                except Exception as ex:
                    L.append(f"- wikipedia search: failed ({str(ex)[:100]})")
            if a.web:
                for q in searches:
                    try:
                        got = research.search_and_store(str(q), web_dir, max_pages=2); added += got
                        L.append(f"- web search '{q}': {', '.join(got) or 'nothing stored'}")
                    except Exception as ex:
                        L.append(f"- web search '{q}': failed ({str(ex)[:120]})")
            elif searches:
                L.append(f"- web search skipped (every engine has refused non-browser clients; pass --web to try): {', '.join(map(str, searches))[:200]}")
            print("\n".join(L[-(len(searches) + len(wb) + 1):]))
            ev = agent.Evidence("all")
            files = ", ".join(f"{fn} ({(ev.meta[fn].get('year') or 'undated')})" for fn in sorted(ev.meta))[:3000]
            if not added:
                break
    def fail(stage, ex):
        import traceback
        L.append(f"\n## FAILED at {stage}\n```\n{traceback.format_exc()[-2500:]}\n```")
        open(qlog, "w", encoding="utf-8").write("\n".join(L))
        print(f"\nFAILED at {stage}: {str(ex)[:200]}\nask log: {qlog}"); sys.exit(1)
    try:
        got = agent.ask(a.model, agent.SYSTEM, P_CLAIM.format(question=a.question, today=today, files=files))
    except Exception as ex:
        fail("writing the claim document", ex)
    doc = str(got.get("document") or f"# {a.question}\nas of: {today}\n\n{a.question}")
    if not doc.lstrip().startswith("#"):
        doc = f"# {a.question}\nas of: {today}\n\n" + doc
    if not re.search(r"(?m)^##\s", doc):      # the claim paragraph must sit in a section, or extraction skips it as a title
        head, _, body = doc.partition("\n\n")
        doc = head + "\n\n## The answer under test\n\n" + (body or doc)
    qdoc = os.path.join(HERE, "claims", f"ask-{stamp}.md"); open(qdoc, "w", encoding="utf-8").write(doc + "\n")
    L += ["", "## claim document", "```", doc, "```", ""]
    print(f"\nclaim document: {qdoc}\n{doc}\n")
    try:
        run_id = agent.run(qdoc, a.model, a.question, a.max_claims, os.path.join(HERE, "logs"), "all", research_on=False)
    except Exception as ex:
        fail("the evaluation run", ex)
    try:
        memory.build()
        rev = review.report([os.path.join(HERE, "logs", f"run-{run_id}.jsonl")])
    except Exception as ex:
        rev = f"(review failed: {str(ex)[:200]})"
    summary = open(os.path.join(HERE, "logs", f"run-{run_id}-summary.md"), encoding="utf-8").read()
    L += ["## answer (the run summary)", summary, "", "## self-review", rev]
    open(qlog, "w", encoding="utf-8").write("\n".join(L))
    print(f"\nask log: {qlog}")

if __name__ == "__main__":
    main()
