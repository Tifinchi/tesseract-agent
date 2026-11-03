#!/usr/bin/env python3
"""Chat directly with the model, under the standing orders.

    python3 chat.py                 # the model with the method (method.md, cube.md, multimodal.md) as its standing orders
    python3 chat.py --with-run      # also load the latest run's summary and trace, so you can ask about it
    python3 chat.py --with-run <id> # a specific run
    python3 chat.py --no-method     # the bare model, no standing orders (a control)
    python3 chat.py --evidence      # also load the evidence folder, so it can cite it

Type a line and press Enter; a line of just `/save` writes the transcript; `/quit` or an empty line ends.
Transcripts are saved to logs/chat-<stamp>.md. Nothing said here is evidence of anything; it is a conversation.
"""
import argparse, datetime, os, sys
import requests

HERE = os.path.dirname(os.path.abspath(__file__))
OLLAMA = os.environ.get("OLLAMA_URL", "http://localhost:11434")

def method_text():
    return "\n\n".join(open(os.path.join(HERE, "method", f), encoding="utf-8").read()
                       for f in ("method.md", "cube.md", "multimodal.md"))

def ask(model, messages, temperature=0.4):
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
    a = ap.parse_args()

    parts = []
    if not a.no_method:
        parts.append("You are a reasoning engine running under the standing orders below. In conversation you may speak "
                     "plainly and in the first person, but you keep the orders' discipline: structure before sequence, "
                     "no confident language about anything not established by independent routes, say 'I don't have a "
                     "route to that' rather than guess, and name the measurement that would settle a question.\n\n" + method_text())
    else:
        parts.append("You are a helpful assistant.")
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
