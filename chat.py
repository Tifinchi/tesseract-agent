#!/usr/bin/env python3
"""Chat directly with the model, under the standing orders.

    python3 chat.py                 # the model with the method (method.md, cube.md, multimodal.md) as its standing orders
    python3 chat.py --with-run      # also load the latest run's summary and trace, so you can ask about it
    python3 chat.py --with-run <id> # a specific run
    python3 chat.py --no-method     # the bare model, no standing orders (a control)
    python3 chat.py --evidence      # also load the evidence folder, so it can cite it

Type a line and press Enter; `/save` writes the transcript; `/quit` or an empty line ends.
`/history <words of a claim>` prints that claim's EXACT verdict history from the logs (the record, not the model's
recollection) and hands it to the model; `/where <file.md>` prints where a datum lives (source, url, retrieved).
`/search <query>`, `/web <url>`, `/wayback <url> [YYYYMMDD]` fetch pages into evidence/ (url, retrieval time,
archive date) and hand them to the model for this conversation. The model never browses; the script fetches,
stores, and dates every page, and the model may only cite what is on file.
Transcripts are saved to logs/chat-<stamp>.md. Nothing said here is evidence of anything; it is a conversation.
"""
import argparse, datetime, os, sys
import requests

HERE = os.path.dirname(os.path.abspath(__file__))
OLLAMA = os.environ.get("OLLAMA_URL", "http://localhost:11434")

def method_text():
    return "\n\n".join(open(os.path.join(HERE, "method", f), encoding="utf-8").read()
                       for f in ("method.md", "cube.md", "multimodal.md"))

def now_line():
    t = datetime.datetime.now().astimezone()
    return f"CURRENT DATE AND TIME: {t.strftime('%A %Y-%m-%d %H:%M %Z (UTC%z)')}. Your training is older than this; dated files are as old as their retrieved/published lines say."

def ask(model, messages, temperature=0.4):
    messages = [{"role": "system", "content": now_line() + "\n\n" + messages[0]["content"]}] + messages[1:]
    r = requests.post(f"{OLLAMA}/api/chat", json={"model": model, "stream": False, "messages": messages,
                                                   "options": {"temperature": temperature, "num_ctx": 16384, "num_predict": 1500}}, timeout=900)
    r.raise_for_status()
    return r.json()["message"]["content"]

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default=os.environ.get("MODEL", "qwen2.5:14b"))
    ap.add_argument("--no-method", action="store_true")
    ap.add_argument("--with-run", nargs="?", const="latest", default=None)
    ap.add_argument("--evidence", action="store_true")
    ap.add_argument("--no-memory", action="store_true", help="do not load the process memory digest")
    a = ap.parse_args()

    parts = []
    if not a.no_method:
        parts.append("You are a reasoning engine running under the standing orders below. In conversation you may speak "
                     "plainly and in the first person, but you keep the orders' discipline: structure before sequence, "
                     "no confident language about anything not established by independent routes, say 'I don't have a "
                     "route to that' rather than guess, and name the measurement that would settle a question. "
                     "About your own history: quote the process memory and the /history record verbatim with run ids; never "
                     "reconstruct a sequence of verdicts from recollection. About ambiguity: when a word in a question has no "
                     "reference ('big', 'similar', 'near'), say so and name the reference that would fix it before answering. "
                     "About citations: name the file and quote it verbatim, or say you have no file for it.\n\n" + method_text())
    else:
        parts.append("You are a helpful assistant.")
    if not a.no_memory:
        import memory as process_memory
        process_memory.build()
        parts.append("YOUR PROCESS MEMORY (your own history across runs, debriefs and chats; changes of mind are kept, not hidden):\n" + process_memory.digest())
    if a.with_run:
        import debrief
        jsonl = debrief.latest_run(None if a.with_run == "latest" else a.with_run)
        summary_path = jsonl.replace(".jsonl", "-summary.md")
        summary = open(summary_path, encoding="utf-8").read() if os.path.exists(summary_path) else "(no summary)"
        parts.append(f"A RUN YOU JUST DID (summary by the script):\n{summary[:9000]}\n\nCONDENSED TRACE:\n{debrief.condensed_trace(jsonl)}")
    if a.evidence:
        evd = os.path.join(HERE, "evidence")
        for fn in sorted(os.listdir(evd)):
            if fn.endswith(".md") and not fn.startswith("."):
                parts.append(f"EVIDENCE [{fn}]:\n" + open(os.path.join(evd, fn), encoding="utf-8").read()[:4000])
    system = "\n\n".join(parts)
    messages = [{"role": "system", "content": system}]
    stamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    out_path = os.path.join(HERE, "logs", f"chat-{stamp}.md")
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    lines = [f"# Chat {stamp} (model: {a.model}; method: {'off' if a.no_method else 'on'}; run: {a.with_run or 'none'}; evidence: {a.evidence})\n"]
    print(f"[{a.model}; method {'off' if a.no_method else 'on'}; run {a.with_run or 'none'}; evidence {'on' if a.evidence else 'off'}]  /quit or empty line to end, /save to write transcript")
    while True:
        try:
            q = input("\nyou> ").strip()
        except EOFError:
            break
        if not q or q == "/quit":
            break
        if q == "/save":
            open(out_path, "w", encoding="utf-8").write("\n".join(lines)); print(f"saved {out_path}"); continue
        if q.startswith("/history "):
            import memory as process_memory
            rec = process_memory.history(q[9:].strip())
            print(f"\n[record]\n{rec}")
            messages.append({"role": "system", "content": "EXACT RECORD (from the logs; quote it, do not reconstruct it):\n" + rec})
            lines += [f"\n**you:** {q}\n", f"**record:**\n```\n{rec}\n```\n"]; continue
        if q.startswith(("/search ", "/web ", "/wayback ")):
            sys.path.insert(0, HERE); import research
            evd = os.path.join(HERE, "evidence")
            try:
                if q.startswith("/search "):
                    added = research.search_and_store(q[8:].strip(), evd, max_pages=3)
                elif q.startswith("/web "):
                    fn = research.store(q[5:].strip(), evd); added = [fn] if fn else []
                else:
                    parts = q[9:].split(); fn, note = research.wayback_store(parts[0], evd, parts[1] if len(parts) > 1 else None)
                    print(f"[wayback] {note}"); added = [fn] if fn else []
            except Exception as ex:
                print(f"[research failed: {str(ex)[:160]}]"); continue
            if not added:
                print("[nothing stored]"); continue
            for fn in added:
                t = open(os.path.join(evd, fn), encoding="utf-8").read()
                messages.append({"role": "system", "content": f"EVIDENCE FETCHED NOW [{fn}] (cite it verbatim by this filename; its header gives url and time):\n{t[:6000]}"})
                lines += [f"\n**you:** {q}\n", f"**fetched:** {fn} — {t.splitlines()[0][:120]}\n"]
            print(f"[stored and loaded: {', '.join(added)}]"); continue
        if q.startswith("/where "):
            sys.path.insert(0, HERE); import agent as eng
            ev = eng.Evidence(os.path.join(HERE, "evidence")); fn = q[7:].strip()
            w = ev.where(fn) if fn in ev.meta else f"no evidence file named {fn}; files: {', '.join(sorted(ev.meta))[:600]}"
            print(f"\n[where] {w}"); messages.append({"role": "system", "content": "WHERE THE DATUM LIVES: " + w})
            lines += [f"\n**you:** {q}\n", f"**where:** {w}\n"]; continue
        messages.append({"role": "user", "content": q})
        try:
            ans = ask(a.model, messages)
        except Exception as ex:
            print(f"(model error: {ex})"); messages.pop(); continue
        messages.append({"role": "assistant", "content": ans})
        print(f"\nagent> {ans}")
        lines += [f"\n**you:** {q}\n", f"**agent:** {ans}\n"]
    open(out_path, "w", encoding="utf-8").write("\n".join(lines))
    print(f"\ntranscript saved: {out_path}")

if __name__ == "__main__":
    main()
