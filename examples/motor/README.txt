MOTOR AND CIRCUIT CALCULATOR
Three-phase induction, single-phase induction, DC brushed, and brushless PM on
a drive, with the feeder, the NEC 430 protection pairing, the start, and an
optional cube-logic reading.
Method and reading: Tifinchi (Tiffany Taylor). Page built with Claude, October 2026.
Version 6 (22 Oct 2026)

Files
  motor-tesseract.html   the whole calculator: one file, no install, no internet needed
  README.txt             this file


1. WHAT IT IS

One page that takes a motor's nameplate (or, for three-phase, its test
results) and the circuit around it, works every operating point from the
motor's equivalent circuit, and shows:

  - rated performance and the operating point you set;
  - the start, the reversal, the stop, and the machine run as a generator;
  - the windings: wye/delta, dual-voltage lead connections, the single-phase
    auxiliary, the DC field; and the reduced-voltage starting methods run
    against the load;
  - conductor sizing and the branch-circuit device, disconnect and overload
    from NEC Article 430, with the inrush check;
  - the three currents that get confused on the job: nameplate, code table,
    and what the motor is actually drawing, with a load estimate from a
    clamp-meter or tachometer reading;
  - power quality, thermal limits, a validation of the model against the
    published tables, and how everything scales with size.

Every check sits beside the NEMA, IEC, DOE or NEC number it should match, so
the model is tested on the page instead of trusted.

Labels (switch at the right of the section bar):
  engineering terms      the default: standard names; the equivalent circuit
                         drawn with live values
  cube logic reading     the same numbers read through the author's frame:
                         faces, the quarter turns J and K, the half turn, the
                         held axis, the balance line
Nothing changes but the words and the centre figure. The physics is standard;
the reading is the author's (sections 6 and 10).


2. OPENING IT

Double-click motor-tesseract.html. Any browser, phones included. Nothing is
sent anywhere; it works offline (the page falls back to the system font). To
share it, send the file. Section headings fold on a click; on a phone all but
the first two sections start folded. The row of links under the title jumps
to each section.


3. QUICK START

  1. Pick the Motor. Then Size, Voltage, Poles (and Type for single-phase or
     DC; rated speed for DC and brushless; the drive supply for brushless).
  2. Read the eight tiles: efficiency and current against the table,
     power factor, speed, the operating point, the efficiency peak, the
     code-minimum conductor, and the branch-circuit device.
  3. Move the Load slider. Open "Protection and field readings" to enter a
     clamp-meter or tachometer reading, pick the breaker or fuse type, set the
     load inertia for the start calculations.
  4. Open "Power quality, thermal and economics" for the real supply.
  5. For a three-phase motor, open "Nameplate, and the measured motor" to
     enter the nameplate (any motor) or IEEE 112 test results (three-phase).


4. INPUTS

Nameplate
  Motor                 three-phase induction (squirrel cage) · single-phase
                        induction · DC brushed · brushless PM on a drive
                        (PMSM, BLDC, ECM).
  Type                  single-phase: capacitor start (CSIR), capacitor start
                        and run (CSCR), permanent split capacitor (PSC),
                        split-phase. DC: permanent magnet, shunt, series,
                        compound.
  System                three-phase and brushless: NEMA (HP, 60 Hz) or IEC
                        (kW, 50 Hz). Single-phase and DC use the NEC tables.
  Size                  three-phase 0.5–500 HP or 0.75–200 kW; single-phase
                        1/6–10 HP; DC 1/4–200 HP; brushless as three-phase.
  Voltage               three-phase NEMA 200/208/230/460/575 V, IEC 380/400/
                        415/690 V; single-phase 115/200/208/230 V; DC armature
                        90/120/180/240/500/550 V; brushless motor 24 to 575 V
                        line-line at rated speed.
  Poles                 2, 4, 6 (brushless 2 to 12). Rated speed, rpm, for DC
                        and brushless.
  Drive supply, front end   brushless only: the drive's input (3-phase 230/
                        400/460/575 V or single-phase 120/240 V) and its
                        rectifier (six-pulse with or without a DC choke, or an
                        active front end / PFC), which set the input current
                        and power factor.
  Load, Load type       10–150 % of rated; constant torque, or pump/fan.
  Drive frequency       three-phase: V/f below base, field weakening above.
  Speed setpoint        brushless: % of rated, 10–150 (constant power above
                        100).
  Armature volts        DC: % of rated, the speed setpoint of a DC drive.
  Feeder run            one way, from the starter (or drive) to the motor.

Nameplate, and the measured motor
  Nameplate efficiency, amps, rpm   any motor: the tiles and checks compare
                        against these instead of the tables, and the nameplate
                        current sets the overload.
  IEEE 112 tests        three-phase only: R1 per phase (line-line ÷ 2, cold),
                        no-load current and watts at rated voltage, locked-
                        rotor volts/amps/watts at reduced voltage (about rated
                        current; never full voltage on a blocked rotor), the
                        test frequency, the leakage split by design letter,
                        friction and windage. The defaults are what the typical
                        10 HP motor would measure: switching to "yes" with them
                        reproduces it, which is the round-trip check.

Protection and field readings
  Raceway ambient, other conductors in the raceway   for the 310.15 derating.
  Available fault current, interrupting rating   kA, for the panel check.
  Drive-to-motor cable, ft   for the reflected-wave flag.
  Capacitors on the load side of the overload   for the 460.9 correction.
  Branch-circuit device     inverse-time breaker, instantaneous-trip breaker
                        (MCP), dual-element time-delay fuse, non-time-delay
                        fuse. Breaker instantaneous multiple (3–20 ×) for the
                        inrush check. Design B energy-efficient (three-phase):
                        the 1100 % MCP row.
  Winding connection    three-phase and brushless: wye or delta, for the
                        per-winding readings. Lead arrangement: 9-lead wye,
                        9-lead delta, 12-lead, for the dual-voltage table.
  External rotor resistance   three-phase: × R2'; 0 is a squirrel cage, any
                        other value is a wound rotor (slip rings), which also
                        changes the Table 430.52 row.
  Autotransformer tap, starter current limit   for the starting-methods table.
  Load inertia          as a multiple of the motor's own (typical: pump 1–2,
                        conveyor 2–5, fan 5–10).
  DC injection braking  three-phase: the DC current as a multiple of FLA.
  Starter or drive current limit   DC and brushless: % of rated.
  Field readings        amps on one line, shaft rpm, line volts: the actual
                        load comes out three ways (section 5, Three loads).

Power quality, thermal and economics
  Supply deviation (%), unbalance (three-phase), THD (three-phase), sag depth
  and duration (induction motors), DC offset in volts (three-phase); ambient,
  altitude, insulation class, service factor, overload relay class; copper
  $/lb, energy $/kWh, run hours, capital rate.


5. THE SECTIONS, IN ORDER (engineering labels; cube label in brackets)

Tiles
  Efficiency and full-load current against the table for this motor type
  (NEMA Premium or IE3; the DOE small-motor floor for single-phase; NEC
  430.247's implied floor for DC; the IE4 floor for brushless), power factor,
  speed, the operating point, the efficiency peak with its loss ratio, the
  code-minimum conductor, and the branch-circuit device with its inrush
  verdict. Green = within the band, yellow = outside but plausible, red = off.

Equivalent circuit at the operating point  [The six faces]
  The circuit drawn with live values: three-phase per-phase circuit;
  single-phase main winding with its forward and backward fields and the
  auxiliary with its capacitor; DC armature loop with E, R_a, brushes and
  field; drive-and-PM-motor per phase. Six cards group the numbers by
  element: resistance, inductance, capacitance, flux and magnetization,
  mechanical, supply. Then the power triangle [sum table] and the loss
  balance [difference table]: fixed losses against load-dependent losses;
  equal at the efficiency peak (ratio 1.00; 45 degrees in the cube reading).
  Losses linear in the load (brushes, a drive's proportional loss) sit
  outside the balance and are shown so.

Checks against known values  [Points of interest]
  One row per condition the circuit predicts, with the computed value, the
  known value, and a verdict. Three-phase: efficiency peak, rated point,
  full-load current, pull-out torque, maximum power transfer (not an
  efficiency optimum), power-factor correction and the self-excitation limit,
  resonance, locked rotor and code letter, Kelvin conductor, unbalance
  derate, DC offset. Single-phase adds starting torque by winding type, the
  no-load current (50–75 % of FLA is normal), the capacitors. DC: speed
  regulation, back-EMF ratio, stall current and starting resistor, brush
  loss, torque per amp. Brushless: motor PF, back-EMF ratio and K_e, base
  speed and field weakening, the drive current limit, line-side harmonics.

Load sensitivity  [Load sweep]
  10 to 150 % of rated: efficiency, PF (E/V for DC), amps, slip or speed,
  torque, loss ratio.

Start, reverse, stop, and the generator  [The time turn: J, J², J³, e^(i pi)]
  The torque–slip curve over the whole range, generator through motor to
  plugging, with the load torque and the DC-injection braking torque drawn
  on it. The table: running (inertia, stored energy); the start
  (acceleration time, peak and average current, heat per start in rotor and
  stator, the rotor's share against ½Jω_s², starts per hour as a thermal
  allowance); the reversal by swapping two leads (current and torque at the
  swap, time to standstill, rotor heat, about three starts' worth); the stop
  (coast, DC injection, plug, regenerative); the same machine driven at
  negative slip as a generator (power out, efficiency, kvar it must draw,
  the self-excitation hazard with a capacitor bank). Single-phase: the start
  with the centrifugal switch dip; no reversal by lead swap, no plugging. DC:
  the current-limited start and its starting resistor, dynamic braking
  resistor, the machine as its own generator above no-load speed. Brushless:
  the drive ramp, regenerative energy and the braking chopper resistor, and
  the back-EMF against the bus at overspeed (the uncontrolled-generator
  fault).

Windings and starting methods  [The same cube, other strings]
  Connection table: wye or delta per-winding volts and amps, the dual-voltage
  lead connections (9-lead wye and delta, 12-lead) with the currents at both
  voltages, the reversal; single-phase 115/230 series/parallel and the
  auxiliary leads; DC field type and lead marks.
  Starting table (three-phase): across the line, wye–delta, part winding,
  autotransformer at the chosen tap, primary resistor to the chosen current,
  soft starter at the chosen limit, and the wound rotor with its external
  resistance, each integrated against the load: line current at start,
  torque at start, whether it reaches speed on the reduced voltage, the
  changeover and its current, the time, the rotor heat. "Cannot move the
  load" and "stalls at N % speed" mean the changeover happens with most of
  the across-the-line inrush, which is the usual wye–delta failure.
  Single-phase: the four winding types at this size side by side (LRA, LRT,
  efficiency, PF, capacitors). DC: the four field types (regulation, torque
  at the current limit). Brushless: time to speed at each drive current limit.

Conductor sizing  [Conductor]
  NEC minimum (125 % of the table current, 75 C copper; parallel sets above
  750 kcmil) and each larger size with drop, efficiency, copper, yearly costs,
  the Kelvin balance and conductor temperature. Two conductors for
  single-phase and DC; the drive's input circuit for brushless. Ampacity
  only: no conduit-fill or ambient correction, no 430.52 sizing here (next
  section).

Protection: the NEC 430 pairing  [The fused face]
  Which current each rule uses (430.6: table for conductor, device and
  disconnect; nameplate for the overload); conductor 430.22; the branch-
  circuit device from Table 430.52 by motor type and device type, with the
  next standard size (240.6) and the Exception 2 ceiling for a hard start;
  the inrush check (1.7 × LRA against the breaker's instantaneous trip, or
  the fuse's short-time hold); disconnect 430.110; overload 430.32 with its
  430.32(C) ceiling. For a drive: 430.122 conductors at 125 % of the drive's
  rated input, the drive as the overload (430.124), and the 430.52 ceiling
  its listing must sit under.

Installation: the pipe, the ground, the panel  [The resistance face in its pipe]
  After the wire size: ampacity after the 310.15 ambient and conductor-
  count derating (raceway ambient and other loaded conductors are inputs;
  the code minimum is bumped when they bite); the equipment grounding
  conductor from 250.122 by the device rating, upsized in proportion when
  the phase conductors are enlarged for voltage drop and never larger than
  them; the EMT trade size from Chapter 9 Tables 4 and 5 at 40 % fill for
  the code-minimum and Kelvin sizes; the voltage dip during the start
  (locked-rotor current through the feeder impedance; over 15 % marginal,
  over 20 % the contactor drops and the start fails on the wire); the
  interrupting rating against the available fault current at the panel
  (110.9, 110.10, 430.8, UL 508A SCCR) with the running motor's first-cycle
  contribution, and the fault current at the motor end through the feeder;
  the 460.9 overload correction when capacitors sit on the load side of
  the relay (the relay must be set from the corrected line current); and
  for a drive-fed motor the reflected wave on a long cable (peak up to 2 ×
  bus past about 50 ft at 460 V / 100 ft at 230 V: inverter-duty motor,
  load reactor or dv/dt filter).

Three loads: nameplate, code table, and the field  [Three readings of the current corner]
  A table with three columns: current, load, power in, efficiency, heat, and
  what each is used for. Nameplate: the overload setting and the thermal
  design point. Code table: conductor, breaker, disconnect, feeder. Field:
  energy cost, heat and life, diagnosis. With a reading entered, the actual
  load comes out four ways: the circuit inverted on the current (exact within
  the model), the DOE current rule, the circuit inverted on the speed, the
  DOE slip rule; a button sets the load slider to it.

System efficiency: load × conductor  [Every variation]
  Motor and feeder together over load and conductor size; the Kelvin size at
  the efficiency-peak load is outlined.

Power quality  [Interference face]
  Three-phase: supply at -10/0/+10 %, unbalance (negative sequence, derate by
  the hottest phase against the NEMA curve), harmonics, DC offset (the
  circuit at zero frequency), sag ride-through and contactor dropout.
  Single-phase: voltage and sag. DC and brushless: what the drive does to the
  line and what it protects the motor from.

Thermal  [Heat]
  Losses to the steady winding temperature, time to the insulation limit,
  life factor, derates, thermal constants, yearly loss cost; the heat chart;
  the overload table (rated, service factor, 125 %, 150 %, -10 % V, the
  chosen point, stall) against the relay or the drive's overload: who trips
  first. For a drive-fed motor the drive's loss is on its own heatsink.

Model validation: every size against the tables  [All sizes against the tables]
  Every size at the chosen voltage, rated load: efficiency against the table
  that applies (NEMA Premium / IE3 / DOE / IE4), current against the NEC
  table (430.250 / 430.248 / 430.247), slip, pull-out, locked rotor. The
  parameters are scaled by size and never see these tables. Three-phase
  4-pole: mean error 0.5 point, 23 of 25 within 1 point.
  Size as the variable [The scale turn K]: the slope of each quantity on a
  log-log fit across the line-up: loss fraction (about -0.2), current (1.0),
  locked-rotor multiple, pull-out, thermal time constant (0.25), inertia
  (1.25), and the power-factor angle, which runs nearly straight against the
  log of the size (about -5 degrees per decade on the 4-pole line-up).

Accuracy and scope  [Accuracy and novelty]
  Sections 8 and 9 below, live on the page.

Sources and assumptions  [Provenance]
  Physics, typical assumptions with their formulas, the tables, and the
  presentation [reading], which changes no number.


6. THE CUBE-LOGIC READING, IN BRIEF (Labels: "cube logic reading")

  Corners       charge q, current i, flux phi, voltage v.
  Faces         one law each: v = Ri, phi = Li, q = Cv, v = dphi/dt,
                i = dq/dt, dphi = M dq. A DC machine has the inductance face
                switched off at steady state; a drive moves the capacitance
                face into its DC bus; the wire is the resistance face read
                from outside the motor, and the fuse sits on it.
  J, the time quarter turn   a time derivative is a quarter turn. On the
                mechanical axis: instant = running, J = the start, J² = the
                reversal (the field turned over, the rotor seeing 2 - s),
                J³ = the stop. On the electrical side the rate cell is the
                load sweep, the inverse cell the conductor, the product cell
                load × conductor.
  e^(i pi) = -1 the half turn: the generator is the motor turned over,
                negative slip, the same curve continued past zero; a DC
                machine becomes its generator the moment E exceeds V.
  K, the scale quarter turn   size as the variable; scale becomes time
                (thermal and mechanical constants grow with size) and scale
                becomes phase (the power-factor angle runs straight against
                the log of the size).
  Held axis     heat and time: what every face's loss turns into, and how
                long a condition can be held.
  Balance line  the 45-degree family of the difference table: loss legs
                balanced is the efficiency peak; copper cost and loss cost
                balanced is the Kelvin conductor. The trap: balancing the
                rotor against the source is pull-out, maximum power transfer,
                not maximum efficiency.
  Three readings of one corner   the current corner read as the nameplate
                says, as the code table says, and as the clamp meter says;
                each tied to the rule that uses it.
  Other strings the same motor connected differently: wye and delta, the
                nine-lead series and parallel, the auxiliary winding, the
                reduced-voltage starts as the quarter turn taken with a face
                scaled.


7. WHAT "GOOD" LOOKS LIKE

  Three-phase: efficiency within 1 point of the table or nameplate; amps 5 to
  15 % under NEC 430.250, within 8 % of a nameplate; pull-out 200 to 300 %;
  locked rotor 5 to 7 × FLA, code F to H; efficiency peak at 75 to 90 % load
  with the loss ratio within 0.1 of 1.00; rated winding about 120 C for
  class F at class B rise.
  Single-phase: efficiency near the DOE floor for capacitor-start motors
  under 3 HP; amps 20 to 35 % under NEC 430.248 (that table is conservative);
  no-load current 50 to 75 % of FLA; capacitor-start LRT 250 to 400 %.
  DC: amps 15 to 30 % under NEC 430.247; speed regulation 3 to 10 % (PM,
  shunt), 10 to 25 % (compound), runaway (series); E/V 85 to 95 %.
  Brushless: motor efficiency 1 to 3 points above the IE4 floor; PF 0.90 to
  0.98; back-EMF 80 to 95 % of the voltage at rated speed.
  If the computed values and the known values disagree by more than the
  bands in section 8, the first suspects are the inputs (voltage, poles, a
  test entered in the wrong units), then the motor not being a standard
  design.


8. HOW ACCURATE

Three-phase, typical parameters: efficiency ±1 point (2 at 1 HP); full-load
amps ±8 % against a nameplate; PF ±0.05; slip ±30 % of itself; pull-out
±20 %; locked rotor ±15 % (one code letter); steady rise ±15 K; thermal times
within a factor of 1.5; relay trip inside its class band; voltage drop ±5 %;
protection sizes exact to the tables, the inrush check a rule of thumb
(1.7 × LRA); start time and heat per start ±25 % with the inertias entered;
plugging, DC injection, coast ±30 %; load from a field reading ±5 % of rated
above half load (current), ±3 % (speed, with a good tachometer); harmonic
loss ±50 %; unbalance derate within 6 points of the NEMA curve; DC offset
exact for the current, first order for torque and saturation.

With a measured three-phase motor: efficiency ±0.5 point; amps ±3 %;
PF ±0.02; slip ±10 %; pull-out ±10 %; locked rotor ±5 %; rise ±10 K.

Single-phase, DC and brushless: typical parameters only; bands about 1.5 ×
the three-phase ones; single-phase starting torque ±30 %; no measured mode.
Part-winding figures (65 % current, 45 % torque) are the classic numbers,
not from the circuit. The scale slopes are a property of the typical
parameters, shown as a check on them.

These bands are estimates of motor-to-motor spread. The outside checks built
into the page are the efficiency and current tables; pull-out, locked rotor,
starting, and the thermal section have not been checked against a measured
motor. The accuracy table on the page says what sets each band.


9. WHAT IS STANDARD AND WHAT IS THE AUTHOR'S

Standard, and found elsewhere: the equivalent circuits and every number they
give (three-phase and single-phase induction, DC, PM on a drive); thermal
models of windings and relays; NEC Article 430 sizing; Kelvin's law;
pull-out, locked rotor, code letters; the starting methods and their
classic ratios; the NEMA, IEC, DOE and NEC tables. Each lives in its own
tool.

What this page does with them: all of it on one page from one circuit per
motor, so any input moves every result together; the three currents kept
apart and tied to their rules; the efficiency peak and the pull-out point
side by side; motor and feeder optimized together; every start method run
against the same load on the same curve; every result beside the number it
should match.

The cube-logic reading (section 6) is the author's: a frame in which every
quantity has a fixed place and a provenance, the time derivative and the
scale derivative are quarter turns, the generator is the half turn, and the
balance line is read twice. It changes no number.


10. LIMITS

Wound-rotor speed control, synchronous wound-field, universal and stepper
motors are not modelled (a wound rotor is covered for starting). Not
modelled: transients and surges, notching, drive bearing currents and
load inertia during a sag, two-speed windings, multiple-motor feeders
(430.24), motor control circuits, raceways other than EMT and conductors
other than THHN, X/R in the fault calculation, arc-flash incident energy. Use the page to
understand and to check; confirm any installation decision against the
nameplate, the manufacturer's data and the code in force.


11. SOURCES USED FOR THE KNOWN VALUES

NEMA MG 1 Table 12-12 (NEMA Premium efficiency, TEFC, 2/4/6-pole, 1-500 HP);
IEC 60034-30-1 IE3 (4-pole, 50 Hz) and IE4 (2/4/6-pole, 0.75-200 kW); DOE
small electric motor standards, 10 CFR 431.446 (capacitor-start and
polyphase open motors, 0.25-3 HP); NEC Tables 430.250 (three-phase),
430.248 (single-phase) and 430.247 (DC) full-load currents; NEC Table 430.52
with 430.52(C) exceptions, 240.6(A) standard ampere ratings, 430.6, 430.22,
430.32, 430.110, 430.122, 430.124, 460.9, 110.9, 110.10, 430.8; NEC Table
310.16 (75 C copper), 310.15(B)(1) and (C)(1) correction and adjustment
factors, Table 250.122, Chapter 9 Tables 4, 5, 8 and 9, 310.10(G); NEMA MG 1
Part 31 (inverter-duty insulation); NEMA MG 1 voltage-unbalance derating curve,
locked-rotor code letters, 12.43 insulation rises, 14.4 altitude; NEMA MG 1
Part 2 lead numbering; IEC 60947-4-1 relay trip classes; IEEE 112
(equivalent-circuit method, leakage split by design letter, stray-load
allowance).
