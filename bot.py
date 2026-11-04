#!/usr/bin/env python3
"""Phone access: a Telegram bot on the Ubuntu box. Commands and chat from the phone; runs happen here.

One-time setup (5 minutes):
  1. In Telegram, message @BotFather → /newbot → follow the prompts → copy the token.
  2. Message your new bot anything, then open https://api.telegram.org/bot<TOKEN>/getUpdates in a browser and
     read your numeric "chat":{"id": ...}. That is your chat id; the bot answers that id and no one else.
  3. On the Ubuntu box:
        export TG_TOKEN=<token>  TG_CHAT=<chat id>
        python3 bot.py
     (keep it running in a terminal, or: nohup python3 bot.py > logs/bot.out 2>&1 &)

Commands (type them in the Telegram chat):
  /pass [n] [research]   one run of claims/khufu-run.md with n claims (default 4), then the self-review; 'research' = web research on
  /trial [n]             three identical runs (sampling check)
  /run <file> [n]        one run of another file in claims/
  /research <query>      search the web and store pages in evidence/ with url + retrieval time
  /review                the latest run's self-review
  /history <words>       a claim's exact verdict history from the logs
  /where <file.md>       where a datum lives
  /status                what is running, how long, the clock
  /memory                the process-memory digest
  /pull                  git pull (after the reviewer pushed a revision)
  /push                  git add logs evidence && commit && push
  /stop                  stop the running job after its current model call
  anything else          chat with the engine (method on, memory on), same as chat.py; transcript saved

Long polling over HTTPS to api.telegram.org; nothing listens on the box. One job at a time; a run is a thread so
chat still answers while it runs. Output longer than one Telegram message is sent in parts.
"""
import datetime, io, os, queue, re, subprocess, sys, threading, time, traceback
import requests

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
TOKEN = os.environ.get("TG_TOKEN") or sys.exit("set TG_TOKEN (from @BotFather)")
CHAT = str(os.environ.get("TG_CHAT") or sys.exit("set TG_CHAT (your numeric chat id)"))
API = f"https://api.telegram.org/bot{TOKEN}"
MODEL = os.environ.get("MODEL", "qwen2.5:14b")

job = {"name": None, "started": None, "thread": None, "stop": False}
chat_messages = None   # the running chat context (system + turns)

def send(text):
    text = text or "(empty)"
    for i in range(0, len(text), 3800):
        try:
            requests.post(f"{API}/sendMessage", json={"chat_id": CHAT, "text": text[i:i + 3800]}, timeout=30)
        except Exception as ex:
            print("send failed:", ex)

def now():
    return datetime.datetime.now().astimezone().strftime("%Y-%m-%d %H:%M %Z")

class Tee(io.TextIOBase):
    """Collect a job's printed output; forward milestone lines to the phone as they happen."""
    def __init__(self):
        self.buf = []
    def write(self, s):
        self.buf.append(s); sys.__stdout__.write(s)
        if re.match(r"\s*(→|\[|calibrated|ledger|folded|TRIAL|=+ run)", s or ""):
            send(s.strip()[:300])
        return len(s)
    def flush(self):
        sys.__stdout__.flush()

def run_job(name, fn):
    if job["thread"] and job["thread"].is_alive():
        send(f"busy: {job['name']} since {job['started']}; /stop to end it"); return
    def body():
        job.update(name=name, started=now(), stop=False)
        send(f"started {name} at {job['started']}")
        tee = Tee(); old = sys.stdout; sys.stdout = tee
        try:
            result = fn()
            send(f"finished {name} at {now()}\n\n" + (result or "")[:3500])
        except KeyboardInterrupt:
            send(f"{name} stopped by hand")
        except Exception:
            send(f"{name} failed:\n" + traceback.format_exc()[-1500:])
        finally:
            sys.stdout = old; job.update(name=None)
    job["thread"] = threading.Thread(target=body, daemon=True); job["thread"].start()

def do_pass(n, research, runs=1, source="claims/khufu-run.md"):
    def fn():
        import agent, memory, review
        ids = []
        for i in range(runs):
            rid = agent.run(os.path.join(HERE, source), MODEL, "", n, os.path.join(HERE, "logs"), os.path.join(HERE, "evidence"), research_on=research)
            ids.append(rid)
            if job["stop"]:
                break
        memory.build()
        rev = review.report([os.path.join(HERE, "logs", f"run-{r}.jsonl") for r in ids])
        stamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
        open(os.path.join(HERE, "logs", f"pass-{stamp}.md"), "w", encoding="utf-8").write(rev)
        return rev
    return fn

def chat_reply(text):
    global chat_messages
    import chat as chat_mod, memory
    if chat_messages is None:
        memory.build()
        system = ("You are a reasoning engine running under the standing orders below, talking with the author from her phone. "
                  "Keep replies short. Quote the process memory verbatim with run ids; never reconstruct history. Name ambiguous "
                  "terms and the reference that would fix them. Cite files verbatim or say you have none.\n\n" + chat_mod.method_text()
                  + "\n\nYOUR PROCESS MEMORY:\n" + memory.digest(max_chars=6000))
        chat_messages = [{"role": "system", "content": system}]
    chat_messages.append({"role": "user", "content": text})
    ans = chat_mod.ask(MODEL, chat_messages)
    chat_messages.append({"role": "assistant", "content": ans})
    with open(os.path.join(HERE, "logs", f"chat-phone-{datetime.date.today():%Y%m%d}.md"), "a", encoding="utf-8") as f:
        f.write(f"\n**you ({now()}):** {text}\n\n**agent:** {ans}\n")
    return ans

def git(*args):
    try:
        return subprocess.check_output(["git", "-C", HERE] + list(args), text=True, stderr=subprocess.STDOUT)[-1500:]
    except subprocess.CalledProcessError as ex:
        return ex.output[-1500:]

def handle(text):
    t = text.strip()
    cmd, _, rest = t.partition(" ")
    cmd = cmd.lower()
    if cmd in ("/start", "/help"):
        send(__doc__.split("Commands")[1][:3000])
    elif cmd == "/pass":
        n = int(re.search(r"\d+", rest).group(0)) if re.search(r"\d+", rest) else 4
        run_job("pass", do_pass(n, "research" in rest))
    elif cmd == "/trial":
        n = int(re.search(r"\d+", rest).group(0)) if re.search(r"\d+", rest) else 4
        run_job("trial", do_pass(n, False, runs=3))
    elif cmd == "/run":
        parts = rest.split(); src = parts[0] if parts else "claims/khufu-run.md"
        n = int(parts[1]) if len(parts) > 1 and parts[1].isdigit() else 4
        run_job(f"run {src}", do_pass(n, "research" in rest, source=src if src.startswith("claims/") else f"claims/{src}"))
    elif cmd == "/research":
        import research
        def fn():
            added = research.search_and_store(rest, os.path.join(HERE, "evidence"), max_pages=3)
            return f"[{now()}] stored: {', '.join(added) if added else 'nothing readable'}"
        run_job("research", fn)
    elif cmd == "/review":
        import review, memory
        memory.build(); js = review.latest(1)
        send(review.report(js) if js else "no runs yet")
    elif cmd == "/history":
        import memory
        memory.build(); send(memory.history(rest))
    elif cmd == "/where":
        import agent
        ev = agent.Evidence(os.path.join(HERE, "evidence"))
        send(ev.where(rest.strip()) if rest.strip() in ev.meta else "no such evidence file; files: " + ", ".join(sorted(ev.meta))[:1500])
    elif cmd == "/status":
        alive = job["thread"] and job["thread"].is_alive()
        send(f"clock {now()}\n" + (f"running: {job['name']} since {job['started']}" if alive else "idle") + f"\nversion {git('rev-parse', '--short', 'HEAD').strip()}")
    elif cmd == "/memory":
        import memory
        memory.build(); send(memory.digest(max_chars=3800))
    elif cmd == "/pull":
        send(git("pull", "--rebase"))
    elif cmd == "/push":
        send(git("add", "logs", "evidence") + git("commit", "-m", f"from phone {now()}") + git("pull", "--rebase") + git("push"))
    elif cmd == "/stop":
        job["stop"] = True; send("will stop after the current run returns (a model call cannot be interrupted mid-flight)")
    else:
        send(chat_reply(t))

def main():
    send(f"tesseract-agent bot up at {now()} (model {MODEL}); /help for commands")
    offset = None
    while True:
        try:
            r = requests.get(f"{API}/getUpdates", params={"timeout": 50, "offset": offset}, timeout=70).json()
            for u in r.get("result", []):
                offset = u["update_id"] + 1
                m = u.get("message") or {}
                if str((m.get("chat") or {}).get("id")) != CHAT or not m.get("text"):
                    continue
                threading.Thread(target=lambda t=m["text"]: handle(t), daemon=True).start()
        except Exception as ex:
            print("poll error:", ex); time.sleep(5)

if __name__ == "__main__":
    main()
