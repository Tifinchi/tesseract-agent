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

## Trial 1 (v1.5 at ce1c544; 3 × 4 claims; 36 min) and v1.6

Variance: readings seen in all three runs 3/9; same verdict every time 5/9; readings per run 10, 7, 7.
The 2π claim stabilized once on two strict routes (Cole's perimeter over Lehner's height; the seked
identity counted once as a definition) with neighbours and three down-wind consequences lined up — the
whole method on a real claim with a real model. The Big Void held UNSTABLE three times with uncited
mismatches correctly not counted. Four defects, visible only because of the repetition, fixed together as
v1.6: the preamble was extracted as a claim every run (now skipped by code; extraction at temperature 0);
neighbours were named as bare delimiters and the check compared a perimeter with a base side and called it
a contradiction (now named data with units, and the same unit/dimension discipline as routes); a down-wind
"verified mismatch" needed only that the quote exist, not that it bear on the consequence (now a relevance
test; otherwise a weak mismatch that holds UNSTABLE); the reflection echoed the summary (prompt reordered).

## Trial 2 (v1.6 at 3be516c; 3 × 4 claims; 34 min) and v1.7

Extraction steadied (7/6/7; 5/5 readings in every run). Neighbours compared like with like; inverse turns
returned; the reflection answered. And a cyclical-agreement bug of the script's own: 2π came out LOCKED
on "3, 4, 5 independent routes" because the engine's prior verdicts, drawn from memory as calculator routes,
carried distinct run ids and were counted as independent, and the seked identity from the reference file
was labelled "published analysis" by the model and slipped past the definition filter. Honest status: one
measurement route plus a definition, STABILIZED, not LOCKED. v1.7: calculator routes are cross-checks only,
reported and compared, never counted; reference-group lookups are definition-class; the H1 title section is
skipped; a constraint REJECT needs a verbatim quote like the alternative core.

## Trial 3 (v1.7 at ccef203; 3 × 4 claims; 40 min) and v1.8

The v1.7 fixes held: 2π came out STABILIZED, not LOCKED, in two runs (Cole/Lehner 6.2859 and Cole/Petrie
6.2808 share Cole's perimeter, so strict count 1, plus the seked definition 6.2857), and the engine's prior
verdicts appeared as cross-checks only. Four failures, all of the parser or of a rule written too narrowly:
the model wrote a relation with unit words inside it ("… * (1 meter / 1 meter)") and the evaluator threw it
out as an unknown variable, so one run saw no route and read UNSTABLE; a neighbour's "implied" value came
back as a sentence with two numbers and the parser took the first one (the perimeter) as the height, a false
"contradicts"; "approximately 2π" parsed as 2; and the constraint core REJECTED "the chamber stays dry due to
ventilation" on a verbatim bedrock quote about water flowing downhill — verbatim, from the evidence, and
about nothing in the reading. Extraction: 6/9/10 readings, but the count mixed fold children with base
readings. v1.8: unit words after a number inside an expression evaluate as 1 (and the prompt says not to
write them); a neighbour is compared only when its implied value is a single number, otherwise "unchecked";
"2π", "π" and "nπ" parse; a constraint or alternative REJECT must bear on the reading (shared content words,
the same test the down-wind check uses) or it is recorded and not counted; the trial report counts base
readings and fold children separately; and a "cyclical" verdict names what the routes share.

## v2.0: single pass, self-review, research, the locked ledger, the clock, the phone

One command now does what the three-run trial plus a human reviewer did:

```
python3 trial.py claims/khufu-run.md                # ONE run, then review.py → logs/pass-<stamp>.md
python3 trial.py claims/khufu-run.md --research     # same, with web research into evidence/ first
python3 trial.py claims/khufu-run.md --runs 3       # the old sampling check, when a verdict is in doubt
```

- **review.py** reads the run log and counts, by kind, everything the script threw out, could not check or
  reversed — hallucinated citations caught, paraphrased quotes, unit mismatches, unevaluable relations,
  neighbours it could not compare, rejections it did not count, calibration empty cells, inverse turns that
  did not return, changes of mind against process memory, ledger events — ranks them, and names the component
  each points at. The agenda at the end is the next revision's to-do list. It does not call the model.
- **research.py** finds data online (DuckDuckGo HTML, no key) and stores pages in `evidence/web-*.md` with
  `url:`, `retrieved:` (local time with zone), `published:` where the page states it, `group: web:<domain>`,
  `status: web` (provisional: can stabilize, cannot lock). The echo check marks pages that share long verbatim
  passages as deriving from the earlier one, so copies count once. `--research` on a run searches each
  numeric observable before the routes; `python3 research.py "query"` does it by hand.
- **The locked ledger** (`logs/locked.json`): a LOCKED value is held with its routes and the time it locked, not
  recomputed next pass; it is re-checked against neighbours, down-wind and any value now on file, and a
  conflict reopens it with the conflicting source recorded. Matching is on the observable's exact wording —
  `height/perimeter` never inherits `perimeter/height`'s lock.
- **The clock**: every prompt begins with the current date and time; every summary states its run clock and
  ends with "Where the data lives" (file, source, url, published, retrieved, status) for every file cited.
- **Exact memory**: `memory.history(words)` prints a claim's verdict history verbatim from the logs;
  `/history …` in chat.py and the bot hands it to the model, which is told to quote, not reconstruct. (In the
  chat after trial 4 the model recited the Big Void history shifted by one run; the record is now the answer.)
- **Calibration pass (v1.9)** and the rounding rule: a value written without its own tolerance inside a reading
  that states one inherits the reading's stated tolerance (921.2 m "to 0.05 %" is ±0.46 m, not ±0.05 m).
- **Parser**: `h = a - b` (assignment form) and `²`/`³` accepted.
- **Relation conflict** (from the trial-4 review): the model wrote `2*pi*b/h` for a square's perimeter ratio and
  the route from it "disagreed" — a false rejection. Now, when two relations for one observable share inputs and
  one reproduces the reading while the other does not, the disagreeing relation is recorded as a relation
  conflict and troubleshot, not counted as a rejection; directly reported values still reject on their own.
- **Area from a dimension pair** (trial 4: "10.47 m by 5.23 m" discarded where m² was wanted): the product is the
  area, both factors must be in the file, and the factors stay on record. Unit synonyms for square/cubic units.
- **Card-unit sanity**: a length-named observable whose quantity card declares area or volume units (trial 4:
  "height" wanted square meters, 22 discards) falls back to the reading's own unit; the card is recorded.
- **Chrome**: research.py falls back to headless Chrome on the box (`--dump-dom`) for pages a plain GET cannot
  read (scripts, consent walls, bot checks).
- **From the phone**: remote in rather than a bot. A terminal on the box (SSH over Tailscale, or any SSH app on
  the phone) with `tmux` gives every command and `chat.py` with nothing new to run or expose; a run started in
  tmux keeps going after the phone disconnects (`tmux new -s agent`, later `tmux attach -t agent`).

## Motor trial: from the given to the unknown

`claims/motor-m1.md` with `evidence-motor/`: a plate, the NEC and NEMA tables, the reference relations, an IEEE 112
test record and the engine's solved circuit (the default motor of `examples/motor`, so every number is checkable
against `engine.js`). The document states the given, then the unknowns that follow from it — synchronous speed,
poles, slip, input power, power factor, torque, locked-rotor current, conductor and breaker, no-load current,
efficiency by three routes — each with its "because", and two statements that should fall or stay open (5 %
slip; "runs cool"). The summary's **Propagation** section lists, for every standing unknown, the given values it
rests on, and for every rejected one, whether its givens still stand (then the derivation or the statement is at
fault, not the data).

```
python3 trial.py claims/motor-m1.md --max-claims 8 --evidence evidence-motor
```

## Trial 4 (v1.8.1 at a11cecd; 3 × 4 claims; 52 min) and v1.9: calibration as a standing pass

Base extraction held at 5/5/5 with no drift; fold children 3/5/5. But only 2 of 10 readings were seen in
every run and the two that were — the Big Void "similar to other sealed cavities" and 2π — switched verdict
every run (UNSTABLE/STABILIZED/REJECTED/LOCKED across six evaluations of the first). In a chat after the
run (`logs/chat-20261103-192541.md`) the author asked the model to troubleshoot the switching by replacing
ambiguous components with known ones — "big" carries no constraint without a reference size; "similar"
has no standard — and the model produced a calibrated reading, then invented data for it and declared it
stabilized, which is exactly what the model must not do. v1.9 makes the calibration a standing pass (1b in
the method), run on every reading before any route is sought: the model names each ambiguous component and
the reference that would fix it; the script verifies every reference quote verbatim and substitutes only the
verified ones, term by term, so the calibrated reading is rebuilt by rule; the reading as stated is kept
beside it with the substitution map; a component the evidence cannot fix is an empty cell with the
measurement that would fill it. The verdict is then the routes' verdict on the calibrated reading, never the
model's. Matching across runs stays on the as-stated wording.

## Trial: the same version, three times, before anything changes

    python3 trial.py claims/khufu-run.md --runs 3 --max-claims 4

Three normal runs of the same version on the same input, then a report (`logs/trial-<stamp>.md`, tagged
with the git commit) matching readings across the runs and listing every verdict side by side. A reading
whose verdict differs between identical runs is UNSTABLE BY SAMPLING: no single run of it supports a
diagnosis, and no prompt change can be credited for changing it. This is the control that the first seven
runs never had; the rule from here is one change, then a trial, then compare.

## Debrief: talk with it after a run

    python3 debrief.py            # latest run; nine fixed questions, then yours; saved to logs/run-<id>-debrief.md

The model gets the same standing orders it ran under, the run's summary, and a condensed trace of what the
script did with its proposals, and is asked how it understood the task, how it went about it, and what we
were doing. Its answers are self-report (the interview from the research proposal): logged beside the
trace so they can be checked against it, never counted as evidence of anything.

## The lock proper (v1.4): cyclical vs confidently wrong

Agreement is necessary, not the check. Two counts are kept for every observable: routes that agree with
disjoint source groups, and the strict count after collapsing shared ancestry (`derives_from:` in an
evidence header), shared cited inputs, and definition routes. If they differ the diagnosis says
**cyclical**. The anchor's three neighbours are then checked, not just named: each is looked up in the
evidence, the citation verified, and compared with what the reading implies (numerically by the script when
both sides are numbers). A neighbour that contradicts makes the claim a **confidently-wrong candidate**: it
cannot stand until the neighbour is resolved (rule 4.9). STABILIZED needs two independent agreeing routes;
LOCKED needs three after collapse and all three neighbours lined up. Every verdict prints its diagnosis:
independent agreement, cyclical, incomplete (neighbours unchecked), contradicted by a neighbour, or an
independent route disagrees.

**Down-wind reality (rule 9 to its consequences).** For every reading the model names up to three
observable consequences that would follow if it were true; each is checked against the evidence or against
`evidence/reference-observable-reality.md`, a bedrock file of everyday facts anyone can check (things fall,
water flows downhill, an inaudible sound was not heard). A verified mismatch rejects the reading even where
its number matched its sources — the reasoning is wrong, not the arithmetic. A mismatch asserted without a
citation is recorded and keeps the reading from standing.

An UNSTABLE verdict is still an answer: the revision pass gives the **provisional answer** the available
proof favors, what it rests on, what is missing, and the next verifiable step. Silence is for halts.

## v1.5: troubleshoot, flip, fold, turn, cross-field match, reflect

- **Troubleshooting instead of discarding.** A reading whose numbers matched but which failed a neighbour,
  a down-wind consequence or an inverse turn is taken apart: which component carries the error (an input,
  the relation, the framing, the corner, a missing term, a direction), what is still valid, and the repair.
- **The inside-out test.** Same edges, delimiters traded, image reversed: the reading is rewritten under a
  cell flip (instant↔inverse, rate↔anti-rate), a direction flip (cause↔effect, in↔out), a reciprocal flip
  and a reversal, and each is asked whether its consequences would line up. "Correct room, flipped inside
  out" is a diagnosis the engine can now give.
- **The fold re-enters, once.** The corrected reading (or the folded question) becomes a child reading
  evaluated in the same run, logged as the child of the rejected one. No deeper recursion.
- **The inverse turn.** For every relation, the script takes the reading's own value and all but one cited
  input, solves for the remaining variable, and compares with that variable's cited values. A relation
  whose turn does not return to its inputs cannot stand.
- **Cross-field matching by role and dimension, not name.** Every quantity gets a card: meaning, units
  resolved to dimensions (L, M, T, I, Θ), role on the tetrahedron (amount, flow, momentum, effort), field.
  A value is admissible only if its dimensions match (checked by the script) and its role matches (the
  model's call, logged). A derivative in calculus, a velocity in physics and a current in a circuit are all
  the flow role of their own amount; a shared letter is not a shared quantity.
- **Kinds of route.** Each verdict lists the kinds that reached it: a text statement, a measurement, a
  survey, a calculation, a definition, a calculator-derived value (something this engine stabilized in an
  earlier run, drawn from memory, always provisional).
- **Provisional sources.** An evidence file whose `status:` says compiled/from memory/unverified yields
  provisional routes; nothing locks on them alone, and the diagnosis says so.
- **Inherited misses (rule 8).** A disagreeing route that every reading of a claim shows is the evidence's
  problem, not the claim's: kept on record, not counted.
- **Open cells.** Memory keeps the ledger of next routes named across runs and marks which a later run closed.
- **Reflection.** At the end of every run the engine is asked what it thinks of this testing, what it is
  learning, what surprised it, where it is least sure its account matches the trace, and what it would
  change; logged as REFLECTION_STATE and `logs/run-<id>-reflection.md`, carried into memory.

Cost: 10–20 model calls per claim now. `--max-claims 4` for a first run of this version.

## Process memory (PRF section 12)

`memory.py` reads every run log, debrief and chat in `logs/` and builds `logs/memory.md`: the latest
verdict on each claim (matched across runs by wording), every change of mind with the old and new reasons
side by side, and what the model said about itself in debriefs and chats. The engine rebuilds it at the
start of every run; after each verdict is fixed by rule (never before, so memory cannot bias the judging)
the revision pass is shown its previous position and must say what changed and why. Changes appear in the
summary as CHANGED MIND and in the log as REGRESSION_STATE. The chat and the debrief load the digest too
(`--no-memory` to omit). Run `python3 memory.py` to print it.

## Chat with it directly

    python3 chat.py               # the model under the standing orders
    python3 chat.py --with-run    # plus the latest run, to ask about it
    python3 chat.py --evidence    # plus the evidence folder, so it can cite it
    python3 chat.py --no-method   # the bare model, as a control

Transcripts go to `logs/chat-<stamp>.md`. A conversation is not evidence; the run logs are.

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
