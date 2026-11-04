source: Wikipedia, "Induction motor" — revision 1383065711 of 2026-10-31 20:21 UTC (the article now)
url: https://en.wikipedia.org/w/index.php?title=Induction_motor&oldid=1383065711
revision: 1383065711
published: 2026-10-31
retrieved: 2026-11-04 14:44 MST (UTC-0700)
group: wiki:induction-motor
status: encyclopedia article, secondary (its own citations name the primary sources); dated by its revision

An induction motor or asynchronous motor is an AC electric motor in which the electric current in the rotor that produces torque is obtained by electromagnetic induction from the magnetic field of the stator winding. An induction motor therefore needs no electrical connections to the rotor. 
Three-phase squirrel-cage induction motors are widely used as industrial drives because they are self-starting, reliable, and economical. Single-phase induction motors are used extensively for smaller loads, such as garbage disposals and stationary power tools. Although traditionally used for constant-speed service, single- and three-phase induction motors are increasingly being installed in variable-speed applications using variable-frequency drives (VFD). VFD offers energy savings opportunities for induction motors in applications like fans, pumps, and compressors that have a variable load.


== History ==

In 1824, the French physicist François Arago formulated the existence of rotating magnetic fields, termed Arago's rotations. By manually turning switches on and off, Walter Baily demonstrated this in 1879, effectively the first primitive induction motor.
The first commutator-free single-phase AC induction motor was invented by Hungarian engineer Ottó Bláthy; he used the single-phase motor to propel his invention, the electricity meter.
The first AC commutator-free polyphase induction motors were independently invented by Galileo Ferraris and Nikola Tesla, a working motor model having been demonstrated by the former in 1885 and by the latter in 1887. Tesla applied for US patents in October and November 1887 and was granted some of these patents in May 1888. In April 1888, the Royal Academy of Science of Turin published Ferraris's research on his AC polyphase motor detailing the foundations of motor operation. In May 1888 Tesla presented the technical paper A New System for Alternating Current Motors and Transformers to the American Institute of Electrical Engineers (AIEE) describing three four-stator-pole motor types: one having a four-pole rotor forming a non-self-starting reluctance motor, another with a wound rotor forming a self-starting induction motor, and the third a true synchronous motor with a separately excited DC supply to the rotor winding.
George Westinghouse, who was developing an alternating current power system at that time, licensed Tesla's patents in 1888 and purchased a US patent option on Ferraris' induction motor concept. Tesla was also employed for one year as a consultant. Westinghouse employee C. F. Scott was assigned to assist Tesla and later took over development of the induction motor at Westinghouse. Steadfast in his promotion of three-phase development, Mikhail Dolivo-Dobrovolsky invented the cage-rotor induction motor in 1889 and the three-limb transformer in 1890. Furthermore, he claimed that Tesla's motor was not practical because of two-phase pulsations, which prompted him to persist in his three-phase work. Although Westinghouse achieved its first practical induction motor in 1892 and developed a line of polyphase 60 hertz induction motors in 1893, these early Westinghouse motors were two-phase motors with wound rotors until B. G. Lamme developed a rotating bar winding rotor.
The General Electric Company (GE) began developing three-phase induction motors in 1891. By 1896, General Electric and Westinghouse signed a cross-licensing agreement for the bar-winding-rotor design, later called the squirrel-cage rotor. Arthur E. Kennelly was the first to bring out the full significance of complex numbers (using j to represent the square root of minus one) to designate the 90º rotation operator in analysis of AC problems. GE's Charles Proteus Steinmetz improved the application of AC complex quantities and developed an analytical model called the induction motor Steinmetz equivalent circuit.
Induction motor improvements flowing from these inventions and innovations were such that a 100-horsepower induction motor built in the 1970s had the same mounting dimensions as a 7.5-horsepower motor in 1897.


== Principle ==


=== 3-phase motor ===

In both induction and synchronous motors, the AC power supplied to the motor's stator creates a magnetic field that rotates in synchronism with the AC oscillations. Whereas a synchronous motor's rotor turns at the same rate as the stator field, an induction motor's rotor rotates at a somewhat slower speed than the stator field. The induction motor's stator magnetic field is therefore changing or rotating relative to the rotor. This induces an opposing current in the rotor, in effect the motor's secondary winding. The rotating magnetic flux induces currents in the rotor windings, in a manner similar to currents induced in a transformer's secondary winding(s).
The induced currents in the rotor windings in turn create magnetic fields in the rotor that react against the stator field. The direction of the rotor magnetic field opposes the change in current through the rotor windings, following Lenz's Law. The cause of induced current in the rotor windings is the rotating stator magnetic field, so to oppose the change in rotor-winding currents the rotor turns in the direction of the stator magnetic field. The rotor accelerates until the magnitude of induced rotor current and torque balances the load on the rotor. Since rotation at synchronous speed does not induce rotor current, an induction motor always operates slightly slower than synchronous speed. The difference, or "slip," between actual and synchronous speed varies from about 0.5% to 5.0% for standard Design B torque curve induction motors. The induction motor's essential character is that torque is created solely by induction instead of the rotor being separately excited as in synchronous or DC machines or being self-magnetized as in permanent magnet motors.
For rotor currents to be induced, the speed of the physical rotor must be either slower or faster than that of the stator's rotating magnetic field (
  
    
      
        
          n
          
            s
          
        
      
    
    {\displaystyle n_{s}}
  
); otherwise the magnetic field would not be moving relative to the rotor conductors and no currents would be induced. As the speed of the rotor drops below synchronous speed, the rotation rate of the magnetic field in the rotor increases, inducing more current in the windings and creating more torque. The ratio between the rotation rate of the magnetic field induced in the rotor and the rotation rate of the stator's rotating field is called "slip". Under load, the speed drops and the slip increases enough to create sufficient torque to turn the load. For this reason, induction motors are sometimes referred to as "asynchronous motors".
An induction motor can be used as an induction generator, or it can be unrolled to form a linear induction motor which can directly generate linear motion. The generating mode for induction motors is complicated by the need to excite the rotor, which begins with only residual magnetization. In some cases, that residual magnetization is enough to self-excite the motor under load. Therefore, it is necessary to either snap the motor and connect it momentarily to a live grid or to add capacitors charged initially by residual magnetism and providing the required reactive power during operation. Similar is the operation of the induction motor in parallel with a synchronous motor serving as a power factor compensator. A feature in the generator mode in parallel to the grid is that the rotor speed is higher than in the driving mode. Then active energy is being given to the grid. Another disadvantage of the induction motor generator is that it consumes a significant magnetizing current I0 = (20–35)%.


=== Synchronous speed ===
An AC motor's synchronous speed, 
  
    
      
        
          f
          
            s
          
        
      
    
    {\displaystyle f_{s}}
  
, is the rotation rate of the stator's magnetic field

  
    
      
        
          f
          
            s
          
        
        =
        
          
            
              2
              f
            
            p
          
        
        ,
      
    
    {\displaystyle f_{s}={2f \over p},}
  

where 
  
    
      
        f
      
    
    {\displaystyle f}
  
 is the frequency of the power supply in hertz and 
  
    
      
        p
      
    
    {\displaystyle p}
  
 is the number of magnetic poles. For synchronous speed 
  
    
      
        
          n
          
            s
          
        
      
    
    {\displaystyle n_{s}}
  
 in RPM, the formula becomes:

  
    
      
        
          n
          
            s
          
        
        =
        
          
            
              2
              f
            
            p
          
        
        ⋅
        60
        =
        
          
            
              120
              f
            
            p
          
        
        .
      
    
    {\displaystyle n_{s}={\frac {2f}{p}}\cdot 60={\frac {120f}{p}}.}
  

For example, for a four-pole, three-phase motor, 
  
    
      
        p
      
    
    {\displaystyle p}
  
 = 4 and 
  
    
      
        
          n
          
            s
          
        
        =
        
          
            
              120
              f
            
            4
          
        
      
    
    {\displaystyle n_{s}={120f \over 4}}
  
 = 1,500 RPM (for 
  
    
      
        f
      
    
    {\displaystyle f}
  
 = 50 Hz) and 1,800 RPM (for 
  
    
      
        f
      
    
    {\displaystyle f}
  
 = 60 Hz) synchronous speed.
The number of magnetic poles, 
  
    
      
        p
      
    
    {\displaystyle p}
  
, is the number of north and south poles per phase. For example; a single-phase motor with 3 north and 3 south poles, having 6 poles per phase, is a 6-pole motor. A three-phase motor with 18 north and 18 south poles, having 6 poles per phase, is also a 6-pole motor. This industry standard method of counting poles results in the same synchronous speed for a given frequency regardless of polarity.


=== Slip ===
Slip, 
  
    
      
        s
      
    
    {\displaystyle s}
  
, is defined as the difference between synchronous speed and operating speed, at the same frequency, expressed in rpm, or in percentage or ratio of synchronous speed. Thus

  
    
      
        s
        =
        
          
            
              
                n
                
                  s
                
              
              −
              
                n
                
                  r
                
              
            
            
              n
              
                s
              
            
          
        
        
      
    
    {\displaystyle s={\frac {n_{s}-n_{r}}{n_{s}}}\,}
  

where

  
    
      
        
          n
          
            s
          
        
      
    
    {\displaystyle n_{s}}
  
 is stator electrical speed, 
  
    
      
        
          n
          
            r
          
        
      
    
    {\displaystyle n_{r}}
  
 is rotor electrical speed.

For small amounts of slip, torque is approximately by:  

  
    
      
        T
        =
        
          
            
              K
              s
              
                E
                
                  2
                
                
                  2
                
              
              
                R
                
                  2
                
              
            
            
              (
              
                R
                
                  2
                
                
                  2
                
              
              +
              
                s
                
                  2
                
              
              
                X
                
                  2
                
                
                  2
                
              
              )
            
          
        
      
    
    {\displaystyle T={\frac {KsE_{2}^{2}R_{2}}{(R_{2}^{2}+s^{2}X_{2}^{2})}}}
  

Where,

  
    
      
        T
      
    
    {\displaystyle T}
  
: Running Torque

  
    
      
        K
      
    
    {\displaystyle K}
  
: Transformer ratio = Rotor turns/stator turns

  
    
      
        s
      
    
    {\displaystyle s}
  
: Slip of Motor

  
    
      
        
          E
          
            2
          
        
      
    
    {\displaystyle E_{2}}
  
: Rotor Voltage

  
    
      
        
          R
          
            2
          
        
      
    
    {\displaystyle R_{2}}
  
: Rotor Resistance

  
    
      
        
          X
          
            2
          
        
      
    
    {\displaystyle X_{2}}
  
: Rotor Reactance
The equation is correct for small and moderate amounts of slip, but not for large amounts of slip, such as a stopped rotor.  Double revolving field theory (in the next section) provides a better approximation to actual torque.  Slip, which varies from zero at synchronous speed and 1 when the rotor is stalled, influences the motor's torque. 
Because the short-circuited rotor windings have small resistance, even a small slip induces a large current in the rotor and produces significant torque. At full rated load, slip varies from more than 5% for small or special purpose motors to less than 1% for large motors. These speed variations can cause load-sharing problems when differently sized motors are mechanically connected. Various methods are available to reduce slip, VFDs often offering the best solution.


=== Double revolving field ===
 The rotor of an induction motor is subject to two rotating magnet fields, which rotate in opposite directions.  Torque is the result of the difference between these two rotating fields.
The illustration shows torque as a function of slip.  The green line shows torque developed by a single-phase induction motor, without a starting winding. No torque is developed when the rotor is stopped. A slight push in either direction will cause the rotor to accelerate in the direction that it was pushed.
Torque is on the vertical axis shown as a green line, and slip is on the horizontal axis. Slip ranges from zero to zero, corresponding to the reverse and forward directions of the rotor, with 1.0 slip in the center as the point where the rotor is stopped and no torque is produced.
Torque is the net result of two counter-rotating magnetic fields, with one shown as a blue line, and the other shown as a red line.  The red and blue lines are mirror images of the typical torque curve shown in the previous section.


=== Torque ===


==== Standard torque ====

The typical speed-torque relationship of a standard NEMA Design B polyphase induction motor is as shown in the curve at right. Suitable for most low performance loads such as centrifugal pumps and fans, Design B motors are constrained by the following typical torque ranges:

Breakdown torque (peak torque), 175–300% of rated torque
Locked-rotor torque (torque at 100% slip), 75–275% of rated torque
Pull-up torque, 65–190% of rated torque.
Over a motor's normal load range, the torque's slope is approximately linear or proportional to slip because the value of rotor resistance divided by slip, 
  
    
      
        
          R
          
            r
          
          ′
        
        
          /
        
        s
      
    
    {\displaystyle R_{r}'/s}
  
, dominates torque in a linear manner. As load increases above rated load, stator and rotor leakage reactance factors gradually become more significant in relation to 
  
    
      
        
          R
          
            r
          
          ′
        
        
          /
        
        s
      
    
    {\displaystyle R_{r}'/s}
  
 such that torque gradually curves towards breakdown torque. As the load torque increases beyond breakdown torque the motor stalls.


==== Starting ====

There are three basic types of small induction motors: split-phase single-phase, shaded-pole single-phase, and polyphase.
In two-pole single-phase motors, the torque goes to zero at 100% slip (zero speed), so these require alterations to the stator such as shaded-poles to provide starting torque. A single phase induction motor requires separate starting circuitry to provide a rotating field to the motor. The normal running windings within such a single-phase motor can cause the rotor to turn in either direction, so the starting circuit determines the operating direction.

In certain smaller single-phase motors, starting is done by means of a copper wire turn around part of a pole; such a pole is referred to as a shaded pole. The current induced in this turn lags behind the supply current, creating a delayed magnetic field around the shaded part of the pole face. This imparts sufficient rotational field energy to start the motor. These motors are typically used in applications such as desk fans and record players, as the required starting torque is low, and the low efficiency is tolerable relative to the reduced cost of the motor and starting method compared to other AC motor designs.
Larger single phase motors are split-phase motors and have a second stator winding fed with out-of-phase current; such currents may be created by feeding the winding through a capacitor or having it receive different values of inductance and resistance from the main winding. In capacitor-start designs, the second winding is disconnected once the motor is up to speed, usually either by a centrifugal switch acting on weights on the motor shaft or a thermistor which heats up and increases its resistance, reducing the current through the second winding to an insignificant level. The capacitor-run designs keep the second winding on when running, improving torque. A resistance start design uses a starter inserted in series with the startup winding, creating reactance.
Self-starting polyphase induction motors produce torque even at standstill. Available squirrel-cage induction motor starting methods include direct-on-line starting, reduced-voltage reactor or auto-transformer starting, star-delta starting or, increasingly, new solid-state soft assemblies and, of course, variable frequency drives (VFDs).
Polyphase motors have rotor bars shaped to give different speed-torque characteristics. The current distribution within the rotor bars varies depending on the frequency of the induced current. At standstill, the rotor current is the same frequency as the stator current, and tends to travel at the outermost parts of the cage rotor bars (by skin effect). The different bar shapes can give usefully different speed-torque characteristics as well as some control over the inrush current at startup.
Although polyphase motors are inherently self-starting, their starting and pull-up torque design limits must be high enough to overcome actual load conditions.
In wound rotor motors, rotor circuit connection through slip rings to external resistances allows change of speed-torque characteristics for acceleration control and speed control purposes.


==== Speed control ====


===== Resistance =====

Before the development of semiconductor power electronics, it was difficult to vary the frequency, and cage induction motors were mainly used in fixed speed applications. Applications, such as electric overhead cranes, used DC drives or wound rotor motors (WRIM) with slip rings for rotor circuit connection to variable external resistance allowing considerable range of speed control. However, resistor losses associated with low speed operation of WRIMs is a major cost disadvantage, especially for constant loads. Large slip ring motor drives, termed slip energy recovery systems, some still in use, recover energy from the rotor circuit, rectify it, and return it to the power system using a VFD.


===== Cascade =====
The speed of a pair of slip-ring motors can be controlled by a cascade connection, or concatenation. The rotor of one motor is connected to the stator of the other. If the two motors are also mechanically connected, they will run at half speed. This system was once widely used in three-phase AC railway locomotives, such as FS Class E.333. By the turn of this century, however, such cascade-based electromechanical systems became much more efficiently and economically solved using power semiconductor elements solutions.


===== Variable-frequency drive =====

In many industrial variable-speed applications, DC and WRIM drives are being displaced by VFD-fed cage induction motors. The most common efficient way to control asynchronous motor speed of many loads is with VFDs. Barriers to adoption of VFDs due to cost and reliability considerations have been reduced considerably over the past three decades such that it is estimated that drive technology is adopted in as many as 30–40% of all newly installed motors.
Variable frequency drives implement the scalar or vector control of an induction motor.
With scalar control, only the magnitude and frequency of the supply voltage are controlled without phase control (absent feedback by rotor position). Scalar control is suitable for application where the load is constant.
Vector control allows independent control of the speed and torque of the motor, making it possible to maintain a constant rotation speed at varying load torque. But vector control is more expensive because of the cost of the sensor (not always) and the requirement for a more powerful controller.


== Construction ==

The stator of an induction motor consists of poles carrying supply current to induce a magnetic field that penetrates the rotor. To optimize the distribution of the magnetic field, windings are distributed in slots around the stator, with the magnetic field having the same number of north and south poles. Induction motors are most commonly run on single-phase or three-phase power, but two-phase motors exist; in theory, induction motors can have any number of phases. Many single-phase motors having two windings can be viewed as two-phase motors, since a capacitor is used to generate a second power phase 90° from the single-phase supply and feeds it to the second motor winding. Single-phase motors require some mechanism to produce a rotating field on startup. Induction motors using a squirrel-cage rotor winding may have the rotor bars skewed slightly to smooth out torque in each revolution.
Standardized NEMA & IEC motor frame sizes throughout the industry result in interchangeable dimensions for shaft, foot mounting, general aspects as well as certain motor flange aspect. Since an open drip proof (ODP) motor design allows a free air exchange from outside to the inner stator windings, this style of motor tends to be slightly more efficient because the windings are cooler. At a given power rating, lower speed requires a larger frame.


== Rotation reversal ==
The method of changing the direction of rotation of an induction motor depends on whether it is a three-phase or single-phase machine. A three-phase motor can be reversed by swapping any two of its phase connections. Motors required to change direction regularly (such as hoists) will have extra switching contacts in their controller to reverse rotation as needed. A variable frequency drive nearly always permits reversal by electronically changing the phase sequence of voltage applied to the motor.
In a single-phase split-phase motor, reversal is achieved by reversing the connections of the starting winding. Some motors bring out the start winding connections to allow selection of rotation direction at installation. If the start winding is permanently connected within the motor, it is impractical to reverse the sense of rotation. Single-phase shaded-pole motors have a fixed rotation unless a second set of shading windings is provided.


== Power factor ==
The power factor of induction motors varies with load, typically from about 0.85 or 0.90 at full load to as low as about 0.20 at no-load, due to stator and rotor leakage and magnetizing reactances. Power factor can be improved by connecting capacitors either on an individual motor basis or, by preference, on a common bus covering several motors. For economic and other considerations, power systems are rarely power factor corrected to unity power factor.
Power capacitor application with harmonic currents requires power system analysis to avoid harmonic resonance between capacitors and transformer and circuit reactances. Common bus power factor correction is recommended to minimize resonant risk and to simplify power system analysis.


== Efficiency ==

For an electric motor, the efficiency, represented by the Greek letter Eta, is defined as the quotient of the mechanical output power and the electric input power, calculated using this formula:

  
    
      
        η
        =
        
          
            Output Mechanical Power
            Input Electrical Power
          
        
      
    
    {\displaystyle \eta ={\frac {\text{Output Mechanical Power}}{\text{Input Electrical Power}}}}
  

Full-load motor efficiency ranges from 85–97%, with losses as follows:

Friction and windage, 5–15%
Iron or core losses, 15–25%
Stator losses, 25–40%
Rotor losses, 15–25%
Stray load losses, 10–20%.
Regulatory authorities in many countries have implemented legislation to encourage the manufacture and use of higher efficiency electric motors. Some legislation mandates the future use of premium-efficiency induction motors in certain equipment. For more information, see: Premium efficiency.


== Steinmetz equivalent circuit ==
Many useful motor relationships between time, current, voltage, speed, power factor, and torque can be obtained from analysis of the Steinmetz equivalent circuit (also termed T-equivalent circuit or IEEE recommended equivalent circuit), a mathematical model used to describe how an induction motor's electrical input is transformed into useful mechanical energy output. The equivalent circuit is a single-phase representation of a multiphase induction motor that is valid in steady-state balanced-load conditions.
The Steinmetz equivalent circuit is expressed simply in terms of the following components:

Stator resistance and leakage reactance (
  
    
      
        
          R
          
            s
          
        
      
    
    {\displaystyle R_{s}}
  
, 
  
    
      
        
          X
          
            s
          
        
      
    
    {\displaystyle X_{s}}
  
).
Rotor resistance, leakage reactance, and slip (
  
    
      
        
          R
          
            r
          
        
      
    
    {\displaystyle R_{r}}
  
, 
  
    
      
        
          X
          
            r
          
        
      
    
    {\displaystyle X_{r}}
  
 or 
  
    
      
        
          R
          
            r
          
          ′
        
      
    
    {\displaystyle R_{r}'}
  
, 
  
    
      
        
          X
          
            r
          
          ′
        
      
    
    {\displaystyle X_{r}'}
  
, and 
  
    
      
        s
      
    
    {\displaystyle s}
  
).
Magnetizing reactance (
  
    
      
        
          X
          
            m
          
        
      
    
    {\displaystyle X_{m}}
  
).
Paraphrasing from Alger in Knowlton, an induction motor is simply an electrical transformer the magnetic circuit of which is separated by an air gap between the stator winding and the moving rotor winding. The equivalent circuit can accordingly be shown either with equivalent circuit components of respective windings separated by an ideal transformer or with rotor components referred to the stator side as shown in the following circuit and associated equation and parameter definition tables.

The following rule-of-thumb approximations apply to the circuit:

Maximum current happens under locked rotor current (LRC) conditions and is somewhat less than 
  
    
      
        
          V
          
            s
          
        
        
          /
        
        X
      
    
    {\displaystyle V_{\text{s}}/X}
  
, with LRC typically ranging between 6 and 7 times rated current for standard Design B motors.
Breakdown torque 
  
    
      
        
          T
          
            max
          
        
      
    
    {\displaystyle T_{\text{max}}}
  
 happens when 
  
    
      
        s
        ≈
        
          R
          
            r
          
          ′
        
        
          /
        
        X
      
    
    {\displaystyle s\approx R_{\text{r}}'/X}
  
 and 
  
    
      
        
          I
          
            s
          
        
        ≈
        0.7
        
        L
        R
        C
      
    
    {\displaystyle I_{\text{s}}\approx 0.7\;LRC}
  
 such that 
  
    
      
        
          T
          
            max
          
        
        ≈
        K
        
          V
          
            s
          
          
            2
          
        
        
          /
        
        2
        X
      
    
    {\displaystyle T_{\text{max}}\approx KV_{\text{s}}^{2}/2X}
  
 and thus, with constant voltage input, a low-slip induction motor's percent-rated maximum torque is about half its percent-rated LRC.
The relative stator to rotor leakage reactance of standard Design B cage induction motors is

  
    
      
        
          
            
              X
              
                s
              
            
            
              X
              
                r
              
              ′
            
          
        
        ≈
        
          
            0.4
            0.6
          
        
      
    
    {\displaystyle {\frac {X_{\text{s}}}{X_{\text{r}}'}}\approx {\frac {0.4}{0.6}}}
  
.
Neglecting stator resistance, an induction motor's torque curve reduces to the Kloss equation

  
    
      
        
          T
          
            em
          
        
        ≈
        
          
            
              2
              
                T
                
                  max
                
              
            
            
              
                
                  s
                  
                    s
                    
                      max
                    
                  
                
              
              +
              
                
                  
                    s
                    
                      max
                    
                  
                  s
                
              
            
          
        
      
    
    {\displaystyle T_{\text{em}}\approx {\frac {2T_{\text{max}}}{{\frac {s}{s_{\text{max}}}}+{\frac {s_{\text{max}}}{s}}}}}
  
, where 
  
    
      
        
          s
          
            max
          
        
      
    
    {\displaystyle s_{\text{max}}}
  
 is slip at 
  
    
      
        
          T
          
            max
          
        
      
    
    {\displaystyle T_{\text{max}}}
  
.


== Linear induction motor ==

Linear induction motors, which work on the same general principles as rotary induction motors (frequently three-phase), are designed to produce straight line motion. Uses include magnetic levitation, linear propulsion, linear actuators, and liquid metal pumping.


== See also ==
AC motor
Circle diagram
Induction generator
Premium efficiency


== Notes ==


== References ==


== Classical sources ==
Bailey, Benjamin Franklin (1911). The Induction Motor. McGraw-Hill. induction motor.
Behrend, Bernhard Arthur (1901). The Induction Motor: A Short Treatise on its Theory and Design, With Numerous Experimental Data and Diagrams. McGraw Publishing Company / Electrical World and Engineer.
Boy de la Tour, Henri (1906). The Induction Motor: Its Theory and Design, Set Forth By a Practical Method of Calculation. Translated Cyprien Odilon Mailloux. McGraw Pub. Co.


== External links ==

Who Invented the Polyphase Electric Motor?
Silvanus Phillips Thompson: Polyphase electric currents and alternate current motors
Induction motor topics from Hyperphysics website hosted by C.R. Nave, GSU Physics and Astronomy Dept.
Cowern Papers
