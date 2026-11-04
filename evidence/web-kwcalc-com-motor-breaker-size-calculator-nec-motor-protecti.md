source: Motor Breaker Size Calculator | NEC Motor Protection Sizing
url: https://kwcalc.com/motor/motor-breaker-size-calculator.html
retrieved: 2026-11-04 00:58 MST (UTC-0700)
published: 2026-10-28
group: web:kwcalc.com
status: web, secondary unless the page is the primary record; verify against the primary before quoting results

Motor Breaker Size Calculator | NEC Motor Protection Sizing 

 Motor Breaker Size Calculator

 Determine the correct circuit breaker size for single-phase and three-phase electric motors using NEC 125% motor protection rules, full-load current calculations, and standard breaker ratings.

 By Nadeem Sial , Senior Electrical Engineer Â· Updated October 28, 2026 

 Motor Breaker Size Calculator

 Motor Power 

 HP 
 kW 

 Voltage (V) 

 V 

 Motor Type 

 Three Phase 
 Single Phase 

 Efficiency (%) 

 % 

 Power Factor 

 Calculate Breaker Size 

 Reset

 Recommended Standard Breaker Size

 â A 

 Motor Current

 â

 Minimum Breaker Current

 â

 Recommended Breaker

 â

 Safety Margin

 â

 Calculations are standard engineering estimates. Verify against local electrical codes and motor nameplate data before installation.

 This tool sizes the breaker at 125% of motor full-load current, rounded up to a standard size. NEC 430.52 permits up to 250% of table FLC for inverse-time breakers where needed for starting. Local electrical codes and authority having jurisdiction (AHJ) requirements should always be followed.

 Related Motor Calculators

 Stepper Motor Calculator 

 Trolling Motor Battery Calculator 

 Motor KV Calculator 

 Motor Nameplate Calculator 

 How to Use Motor Breaker Size Calculator

 Selecting the correct circuit breaker for motor overcurrent protection is a critical step in any motor installation. The breaker must carry normal running current, tolerate motor inrush current at startup, and trip rapidly under fault conditions. Use this Motor Current Calculator -backed tool by following the steps below:

 1
 Enter motor power. Input the rated output power from the motor nameplate.

 2
 Select kW or HP. Choose Kilowatts (kW) or Horsepower (HP) depending on your nameplate rating system.

 3
 Enter voltage. Enter the supply voltage in Volts (V) â for example, 230 V, 460 V, or 415 V.

 4
 Select motor type. Choose Single Phase or Three Phase to match your motor supply configuration.

 5
 Enter efficiency. Enter the motor efficiency percentage from the nameplate (default 90%).

 6
 Enter power factor. Enter the operating power factor, typically 0.80 to 0.92 for induction motors (default 0.85).

 How to Calculate Motor Breaker Size

 Motor circuit breaker sizing follows the NEC Article 430 methodology. The process converts nameplate motor power to full-load current, applies a 125% sizing multiplier, and selects the next larger standard breaker rating. The following formulas and worked example demonstrate the complete calculation procedure used by this motor protection calculator:

 Single-Phase Motor Current Formula

 For single-phase motors, the full-load current (FLC) is calculated from the input power divided by the product of voltage, power factor, and efficiency:

 I = (kW Ã 1000) / (V Ã PF Ã Î·)

 Three-Phase Motor Current Formula

 For three-phase motors, the balanced three-phase power formula applies. The â3 factor accounts for the phase relationship in balanced three-phase systems:

 I = (kW Ã 1000) / (â3 Ã V Ã PF Ã Î·)

 Breaker Sizing Formula (NEC 125% Rule)

 This calculator uses 125% of the motor full-load current (the NEC 430.22 conductor sizing factor) as the minimum breaker rating and rounds up to the nearest standard breaker size. NEC 430.52 sets the maximum rating: up to 250% of the table full-load current for an inverse-time breaker.

 Recommended Breaker = Motor FLC Ã 1.25 â Round up to nearest standard size

 Step-by-Step Worked Example

 Given Parameters: 

 Motor Output Power: 10 HP 

 Supply Voltage: 460 V (Three Phase)

 Motor Efficiency: 90% (0.90)

 Power Factor (Cos Ï): 0.85

 Step 1 â Convert HP to kW

 kW = 10 HP Ã 0.746 = 7.46 kW 

 Step 2 â Calculate Motor Full-Load Current

 I = (7.46 Ã 1000) / (1.73205 Ã 460 Ã 0.85 Ã 0.90)

 I = 7460 / (1.73205 Ã 460 Ã 0.765) = 7460 / 609.51 = 12.24 A 

 Step 3 â Apply NEC 125% Breaker Sizing Rule

 Minimum Breaker Current = 12.24 A Ã 1.25 = 15.30 A 

 Step 4 â Select Standard Breaker Size

 Round up 15.30 A to next standard size â 20 A 

 Step 5 â Calculate Safety Margin

 Safety Margin = ((20 A â 12.24 A) / 12.24 A) Ã 100 = 63.4% 

 Final Verified Results

 Motor Full-Load Current: 12.24 A 

 Minimum Breaker Current (125%): 15.30 A 

 Recommended Standard Breaker: 20 A 

 Safety Margin: 63.4% 

 For related motor protection sizing, also see the Motor Cable Size Calculator and the Motor Contactor Size Calculator to complete your motor starter panel design.

 Motor Breaker Size Chart

 This reference chart lists the approximate full-load current (FLC) and recommended circuit breaker sizes for common motor power ratings. Values are based on a supply voltage of 460 V, three-phase configuration, 0.85 power factor, and 90% motor efficiency. Use this chart for quick field reference before detailed calculation.

 Motor Size (HP) 
 Voltage (V) 
 Phase 
 Approx FLC (A) 
 Recommended Breaker 

 1 HP 
 460 V 
 3-Phase 
 1.22 A 
 15 A 

 2 HP 
 460 V 
 3-Phase 
 2.45 A 
 15 A 

 3 HP 
 460 V 
 3-Phase 
 3.67 A 
 15 A 

 5 HP 
 460 V 
 3-Phase 
 6.12 A 
 15 A 

 7.5 HP 
 460 V 
 3-Phase 
 9.18 A 
 15 A 

 10 HP 
 460 V 
 3-Phase 
 12.24 A 
 20 A 

 15 HP 
 460 V 
 3-Phase 
 18.36 A 
 25 A 

 20 HP 
 460 V 
 3-Phase 
 24.48 A 
 35 A 

 25 HP 
 460 V 
 3-Phase 
 30.60 A 
 40 A 

 30 HP 
 460 V 
 3-Phase 
 36.72 A 
 50 A 

 50 HP 
 460 V 
 3-Phase 
 61.20 A 
 80 A 

 Note: Values calculated using 460 V three-phase supply, 90% efficiency, and 0.85 power factor. FLC values are rounded to two decimal places. Always verify against motor nameplate data and local electrical codes. NEC Table 430.52 may allow higher ratings for inverse-time breakers where nuisance tripping occurs. 

 Motor Breaker Size Calculator Frequently Asked Questions

 How do you size a circuit breaker for a motor?

 Size a motor circuit breaker by calculating the full-load current (FLC), then multiplying by 1.25 per the NEC 125% rule for continuous loads. Round up to the nearest standard breaker size. For example, a motor with 20 A FLC gives 20 Ã 1.25 = 25 A, and 25 A is itself a standard breaker size.

 What is the NEC 125% rule for motor protection?

 In NEC Article 430, the 125% factor applies to branch-circuit conductors (430.22), and overload relays are set at 115% to 125% of nameplate current (430.32). The branch-circuit breaker is governed by NEC 430.52, which sets a maximum rather than a minimum: up to 250% of the table full-load current for an inverse-time breaker. Sizing the breaker at 125% of FLC, as this calculator does, is a conservative starting point; if it trips during motor starting, it may be increased up to the Table 430.52 limit.

 What happens if a motor breaker is undersized?

 An undersized breaker will trip repeatedly during motor starting or normal operation due to elevated inrush and running currents. Repeated tripping accelerates breaker wear, causes production downtime, and risks motor damage if the breaker fails to interrupt a fault quickly enough under sustained thermal stress.

 Should I use a fuse or a circuit breaker for motor protection?

 Both are acceptable under NEC Article 430. Time-delay fuses handle motor inrush better and offer faster fault response, while MCCBs provide resettable protection and are more convenient. MCCBs with motor protection settings are preferred in industrial applications for ease of maintenance and faster system restoration after a trip.

 What happens if a motor breaker is oversized?

 An oversized breaker may fail to trip during overloads or minor faults, allowing prolonged overcurrent to damage motor windings, insulation, and bearings. Motor overload relays provide a second protection layer, but the main breaker must still be correctly sized to reliably clear short-circuit faults before catastrophic motor failure occurs.

 Does motor starting current affect breaker selection?

 Yes. Motor inrush current at startup can be 6 to 8 times the full-load current. Standard inverse-time breakers tolerate this brief inrush without tripping. Instantaneous-trip breakers or motor circuit protectors (MCPs) must be set above the inrush level â typically 8 to 13 times FLC â to avoid nuisance tripping during motor starting.

 Standards and References

 The formulas and reference values on this page follow these standards. For design work, check results against the current edition that applies in your country and the equipment manufacturer's data.

 IEC 61439-1 and -2 â Low-voltage switchgear and controlgear assemblies, including busbar temperature-rise limits. Published by IEC .

 IEC 60947-2 and 60947-4-1 â Low-voltage circuit-breakers, contactors and motor starters. Published by IEC .

 IEC 60269-1 â Low-voltage fuses â general requirements. Published by IEC .

 NFPA 70 (NEC) Article 240 â Overcurrent protection and standard breaker and fuse ratings (240.6). Published by NFPA .

 Nadeem Sial

 Senior Electrical Engineer

 This calculator and technical guide were developed and verified by Nadeem Sial to ensure engineering and calculation precision.
 View Full Profile â 

 Related Calculators

 Panel Design 
 Breaker Size Calculator

 Calculate the correct circuit breaker size for single-phase and three-phase electrical loads.

 Open calculator 

 Generator 
 Generator Breaker Size Calculator

 Use our generator-breaker-size-calculator to find the perfect circuit breaker.

 Open calculator 

 Motor 
 Motor kW Calculator

 Calculate electric motor power in kilowatts using voltage, current, power factor, efficiency and motor type.

 Open calculator
