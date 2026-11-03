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

Run it on `data/khufu-test.md`. That file keeps the raw facts of the Khufu run but removes the
conclusions drawn from them. Read the summary's "Empty cells" section. The run that produced the file
turned those facts into three cells: the unscanned bedrock under the Subterranean Chamber (radar, a probe
in the Grotto fill), the coffer lid against the drilled granite fragments (hole spacing vs the coffer's
pin holes), and the Big Void (a borehole). If the agent names them from the facts alone, it is running
on the method. If it names a fourth that holds up, it is better than the run was. It should also REJECT
the hypotheses in "Trials that failed" with the number the source gives, and it should never STABILIZE an
interpretation (the inversion, "Khufu's secret") — those are UNSTABLE or SILENCE.

Kinds drive the path (v0.2). Extraction labels each claim record / estimate / inference /
rejected_by_source / open_question, and the script, not the model, bounds what each may become: a record
can only STABILIZE or be REJECTED by another record; an estimate cannot STABILIZE without a measurement;
an inference with no measurable prediction cannot STABILIZE; an open question goes straight to naming its
measurement. The evaluator is blind: it never sees the kind label or any expected outcome, so its verdict is unaided.
The script applies the kind bounds afterwards and logs both (`synthesis_blind` vs `synthesis`); the
summary reports how often the blind verdict agreed with the rule. That agreement rate is the measure of
whether the model is reasoning or the rule is carrying it.

Run log: `logs/` holds every run. The first (2026-11-02, 10 claims, 6.4 min) sorted correctly but doubted
the source's own records, never extracted a rejectable claim, and was given a test file with the facts
cut out; v0.1 fixed all three in the prompts and the test file. The second run (14 claims, 8.3 min) overshot the
other way: it stabilized computed estimates and an interpretation, and its alternative check rejected two
plain records with invented competitors. v0.2 moved the record/estimate/inference distinction out of the
model's judgment and into the script's routing.

## What goes in the log

Each line is one pass for one claim: `pass_`, `claim`, the input it read, the output JSON, the
deciding number or "none available", what it cites, timestamp, model. Lines are never edited.
Push the logs; that is how the loop gets reviewed.

## Not in v0, on purpose

No vector database, no fine-tuning, no second model, no web UI, no Docker, no agents calling agents.
Each of those is added only when a logged run shows the current version failing for its lack.
