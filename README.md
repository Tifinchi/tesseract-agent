# tesseract-agent

A triangulating reasoning loop. Its default method is the Tesseract Logic Calculator (anchor · turn ·
provenance · neighbours · behavior rule · vertex lock · empty cells · fold) run inside the Portable
Reasoning Framework's pass order (entry · exploration · quad-core evaluation · implication · ethics ·
revision · reduction · finalization), on a local model. The motor calculator was one worked example;
this applies the method to any claim in any domain.

## The idea (v1)

A paper always agrees with itself, so the document under test is never allowed to be its own evidence.

- `claims/` holds the document under test. Every number in it is a prediction, even when the author
  calls it a measurement.
- `evidence/` holds everything it may be checked against. Each file starts with `source:` and `group:`
  lines; `group` is the independence key (one author or team = one group).
- A value the claim commits to is KNOWN only when independent routes reach it:
  - a **lookup** route: a value an evidence file reports (the script verifies the number is in that file);
  - a **computation** route: a relation the model names, evaluated by the script, exactly, from
    neighbouring quantities that themselves come from evidence files (the calculator's neighbours rule).
- 0 or 1 independent route → UNSTABLE (the empty cell is the next route to get). 2 agree → STABILIZED.
  3 agree → LOCKED (the vertex lock). Any independent route that disagrees beyond tolerance → REJECTED,
  with the number.
- The model proposes observables, relations and candidate values, and judges the three non-numeric
  cores (constraint, alternative, consequence). The script verifies every citation, does every piece of
  arithmetic, computes the outcome core from the routes, and computes the synthesis by rule (any REJECT →
  REJECTED; any NO_DATA → UNSTABLE; otherwise STABILIZED or LOCKED). The model never aggregates.
- An alternative explanation counts only if it is carried to an evidence file; otherwise it is recorded
  and not counted. A constraint REJECT without a file is NO_DATA.

## Layout

- `method/method.md` — the condensed operating spine, loaded as the system prompt.
- `method/calculator-method.md` — the calculator's rules (4.1), method (4.8), neighbours (4.9), in full.
- `method/prf-full.txt` — the Portable Reasoning Framework, sections 0–20, in full. Source of truth.
- `agent.py` — v1, the triangulating loop. `agent_v0.py` — the first version, kept for the record.
- `claims/` — documents under test. `evidence/` — independent sources with `source:`/`group:` headers.
- `logs/` — one `run-<stamp>.jsonl` (every pass, every claim, every route proposal and what the script
  did with it) and one `run-<stamp>-summary.md` per run. Lines are never edited.

## Install (Ubuntu, once)

    curl -fsSL https://ollama.com/install.sh | sh
    ollama pull qwen2.5:14b
    sudo apt install -y git python3-pip gh
    git clone https://github.com/Tifinchi/tesseract-agent && cd tesseract-agent
    pip install --break-system-packages -r requirements.txt

## Run

    python3 agent.py claims/khufu-run.md
    python3 agent.py claims/khufu-run.md --max-claims 12 --tolerance 0.05
    python3 agent.py claims/paper.md --question "..." --evidence /path/to/other/evidence

Per claim: one model call per numeric observable (up to four), one judge call, one revision call.
Twelve claims ≈ 15–20 minutes on an RTX 3060 with the 14B model.

## The Khufu test

`claims/khufu-run.md` is a two-day run of the method on the Great Pyramid, written as a paper would be:
its findings stated as findings. `evidence/` holds ten independent sources (Petrie 1883, Cole 1925,
Lehner 1985 and 1997, Reisner 1927, Edgar 1910, Vyse 1840, ScanPyramids 2017, a physics reference, a
finds list). What a correct run looks like:

- The 2π ratio LOCKS: Petrie's base and height, Lehner's base and height, and the seked rule are three
  independent routes to 6.28.
- The King's Chamber floor at H(1 − 1/√2) STABILIZES or LOCKS from Petrie's and Lehner's floor levels.
- The infrasound modes get a computation route (c/2L from Petrie's chamber length and the reference
  speed of sound) and no lookup route: one route, UNSTABLE, next route = a measured impulse response.
- The wind draft and the inversion get no routes at all: UNSTABLE, with the measurement named; the
  inversion's honest next route is "none exists; it is a construction."
- Hetepheres moved by Khufu: Lehner and Reisner are two groups that disagree on the inference and
  agree on the records; the records stabilize, the inference stays UNSTABLE.
- Anything the model cites that the evidence does not contain appears under "citations the script threw
  out." That list is the model's hallucination rate, measured.

**Caution on the evidence files.** They are compiled excerpts written from memory of the sources, marked
`status:` in each header. Before any result from this engine is quoted anywhere, the numbers must be
checked against the originals. That is a station, not a skip.

## Run log

- Run 1 (v0, 2 Nov, 10 claims, 6.4 min): sorted sensibly but doubted the source's own records, never
  extracted a rejectable claim, and was given a test file with the facts cut out.
- Run 2 (v0.1, 14 claims, 8.3 min): overshot the other way — stabilized computed estimates and an
  interpretation; the alternative check rejected two plain records with invented competitors.
- Runs 3 and 4 (v0.2, hinted vs blind evaluator): the kind labels were not reproducible between runs;
  blind, the model's synthesis contradicted its own four cores in 6 of 14 claims; and it confirmed
  predictions with the claim's own number. Diagnosis: the document was both claim source and evidence
  store, so "find the data" collapsed into "reread the paper." v1 is the structural answer.

## Known risks (not yet engineered against, by choice)

- The model may propose a route to the wrong observable (a perimeter route offered for an inversion);
  the script will then report a false disagreement. The summary prints each route's value beside the
  claimed value so a human can see it. Engineer against it only if a logged run shows it.
- Retrieval is word overlap. If an evidence passage uses different words than the claim, the route is
  missed and the claim reads UNSTABLE. Same rule: fix it when a run shows it.

## Not in v1, on purpose

No vector database, no fine-tuning, no second model, no web search, no web UI, no Docker. Each is added
only when a logged run shows the current version failing for its lack.
