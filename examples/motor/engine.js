// Motor Tesseract engine — per-phase induction-motor equivalent circuit,
// typical size-scaled parameters, points of interest, and the known tables.
// Pure functions; no DOM. Used by the page and by the test runner.

// ---------- Known tables (data, with sources) ----------
// NEMA Premium nominal full-load efficiency, totally enclosed fan-cooled,
// 600 V or less (NEMA MG 1 Table 12-12 / DOE 10 CFR 431.25). [2-pole, 4-pole, 6-pole]
const NEMA_PREMIUM_TEFC = {
  1:[77.0,85.5,82.5], 1.5:[84.0,86.5,87.5], 2:[85.5,86.5,88.5], 3:[86.5,89.5,89.5],
  5:[88.5,89.5,89.5], 7.5:[89.5,91.7,91.0], 10:[90.2,91.7,91.0], 15:[91.0,92.4,91.7],
  20:[91.0,93.0,91.7], 25:[91.7,93.6,93.0], 30:[91.7,93.6,93.0], 40:[92.4,94.1,94.1],
  50:[93.0,94.5,94.1], 60:[93.6,95.0,94.5], 75:[93.6,95.4,94.5], 100:[94.1,95.4,95.0],
  125:[95.0,95.4,95.0], 150:[95.0,95.8,95.8], 200:[95.4,96.2,95.8], 250:[95.8,96.2,95.8],
  300:[95.8,96.2,95.8], 350:[95.8,96.2,95.8], 400:[95.8,96.2,95.8], 450:[95.8,96.2,95.8],
  500:[95.8,96.2,95.8]
};
// IEC 60034-30-1 IE3, 4-pole, 50 Hz, nominal efficiency at rated power.
const IE3_4P = {
  0.75:82.5, 1.1:84.1, 1.5:85.3, 2.2:86.7, 3:87.7, 4:88.6, 5.5:89.6, 7.5:90.4, 11:91.4,
  15:92.1, 18.5:92.6, 22:93.0, 30:93.6, 37:93.9, 45:94.2, 55:94.6, 75:95.0, 90:95.2,
  110:95.4, 132:95.6, 160:95.8, 200:96.0
};
// NEC Table 430.250, three-phase induction motors, full-load amperes.
// HP: [200 V, 208 V, 230 V, 460 V, 575 V]  (null = not listed)
const NEC_430_250 = {
  0.5:[2.5,2.4,2.2,1.1,0.9], 0.75:[3.7,3.5,3.2,1.6,1.3], 1:[4.8,4.6,4.2,2.1,1.7],
  1.5:[6.9,6.6,6.0,3.0,2.4], 2:[7.8,7.5,6.8,3.4,2.7], 3:[11.0,10.6,9.6,4.8,3.9],
  5:[17.5,16.7,15.2,7.6,6.1], 7.5:[25.3,24.2,22,11,9], 10:[32.2,30.8,28,14,11],
  15:[48.3,46.2,42,21,17], 20:[62.1,59.4,54,27,22], 25:[78.2,74.8,68,34,27],
  30:[92,88,80,40,32], 40:[120,114,104,52,41], 50:[150,143,130,65,52],
  60:[177,169,154,77,62], 75:[221,211,192,96,77], 100:[285,273,248,124,99],
  125:[359,343,312,156,125], 150:[414,396,360,180,144], 200:[552,528,480,240,192],
  250:[null,null,null,302,242], 300:[null,null,null,361,289], 350:[null,null,null,414,336],
  400:[null,null,null,477,382], 450:[null,null,null,515,412], 500:[null,null,null,590,472]
};
const NEC_VOLTS = [200,208,230,460,575];
// NEMA MG-1 derating factor for voltage unbalance (the published curve, tabulated).
const UNBALANCE_DERATE = [[0,1.00],[0.5,1.00],[1.0,0.99],[1.5,0.97],[2.0,0.95],[2.5,0.93],[3.0,0.89],[3.5,0.85],[4.0,0.82],[4.5,0.78],[5.0,0.76]];

// NEMA voltage menu (60 Hz) and IEC menu (50 Hz)
const NEMA_VOLTAGES = [200,208,230,460,575];
const IEC_VOLTAGES = [380,400,415,690];
const NEMA_HP = [0.5,0.75,1,1.5,2,3,5,7.5,10,15,20,25,30,40,50,60,75,100,125,150,200,250,300,350,400,450,500];
const IEC_KW = [0.75,1.1,1.5,2.2,3,4,5.5,7.5,11,15,18.5,22,30,37,45,55,75,90,110,132,160,200];

// ---------- complex helpers ----------
const C = (re,im)=>({re,im});
const cadd=(a,b)=>C(a.re+b.re,a.im+b.im);
const csub=(a,b)=>C(a.re-b.re,a.im-b.im);
const cmul=(a,b)=>C(a.re*b.re-a.im*b.im,a.re*b.im+a.im*b.re);
const cdiv=(a,b)=>{const d=b.re*b.re+b.im*b.im;return C((a.re*b.re+a.im*b.im)/d,(a.im*b.re-a.re*b.im)/d);};
const cabs=a=>Math.hypot(a.re,a.im);
const cpar=(a,b)=>cdiv(cmul(a,b),cadd(a,b));
const cinv=a=>cdiv(C(1,0),a);

// ---------- typical parameters, scaled by size ----------
// Per-unit on S_base = P_rated / 0.78. Exponents follow the size trend of
// NEMA design B motors (resistances fall with size; magnetizing reactance rises).
function typicalParams(hp, poles){
  const lg=Math.log10(hp);
  const pole=poles;
  const r1=0.040*Math.pow(hp,-0.33);                       // stator resistance, pu
  const r2=0.030*Math.pow(hp,-0.30);                       // rotor resistance (referred), pu
  const x1=0.085+0.010*lg, x2=x1;                          // leakage reactances, pu
  const xm=Math.min(4.0,1.3+0.9*lg)*({2:1.15,4:1.0,6:0.85,8:0.72}[pole]);   // magnetizing, pu
  const core=0.034*Math.pow(hp,-0.17)*({2:1.3,4:1.0,6:0.9,8:0.85}[pole]);   // core loss / P_rated
  const fw=0.024*Math.pow(hp,-0.24)*({2:1.6+2.5/hp,4:1.0,6:0.8,8:0.7}[pole]); // friction & windage / P_rated
  const stray= hp<=125?0.018: hp<=500?0.015:0.012;         // IEEE 112 stray-load allowance
  return {r1,r2,x1,x2,xm,core,fw,stray};
}

// ---------- the motor at one operating point ----------
// spec: {P_W (rated output, W), V_LL (line-line volts), f (Hz), poles, hp (size for scaling)}
// opts: {vdev (fraction, e.g. +0.1), unbalance (%), thd (%), kvar (capacitor kvar, 3-phase)}
function buildMotor(spec){
  const p=typicalParams(spec.hp,spec.poles);
  const S_base=spec.P_W/0.78;
  const Z_base=spec.V_LL*spec.V_LL/S_base;
  const V1=spec.V_LL/Math.sqrt(3);
  const ns=120*spec.f/spec.poles;            // rpm
  const ws=2*Math.PI*ns/60;                  // rad/s
  const m={
    R1:p.r1*Z_base, X1:p.x1*Z_base, R2:p.r2*Z_base, X2:p.x2*Z_base, Xm:p.xm*Z_base,
    Rc:3*V1*V1/(p.core*spec.P_W),            // core loss = p.core*P at rated voltage
    Pfw0:p.fw*spec.P_W, Pstray0:p.stray*spec.P_W,
    V1, ns, ws, pu:p, Z_base, S_base, spec,
    ffac:1, sat:{a:0.25,n:6}, measured:false   // drive frequency / base; magnetizing saturation
  };
  if(spec.measured){ const t=paramsFromTests(spec,spec.measured); Object.assign(m,{R1:t.R1,R2:t.R2,X1:t.X1,X2:t.X2,Xm:t.Xm,Rc:t.Rc,Pfw0:t.Pfw0,Pstray0:t.Pstray0,measured:true,tests:t});
    // the no-load test sees the magnetizing reactance at no-load flux, a little above rated; bring it to rated flux through the saturation curve
    for(let k=0;k<12;k++){ const ref=ratedPoint(m); if(!ref) break; const g=(1+m.sat.a*Math.pow(t.E_nl/ref.E,m.sat.n))/(1+m.sat.a); const Xm=t.Xm*g; const done=Math.abs(Xm-m.Xm)<1e-9*Xm; m.Xm=Xm; if(done) break; }
  }
  m._ref=ratedPoint(m);                       // rated point: base frequency, rated voltage, linear X_m
  m.E_ref=m._ref?m._ref.E:undefined;                           // rated air-gap EMF: the flux reference for saturation
  m.ffac=spec.ffac||1;
  return m;
}
// Saturation: the magnetizing current rises faster than the flux above the knee.
// g = (1 + a·φ^n)/(1 + a) with φ the flux relative to rated (E/f against E_ref/f_base); g = 1 at rated.
function satFactor(m, E){ if(!m.E_ref) return 1; const ff=m.ffac||1; const phi=E/(ff*m.E_ref); return (1+m.sat.a*Math.pow(phi,m.sat.n))/(1+m.sat.a); }
// The circuit at the drive frequency: reactances scale with f, core-loss resistance as f^0.7
// (hysteresis and eddy together), the voltage follows V/f below base and holds above it.
function atFreq(m){ const ff=m.ffac||1; return {ff, vf: ff<=1?ff:1, X1:m.X1*ff, X2:m.X2*ff, Xm:m.Xm*ff, Rc:m.Rc*Math.pow(ff,0.7), ws:m.ws*ff, ns:m.ns*ff}; }

function solvePoint(m, s, vfac=1){
  const q=atFreq(m);
  const V=C(m.V1*vfac*q.vf,0);
  const Zr=C(m.R2/s,q.X2);
  let Xm=q.Xm, Zmag, Zgap, Zin, I1, E, Ea=0;
  for(let k=0;k<10;k++){
    Zmag=cpar(C(q.Rc,0),C(0,Xm)); Zgap=cpar(Zmag,Zr); Zin=cadd(C(m.R1,q.X1),Zgap);
    I1=cdiv(V,Zin); E=cmul(I1,Zgap); const Enew=cabs(E);
    const Xnew=q.Xm/satFactor(m,Enew);
    if(Math.abs(Enew-Ea)<1e-7*Math.max(1,Enew)) {Xm=Xnew; break;}
    Ea=Enew; Xm=0.5*Xm+0.5*Xnew;
  }
  Zmag=cpar(C(q.Rc,0),C(0,Xm)); Zgap=cpar(Zmag,Zr); Zin=cadd(C(m.R1,q.X1),Zgap); I1=cdiv(V,Zin); E=cmul(I1,Zgap);
  const I2=cdiv(E,Zr);
  const I1a=cabs(I1), I2a=cabs(I2); Ea=cabs(E);
  const Pin=3*(V.re*I1.re+V.im*I1.im);
  const Pscl=3*I1a*I1a*m.R1;
  const Pcore=3*Ea*Ea/q.Rc;
  const Pag=3*I2a*I2a*m.R2/s;
  const Prcl=s*Pag;
  const Pmech=(1-s)*Pag;
  const n=(1-s)*q.ns;
  const Pfw=m.Pfw0*Math.pow((1-s)*q.ff,2.5);
  const Tg=Pag/q.ws;
  return {s,n,V1:V.re,I1:I1a,I1c:I1,I2:I2a,E:Ea,Pin,Pscl,Pcore,Pag,Prcl,Pmech,Pfw,Tg,Zin,Zgap,Zmag,
          Q:3*(V.re*(-I1.im)), S:3*V.re*I1a, Xm_eff:Xm, sat:q.Xm/Xm, flux:Ea/(q.ff*(m.E_ref||Ea)), ws:q.ws, ns:q.ns, ff:q.ff};
}

function pullout(m, vfac=1){
  const q=atFreq(m);
  const Zmag=cpar(C(q.Rc,0),C(0,q.Xm));
  const Zs=C(m.R1,q.X1);
  const Vth=m.V1*vfac*q.vf*cabs(Zmag)/cabs(cadd(Zs,Zmag));
  const Zth=cpar(Zs,Zmag);
  const Rth=Zth.re, Xth=Zth.im;
  const smax=m.R2/Math.hypot(Rth,Xth+q.X2);
  const Tmax=3*Vth*Vth/(2*q.ws*(Rth+Math.hypot(Rth,Xth+q.X2)));
  return {smax,Tmax,Rth,Xth,Vth};
}

// Rated point at rated voltage: stray ∝ (P_mech/P_rated)², which equals the
// rated stray allowance at the solution. Its rotor current is the reference
// for stray scaling (∝ I2², i.e. ∝ torque²) at every other point.
function ratedPoint(m){
  const saveF=m.ffac, saveE=m.E_ref; m.ffac=1; m.E_ref=null;
  const out=ratedPointInner(m); m.ffac=saveF; m.E_ref=saveE; return out;
}
function ratedPointInner(m){
  const P=m.spec.P_W, po=pullout(m,1);
  const outAt=s=>{const r=solvePoint(m,s,1); r.Pstray=m.Pstray0; r.Pout=r.Pmech-r.Pfw-r.Pstray; return r;};   // rated stray allowance by definition
  let lo=1e-7, hi=po.smax*0.98;
  if(outAt(hi).Pout<P) return null;
  for(let k=0;k<80;k++){const mid=0.5*(lo+hi); if(outAt(mid).Pout<P) lo=mid; else hi=mid;}
  return outAt(0.5*(lo+hi));
}
// Solve for the slip that delivers P_out = load·P_rated at voltage factor vfac
// Below base frequency the load is a fraction of rated torque (a drive holds V/f and torque);
// above base the drive holds voltage, so available power is constant. A centrifugal load
// (pump or fan) follows the affinity law: torque ∝ speed², so load·ff² of rated torque.
function solveLoad(m, load, vfac=1){
  const ref=m._ref||(m._ref=ratedPoint(m)); if(!ref) return null;
  const ff=m.ffac||1; const tq=(m.loadType==='pump')? load*ff*ff : load;
  const P_target=tq*m.spec.P_W*Math.min(1,ff);
  const po=pullout(m,vfac);
  const outAt=s=>{const r=solvePoint(m,s,vfac); r.Pstray=m.Pstray0*(r.I2/ref.I2)**2; r.Pout=r.Pmech-r.Pfw-r.Pstray; return r;};
  let lo=1e-7, hi=po.smax*0.98;
  if(outAt(hi).Pout<P_target) return null;
  for(let k=0;k<80;k++){const mid=0.5*(lo+hi); if(outAt(mid).Pout<P_target) lo=mid; else hi=mid;}
  const r=outAt(0.5*(lo+hi));
  r.load=load; r.eta=r.Pout/r.Pin; r.pf=r.Pin/r.S;
  r.T=r.Pout/(2*Math.PI*r.n/60);
  r.Tr_ref=(m._ref?m._ref.Pag/m.ws:r.Pag/r.ws);
  r.Ploss=r.Pin-r.Pout;
  r.Pconst=r.Pcore+r.Pfw; r.Pvar=r.Pscl+r.Prcl+r.Pstray;
  r.pullout=po;
  return r;
}

// Split the losses into the leg that does not move with load and the leg that does.
// The magnetizing current's share of stator copper loss belongs to the fixed leg.
function splitLosses(m, r){
  const nl=m._nl||(m._nl=solvePoint(m,1e-7,1));
  const Pcu_fixed=3*nl.I1*nl.I1*m.R1;
  const fixed=r.Pcore+r.Pfw+Pcu_fixed;
  const variable=(r.Pscl-Pcu_fixed)+r.Prcl+r.Pstray;
  return {fixed,variable,Pcu_fixed};
}
// Max-efficiency load by golden-section search; the legs at that point are reported
// so the balance can be checked rather than assumed.
function lossBalance(m){
  let a=0.05,b=3.0; const g=(Math.sqrt(5)-1)/2;
  const eta=L=>{const r=solveLoad(m,L); return r? r.eta : -1;};
  let c=b-g*(b-a), d=a+g*(b-a), fc=eta(c), fd=eta(d);
  for(let k=0;k<60;k++){ if(fc>fd){b=d;d=c;fd=fc;c=b-g*(b-a);fc=eta(c);} else {a=c;c=d;fc=fd;d=a+g*(b-a);fd=eta(d);} }
  let L=0.5*(a+b); let r=solveLoad(m,L);
  if(!r){ let best=null; for(let x=0.05;x<=3.0;x+=0.05){ const q=solveLoad(m,x); if(q&&(!best||q.eta>best.eta)){best=q;L=x;} } r=best; }
  if(!r) return null;
  const legs=splitLosses(m,r);
  return {load:L, r, legs, ratio:legs.variable/legs.fixed, angle:Math.atan2(legs.variable,legs.fixed)*180/Math.PI};
}

// Locked rotor: deep-bar rotor (R2 up with rotor frequency) and leakage-path
// saturation (X1, X2 down) at standstill, the standard design-B behaviour.
function lockedRotor(m, vfac=1){
  const q=atFreq(m);
  const V=C(m.V1*vfac*q.vf,0);
  const kR=kRofSize(m.spec.hp);   // deep-bar rise of rotor resistance at standstill
  const Zr=C(m.R2*kR,q.X2*0.75);
  const Zmag=cpar(C(q.Rc,0),C(0,q.Xm));
  const Zgap=cpar(Zmag,Zr);
  const Zin=cadd(C(m.R1,q.X1*0.8),Zgap);
  const I1=cdiv(V,Zin); const E=cmul(I1,Zgap); const I2=cdiv(E,Zr);
  const I_LR=cabs(I1); const T_LR=3*cabs(I2)**2*m.R2*kR/q.ws;
  const kvaPerHp=Math.sqrt(3)*m.spec.V_LL*vfac*I_LR/1000/(m.spec.P_W/746);
  const codes=[['A',0,3.15],['B',3.15,3.55],['C',3.55,4.0],['D',4.0,4.5],['E',4.5,5.0],['F',5.0,5.6],['G',5.6,6.3],['H',6.3,7.1],['J',7.1,8.0],['K',8.0,9.0],['L',9.0,10.0],['M',10.0,11.2],['N',11.2,12.5],['P',12.5,14.0],['R',14.0,16.0],['S',16.0,18.0],['T',18.0,20.0],['U',20.0,22.4],['V',22.4,1e9]];
  const code=(codes.find(c=>kvaPerHp>=c[1]&&kvaPerHp<c[2])||codes[codes.length-1])[0];
  return {I_LR, kvaPerHp, code, T_LR, pf:Math.cos(Math.atan2(-I1.im,I1.re))};
}

// Negative-sequence (unbalance) extra loss at an operating point
function unbalanceLoss(m, r, u){ // u = unbalance fraction (e.g. 0.03)
  if(u<=0) return {I1n:0,I2n:0,dP:0};
  const s=r.s, s2=2-s;
  const q=atFreq(m);
  const R2n=m.R2*1.4;                      // rotor resistance at near-double frequency (skin)
  const Zr=C(R2n/s2,q.X2);
  const Zgap=cpar(C(0,q.Xm),Zr);
  const Zin=cadd(C(m.R1,q.X1),Zgap);
  const Vn=u*m.V1*q.vf;
  const I1n=Vn/cabs(Zin);
  const E=I1n*cabs(Zgap);
  const I2n=E/cabs(Zr);
  const dP=3*(I1n*I1n*m.R1+I2n*I2n*R2n);
  return {I1n,I2n,dP};
}
function derateFromTable(u){ // u in percent
  const t=UNBALANCE_DERATE; if(u<=0) return 1; if(u>=5) return 0.76;
  for(let i=1;i<t.length;i++){ if(u<=t[i][0]){const [a,fa]=t[i-1],[b,fb]=t[i]; return fa+(fb-fa)*(u-a)/(b-a);} }
  return 0.76;
}
// Load at which (rated-load loss) = loss(load) + extra; a loss-budget derate
function derateFromLoss(m, extraW){
  const rr=solveLoad(m,1)||(m._ref); if(!rr) return 1; const budget=rr.Ploss!=null?rr.Ploss:(rr.Pin-rr.Pout);
  let lo=0.3, hi=1.0;
  for(let k=0;k<40;k++){const mid=0.5*(lo+hi); const r=solveLoad(m,mid); if(!r){hi=mid;continue;} const tot=r.Ploss+extraW; if(tot>budget) hi=mid; else lo=mid;}
  return 0.5*(lo+hi);
}
// Harmonic extra loss for a given voltage THD (%) split over 5,7,11,13
function harmonicLoss(m, r, thd){
  if(thd<=0) return {dP:0,hvf:0,parts:[]};
  const split=[[5,0.80],[7,0.50],[11,0.25],[13,0.20]]; // fractions of THD (sum of squares ≈ 1)
  let dP=0, hvf2=0; const parts=[]; const q=atFreq(m);
  for(const [h,f] of split){
    const Vh=thd/100*f*m.V1*q.vf; hvf2+=(thd/100*f)**2/h;
    const sh = (h%6===5)? (h+1-r.s)/h : (h-1+r.s)/h;   // 5th,11th negative seq; 7th,13th positive
    const sk=Math.sqrt(h);
    const Zr=C(m.R2*sk/sh, h*q.X2);
    const Zgap=cpar(C(0,h*q.Xm),Zr);
    const Zin=cadd(C(m.R1*sk,h*q.X1),Zgap);
    const Ih=Vh/cabs(Zin); const I2h=Ih*cabs(Zgap)/cabs(Zr);
    const p=3*(Ih*Ih*m.R1*sk+I2h*I2h*m.R2*sk); dP+=p; parts.push({h,Vh,Ih,p});
  }
  return {dP,hvf:Math.sqrt(hvf2),parts};
}

// Capacitor sizing (three-phase kvar) for a target PF, and the self-excitation limit
function capacitors(m, r){
  const P=r.Pin, Q=r.Q;
  const Qunity=Q;                                 // kvar to reach unity
  const Q95=Q-P*Math.tan(Math.acos(0.95));        // kvar to reach 0.95 lag
  const nl=solvePoint(m,1e-7);                    // no-load (ideal)
  const Qnl=nl.Q;                                  // no-load magnetizing kvar
  const Qlimit=0.9*Qnl;                            // common rule: ≤ 90 % of no-load kvar
  const q=atFreq(m); const w=2*Math.PI*m.spec.f*q.ff;
  const Cres=1/(w*w*(q.Xm/w));                      // C that resonates with X_m (per phase, wye)
  const Cunity=Qunity/(3*w*(m.V1*q.vf)**2);
  return {Qunity,Q95,Qnl,Qlimit,Cunity,Cres,ratio:Cunity/Cres};
}

// ---------- known lookups ----------
function knownEta(system, size, poles){
  if(system==='NEMA'){const row=NEMA_PREMIUM_TEFC[size]; if(!row) return null; return row[{2:0,4:1,6:2}[poles]]??null;}
  if(poles!==4) return null; return IE3_4P[size]??null;
}
function knownFLA(hp, V){ const row=NEC_430_250[hp]; if(!row) return null; const i=NEC_VOLTS.indexOf(V); if(i<0) return null; return row[i]; }

function makeSpec(system,size,V,poles,freqHz){
  const P_W = system==='NEMA'? size*746 : size*1000;
  const hp = system==='NEMA'? size : size/0.746;
  const f=system==='NEMA'?60:50;
  return {P_W, V_LL:V, f, poles, hp, size, system, ffac: freqHz? freqHz/f : 1};
}

const MotorEngine={NEMA_PREMIUM_TEFC,IE3_4P,NEC_430_250,NEC_VOLTS,UNBALANCE_DERATE,NEMA_VOLTAGES,IEC_VOLTAGES,NEMA_HP,IEC_KW,
  typicalParams,buildMotor,solvePoint,solveLoad,ratedPoint,pullout,splitLosses,lossBalance,lockedRotor,unbalanceLoss,derateFromTable,derateFromLoss,harmonicLoss,capacitors,knownEta,knownFLA,makeSpec};
if(typeof module!=='undefined') module.exports=MotorEngine;

// ---------- Half turn: the conductor (NEC Chapter 9 Tables 8/9, Table 310.16) ----------
// size, kcmil, DC resistance Ω/1000 ft at 75 °C (Table 8, uncoated copper),
// AC reactance Ω/1000 ft in PVC conduit (Table 9), ampacity A (310.16, 75 °C copper)
const WIRE=[
 ['14 AWG',4.11,3.07,0.058,20],['12 AWG',6.53,1.93,0.054,25],['10 AWG',10.38,1.21,0.050,35],
 ['8 AWG',16.51,0.764,0.052,50],['6 AWG',26.24,0.491,0.051,65],['4 AWG',41.74,0.308,0.048,85],
 ['3 AWG',52.62,0.245,0.047,100],['2 AWG',66.36,0.194,0.045,115],['1 AWG',83.69,0.154,0.046,130],
 ['1/0 AWG',105.6,0.122,0.044,150],['2/0 AWG',133.1,0.0967,0.043,175],['3/0 AWG',167.8,0.0766,0.042,200],
 ['4/0 AWG',211.6,0.0608,0.041,230],['250 kcmil',250,0.0515,0.041,255],['300 kcmil',300,0.0429,0.041,285],
 ['350 kcmil',350,0.0367,0.040,310],['400 kcmil',400,0.0321,0.040,335],['500 kcmil',500,0.0258,0.039,380],
 ['600 kcmil',600,0.0214,0.039,420],['750 kcmil',750,0.0171,0.038,475]
].map(([name,kcmil,R,X,amp])=>({name,kcmil,R,X,amp,lbPerKft:3.05*kcmil}));

// Parallel sets (NEC 310.10(G): 1/0 AWG and larger may be paralleled): each set carries its share,
// so the set resistance and reactance divide by the count and the ampacity and copper multiply.
const WIRE_OPTS=[];
for(const sets of [1,2,3,4]) for(const w of WIRE){ if(sets>1&&w.kcmil<105) continue;
  WIRE_OPTS.push({name:sets>1?`${sets} × ${w.name}`:w.name, kcmil:w.kcmil*sets, R:w.R/sets, X:w.X/sets, amp:w.amp*sets, lbPerKft:w.lbPerKft*sets, sets, base:w}); }
WIRE_OPTS.sort((a,b)=>a.amp-b.amp||a.sets-b.sets);
// Minimum conductor: ampacity ≥ 125 % of the Table 430.250 current (NEC 430.22),
// or of the computed current where the size is not in the table.
function minWireIndex(I_table){ const need=1.25*I_table; const i=WIRE_OPTS.findIndex(w=>w.amp>=need); return i<0?WIRE_OPTS.length-1:i; }

// One wire choice: voltage drop, terminal voltage, motor re-solved at that voltage,
// feeder loss, system efficiency, copper and Kelvin's-law cost balance.
// econ: {dollarsPerLb, dollarsPerKWh, hoursPerYear, capitalRate (per year), installFactor}
// opts: {phases: 3 | 1 | 0 (DC), solve: (load, vfac) → point with I1, pf, Pin, Pout; V: line voltage}
function wireCase(m, load, w, lengthFt, econ, opts={}){
  const ph=opts.phases??3; const solve=opts.solve||((L,vf)=>solveLoad(m,L,vf)); const V=opts.V||m.spec.V_LL;
  const kv= ph===3?Math.sqrt(3):2; const nc= ph===3?3:2; const cur=r=>opts.current?opts.current(r):r.I1; const pfOf=r=>opts.pf?opts.pf(r):r.pf;
  // iterate: motor current depends on terminal voltage which depends on current
  let vfac=1, r=null;
  for(let k=0;k<12;k++){
    r=solve(load,vfac); if(!r) return null;
    const theta= ph===0?0:Math.acos(Math.min(1,pfOf(r)));
    const vd=kv*cur(r)*lengthFt/1000*(w.R*Math.cos(theta)+(ph===0?0:w.X*Math.sin(theta)));
    vfac=(V-vd)/V;
  }
  const theta= ph===0?0:Math.acos(Math.min(1,pfOf(r)));
  const vd=kv*cur(r)*lengthFt/1000*(w.R*Math.cos(theta)+(ph===0?0:w.X*Math.sin(theta)));
  const Pwire=nc*cur(r)*cur(r)*w.R*lengthFt/1000;
  const Pin_sys=r.Pin+Pwire;
  const eta_sys=r.Pout/Pin_sys;
  const copperLb=nc*w.lbPerKft*lengthFt/1000;
  const capital=copperLb*econ.dollarsPerLb*econ.installFactor;
  const annualCapital=capital*econ.capitalRate;
  const annualLoss=Pwire/1000*econ.hoursPerYear*econ.dollarsPerKWh;
  return {w,r,vfac,vd,vdPct:100*vd/V,Pwire,eta_sys,copperLb,capital,annualCapital,annualLoss,
          angle:Math.atan2(annualLoss,annualCapital)*180/Math.PI};
}
// Kelvin's law: the continuous optimum area where annual loss cost = annual conductor cost.
// For resistance R = ρ/A per unit length, loss cost ∝ I²ρ/A and capital ∝ A, so
// A_opt = I·sqrt(c_loss·ρ / c_cap) — then the nearest standard size.
function kelvinOptimum(m, load, lengthFt, econ, opts={}){
  const solve=opts.solve||((L,vf)=>solveLoad(m,L,vf)); const r=solve(load,1); if(!r) return null;
  const I=opts.current?opts.current(r):r.I1; const nc=(opts.phases??3)===3?3:2;
  // ρ in Ω·kcmil/1000 ft at 75 °C ≈ 12.9 (from Table 8: 4.11 kcmil × 3.07 Ω/kft)
  const rho=12.9;
  const cLoss=nc*econ.hoursPerYear*econ.dollarsPerKWh/1000;      // $/yr per (A²·Ω) per 1000 ft, all conductors
  const cCap=nc*3.05*econ.dollarsPerLb*econ.installFactor*econ.capitalRate; // $/yr per kcmil per 1000 ft
  const Aopt=I*Math.sqrt(cLoss*rho/cCap);
  let best=WIRE_OPTS[0], bestd=1e9; for(const w of WIRE_OPTS){const d=Math.abs(Math.log(w.kcmil/Aopt)); if(d<bestd-1e-9){bestd=d;best=w;}}
  return {Aopt,nearest:best,I};
}

// Three-quarter turn: system efficiency over load × wire size
function variationGrid(m, wires, loads, lengthFt, econ, opts={}){
  return wires.map(w=>loads.map(L=>{const c=wireCase(m,L,w,lengthFt,econ,opts); return c?{L,w:w.name,eta_sys:c.eta_sys,eta_motor:c.r.eta,vdPct:c.vdPct,Pwire:c.Pwire}:null;}));
}

Object.assign(MotorEngine,{WIRE,WIRE_OPTS,minWireIndex,wireCase,kelvinOptimum,variationGrid});

// ---------- Held axis: heat and time ----------
// Insulation classes (NEMA MG 1 12.43): allowable rise by resistance at 1.0 service factor,
// 40 °C ambient, and the class temperature (hot spot). Service factor 1.15 allows 10 K more.
const INSULATION={B:{rise:80,total:130},F:{rise:105,total:155},H:{rise:125,total:180}};
// Design point: premium motors are commonly class F insulation run at class B rise, so the
// rated losses produce an 80 K winding rise. R_th follows from that; the heating time
// constant is typical, growing with size.
function thermalModel(m){
  const rated=m._ref||ratedPoint(m);
  const designRise=80;
  const Rth=designRise/(rated.Pin-rated.Pout);          // K per W
  const tau=15*Math.pow(m.spec.hp,0.25);                 // minutes, typical heating time constant
  return {Rth,tau,designRise,ratedLoss:rated.Pin-rated.Pout};
}
function steadyTemp(th, lossW, ambient){ const rise=th.Rth*lossW; return {rise, winding:ambient+rise, hotspot:ambient+rise+10}; }
// Minutes from winding temperature theta0 to the limit, heading for steady state thetaSS
function timeToLimit(th, theta0, thetaSS, limit){ if(thetaSS<=limit) return Infinity; if(theta0>=limit) return 0; return th.tau*Math.log((thetaSS-theta0)/(thetaSS-limit)); }
// Overload relay as a first-order thermal model: trips when its heat state reaches the
// 1.05× threshold; the time constant is fitted so a class-N relay trips in N seconds at
// 7.2 × setting (IEC 60947-4-1). Seconds; Infinity below 1.05 × setting.
function relayTrip(I, Iset, cls){ const x=I/Iset; const a=(1.05/x)**2; if(a>=1) return Infinity; const tau=cls*46.5; return -tau*Math.log(1-a); }
// Insulation life relative to the class-B design point (120 °C winding), halving per 10 K
function lifeFactor(winding){ return Math.pow(2,(120-winding)/10); }
// Ambient and altitude derate: the allowable rise shrinks one-for-one above 40 °C and the
// output goes as the square root of it; above 3300 ft, 3 % per 1000 ft (common rule, NEMA MG 1 14.4)
function thermalDerate(ambient, altitudeFt, riseClass){
  const rise=Math.max(0,riseClass-Math.max(0,ambient-40));
  const alt=Math.max(0,1-0.03*Math.max(0,(altitudeFt-3300)/1000));
  return Math.sqrt(rise/riseClass)*alt;
}
// Conductor temperature from the 75 °C ampacity column (30 °C ambient basis)
function wireTemp(I, amp, ambient=30){ return ambient+(75-30)*(I/amp)**2; }
// Locked-rotor losses (all heat, nothing out)
function lockedRotorLoss(m, vfac=1){
  const q=atFreq(m); const kR=kRofSize(m.spec.hp);
  const V=C(m.V1*vfac*q.vf,0); const Zr=C(m.R2*kR,q.X2*0.75); const Zmag=cpar(C(q.Rc,0),C(0,q.Xm)); const Zgap=cpar(Zmag,Zr); const Zin=cadd(C(m.R1,q.X1*0.8),Zgap);
  const I1=cdiv(V,Zin); const E=cmul(I1,Zgap); const I2=cdiv(E,Zr);
  return 3*(cabs(I1)**2*m.R1+cabs(I2)**2*m.R2*kR)+3*cabs(E)**2/q.Rc;
}
Object.assign(MotorEngine,{INSULATION,thermalModel,steadyTemp,timeToLimit,relayTrip,lifeFactor,thermalDerate,wireTemp,lockedRotorLoss});

// ---------- Dirty power: a voltage sag ----------
// depth = remaining voltage as a fraction of nominal; cycles = duration. The motor rides
// through if its pull-out torque at the sag voltage still exceeds the load torque; otherwise
// it decelerates toward stall and draws locked-rotor current at the sag voltage. The
// contactor is the usual weak point: an AC coil drops out below about 75 % for more than
// a cycle or two unless it has a ride-through supply.
function sag(m, load, vfac, depth, cycles){
  const vsag=vfac*depth;
  const rNow=solveLoad(m,load,vfac); if(!rNow) return null;
  const po=pullout(m,vsag);
  const Tload=rNow.T;
  const margin=po.Tmax/Tload;
  const rSag=margin>1? solveLoad(m,load,vsag) : null;
  const lr=lockedRotor(m,vsag);
  const contactor= depth<0.75 && cycles>=2;
  const reaccel=lockedRotor(m,vfac);
  return {vsag, margin, ridesThrough: margin>1&&!!rSag, I_sag: rSag? rSag.I1 : lr.I_LR, slip_sag: rSag? rSag.s : 1, contactor, I_reaccel: reaccel.I_LR, Tmax_sag: po.Tmax, Tload};
}
Object.assign(MotorEngine,{satFactor,atFreq,sag});

// ---------- DC: the circuit with the inductance face switched off ----------
// A DC component between two lines sees only the winding resistance: I_dc = V_dc/(2R₁).
// Its MMF is a stationary field (the same physics as DC injection braking): the rotor at
// speed n sees it at rotor frequency, draws current, and makes a braking torque that the
// supply must overcome. The DC flux also biases the core, so one half-cycle saturates.
function dcOffset(m, r, dcFrac){
  if(dcFrac<=0) return {I_dc:0,Pcu:0,I_eq:0,T_brake:0,P_rotor:0,bias:0,satPeak:1};
  const Vdc=dcFrac*m.spec.V_LL;
  const I_dc=Vdc/(2*m.R1);
  const Pcu=2*I_dc*I_dc*m.R1;
  const I_eq=Math.sqrt(2/3)*I_dc;                    // equivalent balanced AC current of a two-line DC injection
  const q=atFreq(m);
  const sr=r.n/q.ns;                                 // the rotor's slip against a stationary field
  const R2s=m.R2/Math.max(sr,1e-6);
  const I2=I_eq*q.Xm/Math.hypot(R2s,q.Xm+q.X2);
  const T_brake=3*I2*I2*R2s/q.ws;
  const P_rotor=T_brake*2*Math.PI*r.n/60;            // all of it is rotor heat
  const Im=r.E/r.Xm_eff;                             // rated-ish magnetizing current (rms)
  const bias=I_eq/(Math.sqrt(2)*Im);                 // DC flux against the peak AC flux
  const satPeak=satFactor(m, (1+bias)*r.E*q.ff/q.ff); // magnetizing multiplier on the saturated half-cycle
  return {I_dc,Pcu,I_eq,T_brake,P_rotor,bias,satPeak};
}
// Unbalance derate by the hottest phase: the negative-sequence current adds to the
// positive-sequence current in one phase, so the allowed positive-sequence current is
// what leaves that phase at its rated current. This is what the NEMA curve tracks.
function derateHotPhase(r, unb){ return Math.max(0,1-unb.I1n/r.I1); }

// ---------- Measured motor: IEEE 112 no-load and locked-rotor tests ----------
// Deep bar: the AC/DC resistance ratio of a rectangular bar is k(ξ)=ξ(sinh2ξ+sin2ξ)/(cosh2ξ−cos2ξ),
// ξ = bar depth / skin depth, and the skin depth goes as 1/√f. The typical k at line frequency
// fixes ξ for the size; a locked-rotor test at a lower frequency then sees a smaller k.
function deepBarK(xi){ if(xi<1e-3) return 1; const a=2*xi; return xi*(Math.sinh(a)+Math.sin(a))/(Math.cosh(a)-Math.cos(a)); }
function xiFromK(k){ let lo=0, hi=8; for(let i=0;i<60;i++){ const mid=0.5*(lo+hi); if(deepBarK(mid)<k) lo=mid; else hi=mid; } return 0.5*(lo+hi); }
function kRofSize(hp){ return Math.min(3.2,1.6+0.7*Math.log10(hp)); }
// t: {R1 (Ω per phase, DC test: line-line / 2 for a wye), Inl (A), Pnl (W, three-phase, at rated voltage),
//     Vlr (V line-line at the locked-rotor test), Ilr (A), Plr (W, three-phase), flr (Hz, optional: test frequency),
//     Pfw (W, optional), split (optional: X1/(X1+X2); IEEE 112 gives 0.5 A and D, 0.4 B, 0.3 C)}
function paramsFromTests(spec, t){
  const V1=spec.V_LL/Math.sqrt(3); const split=t.split!=null?t.split:0.4;
  // no-load: the apparent impedance; the rotor branch is open, F&W rides on the input power
  const Zn=V1/t.Inl, Rn=t.Pnl/(3*t.Inl*t.Inl), Xnl=Math.sqrt(Math.max(0,Zn*Zn-Rn*Rn));
  const Prot=Math.max(0,t.Pnl-3*t.Inl*t.Inl*t.R1);        // core + friction and windage
  const Pfw=t.Pfw!=null? t.Pfw : 0.4*Prot; const Pcore=Math.max(1,Prot-Pfw);
  const cth=Math.min(1,Rn/Zn), sth=Math.sqrt(Math.max(0,1-cth*cth)); const Inl=C(t.Inl*cth,-t.Inl*sth);
  // locked rotor: the apparent impedance at the test frequency, brought to the rated frequency
  const flr=t.flr>0?t.flr:spec.f; const fr=flr/spec.f;
  const V1l=t.Vlr/Math.sqrt(3); const Zl=V1l/t.Ilr, Rl=t.Plr/(3*t.Ilr*t.Ilr), Xl=Math.sqrt(Math.max(0,Zl*Zl-Rl*Rl));
  const xi=xiFromK(kRofSize(spec.hp)); const kR_test=deepBarK(xi*Math.sqrt(fr)), kR_line=deepBarK(xi);
  let X1=split*Xl/fr, X2=(1-split)*Xl/fr, Xm=Math.max(0.1,Xnl-X1), Rc=1e9, R2lr=Math.max(1e-6,Rl-t.R1), E_nl=V1;
  for(let k=0;k<200;k++){
    E_nl=cabs(csub(C(V1,0),cmul(Inl,C(t.R1,X1)))); Rc=3*E_nl*E_nl/Pcore; Xm=Math.max(0.1,Xnl-X1);
    // exact for the circuit: take the stator leg off the measured impedance, then the magnetizing branch
    const Zmag=cpar(C(Rc*Math.pow(fr,0.7),0),C(0,Xm*fr));
    const Zgap=csub(C(Rl,Xl),C(t.R1,X1*fr));
    const Yr=csub(cinv(Zgap),cinv(Zmag)); const Zr=cinv(Yr);
    const R2new=Math.max(1e-6,Zr.re), X2new=Math.max(1e-6,Zr.im/fr);
    const X1new=0.5*(X1+split/(1-split)*X2new);              // damped: the map X1 → Xl−X1 has slope −1
    const done=Math.abs(X1new-X1)<1e-10*Math.max(1,X1)&&Math.abs(R2new-R2lr)<1e-10*Math.max(1,R2lr);
    X1=X1new; X2=(1-split)/split*X1; R2lr=R2new; if(done) break;
  }
  const R2=R2lr/kR_test;                                     // running rotor resistance
  const stray= spec.hp<=125?0.018: spec.hp<=500?0.015:0.012;
  return {R1:t.R1,R2,X1,X2,Xm,Rc,E_nl,Pfw0:Pfw,Pstray0:stray*spec.P_W,Pcore_nl:Pcore,Prot,Xnl,Xlr:Xl,R2lr,kR_test,kR_line,flr,split};
}
Object.assign(MotorEngine,{dcOffset,derateHotPhase,paramsFromTests,deepBarK,xiFromK,kRofSize,C,cadd,csub,cmul,cdiv,cabs,cpar,cinv,solvePoint,ratedPointInner});
