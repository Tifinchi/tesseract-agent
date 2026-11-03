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
- **Bands, not a flat tolerance (v1.1).** Every value carries a band from how its source wrote it: a stated
  ± or "to x %" is used as written; a bare number gets half its last digit (the truth of rounding); a hedged
  number (~, ≈, about) gets ±10 %; a bound (≥, ≤) is compared as a bound. A computed route propagates its
  inputs' relative bands in quadrature. Two values agree when their gap is within 2σ of the combined band
  (the calculator's rule 8). The summary prints both values with both bands so "agree" is visible.
  Extraction also names the precision the question needs; a route whose band is wider than that counts
  but is marked **coarse**, and a LOCK requires three routes that all meet it.
- **Routes carry their process (v1.2).** Every route records how it reached its value — "reported in
  petrie-1883.md: '…'", "computed 4*b/h from b=230.33 [lehner-1997.md], h=146.59 [lehner-1997.md]" — and the
  summary prints it. Two routes that agree by different processes lock a corner; two by the same process
  from the same group are one route. Qualitative claims get **text routes**: a sentence copied verbatim from
  an evidence file (the script checks it character for character), with its stance (supports/contradicts)
  and the process that produced it (measurement, survey, excavation report, published analysis, argument,
  secondary summary). The same verbatim check shields the alternative core: a REJECT there needs the
  sentence that states the alternative, verbatim, or it is recorded and not counted.
- **v1.3: readings, enumerated routes, definitions, fit accounts.** Extraction writes out each claim's
  readings when the wording allows more than one ("nothing leaves" = exactly zero, or = inaudible outside)
  and each reading is judged on its own; the summary says "fits if you mean this; does not if you mean
  that." For a numeric observable the model names the relation and its variables once; the script then
  gathers every evidence value for each variable (checking number, file, and unit), forms every combination
  through the relation, computes each exactly, and keeps the largest set of routes whose source groups do
  not overlap (the vertex lock by code). A relation whose result does not move when its inputs are perturbed
  is a definition, counts once, and never as a cross-group measurement. Text routes count only for
  qualitative readings and must say what part of the reading they cover. Every verdict carries the script's
  deterministic account of the fit and the model's one-line why.
- **The cube is in the standing orders.** `method/cube.md` carries the author's ascii geometry verbatim —
  the six face strings, the eight corners with their coordinates, neighbours and opposites, the two
  tetrahedra, the face laws, the turns — and every claim is anchored on it at extraction (corner, cell,
  held axis, the three neighbours to check), logged with the claim.

## Layout

- `method/method.md` — the condensed operating spine, loaded as the system prompt.
- `method/cube.md` — the ascii cube, verbatim, with the corner table; loaded with the spine.
- `method/calculator-method.md` — the calculator's rules (4.1), method (4.8), neighbours (4.9), in full.
- `method/prf-full.txt` — the Portable Reasoning Framework, sections 0–20, in full. Source of truth.
- `examples/motor/` — the motor calculator (the built page, its manual, the engine source) and
  `WHY-IT-WORKS.md`: how it instantiates the method and how each result is reached by more than one route.
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

Per reading: one call to name relations, one call per variable to gather values, one judge call, one
revision call. Ten claims ≈ 20–30 minutes on an RTX 3060 with the 14B model. `--max-claims 6` for a quick run.

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
- Run 5 (v1, 12 claims, 4.7 min): first cross-source computation found on its own (Cole's perimeter over
  Lehner's height = 6.2859); Big Void correctly one route; salt crust correctly no route (evidence gap).
  Three bugs, all in the script: "5½" parsed as 5 and falsely rejected the 2π claim; flat two-claims-per-
  section wasted slots on the preamble; "four-inch" in words failed the number check. v1.1 fixed all three
  and replaced the flat 5 % tolerance with bands at 2σ.
- Run 6 (v1.1, 11 claims, 5.1 min): honest and underpowered — nine UNSTABLE each with a next route, no
  hallucinated citation, but zero routes to the 2π ratio (the seked relation was written with implicit
  multiplication and the evaluator refused it), and two rejections from the alternative core that named a
  file containing no alternative. v1.2: implicit multiplication accepted; alternative REJECT needs a
  verbatim quote; text routes with process for qualitative claims.
- Run 7 (v1.2, 11 claims, 5.3 min): alternative shield worked (one correct rejection with Vyse's verbatim
  record); three paraphrases caught as non-verbatim; but 2π "stabilized" on a definition counted as a
  cross-group computation plus a quoted angle, and "the only writing" stabilized on quotes that cover the
  name but not "only." v1.3 answers both.
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
