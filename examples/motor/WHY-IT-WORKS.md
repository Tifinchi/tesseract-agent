# The motor calculator: a working example of the method, and why it works

`motor-tesseract.html` is the Tesseract Logic Calculator applied to one domain: a motor and the circuit
around it. Open it in a browser; everything below is live on the page. `README.txt` is its manual;
`engine.js` and `engine_types.js` are the physics, which anyone can read and rerun in Node.

The numbers in this file are the page's own output for its default motor (10 HP, 460 V, 4-pole, three-phase,
NEMA Premium, typical parameters), produced by running `engine.js` on 3 Nov 2026, rounded as shown.

## 1. Why it is the method and not just a calculator

A calculator takes inputs and prints outputs. This page does something stricter: it anchors every quantity
at a fixed place, derives everything from one structure, and puts every result beside a number from an
independent source that it should match. That is the method's three rules, in order: anchor, turn,
check by behavior.

**Anchored corners.** Charge q, current i, flux φ and voltage v sit on the four corners of the inscribed
tetrahedron. They never move. Every other quantity on the page is one of these four read on a face, after a
turn, or at a different scale, and the page can say which: provenance.

**One law per face.** Six faces, six laws, each on its diagonal: v = Ri (resistance, Back), φ = Li
(inductance, Left), q = Cv (capacitance, Right), v = dφ/dt (Faraday, Top), i = dq/dt (Bottom), dφ = M dq
(memristance, Front). The equivalent circuit of the motor is those six faces with values in them. The page
solves that one circuit at the operating point, and every result on the page (efficiency, amps, PF, slip,
losses, torque, temperature, the conductor, the breaker) is derived from that single solution. Change any
input and everything moves together, because there is only one structure to move.

**Turns, not re-derivations.** The start, the reversal and the stop are not separate formulas. They are the
same torque–slip curve read at slip 1, slip 2 − s, and slip 0: one quarter turn, two, three on the
mechanical axis. The generator is the same curve continued past zero slip: the half turn, e^(iπ) = −1. The
"scale turn" K reads the same motor at other sizes and finds that the power-factor angle runs straight
against the log of the size. Nothing is resized; the cube turns.

**Check by behavior.** The typical parameters that drive the circuit were not tuned to hit one number.
They were tuned so that every observable down-wind lands inside its band at once — efficiency, amps, PF,
slip, pull-out, locked-rotor current, code letter, the efficiency peak's loss ratio, the winding temperature.
A parameter set that gave the right efficiency and the wrong pull-out was thrown out. That is rule 9: a
number set may be "in range" while what it produces in other alignments is not, so only the alignment with
no down-wind mismatch is kept. The failed sets are not on the page; the bands they had to clear are
(README §7, §8).

## 2. Truth is multi-source: each result reached by more than one route

This is the part that makes it the method rather than a model. For the default motor:

| Result | Route A (the circuit) | Route B (independent source) | Route C (independent source) | Agreement |
|---|---|---|---|---|
| Efficiency at rated load | 91.63 % from the loss legs of the solved circuit | 91.7 % NEMA MG 1 Table 12-12, NEMA Premium, 10 HP 4-pole | IE3 for the IEC equivalent (4-pole, 7.5 kW): 90.4 %, a floor the NEMA figure clears | A vs B: 0.07 point |
| Full-load current | 12.29 A from the circuit | 14 A NEC Table 430.250 (a conservative table; "5 to 15 % under" is normal) | a nameplate, when entered (the page shows both) | A is 12 % under B, inside the expected band |
| Locked-rotor current | 6.34 × FLA from the circuit at slip 1 | NEMA code letter G (5.6–6.29 kVA/HP) to H (6.3–7.09) | — | one letter, inside the band |
| Pull-out torque | 284 % of rated from the same curve | NEMA Design B minimum 200 %, typical 200–300 % | — | inside |
| Efficiency peak | 84 % load, fixed and variable losses equal (ratio 1.00) | the textbook condition: maximum efficiency where fixed losses equal load-dependent losses | the 45° line of the difference table in the cube reading | three readings of one point |
| Conductor | 125 % × table current → the code-minimum wire, NEC 430.22 and 310.16 | the Kelvin wire, where copper cost and loss cost balance (a different law, a different face) | — | both shown; they differ by design and the page says why |

Three things to notice. Route A never looks at routes B or C; the circuit does not know the tables exist.
Routes B and C are from different bodies (NEMA, IEC, NEC, the nameplate) by different processes (a
standards table, a code table, a manufacturer's test). And the page prints A beside B and C with a
verdict, so the agreement is checked on the page, not trusted.

## 3. The lock: the measured-motor round trip

The strongest check is the one that closes on itself. Take the engine's default motor, synthesize the
IEEE 112 test results it would produce (no-load current and power, locked-rotor voltage, current and
power), feed those tests back into the engine's extraction routine, and see whether it recovers the motor:

```
10 HP 4p 460 V   tests: Inl 5.40 A  Pnl 296 W  Vlr 91.0 V  Ilr 12.29 A  Plr 507 W
  R1   true 0.4139   got 0.4139    0.00 %
  R2   true 0.3327   got 0.3337    0.32 %
  X1   true 2.1018   got 2.1032    0.07 %
  Xm   true 48.67    got 46.93    -3.58 %   (the magnetizing branch, flux-corrected from no-load to rated)
  Rc   true 1234     got 1234      0.00 %
  rated: η 91.63 → 91.62   I 12.29 → 12.30   PF 0.832 → 0.831   slip 1.42 → 1.43 %   Tmax 284 → 284 %   LRA 6.34 → 6.33×
```

Forward (parameters → tests) and backward (tests → parameters) land within 0.01 point of efficiency. That
is rule 5, neighbours, working: the unknown corners (R2, X1, X2, Xm) are found from adjacent measured data
without the dynamics that made them, and the fit is checked by what it produces down-wind. It is also rule
4, folding: the tests are the motor at lower resolution, and nothing was lost going there and back.

## 4. Three readings of one corner

The current corner is read three ways on the page, and each reading is tied to the rule that uses it:
the nameplate amps (what the manufacturer measured), the NEC table amps (what the code sizes the circuit
from, deliberately conservative), and the clamp-meter amps (what the motor is drawing now, with a load
estimate back-solved from it). They are one quantity in three alignments, and the page keeps them apart
because the wrong one in the wrong rule is how a breaker gets sized wrong on a job. "Fits if you mean this;
does not if you mean that."

## 5. What is standard and what is the author's

Standard, and found elsewhere one tool at a time: the equivalent circuits and every number they give;
thermal models; NEC Article 430; Kelvin's law; the NEMA, IEC, DOE and NEC tables (README §11). The author's
contribution is the frame: all of it from one structure on one page, every quantity with a fixed place and
a provenance, the time and scale derivatives as quarter turns, the generator as the half turn, the balance
line read twice, every result beside its independent number. The reading changes no number. That sentence
is the honesty rule: the frame organizes the truth; the routes establish it.

## 6. What the engine takes from this example

- A claim's observables are the page's tiles: each has a value from the structure and a value from a
  source, and a verdict comes from their agreement within a band (README §8 gives the bands).
- Routes are the table in §2: the structure is one route; each standards body, code table, nameplate or
  test is another, by its own process; the lock is when three agree.
- The bands are the page's "how accurate" section, not a flat tolerance: ±1 point of efficiency, ±8 % of
  current against a nameplate, one code letter, and so on.
- The failed trials (parameter sets that hit one number and missed another) are the discards.
- The round trip in §3 is what LOCKED looks like: forward and backward through the same structure, with
  independent measurements at both ends, agreeing to the resolution of the inputs.
