source: examples/motor/engine.js, solved equivalent circuit for the default 10 HP motor (run 3 Nov 2026; see examples/motor/WHY-IT-WORKS.md)
group: engine
derives_from: test
status: computed output of the equivalent circuit from typical parameters; a model route, not a measurement

Rated operating point from the solved circuit: efficiency 91.63 %, line current 12.29 A, power factor 0.832, slip 1.42 % (rotor speed 1774 rpm), pull-out torque 284 % of rated, locked-rotor current 6.34 times full-load current (77.9 A). Efficiency peak at 84 % load where fixed and variable losses are equal. Round trip through the IEEE 112 tests recovers the rated point within 0.01 point of efficiency.
