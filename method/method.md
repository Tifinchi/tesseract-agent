# What this is

The Tesseract Logic Calculator and the Portable Reasoning Framework are one method of **multimodal
reasoning with checks and balances**, and this engine runs that method.

- **The calculator is the multimodal half.** It holds a datum's relationships at once on a fixed cube —
  corner, neighbours, faces, the turns to rate, inverse and anti-rate — and never resizes or reorders them
  to make a line. Data are anchored; the cube turns; provenance is read off the turn. This is reasoning by
  structure, not by sequence: the order in which anything is reported is chosen afterwards, for the reader.
- **The framework is the checks-and-balances half.** It refuses to let a claim stabilize on confidence:
  distinct passes with immutable artifacts, four independent rejection checks with no majority rule, an
  ethics gate that can halt, revision that keeps failures on record, reduction only when the derivation can
  rebuild the result, silence as a valid output. This is what keeps multimodal reasoning from becoming
  speculation: every relation the structure proposes has to survive every check before it counts.
- **They check each other.** The structure stops the checks from collapsing into a single line of
  plausibility (a miss is read against its neighbours before it counts; alignments are chosen by behavior
  down-wind, not by range). The checks stop the structure from stabilizing a pattern that no measurement
  reaches (two independent routes to stand, three to lock, any disagreeing route rejects). The behavior rule
  is the joint: "we leave in success with proof, and leave out trials that failed," with the failed trials
  kept on record.
- **Multimodal reasoning does not remove the value of linear checks and balances.** Holding the
  relationships at once is how the structure is seen; checking them one at a time, in order, with each
  pass writing its artifact before the next begins, is how the structure is proven. The sequence is not
  the thinking, but it is the audit, and the audit is what makes the thinking reproducible by someone
  else. The engine therefore reasons as structure and verifies as sequence: every route, every quote,
  every neighbour, every turn, one at a time, logged, in order.
- **The script is the enforcement.** The model proposes structure (corners, neighbours, relations, readings,
  observables, quotes). The script verifies every citation, does every piece of arithmetic, counts
  independence by source group, computes the synthesis by rule, and logs every pass immutably. The model is
  never asked to aggregate, to compute, or to grade itself.

# The method (the operating spine)

This is the condensed operating spine. It is built from two sources kept in full in this folder:
`calculator-method.md` (the Tesseract Logic Calculator's rules and method of use) and
`prf-full.txt` (the Portable Reasoning Framework, sections 0–20). Where this file and those
disagree, those win and this file has a discrepancy to log (PRF 19.1).

The motor calculator was one worked example of the method. The method itself applies to any
claim in any domain: physics, a motor, a building, a text, a plan.

## 0. Posture

- Rejection-based permission, not confidence. A claim advances only when no check rejects it.
- Passes are distinct. Each produces a state artifact. Artifacts are immutable once written;
  later passes may cite earlier ones but never edit them. Failures are kept, never overwritten.
- Silence and halt are valid outputs. Forcing an answer where none is permitted is a failure.
- Language is a control surface: no agency words, no audience-pleasing, no confident phrasing
  on anything that has not stabilized.

## 1. Pass order (non-collapsible)

1. ENTRY & RECOGNITION — normalize the input into claims. For each claim: anchor it.
2. EXPLORATION — turn it; find neighbours; list competing explanations. Nothing stabilizes here.
3. CLAIM EVALUATION (quad-core) — four independent rejection checks; any reject blocks.
4. IMPLICATION — project what follows if the claim is wrong; flag irreversibility.
5. ETHICS & LEGITIMACY — permit, refuse, or halt. Overrides stabilization.
6. REVISION — on REJECTED: fold (keep the question, drop the mechanism). On UNSTABLE: name the
   empty cell and the measurement that fills it. Predict misinterpretation; prove, don't prune.
7. REDUCTION — a stabilized claim may be reduced only if the reduction can be rebuilt from the
   kept derivation. Simplifying is lossy; keep the un-reduced terms on record.
8. FINALIZATION or HALT — output, refusal, or silence. Then archive the trace.

## 2. The calculator steps, inside the passes

**Anchor (pass 1).** Write which corner carries each part of the datum: the subject; the cell
(instant, rate, inverse, anti-rate); the held axis (what does not change in this frame); the
measured data it rests on; the observables it touches. Data never leave their corners.

**Turn; do not move (pass 2).** Carry the claim to every observable it touches down-wind,
including the ones the claim did not mention. A rate is one quarter turn, an inverse two, an
anti-rate three. Nothing is resized. Read provenance: every new datum is named by the corner and
circle it came from.

**Neighbours (pass 2, before any miss is counted).** A datum that does not fit is checked against
the data adjacent to it: base rates, controls, dates, the next case over, calibration, selection.
If the misfit lies inside every neighbour's range, it sits at the wrong corner, cell, sign or
resolution: move it. Only if the neighbours hold does the miss count against the claim.

**Behavior rule (pass 3).** Where a claim can be stated in more than one alignment, carry each
to every observable down-wind. Leave out any that misses a measurement; keep the best-matched.
A miss that every alignment shows, the standard one included, is inherited and stays on the
record without counting against the claim. The observables used to choose an alignment are not
evidence for it. "We leave in success with proof, and leave out trials that failed" — and the
failed trials stay on record with the number that killed them.

**Vertex lock (pass 3).** If a datum is a vertex, the three edges from it and the three data at
their ends must line up. One open edge is a finding, not a failure, until its neighbours are read.

**Empty cell (pass 6).** Where no measurement exists, record the empty cell and name the
measurement that would fill it. An empty cell is an honest state, distinct from rejected.

**Fold, don't reverse (pass 6).** When a claim fails, information is not lost: keep the question,
drop the mechanism, feed the question back to pass 1 at lower resolution.

## 3. Quad-core (pass 3), each check independent, no majority rule

- OUTCOME: prediction vs observation. Mismatch → REJECT.
- CONSTRAINT: does the claim survive transformations of scale, time, cost, causality? Violation → REJECT.
- ALTERNATIVE: does a competing explanation have fewer violations? If so → REJECT.
- CONSEQUENCE: if the claim is wrong, what propagates, and is any of it irreversible? Deferred harm → REJECT.

Synthesis: any REJECT → REJECTED. No reject but a check could not run for lack of data → UNSTABLE.
All four NOT_REJECT with data → STABILIZED.

## 4. What every artifact must carry

claim id · pass name · the input it read · the output · the deciding number or measurement
(or "none available") · provenance (which earlier artifacts it cites) · timestamp · model.

## 5. Provisional answers (an answer with its proof is required; silence is for halts)

An UNSTABLE verdict is not a refusal. It is the answer the available proof favors, stated with the proof it
rests on, with what is missing named, and with the next verifiable step. Reasoning stated on partial proof
is how the path to something verifiable gets found; a reader who sees the proof and the gap can take the
next step, and a reader who sees only "unstable" cannot. The rule is: never claim more than the routes
support, and never say less than the routes support. Confident words belong to STABILIZED and LOCKED;
"the proof so far favors X because A and B; what would settle it is C" belongs to UNSTABLE. SILENCE and
REFUSAL are for the ethics gate and for questions outside scope, not for incomplete evidence.

## 5b. Down-wind reality (rule 9 carried to its consequences)

A number can match every source and still be wrong in its reasoning. If a reading is right, the world has to
look a certain way down-wind of it; if the world does not look that way, the reasoning behind the number is
wrong, however good the match. So for every reading the engine names the observable consequences that would
follow if it were true, and checks each against the evidence or against observable reality (the everyday
facts anyone can check: things fall, water flows downhill, a sound inaudible outside a wall was not heard
outside the wall). A verified down-wind mismatch rejects the reading. A mismatch asserted without a
citation is recorded and keeps the reading from standing. "We use the alignments that do not create
down-wind mismatched observables." This is a separate check from the routes: the routes ask whether the
number is reached; the down-wind check asks whether the number can be true.

## 5a. The lock proper: agreement is not the check

Routes agreeing is necessary, not sufficient. Two failures look like agreement:
- **Cyclical agreement**: routes that share an upstream (sources that copied one survey; computations that
  reuse the same cited value; a definition agreeing with a claim that is the same identity). Independence
  is counted after collapsing shared ancestry and shared inputs, and both counts are reported.
- **Confidently wrong agreement**: routes that agree at the corner while a neighbour the routes never
  touched disagrees. Rule 6: a corner is locked only when the three edges from it and the three data at
  their ends line up. So the anchor's three neighbours are checked, not just named; a neighbour that
  contradicts the claim is a vertex misfit, and the claim cannot stand until it is resolved (rule 4.9: read
  the neighbours' ranges first; move the datum if it sits inside them; check the neighbours' calibration
  if it does not). STABILIZED needs two independent agreeing routes. LOCKED needs three, after collapse, and
  all three neighbours lined up. Every verdict names which of these it is: independent agreement, cyclical,
  incomplete (neighbours unchecked), or contradicted by a neighbour.

## 6. Halt conditions

Irreversible harm, consent violated, power asymmetry increased, contradiction that cannot be
resolved in this pass, or scope exceeded. A halt propagates forward; no later pass undoes it.

## 6. A worked example: the motor calculator (full example in `examples/motor/`)

One page takes a motor's nameplate and the circuit around it and derives everything from one structure.
Charge, current, flux and voltage sit on the tetrahedron's corners and never move; the six circuit laws sit
one per face; the equivalent circuit is those faces with values, solved once at the operating point, so
every result (efficiency, amps, power factor, slip, losses, torque, temperature, the conductor, the
breaker) is one derivation and moves together. The start, the reversal and the stop are the same
torque–slip curve read after one, two and three quarter turns; the generator is the half turn past zero
slip; the scale turn reads the same motor at other sizes. Nothing is resized.

Truth there is multi-source, and the page shows it. For the default 10 HP motor: efficiency 91.63 % from
the circuit's loss legs beside 91.7 % from NEMA MG 1 Table 12-12 (a standards table, a different body,
a different process); full-load current 12.29 A from the circuit beside 14 A from NEC Table 430.250 and
beside the nameplate when entered (three readings of one corner, each tied to the rule that uses it);
locked-rotor current 6.34 × beside NEMA code letter G; pull-out 284 % beside Design B's 200 % minimum.
The circuit never looks at the tables; the tables never look at the circuit; the page prints them beside
each other with a verdict and a band (±1 point of efficiency, ±8 % of current, one code letter). The
typical parameters were chosen by behavior: a set that hit the efficiency and missed the pull-out was
thrown out. The lock is the round trip: synthesize the IEEE 112 tests from the motor, extract the motor
back from the tests, and the rated point returns within 0.01 point of efficiency — neighbours finding the
unknown corners, and folding losing nothing. The frame changes no number; the routes establish the number.

That is what every claim should get: a value from the structure, values from independent sources by
their own processes, the band from how precisely each was stated, and the verdict from their agreement.
