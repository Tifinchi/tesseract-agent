# tesseract-agent

A reasoning loop whose default method is the Tesseract Logic Calculator (anchor · turn · provenance ·
neighbours · behavior rule · empty cells · fold) run inside the Portable Reasoning Framework's pass
order (entry · exploration · quad-core evaluation · implication · ethics · revision · reduction ·
finalization), on a local model. The motor calculator was one worked example; this applies the method
to any claim in any domain.

v0 is deliberately small: one script, one model, a folder of markdown as the datum store, grep-grade
retrieval, append-only JSON logs. Nothing else until something here is proven insufficient.

## Layout

- `method/method.md` — the condensed operating spine the agent loads as its system prompt.
- `method/calculator-method.md` — the calculator's rules (4.1), method (4.8), neighbours (4.9), in full.
- `method/prf-full.txt` — the Portable Reasoning Framework, sections 0–20, in full. Source of truth.
- `agent.py` — the loop. Three model calls per claim (anchor+explore, evaluate+implicate+ethics,
  revise+reduce+finalize); every pass still writes its own immutable artifact.
- `data/` — things to reason over. `khufu-run.md` is a worked trace; `khufu-test.md` is the same
  with the "Empty cells" section removed.
- `logs/` — one `run-<stamp>.jsonl` (every pass, every claim) and one `run-<stamp>-summary.md` per run.

## Install (Ubuntu, once)

    curl -fsSL https://ollama.com/install.sh | sh
    ollama pull qwen2.5:14b          # ~9 GB; fits a 12 GB GPU at 4-bit
    git clone https://github.com/Tifinchi/tesseract-agent && cd tesseract-agent
    pip install -r requirements.txt

## Run

    python agent.py data/khufu-test.md
    python agent.py data/khufu-test.md --question "Where is the coffer lid?" --max-claims 6
    MODEL=qwen2.5:7b python agent.py data/khufu-test.md     # faster, dumber

Expect roughly 10–20 s per model call on an RTX 3060, so ~1 minute per claim; ten claims ≈ 10–15 min.

## The acceptance test for v0

Run it on `data/khufu-test.md` and read the summary's "Empty cells" section. The run that produced the
file named three: the unscanned bedrock under the Subterranean Chamber (radar), the coffer lid against
the drilled granite fragments (a tape measure), and the Big Void (a borehole). If the agent names them
without being told, it is running on the method. If it names a fourth that holds up, it is better than
the run was.

## What goes in the log

Each line is one pass for one claim: `pass_`, `claim`, the input it read, the output JSON, the
deciding number or "none available", what it cites, timestamp, model. Lines are never edited.
Push the logs; that is how the loop gets reviewed.

## Not in v0, on purpose

No vector database, no fine-tuning, no second model, no web UI, no Docker, no agents calling agents.
Each of those is added only when a logged run shows the current version failing for its lack.
