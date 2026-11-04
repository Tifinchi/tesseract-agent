source: Motor Breaker Size Chart: NEC Article 430 Sizing Guide & Decision Tree | ElectricalFlux
url: https://electricalflux.com/wire-general/motor-breaker-size-chart-nec-430-guide
retrieved: 2026-11-04 00:58 MST (UTC-0700)
published: 2026-09-09
group: web:electricalflux.com
status: web, secondary unless the page is the primary record; verify against the primary before quoting results

Motor Breaker Size Chart: NEC Article 430 Sizing Guide & Decision Tree | ElectricalFlux 

 General Wiring & Projects Motor Breaker Size Chart: NEC Article 430 Sizing Guide & Decision Tree
 Find the exact breaker size for your AC motor using our NEC Article 430 motor breaker size chart. Includes FLA multipliers, decision trees, and quick-jumps.
 David Chen Published September 9, 2026 

 Sizing a breaker for an AC motor is fundamentally different from sizing one for a resistive load like a baseboard heater. Motors are inductive and draw massive inrush current—known as Locked Rotor Amps (LRA)—during startup. If you size the breaker to the motor's normal running current, it will trip instantly every time you flip the switch. The direct answer: for a standard single-phase AC motor on an inverse-time thermal-magnetic breaker, multiply the motor's Full Load Amps (FLA) by 2.5 (250%) and round up to the next standard breaker size per NEC 240.6.

 The Motor Breaker Size Chart (NEC Article 430)

 The following chart provides the maximum standard inverse-time breaker sizes for common single-phase AC motors. 

 Source Standard: Full Load Amps (FLA) derived from NEC Table 430.248 . Maximum breaker sizing calculated per NEC 430.52 (250% multiplier for inverse-time breakers) and rounded up to standard sizes per NEC 240.6(A). 

 Motor HP 
 115V FLA 
 230V FLA 
 Max Breaker (230V @ 250%) 
 Standard Breaker Size (Round Up) 

 1/2 HP 
 9.8 A 
 4.9 A 
 12.25 A 
 15 A 

 3/4 HP 
 13.8 A 
 6.9 A 
 17.25 A 
 20 A 

 1 HP 
 16.0 A 
 8.0 A 
 20.0 A 
 20 A 

 1.5 HP 
 20.0 A 
 10.0 A 
 25.0 A 
 25 A 

 2 HP 
 24.0 A 
 12.0 A 
 30.0 A 
 30 A 

 3 HP 
 34.0 A 
 17.0 A 
 42.5 A 
 45 A 

 5 HP 
 56.0 A 
 28.0 A 
 70.0 A 
 70 A 

 How to Read This Table

 Start by identifying your system voltage (115V or 230V) and locating the corresponding Full Load Amps (FLA) column. The FLA represents the current the motor draws while running at its rated load and speed. The fourth column applies the NEC 430.52 rule, multiplying the 230V FLA by 2.5 to accommodate the startup inrush current without nuisance tripping. Finally, the fifth column maps that calculated value to the nearest standard breaker size available at your electrical supplier (e.g., 15, 20, 25, 30, 35, 40, 45, 50, 60, 70A). If the exact calculated value matches a standard size, use it; if it falls between sizes, you must round up.

 Which Column Applies and How Derating Modifies Values

 Which column applies to your installation? Always defer to the motor's physical nameplate FLA over the chart's HP-based FLA. Manufacturers design motors with varying efficiencies; a high-efficiency 2 HP motor might only draw 10.5A at 230V, while a standard model draws 12A. If the nameplate is legible, use the printed FLA for your 250% calculation. Only use the HP column in this chart if the nameplate is faded, missing, or unreadable (a common scenario on older pool pumps or vintage table saws). For a deeper understanding of reading these physical labels, refer to Fluke's guide on motor nameplate basics .

 How derating rows modify the base value: Unlike wire ampacity, which requires strict mathematical derating for ambient temperatures above 30°C (86°F) per NEC 310.15, motor branch-circuit short-circuit breakers are not mathematically derated for heat in the same way. The 250% multiplier already provides a massive buffer. However, if your breaker is installed in a high-ambient environment (like an unventilated outdoor pump house in the Southwest hitting 115°F), the breaker's internal thermal bimetallic strip will trip closer to its lower threshold. If you experience 'thermal creep' nuisance tripping in hot environments, the NEC permits you to step up to the next standard breaker size, provided you do not exceed 400% of the FLA for inverse-time breakers under the exceptions in NEC 430.52(C)(1).

 Decision Path: Sizing Your Motor Breaker Step-by-Step

 Follow this exact sequence to terminate your sizing process with one concrete breaker pick. Do not skip steps.

 Motor Breaker Decision Tree

 Step 1: Locate the FLA. Read the motor nameplate. If 230V FLA is 12A, proceed to Step 2. (If no nameplate, use the 230V FLA for the motor's HP from the chart above).

 Step 2: Apply the 250% Multiplier. Multiply the FLA by 2.5. (Example: 12A × 2.5 = 30A).

 Step 3: Match to Standard Sizes. Look at NEC 240.6 standard sizes (15, 20, 25, 30, 35, 40, 45, 50, 60). 

 If the result is an exact standard size (e.g., 30A): Pick that exact size. Result: 30A Breaker. 

 If the result is NOT a standard size (e.g., 12.5A FLA × 2.5 = 31.25A): Round UP to the next standard size. Result: 35A Breaker. 

 Step 4: The Startup Exception. Install the breaker and test motor startup. If the high inrush current still trips the breaker instantly (common with high-inertia loads like large blowers or deep well pumps), invoke NEC 430.52(C)(1)(b). Step up to the next standard size (e.g., move from 35A to 40A). Final Result: 40A Breaker. 

 What the Chart Cannot Tell You (Edge Cases & Limitations)

 A motor breaker size chart is only one-third of the electrical puzzle. Relying on it blindly will lead to failed inspections or burnt wires. Here is what the chart leaves out:

 Wire Sizing (NEC 430.22): You do not size the wire to the breaker. Motor branch circuit conductors must be sized at 125% of the motor's FLA. For a 2 HP motor (12A FLA), the wire must handle 15A (12 × 1.25), meaning 14 AWG copper is technically sufficient for the motor's running load. However, because NEC 430.52 allows a 30A breaker to protect this circuit, you must ensure the motor's internal overload relay is properly sized to protect the 14 AWG wire from continuous overloads. In practice, most electricians pull 10 AWG for a 2 HP / 30A circuit to satisfy local inspectors who default to standard breaker-to-wire mapping (NEC 240.4), but the strict NEC motor rule allows the oversized breaker on smaller wire if the motor overload relay is active and correctly rated.

 Overload Protection vs. Short Circuit Protection: The breaker in the panel only protects against short circuits and ground faults. It does not protect the motor from burning out due to a mechanical jam. That is the job of the motor overload relay (or internal thermal protector), which is sized between 115% and 125% of the FLA. If your motor lacks an internal overload, you must install a manual motor starter with adjustable external overload dials.

 Three-Phase Motors: The chart above is strictly for single-phase AC motors. Three-phase motors draw significantly less current per horsepower. A 5 HP three-phase motor at 230V only draws about 15.2A, requiring a much smaller 40A breaker. Always consult NEC Table 430.250 for three-phase FLA values.

 Bookmark Quick-Jumps: Most Queried Motor Sizes

 For the most common DIY and residential jobsite motors, here are the concrete, final answers for 230V single-phase installations using standard inverse-time breakers:

 Application 
 Motor Size 
 Required 230V Breaker 
 Minimum Copper Wire (125% FLA) 

 Residential Pool Pump 
 1.5 HP 
 25 A (Double Pole) 
 12 AWG THHN / NM-B 

 Table Saw / Air Compressor 
 2 HP 
 30 A (Double Pole) 
 10 AWG THHN / NM-B 

 Deep Well Submersible Pump 
 3 HP 
 45 A (Double Pole) 
 8 AWG THHN / NM-B 

 Commercial HVAC Condenser 
 5 HP 
 70 A (Double Pole) 
 4 AWG THHN 

 Jobsite Tip: When wiring a 230V motor, you are using two hot legs and a ground. There is no neutral wire required for a standard 230V single-phase motor. Ensure your equipment grounding conductor (EGC) is sized per NEC 250.122 based on the breaker size , not the wire size. For a 30A breaker, a 10 AWG copper ground is the minimum requirement.

 Back to Electrical Wiring 
 Related guides
 General Wiring & Projects Best Electrical Wire Tracing Tools for Hidden Circuits (2026) 
 WIRING 

 General Wiring & Projects Real Cost of Electrical Wiring: DIY vs Professional Analysis 
 WIRING 

 General Wiring & Projects Commercial Electrical Wiring Switch Guide: Specs & NEC Rules 
 WIRING 

 General Wiring & Projects Cost of Conduit for Electrical Wiring Underground: 2026 Guide 
 WIRING 

 General Wiring & Projects DIY vs Pro: Decoding the Electrical Wiring Bill Format 
 WIRING 

 General Wiring & Projects Wiring an Electric Fan with Relay: Complete Tool & Material Guide 
 WIRING
