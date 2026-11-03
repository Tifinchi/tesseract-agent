
// ======================================================================================
// Other motor types: single-phase induction, DC brushed, brushless PM on a drive;
// NEC 430 protection pairing; load estimation from field readings.
// Same frame: six faces, the instant / rate / inverse / product cells, the held axis.
// ======================================================================================
(function(E){
const {C,cadd,csub,cmul,cdiv,cabs,cpar,cinv}=E;

// ---------- Tables ----------
// NEC Table 430.248: single-phase AC motors, full-load current, [115, 200, 208, 230] V
const SP_SIZES=[{hp:1/6,label:'1/6 HP'},{hp:0.25,label:'1/4 HP'},{hp:1/3,label:'1/3 HP'},{hp:0.5,label:'1/2 HP'},{hp:0.75,label:'3/4 HP'},{hp:1,label:'1 HP'},{hp:1.5,label:'1½ HP'},{hp:2,label:'2 HP'},{hp:3,label:'3 HP'},{hp:5,label:'5 HP'},{hp:7.5,label:'7½ HP'},{hp:10,label:'10 HP'}];
const NEC_430_248=[[4.4,2.5,2.4,2.2],[5.8,3.3,3.2,2.9],[7.2,4.1,4.0,3.6],[9.8,5.6,5.4,4.9],[13.8,7.9,7.6,6.9],[16,9.2,8.8,8.0],[20,11.5,11.0,10],[24,13.8,13.2,12],[34,19.6,18.7,17],[56,32.2,30.8,28],[80,46.0,44.0,40],[100,57.5,55.0,50]];
const SP_VOLTS=[115,200,208,230];
// NEC Table 430.247: DC motors, full-load current at base speed, [90,120,180,240,500,550] V
const DC_SIZES=[0.25,1/3,0.5,0.75,1,1.5,2,3,5,7.5,10,15,20,25,30,40,50,60,75,100,125,150,200];
const NEC_430_247=[[4.0,3.1,2.0,1.6,null,null],[5.2,4.1,2.6,2.0,null,null],[6.8,5.4,3.4,2.7,null,null],[9.6,7.6,4.8,3.8,null,null],[12.2,9.5,6.1,4.7,null,null],[null,13.2,8.3,6.6,null,null],[null,17,10.8,8.5,null,null],[null,25,16,12.2,null,null],[null,40,27,20,null,null],[null,58,null,29,13.6,12.2],[null,76,null,38,18,16],[null,null,null,55,27,24],[null,null,null,72,34,31],[null,null,null,89,43,38],[null,null,null,106,51,46],[null,null,null,140,67,61],[null,null,null,173,83,75],[null,null,null,206,99,90],[null,null,null,255,123,111],[null,null,null,341,164,148],[null,null,null,425,205,185],[null,null,null,506,246,222],[null,null,null,675,330,294]];
const DC_VOLTS=[90,120,180,240,500,550];
// DOE small electric motor standards, 10 CFR 431.446: minimum average full-load efficiency, open motors, [6-pole, 4-pole, 2-pole]
const DOE_CS={0.25:[62.2,68.5,66.6],[1/3]:[66.6,72.4,70.5],0.5:[76.2,76.2,72.4],0.75:[80.2,81.8,76.2],1:[81.1,82.6,80.4],1.5:[null,83.8,81.5],2:[null,84.5,82.9],3:[null,null,84.1]};
const DOE_POLY={0.25:[67.5,69.5,65.6],[1/3]:[71.4,73.4,69.5],0.5:[75.3,78.2,73.4],0.75:[81.7,81.1,76.8],1:[82.5,83.5,77.0],1.5:[83.8,86.5,84.0],2:[null,86.5,85.5],3:[null,86.9,85.5]};
// IEC 60034-30-1 IE4, 50 Hz, [2-pole, 4-pole, 6-pole]
const IE4={0.75:[83.5,85.7,82.7],1.1:[85.2,87.2,84.5],1.5:[86.5,88.2,85.9],2.2:[88.0,89.5,87.4],3:[89.1,90.4,88.6],4:[90.0,91.1,89.5],5.5:[90.9,91.9,90.5],7.5:[91.7,92.6,91.3],11:[92.6,93.3,92.3],15:[93.3,93.9,92.9],18.5:[93.7,94.2,93.4],22:[94.0,94.5,93.7],30:[94.5,94.9,94.2],37:[94.8,95.2,94.5],45:[95.0,95.4,94.8],55:[95.3,95.7,95.1],75:[95.6,96.0,95.4],90:[95.8,96.1,95.6],110:[96.0,96.3,95.8],132:[96.2,96.4,96.0],160:[96.3,96.6,96.2],200:[96.5,96.7,96.3]};
// NEC 240.6(A) standard ampere ratings (breakers and fuses); 1, 3, 6 A fuses and 10 A added for small loads
const STD_AMPS=[1,3,6,10,15,20,25,30,35,40,45,50,60,70,80,90,100,110,125,150,175,200,225,250,300,350,400,450,500,600,700,800,1000,1200,1600,2000,2500,3000,4000,5000,6000];
const SWITCH_AMPS=[30,60,100,200,400,600,800,1200];
// NEC Table 430.52: maximum rating of the branch-circuit short-circuit and ground-fault device, % of the table FLA
const T430_52={ sp:{ntd:300,de:175,it:800,inv:250}, sc:{ntd:300,de:175,it:800,inv:250}, scB:{ntd:300,de:175,it:1100,inv:250}, sync:{ntd:300,de:175,it:800,inv:250}, wr:{ntd:150,de:150,it:800,inv:150}, dc:{ntd:150,de:150,it:250,inv:150} };
const DEVICE_NAMES={inv:'inverse-time breaker',it:'instantaneous-trip breaker (MCP)',de:'dual-element time-delay fuse',ntd:'non-time-delay fuse'};
function nextStd(a){ return STD_AMPS.find(v=>v>=a-1e-9)||STD_AMPS[STD_AMPS.length-1]; }
function prevStd(a){ let r=STD_AMPS[0]; for(const v of STD_AMPS){ if(v<=a+1e-9) r=v; } return r; }
function knownFLA_SP(hp,V){ const i=SP_SIZES.findIndex(s=>Math.abs(s.hp-hp)<1e-6), j=SP_VOLTS.indexOf(V); return (i<0||j<0)?null:NEC_430_248[i][j]; }
function knownFLA_DC(hp,V){ const i=DC_SIZES.findIndex(s=>Math.abs(s-hp)<1e-6), j=DC_VOLTS.indexOf(V); return (i<0||j<0)?null:NEC_430_247[i][j]; }
function knownEtaDOE(table,hp,poles){ const row=table[hp]??table[Object.keys(table).find(k=>Math.abs(Number(k)-hp)<1e-6)]; if(!row) return null; const v=row[{6:0,4:1,2:2}[poles]]; return v??null; }
function knownEtaIE4(kW,poles){ const row=IE4[kW]; if(!row) return null; return row[{2:0,4:1,6:2}[poles]??2]; }

// ---------- Single-phase induction: two windings, forward and backward fields ----------
// Main winding α and auxiliary β (turns ratio a, referred to the main). Forward and backward
// components of the main-winding current, I_f = (I_α − j a I_β)/2 and I_b = (I_α + j a I_β)/2,
// see the rotor through Z_f = jX_m ∥ (R₂′/s + jX₂′) and Z_b = jX_m ∥ (R₂′/(2−s) + jX₂′).
// With the auxiliary open the circuit collapses to the familiar half-impedance single-winding form.
function spParams(hp){
  const lg=Math.log10(hp);
  return { r1:0.050*Math.pow(hp,-0.22), r2:0.085*Math.pow(hp,-0.22), x1:0.12, x2:0.09, xm:3.0+0.5*lg,
           core:0.024*Math.pow(hp,-0.2), fw:0.020*Math.pow(hp,-0.2), stray:0.015, a:1.3 };
}
// kind: 'split' (resistance split, aux off at run), 'csir' (capacitor start, aux off at run),
//       'cscr' (capacitor start and run), 'psc' (permanent split capacitor, one run cap)
function spBuild(spec){
  const p=spParams(spec.hp); const S_base=spec.P_W/0.5; const Z_base=spec.V*spec.V/S_base;
  const ns=120*spec.f/spec.poles, ws=2*Math.PI*ns/60;
  const m={type:'sp',kind:spec.kind||'csir',spec,R1:p.r1*Z_base,R2:p.r2*Z_base,X1:p.x1*Z_base,X2:p.x2*Z_base,Xm:p.xm*Z_base,
    Pcore0:p.core*spec.P_W,Pfw0:p.fw*spec.P_W,Pstray0:p.stray*spec.P_W,a:p.a,V:spec.V,ns,ws,Z_base,S_base,pu:p,
    rbStart:3.0, rbRun:1.2, xb:1.0, Xc_start:0, Xc_run:0, loadType:'constant'};
  // capacitors: start cap for maximum locked-rotor torque; run cap for the least backward field at rated load
  const runAux = (m.kind==='cscr'||m.kind==='psc');
  if(m.kind==='csir'||m.kind==='cscr'){ m.Xc_start=bestXc(m,1,'start',x=>spSolve(m,1,1,'start',x).T); }
  if(m.kind==='split'){ m.Xc_start=0; }
  if(runAux){ m.Xc_run=bestXc(m,0.03,'run',x=>-cabs(spSolve(m,0.03,1,'run',x).Ib))/0.7; if(m.kind==='psc') m.Xc_start=m.Xc_run; }   // the balance capacitor is the ideal; production motors fit about 70 % of it
  m.runMode = runAux?'run':'off';
  m.startMode = m.kind==='split'?'split':'start';
  m._ref=spRated(m); if(!m._ref) return m;
  m._nl=spSolve(m,1e-6,1,m.runMode);
  return m;
}
function bestXc(m,s,mode,score){ let best=0,bs=-Infinity; const Zb=m.Z_base; for(let k=0.2;k<=6;k*=1.08){ const x=k*Zb; const v=score(x); if(v>bs){bs=v;best=x;} } return best; }
function spSolve(m,s,vfac=1,mode,XcOverride){
  const V=m.V*vfac; const Zf=cpar(C(0,m.Xm),C(m.R2/Math.max(s,1e-9),m.X2)), Zb=cpar(C(0,m.Xm),C(m.R2/(2-s),m.X2));
  const Z1=C(m.R1,m.X1); let If,Ib,IaRef=C(0,0),rb=0;
  if(mode==='off'){ const Zin=cadd(Z1,cmul(C(0.5,0),cadd(Zf,Zb))); const Im=cdiv(C(V,0),Zin); If=cmul(C(0.5,0),Im); Ib=If; }
  else {
    const Xc = XcOverride!=null?XcOverride:(mode==='start'?m.Xc_start:(mode==='split'?0:m.Xc_run));
    rb = (mode==='run')?m.rbRun:(mode==='split'?6.0:m.rbStart);
    const Zb1=C(rb*m.R1, (mode==='split'?0.5:m.xb)*m.X1 - Xc/(m.a*m.a));
    const A11=cadd(Z1,Zf), A12=cadd(Z1,Zb), A21=cmul(C(0,1),cadd(Zb1,Zf)), A22=cmul(C(0,-1),cadd(Zb1,Zb));
    const b1=C(V,0), b2=C(V/m.a,0); const det=csub(cmul(A11,A22),cmul(A12,A21));
    If=cdiv(csub(cmul(b1,A22),cmul(A12,b2)),det); Ib=cdiv(csub(cmul(A11,b2),cmul(A21,b1)),det);
    IaRef=cmul(C(0,1),csub(If,Ib));
  }
  const Im=cadd(If,Ib); const Ia=cdiv(IaRef,C(m.a,0)); const Pcore=m.Pcore0*vfac*vfac; const Iline=cadd(cadd(Im,Ia),C(Pcore/V,0));
  const Pgf=2*cabs(If)**2*Zf.re, Pgb=2*cabs(Ib)**2*Zb.re;
  const T=(Pgf-Pgb)/m.ws; const Pmech=(1-s)*(Pgf-Pgb); const Prcl=s*Pgf+(2-s)*Pgb;
  const Pscl=cabs(Im)**2*m.R1+cabs(IaRef)**2*rb*m.R1;
  const Pfw=m.Pfw0*Math.pow(Math.max(0,1-s),2.5);
  const Pin=V*Iline.re; const I1=cabs(Iline); const S=V*I1; const Q=Math.sqrt(Math.max(0,S*S-Pin*Pin))*Math.sign(-Iline.im||1);
  return {s,n:m.ns*(1-s),V1:V,I1,Imain:cabs(Im),Iaux:cabs(Ia),If,Ib,Pin,Pscl,Prcl,Pcore,Pfw,Pgf,Pgb,Pmech,Tg:T,T,S,Q,pf:Pin/S,ws:m.ws,ns:m.ns,E:cabs(cmul(If,Zf)),Zin:cdiv(C(V,0),Iline),mode};
}
function spTorqueMax(m,vfac,mode){ let best={s:0.05,T:-1}; for(let s=0.02;s<=0.9;s+=0.01){ const r=spSolve(m,s,vfac,mode); if(r.T>best.T) best={s,T:r.T}; } let lo=Math.max(0.01,best.s-0.01), hi=Math.min(0.95,best.s+0.01); for(let k=0;k<40;k++){ const a=lo+(hi-lo)*0.382, b=lo+(hi-lo)*0.618; if(spSolve(m,a,vfac,mode).T<spSolve(m,b,vfac,mode).T) lo=a; else hi=b; } const s=0.5*(lo+hi); return {smax:s,Tmax:spSolve(m,s,vfac,mode).T}; }
function spOut(m,s,vfac,mode,ref){ const r=spSolve(m,s,vfac,mode); r.Pstray=ref?m.Pstray0*Math.pow(cabs(r.If)/cabs(ref.If),2):m.Pstray0; r.Pout=r.Pmech-r.Pfw-r.Pstray; return r; }
function spRated(m){ const po=spTorqueMax(m,1,m.runMode); let lo=1e-6, hi=po.smax*0.98; if(spOut(m,hi,1,m.runMode,null).Pout<m.spec.P_W) return null; for(let k=0;k<70;k++){ const mid=0.5*(lo+hi); if(spOut(m,mid,1,m.runMode,null).Pout<m.spec.P_W) lo=mid; else hi=mid; } const r=spOut(m,0.5*(lo+hi),1,m.runMode,null); r.eta=r.Pout/r.Pin; r.Ploss=r.Pin-r.Pout; r.T=r.Pout/(2*Math.PI*r.n/60); return r; }
function spSolveLoad(m,load,vfac=1){ const ref=m._ref; if(!ref) return null; const po=spTorqueMax(m,vfac,m.runMode); const P_target=load*m.spec.P_W; let lo=1e-6, hi=po.smax*0.98; if(spOut(m,hi,vfac,m.runMode,ref).Pout<P_target) return null; for(let k=0;k<70;k++){ const mid=0.5*(lo+hi); if(spOut(m,mid,vfac,m.runMode,ref).Pout<P_target) lo=mid; else hi=mid; } const r=spOut(m,0.5*(lo+hi),vfac,m.runMode,ref); r.load=load; r.eta=r.Pout/r.Pin; r.T=r.Pout/(2*Math.PI*r.n/60); r.Ploss=r.Pin-r.Pout; r.Pconst=r.Pcore+r.Pfw; r.Pvar=r.Pscl+r.Prcl+r.Pstray; r.pullout={smax:po.smax,Tmax:po.Tmax}; return r; }
function spLockedRotor(m,vfac=1){ const r=spSolve(m,1,vfac,m.startMode); const kvaPerHp=m.V*vfac*r.I1/1000/(m.spec.P_W/746); return {I_LR:r.I1,T_LR:r.T,kvaPerHp,pf:r.pf,Imain:r.Imain,Iaux:r.Iaux,Ploss:r.Pin}; }
function spSplitLosses(m,r){ const nl=m._nl; const Pcu_fixed=nl?nl.Pscl+nl.Prcl:0; const fixed=r.Pcore+r.Pfw+Pcu_fixed; const variable=Math.max(0,r.Pscl+r.Prcl-Pcu_fixed)+r.Pstray; return {fixed,variable,Pcu_fixed}; }

// ---------- DC brushed: permanent magnet, shunt (separately excited), series ----------
// V = E + I_a R_a + V_brush, E = K ω, T = K I_a. The inductance face is switched off in steady
// state: DC is the circuit with no reactance, which is why the stall current is V/R_a.
function dcBuild(spec){
  const hp=spec.hp, V=spec.V; const kind=spec.kind||'pm';
  const Z_b=V*V/(spec.P_W/0.85);
  const Ra=0.085*Math.pow(hp,-0.28)*Z_b, Rs=(kind==='series')?0.5*Ra:(kind==='compound'?0.15*Ra:0);
  const Prot0=0.055*Math.pow(hp,-0.22)*spec.P_W;            // iron + friction and windage at rated speed
  const Pfld=(kind==='shunt'||kind==='compound')?0.03*Math.pow(hp,-0.15)*spec.P_W:0;   // shunt field, constant
  const Vb=2;                                               // brush drop, two brushes
  const wr=2*Math.PI*spec.n_rated/60;
  const m={type:'dc',kind,spec,Ra,Rs,Prot0,Pfld,Vb,V,wr,n_rated:spec.n_rated,loadType:'constant'};
  // rated armature current: (V − I_a(R_a+R_s) − V_b)·I_a − P_rot = P
  let lo=0, hi=V/(Ra+Rs); for(let k=0;k<80;k++){ const mid=0.5*(lo+hi); const E=V-mid*(Ra+Rs)-Vb; const Pout=E*mid-Prot0; if(Pout<spec.P_W&&E*mid<V*mid/2) lo=mid; else if(Pout<spec.P_W) lo=mid; else hi=mid; }
  const Ia=0.5*(lo+hi); const E=V-Ia*(Ra+Rs)-Vb;
  m.Ia_r=Ia; m.E_r=E; m.K=(kind==='series')?E/(Ia*wr):E/wr; m.T_em_r=E*Ia/wr;
  m._ref=dcSolveLoad(m,1,1); m._ref.I2=0; m.ws=wr; m.ns=spec.n_rated;
  return m;
}
function dcSolveLoad(m,load,vfac=1){
  const V=m.V*vfac, Vb=m.Vb, R=m.Ra+m.Rs; const Tsh=load*m._ref_T||load*(m.spec.P_W/m.wr);
  let w=m.wr, Ia=m.Ia_r;
  for(let k=0;k<60;k++){
    const Prot=m.Prot0*Math.pow(Math.max(w,1e-3)/m.wr,1.5); const Tem=Tsh+Prot/Math.max(w,1e-3);
    if(m.kind==='series'){ Ia=Math.sqrt(Math.max(0,Tem/m.K)); const E=Math.max(0,V-Ia*R-Vb); w=E/(m.K*Math.max(Ia,1e-9)); if(w>8*m.wr) w=8*m.wr; }
    else if(m.kind==='compound'){ let Kc=m.K; for(let j=0;j<8;j++){ Ia=Tem/Kc; Kc=m.K*(0.88+0.12*Ia/m.Ia_r); } const E=V-Ia*R-Vb; w=E/Kc; if(w<1e-3) w=1e-3; }
    else { Ia=Tem/m.K; const E=V-Ia*R-Vb; w=E/m.K; if(w<1e-3) w=1e-3; }
  }
  const Keff=m.kind==='series'?m.K*Ia:(m.kind==='compound'?m.K*(0.88+0.12*Ia/m.Ia_r):m.K);
  const E=Keff*w; const Prot=m.Prot0*Math.pow(w/m.wr,1.5);
  const Pscl=Ia*Ia*R, Pbrush=Vb*Ia, Pfld=m.Pfld; const Pin=V*Ia+Pfld; const Pout=Tsh*w;
  const n=w*60/(2*Math.PI); const Ifld=Pfld/V; const I1=Ia+Ifld;
  return {load,V1:V,I1,Ia,Ifld,E,n,s:0,w,T:Tsh,Pin,Pout,eta:Pout/Pin,pf:1,S:Pin,Q:0,Pscl,Prcl:0,Pcore:Prot*0.5,Pfw:Prot*0.5,Pstray:0,Pbrush,Pfld,Ploss:Pin-Pout,Pconst:Prot+Pfld,Pvar:Pscl+Pbrush,ws:m.wr,ns:m.n_rated,Zin:C(V/I1,0)};
}
// The balance that locates the efficiency peak is between the fixed losses and the losses that go as I²;
// a loss linear in the current (brushes) or in the power (a drive's proportional loss) shifts the peak by nothing.
function dcSplitLosses(m,r){ const fixed=r.Pcore+r.Pfw+r.Pfld; const variable=r.Pscl; return {fixed,variable,linear:r.Pbrush,linearName:'brush drop',Pcu_fixed:0}; }
function dcStall(m,vfac=1,limit=null){ const V=m.V*vfac; const I=limit?limit*m.Ia_r:(V-m.Vb)/(m.Ra+m.Rs); const T=(m.kind==='series')?m.K*I*I:(m.kind==='compound'?m.K*(0.88+0.12*I/m.Ia_r)*I:m.K*I); return {I,T,Ploss:I*I*(m.Ra+m.Rs)+m.Vb*I+m.Pfld,Rstart: V/(1.5*m.Ia_r)-(m.Ra+m.Rs)}; }
function dcNoLoad(m,vfac=1){ return dcSolveLoad(m,0.0001,vfac); }

// ---------- Brushless PM (PMSM / BLDC) on a drive ----------
// Per phase: V = E + I(R + jωL) with the current in phase with E (i_d = 0, the usual control
// below base speed). T = 3 p λ I. Above base speed the drive holds voltage and weakens the field.
function pmBuild(spec){
  const hp=spec.hp, V_LL=spec.V_LL, p=spec.poles/2; const wr=2*Math.PI*spec.n_rated/60; const we=wr*p; const fr=we/(2*Math.PI);
  const S_base=spec.P_W/0.9, Z_base=V_LL*V_LL/S_base;
  const R=0.055*Math.pow(hp,-0.30)*Z_base, X=0.35*Z_base, L=X/we;
  const m={type:'pm',spec,p,R,L,X,wr,we,fr,V1:V_LL/Math.sqrt(3),Pfe0:0.022*Math.pow(hp,-0.2)*spec.P_W,Pfw0:0.012*Math.pow(hp,-0.2)*spec.P_W,Pstray0:0.005*spec.P_W,
    drive:{k:0.025,fixed:0.005*spec.P_W,pf:spec.frontPF||0.92,phases:spec.inPhases||3,Vin:spec.Vin||V_LL},loadType:'constant',ns:spec.n_rated,ws:wr};
  // rated: output P at rated speed: find I with Pout(I) = P
  const out=I=>{ const E=Math.sqrt(Math.max(0,m.V1*m.V1-(I*X)**2))-I*R; return {E,Pout:3*E*I-m.Pfw0-m.Pstray0}; };
  let lo=0, hi=m.V1/Math.hypot(R,X); for(let k=0;k<80;k++){ const mid=0.5*(lo+hi); if(out(mid).Pout<spec.P_W) lo=mid; else hi=mid; }
  const I=0.5*(lo+hi); const E=out(I).E; m.I_r=I; m.E_r=E; m.lam=E/we; m.Kt=3*p*m.lam;
  m._ref=pmSolveLoad(m,1,1); m._ref.I2=0;
  return m;
}
function pmSolveLoad(m,load,sf=1){ // sf = speed / rated
  const w=m.wr*Math.max(sf,1e-3), we=w*m.p; const X=m.L*we; let E=m.lam*we; let fw=false;
  const tq=(m.loadType==='pump')?load*sf*sf:load; const Tsh=tq*(m.spec.P_W/m.wr); const Tmax=(sf>1)?(m.spec.P_W/m.wr)/sf:Infinity;
  const T=Math.min(Tsh,Tmax); const Pfw=m.Pfw0*Math.pow(sf,2.5), Pstray=m.Pstray0*(T/(m.spec.P_W/m.wr))**2;
  const Tem=T+(Pfw+Pstray)/w; let I=Tem/m.Kt; let V1=Math.hypot(E+I*m.R,I*X); let fwFrac=1;
  if(V1>m.V1*1.0001){ fw=true; // field weakening: reduce the magnet axis flux seen by the terminals until V fits
    let lo=0, hi=1; for(let k=0;k<60;k++){ const mid=0.5*(lo+hi); const Em=m.lam*we*mid; const Iq=Tem/(m.Kt*mid); const Vt=Math.hypot(Em+Iq*m.R,Iq*X); if(Vt>m.V1) hi=mid; else lo=mid; }
    fwFrac=0.5*(lo+hi); E=m.lam*we*fwFrac; I=Tem/(m.Kt*fwFrac); V1=Math.hypot(E+I*m.R,I*X); }
  const Pfe=m.Pfe0*Math.pow(we/m.we,1.5)*Math.pow(E/(m.E_r||E),2); const Pscl=3*I*I*m.R;
  const Pin_m=3*E*I+Pscl+Pfe; const Pout=T*w; const S=3*V1*I; const pf=Math.min(1,Pin_m/S);
  const Pdrv=m.drive.k*Pin_m+m.drive.fixed; const Pin=Pin_m+Pdrv;
  const Iin=m.drive.phases===3? Pin/(Math.sqrt(3)*m.drive.Vin*m.drive.pf) : Pin/(m.drive.Vin*m.drive.pf);
  return {load,sf,n:w*60/(2*Math.PI),w,s:0,V1,I1:I,Iin,E,T,Tmax,fieldWeakening:fw,fwFrac,Pin_m,Pin,Pout,eta:Pout/Pin,eta_m:Pout/Pin_m,pf,S,Q:Math.sqrt(Math.max(0,S*S-Pin_m*Pin_m)),Pscl,Prcl:0,Pcore:Pfe,Pfw,Pstray,Pdrv,Ploss:Pin-Pout,Pconst:Pfe+Pfw+m.drive.fixed,Pvar:Pscl+Pstray+m.drive.k*Pin_m,ws:m.wr,ns:m.spec.n_rated,Zin:C((E+I*m.R)/Math.max(I,1e-9),X),fe:we/(2*Math.PI)};
}
function pmSplitLosses(m,r){ const fixed=r.Pcore+r.Pfw+m.drive.fixed; const variable=r.Pscl+r.Pstray; return {fixed,variable,linear:m.drive.k*r.Pin_m,linearName:'drive, proportional',Pcu_fixed:0}; }
function pmStall(m,limit=1.5){ const I=limit*m.I_r; return {I,T:m.Kt*I,Ploss:3*I*I*m.R+m.drive.fixed}; }

// ---------- Generic helpers over all types ----------
function lossBalanceGeneric(solve,split){ let a=0.05,b=3.0; const g=(Math.sqrt(5)-1)/2; const f=L=>{const r=solve(L); if(!r) return -1; return r.eta;}; let c=b-g*(b-a), d=a+g*(b-a); for(let k=0;k<60;k++){ if(f(c)<f(d)) a=c; else b=d; c=b-g*(b-a); d=a+g*(b-a); } let L=0.5*(a+b); let r=solve(L); if(!r){ let best=null; for(let x=0.05;x<=3.0;x+=0.05){ const q=solve(x); if(q&&(!best||q.eta>best.eta)){best=q;L=x;} } r=best; } if(!r) return null; const legs=split(r); return {load:L,r,legs,ratio:legs.variable/legs.fixed,angle:Math.atan2(legs.variable,legs.fixed)*180/Math.PI}; }

// ---------- NEC 430 protection pairing ----------
// kind: 'sp' single-phase, 'sc' polyphase squirrel cage, 'scB' Design B energy-efficient, 'dc', 'drive' (power conversion equipment)
// I_table: the Table 430.248/.250/.247 current (430.6(A)(1)); I_name: nameplate FLA (430.6(A)(2), overload only)
function protection(o){
  const kind=o.kind==='drive'?'sc':o.kind; const row=T430_52[kind]||T430_52.sc; const dev=o.device||'inv';
  const It=o.I_table, In=o.I_name||o.I_table; const sf=o.sf||1.15; const LRA=o.LRA||0;
  const pct=row[dev]; const maxA=pct/100*It; const std=nextStd(maxA);
  const ex2pct= dev==='ntd'?400 : dev==='de'?225 : dev==='it'?(kind==='scB'?1700:1300) : (It<=100?400:300);
  const maxA2=ex2pct/100*It; const std2=prevStd(maxA2);
  const instMult=o.instMult||10;
  const need=1.7*LRA;                       // first-half-cycle asymmetry allowance on the locked-rotor current
  let inrush;
  if(dev==='inv'){ const trip=std*instMult; inrush={need,trip,ok:trip>=need,note:`instantaneous ≈ ${instMult} × ${std} A = ${Math.round(trip)} A against ${Math.round(need)} A (1.7 × LRA)`}; if(!inrush.ok){ const alt=STD_AMPS.find(v=>v*instMult>=need&&v<=std2); inrush.alt=alt||null; } }
  else if(dev==='it'){ inrush={need,trip:maxA,ok:maxA>=need,note:`setting ${Math.round(maxA)} A (${pct} %) against ${Math.round(need)} A (1.7 × LRA)`}; if(!inrush.ok){ inrush.alt=Math.min(maxA2,need); } }
  else if(dev==='de'){ inrush={need:LRA,trip:5*std,ok:LRA<=5*std,note:`dual-element fuses hold 500 % for about 10 s: ${Math.round(5*std)} A against LRA ${Math.round(LRA)} A`}; }
  else { inrush={need:LRA,trip:3*std,ok:LRA<=3*std,note:`non-time-delay fuses hold about 300 % for a few seconds: ${Math.round(3*std)} A against LRA ${Math.round(LRA)} A`}; }
  const disc=1.15*It; const discStd=SWITCH_AMPS.find(v=>v>=disc)||SWITCH_AMPS[SWITCH_AMPS.length-1];
  const olPct=sf>=1.15?125:115, olMaxPct=sf>=1.15?140:130;
  const cond=1.25*It;
  return {device:dev,deviceName:DEVICE_NAMES[dev],kindRow:kind,pct,maxA,std,ex2pct,maxA2,std2,inrush,disc,discStd,overload:{pct:olPct,set:olPct/100*In,maxPct:olMaxPct,max:olMaxPct/100*In,basis:o.I_name?'nameplate':'table (no nameplate given)'},cond,I_table:It,I_name:In,LRA};
}

// ---------- Load from field readings ----------
// Three ways to read the actual load: invert the circuit on the measured current (exact within the
// model), the slip method (DOE: load ≈ slip/slip_rated, corrected for voltage²), the current method
// (load ≈ I/I_rated · V/V_rated, poor below half load because the magnetizing current does not scale).
function estimateLoad(o){ // o: {solve(L,vfac)→{I1,n}, ref:{I1,n,ns}, Vrated, meas:{I,n,V}}
  const vf=(o.meas.V&&o.Vrated)?o.meas.V/o.Vrated:1; const out={};
  if(o.meas.I>0){ let lo=0.0, hi=2.0; const at=L=>{const r=o.solve(L,vf); return r?r.I1:Infinity;}; if(at(0.001)>=o.meas.I) out.fromCurrent={load:0,note:'below no-load current'}; else { let ok=true; if(at(hi)<o.meas.I){ out.fromCurrent={load:null,note:'above the current at 200 % load'}; ok=false; } if(ok){ for(let k=0;k<50;k++){ const mid=0.5*(lo+hi); if(at(mid)<o.meas.I) lo=mid; else hi=mid; } out.fromCurrent={load:0.5*(lo+hi)}; } }
    out.currentRule={load:o.meas.I/o.ref.I1*vf}; }
  if(o.meas.n>0&&o.ref.ns){ const sr=(o.ref.ns-o.ref.n)/o.ref.ns, sm=(o.ref.ns-o.meas.n)/o.ref.ns; out.slipRule={load:sr>0?(sm/sr)/(vf*vf):null};
    let lo=0, hi=2.0; const at=L=>{const r=o.solve(L,vf); return r?r.n:-Infinity;}; if(at(hi)>o.meas.n||at(0.001)<o.meas.n) out.fromSpeed={load:null,note:'speed outside the model range at this voltage'}; else { for(let k=0;k<50;k++){ const mid=0.5*(lo+hi); if(at(mid)>o.meas.n) lo=mid; else hi=mid; } out.fromSpeed={load:0.5*(lo+hi)}; } }
  return out;
}

Object.assign(E,{SP_SIZES,NEC_430_248,SP_VOLTS,DC_SIZES,NEC_430_247,DC_VOLTS,DOE_CS,DOE_POLY,IE4,STD_AMPS,SWITCH_AMPS,T430_52,DEVICE_NAMES,nextStd,prevStd,knownFLA_SP,knownFLA_DC,knownEtaDOE,knownEtaIE4,
  spParams,spBuild,spSolve,spSolveLoad,spRated,spLockedRotor,spTorqueMax,spSplitLosses,dcBuild,dcSolveLoad,dcSplitLosses,dcStall,dcNoLoad,pmBuild,pmSolveLoad,pmSplitLosses,pmStall,lossBalanceGeneric,protection,estimateLoad});
if(typeof module!=='undefined') module.exports=E;
})(typeof module!=='undefined'?require('./engine.js'):MotorEngine);

// ======================================================================================
// The time turn on the mechanical axis: the instant is running; the quarter turn J is the
// start (the rate); the half turn J² is the reversal (the field turned over: two leads swapped);
// the three-quarter turn J³ is the stop (the anti-rate). e^{iπ} = −1: the generator is the motor
// turned over, negative slip. The scale turn K: size as the variable, phase against log size.
// ======================================================================================
(function(E){
const {C,cadd,csub,cmul,cdiv,cabs,cpar} = E;
// Typical rotor inertia by size and speed (NEMA frames): about 0.0045·HP^1.25 kg·m² at 4 poles.
function inertiaOf(hp,poles){ return 0.0045*Math.pow(hp,1.25)*Math.pow((poles||4)/4,0.9); }
// Three-phase torque–slip curve over the whole range, rotor deep-bar and leakage saturation
// blended by rotor frequency (|s|·f) and by how close the current is to locked rotor.
function im3Point(m,vfac,s){
  const q=E.atFreq(m); const xi=E.xiFromK(E.kRofSize(m.spec.hp)); const a=Math.min(1,Math.abs(s));
  const kR=E.deepBarK(xi*Math.sqrt(a)); const kx1=1-0.2*a, kx2=1-0.25*a; const ss=(Math.abs(s)<1e-6)?1e-6*Math.sign(s||1):s;
  const V=C(m.V1*vfac*q.vf,0); const Zr=C(m.R2*kR/ss,q.X2*kx2); const Zmag=cpar(C(q.Rc,0),C(0,q.Xm)); const Zgap=cpar(Zmag,Zr); const Zin=cadd(C(m.R1,q.X1*kx1),Zgap);
  const I1=cdiv(V,Zin); const Eg=cmul(I1,Zgap); const I2=cdiv(Eg,Zr);
  const I1a=cabs(I1), I2a=cabs(I2); const Pag=3*I2a*I2a*m.R2*kR/ss; const T=Pag/q.ws; const Pscl=3*I1a*I1a*m.R1; const Prcl=3*I2a*I2a*m.R2*kR; const Pin=3*(V.re*I1.re+V.im*I1.im);
  return {s,n:q.ns*(1-s),w:q.ws*(1-s),I1:I1a,I2:I2a,T,Pag,Pscl,Prcl,Pin,kR,ws:q.ws,ns:q.ns};
}
// Integrate dω/dt = (T_motor − T_load)/J from s0 to the running point (or to a stall).
function startRun(pointFn,ws,Jtot,loadT,s0,sEnd,opts={}){
  const dir=s0>sEnd?-1:1; const ds=0.002*dir; let s=s0, t=0, Er=0, Es=0, Isum=0, n=0, Imax=0, Tmin=Infinity, pts=[];
  const limit=opts.maxT||600;
  while((dir<0&&s>sEnd)||(dir>0&&s<sEnd)){
    const p=pointFn(s); const w=ws*(1-s); const Tl=loadT(w); const Tnet=p.T-Tl;
    if(opts.brake){ /* decelerating: Tnet already signed by pointFn */ }
    if(!opts.brake&&Tnet<=0.02*Math.abs(Tl||p.T)+1e-9){ const stable=opts.smax!=null&&Math.abs(s)<opts.smax; return {ok:stable,settledS:stable?s:null,stallS:stable?null:s,stallN:ws*(1-s)*60/(2*Math.PI),t,Er,Es,Iavg:n?Isum/n:0,Imax,Tmin:Math.min(Tmin,p.T),pts}; }
    const dw=-ws*ds; const dt=Math.abs(dw/(Tnet/Jtot)); if(!isFinite(dt)||dt<0) break;
    t+=dt; Er+=p.Prcl*dt; Es+=p.Pscl*dt; Isum+=p.I1; n++; Imax=Math.max(Imax,p.I1); Tmin=Math.min(Tmin,p.T);
    if(n%10===0) pts.push({s,n:ws*(1-s)*60/(2*Math.PI),T:p.T,I:p.I1,t});
    s+=ds; if(t>limit) return {ok:false,stallS:s,t,Er,Es,Iavg:Isum/n,Imax,Tmin,pts,timeout:true};
  }
  return {ok:true,t,Er,Es,Iavg:n?Isum/n:0,Imax,Tmin,pts};
}
function im3Start(m,vfac,Jtot,loadT,sRun){ const po=E.pullout(m,vfac); return startRun(s=>im3Point(m,vfac,s),E.atFreq(m).ws,Jtot,loadT,1,Math.max(sRun,0.002),{smax:po.smax}); }
// Plugging: two leads swapped while running at slip sRun; the new field runs backward, s → 2 − sRun.
// From there the rotor decelerates to standstill (s = 1) and, if left connected, runs up in reverse.
function im3Plug(m,vfac,Jtot,loadT,sRun){
  const ws=E.atFreq(m).ws; const p0=im3Point(m,vfac,2-sRun);
  // deceleration: the motor torque (toward the reverse direction) and the load torque both oppose the forward motion
  const dec=startRun(s=>{const p=im3Point(m,vfac,s); return Object.assign({},p,{T:p.T+loadT(Math.abs(ws*(1-s)))*Math.sign(1)});},ws,Jtot,w=>0,2-sRun,1.0001,{brake:true});
  const rev=startRun(s=>im3Point(m,vfac,s),ws,Jtot,loadT,0.9999,Math.max(sRun,0.002),{smax:E.pullout(m,vfac).smax});
  return {I0:p0.I1,T0:p0.T,t_stop:dec.t,Er_stop:dec.Er,Es_stop:dec.Es,t_reverse:dec.t+(rev.ok?rev.t:Infinity),Er_total:dec.Er+rev.Er,ok:rev.ok};
}
// DC injection braking: a DC current in the stator makes a stationary field; the rotor at speed n sees it at
// slip n/n_s and brakes. Current I_dc between two lines → equivalent balanced I_eq = √(2/3)·I_dc.
function im3DcBrakeT(m,Ieq,n){ const q=E.atFreq(m); const sr=Math.max(n/q.ns,1e-6); const R2s=m.R2/sr; const I2=Ieq*q.Xm/Math.hypot(R2s,q.Xm+q.X2); return 3*I2*I2*R2s/q.ws; }
function im3DcBrake(m,Ieq,Jtot,loadT,n0){
  const q=E.atFreq(m); let w=2*Math.PI*n0/60, t=0, Er=0, Tpeak=0, npeak=0; const dt=0.002; const Pst=3*Ieq*Ieq*m.R1;
  while(w>0.5&&t<600){ const n=w*60/(2*Math.PI); const Tb=im3DcBrakeT(m,Ieq,n); if(Tb>Tpeak){Tpeak=Tb;npeak=n;} const Tl=loadT(w); w-=(Tb+Tl)/Jtot*dt; t+=dt; Er+=Tb*w*dt; }
  return {t_stop:t,Er,Es:Pst*t,Tpeak,npeak,Pst};
}
// The generator: the same circuit at negative slip. Mechanical power in, electrical power out.
function im3Regen(m,vfac,s){ const p=E.solvePoint(m,-Math.abs(s),vfac); const Pmech_in=-p.Pmech; const Pel_out=-p.Pin; return {s:-Math.abs(s),n:p.n,I1:p.I1,Pmech_in,Pel_out,eta:Pel_out>0?Pel_out/(Pmech_in+p.Pfw):0,Q:p.Q,T:p.Tg,Pfw:p.Pfw}; }
// Drive or starter ramps: constant available torque against the load
function rampStart(Jtot,Tavail,loadT,w1){ let w=0,t=0; const dt=0.002; while(w<w1&&t<600){ const Tnet=Tavail-loadT(w); if(Tnet<=1e-6*Math.max(1,Tavail)) return {ok:false,t,stallW:w}; w+=Tnet/Jtot*dt; t+=dt; } if(t>=600) return {ok:false,t,stallW:w}; return {ok:true,t,Ekin:0.5*Jtot*w1*w1}; }
function coastStop(Jtot,loadT,w0){ let w=w0,t=0; const dt=0.005; while(w>0.5&&t<3600){ const Tl=loadT(w)+0.02*loadT(w0)+1e-6; w-=Tl/Jtot*dt; t+=dt; } return t; }
// The scale turn: log-log slopes of each quantity against size, from the line-up
function scaleSlopes(all,keys){ const out={}; const xs=all.map(a=>Math.log10(a.size)); for(const k of keys){ const pts=all.map((a,i)=>[xs[i],a[k]]).filter(p=>p[1]!=null&&isFinite(p[1])&&p[1]>0).map(p=>[p[0],Math.log10(p[1])]); if(pts.length<3){out[k]=null;continue;} const n=pts.length, mx=pts.reduce((s,p)=>s+p[0],0)/n, my=pts.reduce((s,p)=>s+p[1],0)/n; let sxx=0,sxy=0; for(const p of pts){sxx+=(p[0]-mx)**2; sxy+=(p[0]-mx)*(p[1]-my);} out[k]=sxx?sxy/sxx:null; } return out; }
function linSlope(xs,ys){ const pts=xs.map((x,i)=>[x,ys[i]]).filter(p=>p[1]!=null&&isFinite(p[1])); const n=pts.length; if(n<3) return null; const mx=pts.reduce((s,p)=>s+p[0],0)/n, my=pts.reduce((s,p)=>s+p[1],0)/n; let sxx=0,sxy=0,syy=0; for(const p of pts){sxx+=(p[0]-mx)**2; sxy+=(p[0]-mx)*(p[1]-my); syy+=(p[1]-my)**2;} return {slope:sxy/sxx,intercept:my-sxy/sxx*mx,r2:sxx&&syy?(sxy*sxy)/(sxx*syy):null}; }
function im1Start(m,vfac,Jtot,loadT,sRun){ const po=E.spTorqueMax(m,vfac,m.runMode); const pt=s=>{ const mode=(s>0.25)?m.startMode:m.runMode; const r=E.spSolve(m,s,vfac,mode); return {s,T:r.T,I1:r.I1,Prcl:r.Prcl,Pscl:r.Pscl}; }; return startRun(pt,m.ws,Jtot,loadT,1,Math.max(sRun,0.002),{smax:po.smax}); }
Object.assign(E,{inertiaOf,im1Start,im3Point,startRun,im3Start,im3Plug,im3DcBrakeT,im3DcBrake,im3Regen,rampStart,coastStop,scaleSlopes,linSlope});
})(typeof module!=='undefined'?module.exports:MotorEngine);

// ======================================================================================
// Windings and starting methods: the same motor, connected differently. Wye start, part winding,
// autotransformer, primary resistor, soft starter, wound rotor with external resistance.
// ======================================================================================
(function(E){
const {C,cadd,csub,cmul,cdiv,cabs,cpar} = E;
// The whole-range point with external series impedance (primary resistor/reactor) and external
// rotor resistance (wound rotor), the external rotor part without the deep-bar rise.
function im3PointX(m,vfac,s,opt={}){
  const q=E.atFreq(m); const xi=E.xiFromK(E.kRofSize(m.spec.hp)); const a=Math.min(1,Math.abs(s));
  const kR=E.deepBarK(xi*Math.sqrt(a)); const kx1=1-0.2*a, kx2=1-0.25*a; const ss=(Math.abs(s)<1e-6)?1e-6*Math.sign(s||1):s;
  const Rs=opt.Rs||0, Xs=opt.Xs||0, rext=opt.rext||0;
  const R2tot=m.R2*(kR+rext);
  const V=C(m.V1*vfac*q.vf,0); const Zr=C(R2tot/ss,q.X2*kx2); const Zmag=cpar(C(q.Rc,0),C(0,q.Xm)); const Zgap=cpar(Zmag,Zr); const Zin=cadd(C(m.R1+Rs,q.X1*kx1+Xs),Zgap);
  const I1=cdiv(V,Zin); const Eg=cmul(I1,Zgap); const I2=cdiv(Eg,Zr);
  const I1a=cabs(I1), I2a=cabs(I2); const Pag=3*I2a*I2a*R2tot/ss; const T=Pag/q.ws; const Pscl=3*I1a*I1a*m.R1; const Prcl=3*I2a*I2a*m.R2*kR; const Pext=3*I2a*I2a*m.R2*rext; const Pres=3*I1a*I1a*Rs;
  return {s,n:q.ns*(1-s),I1:I1a,I2:I2a,T,Pag,Pscl,Prcl,Pext,Pres,kR,ws:q.ws,ns:q.ns,Vm:cabs(V)-0};
}
// A staged start: each stage has a point function and a stop rule; the next stage picks up at that slip.
function stagedStart(m,vfac,Jtot,loadT,sRun,stages){
  const ws=E.atFreq(m).ws; const po=E.pullout(m,vfac); let s=1, t=0, Er=0, Es=0, Eres=0, Imax=0, Iline0=null, T0=null, log=[];
  for(const stg of stages){
    const ds=0.002; let settled=false, stalled=false, n=0, Isum=0, tStage=0;
    const sEnd=Math.max(sRun,0.002);
    while(s>sEnd){
      const p=stg.point(s); const w=ws*(1-s); const Tl=loadT(w); const Tnet=p.T-Tl; const Iline=stg.line?stg.line(p):p.I1;
      if(Iline0==null){ Iline0=Iline; T0=p.T; }
      if(Tnet<=0.02*Math.abs(Tl||p.T)+1e-9){ if(s<(stg.smax||po.smax)) settled=true; else stalled=true; break; }
      const dt=Math.abs(ws*ds/(Tnet/Jtot)); t+=dt; tStage+=dt; Er+=(p.Prcl+(p.Pext||0))*dt; Es+=p.Pscl*dt; Eres+=(p.Pres||0)*dt; Isum+=Iline; n++; Imax=Math.max(Imax,Iline);
      if(stg.timer&&tStage>=stg.timer) break;
      s-=ds; if(t>600) { stalled=true; break; }
    }
    log.push({name:stg.name,sEnd:s,t:tStage,settled,stalled,Iavg:n?Isum/n:0});
    if(stalled&&!stg.carryOn) return {ok:false,stallS:s,stallN:ws*(1-s)*60/(2*Math.PI),t,Er,Es,Eres,Imax,Iline0,T0,log};
    if(s<=sEnd) break;
  }
  return {ok:s<=Math.max(sRun,0.002)+1e-9||log[log.length-1].settled,sEnd:s,t,Er,Es,Eres,Imax,Iline0,T0,log};
}
function startMethods(m,vfac,Jtot,loadT,sRun,opt={}){
  const dol=s=>im3PointX(m,vfac,s);
  const full={name:'full voltage',point:dol};
  const out={};
  out.dol=stagedStart(m,vfac,Jtot,loadT,sRun,[full]);
  // wye start: windings at V/√3; torque 1/3, line current 1/3 (the circuit at vfac/√3, its current over √3)
  const yd1={name:'wye',point:s=>{const p=im3PointX(m,vfac/Math.sqrt(3),s); return Object.assign({},p,{I1:p.I1/Math.sqrt(3)});},carryOn:true,timer:opt.ydTimer||10};
  out.yd=stagedStart(m,vfac,Jtot,loadT,sRun,[yd1,full]); out.yd.trans=out.yd.log[0]; if(out.yd.trans){ const pt=dol(Math.max(out.yd.trans.sEnd,sRun)); out.yd.Itrans=pt.I1; }
  // part winding: half the winding first; the classic figures, 65 % current and 45 % torque, on a 1 to 2 s timer
  const pw1={name:'part winding',point:s=>{const p=dol(s); return Object.assign({},p,{I1:0.65*p.I1,T:0.45*p.T,Pscl:0.65*0.65*p.Pscl,Prcl:0.45*p.Prcl});},carryOn:true,timer:opt.pwTimer||2};
  out.pw=stagedStart(m,vfac,Jtot,loadT,sRun,[pw1,full]); out.pw.trans=out.pw.log[0]; if(out.pw.trans){ out.pw.Itrans=dol(Math.max(out.pw.trans.sEnd,sRun)).I1; }
  // autotransformer at tap k: motor at k·V, line current k × motor current, torque k²
  const k=opt.tap||0.65;
  const at1={name:`autotransformer ${Math.round(100*k)} % tap`,point:s=>im3PointX(m,vfac*k,s),line:p=>k*p.I1,carryOn:true,timer:opt.atTimer||10};
  out.at=stagedStart(m,vfac,Jtot,loadT,sRun,[at1,full]); out.at.trans=out.at.log[0]; if(out.at.trans){ out.at.Itrans=dol(Math.max(out.at.trans.sEnd,sRun)).I1; }
  // primary resistor sized for a starting current target (× FLA)
  const Itarget=(opt.prLimit||3.0)*(opt.Ifla||1); let lo=0, hi=50*m.R1; const I0=Rs=>im3PointX(m,vfac,1,{Rs}).I1;
  if(I0(0)>Itarget){ for(let i=0;i<60;i++){ const mid=0.5*(lo+hi); if(I0(mid)>Itarget) lo=mid; else hi=mid; } } else { hi=0; }
  const Rs=0.5*(lo+hi); const pr1={name:`primary resistor ${Rs.toFixed(2)} Ω`,point:s=>im3PointX(m,vfac,s,{Rs}),carryOn:true,timer:opt.prTimer||10};
  out.pr=stagedStart(m,vfac,Jtot,loadT,sRun,[pr1,full]); out.pr.Rs=Rs; out.pr.trans=out.pr.log[0]; if(out.pr.trans){ out.pr.Itrans=dol(Math.max(out.pr.trans.sEnd,sRun)).I1; }
  // soft starter: current limit; the voltage is cut back until the motor's own current falls under the limit
  const Ilim=(opt.ssLimit||3.0)*(opt.Ifla||1);
  const ss1={name:`soft start at ${Math.round(100*(opt.ssLimit||3))} %`,point:s=>{const p=dol(s); const v=Math.min(1,Ilim/p.I1); return Object.assign({},p,{I1:p.I1*v,T:p.T*v*v,Pscl:p.Pscl*v*v,Prcl:p.Prcl*v*v});}};
  out.ss=stagedStart(m,vfac,Jtot,loadT,sRun,[ss1]);
  // wound rotor: external rotor resistance in for the start, shorted after
  if(opt.rext>0){ const wr1={name:`rotor resistance ${opt.rext} × R₂′`,point:s=>im3PointX(m,vfac,s,{rext:opt.rext}),carryOn:true,timer:opt.wrTimer||10}; out.wr=stagedStart(m,vfac,Jtot,loadT,sRun,[wr1,full]); out.wr.trans=out.wr.log[0]; }
  const po=E.pullout(m,vfac); const q=E.atFreq(m); const kR1=E.deepBarK(E.xiFromK(E.kRofSize(m.spec.hp)));
  out.rextOpt=Math.max(0,Math.hypot(po.Rth,po.Xth+q.X2*0.75)/m.R2-kR1);   // external resistance that puts pull-out at standstill
  return out;
}
// Lead connections for dual-voltage motors (NEMA MG 1 Part 2 standard numbering)
const LEADS={
  wye9:{low:'L1–T1–T7 · L2–T2–T8 · L3–T3–T9 · join T4–T5–T6',high:'L1–T1 · L2–T2 · L3–T3 · join T4–T7 · T5–T8 · T6–T9',note:'nine leads, wye: low voltage puts the two coil groups of each phase in parallel, high voltage in series'},
  delta9:{low:'L1–T1–T6–T7 · L2–T2–T4–T8 · L3–T3–T5–T9',high:'L1–T1 · L2–T2 · L3–T3 · join T4–T7 · T5–T8 · T6–T9',note:'nine leads, delta: same series/parallel idea with the groups closed in a delta'},
  wye12:{low:'as wye9 low, with T10–T11–T12 joined as the second star point',high:'as wye9 high, with T10–T11–T12 joined',note:'twelve leads: wye–delta starting is possible at either voltage because both ends of every coil group are out'},
  sp:{low:'the two run windings in parallel (T1–T3 to one line, T2–T4 to the other), auxiliary across one line pair',high:'the two run windings in series (join T2–T3), auxiliary across one run winding',note:'reverse by swapping the auxiliary leads (T5 and T8 on most motors); lead numbers vary by manufacturer'},
};
Object.assign(E,{im3PointX,stagedStart,startMethods,LEADS});
})(typeof module!=='undefined'?module.exports:MotorEngine);

// ======================================================================================
// Installation: the pipe, the ground wire and the panel. NEC 250.122, Chapter 9 Tables 4 and 5,
// 310.15(B) and (C), the starting dip, available fault current and interrupting ratings,
// 460.9 capacitors on the load side of the overload, drive reflected waves.
// ======================================================================================
(function(E){
// NEC Table 250.122: copper EGC by rating of the overcurrent device (not exceeding)
const EGC=[[15,'14 AWG'],[20,'12 AWG'],[60,'10 AWG'],[100,'8 AWG'],[200,'6 AWG'],[300,'4 AWG'],[400,'3 AWG'],[500,'2 AWG'],[600,'1 AWG'],[800,'1/0 AWG'],[1000,'2/0 AWG'],[1200,'3/0 AWG'],[1600,'4/0 AWG'],[2000,'250 kcmil'],[2500,'350 kcmil'],[3000,'400 kcmil'],[4000,'500 kcmil'],[5000,'700 kcmil'],[6000,'800 kcmil']];
// Chapter 9 Table 5: THHN/THWN area, in²
const AREA={'14 AWG':0.0097,'12 AWG':0.0133,'10 AWG':0.0211,'8 AWG':0.0366,'6 AWG':0.0507,'4 AWG':0.0824,'3 AWG':0.0973,'2 AWG':0.1158,'1 AWG':0.1562,'1/0 AWG':0.1855,'2/0 AWG':0.2223,'3/0 AWG':0.2679,'4/0 AWG':0.3237,'250 kcmil':0.397,'300 kcmil':0.4608,'350 kcmil':0.5242,'400 kcmil':0.5863,'500 kcmil':0.7073,'600 kcmil':0.8676,'700 kcmil':0.9887,'750 kcmil':1.0496,'800 kcmil':1.1085};
// Chapter 9 Table 4: EMT, 40 % fill (over two conductors), in²
const EMT=[['1/2"',0.122],['3/4"',0.213],['1"',0.346],['1 1/4"',0.598],['1 1/2"',0.814],['2"',1.342],['2 1/2"',2.343],['3"',3.538],['3 1/2"',4.618],['4"',5.901]];
// 310.15(B)(1): ambient correction, 75 °C conductors, 30 °C basis
function ambientFactor(tC){ if(tC<=25) return 1.05; if(tC<=30) return 1.00; if(tC<=35) return 0.94; if(tC<=40) return 0.88; if(tC<=45) return 0.82; if(tC<=50) return 0.75; if(tC<=55) return 0.67; if(tC<=60) return 0.58; if(tC<=70) return 0.33; return 0; }
// 310.15(C)(1): more than three current-carrying conductors in a raceway
function countFactor(n){ if(n<=3) return 1; if(n<=6) return 0.8; if(n<=9) return 0.7; if(n<=20) return 0.5; if(n<=30) return 0.45; if(n<=40) return 0.4; return 0.35; }
function egcFor(ocpdA){ for(const [a,sz] of EGC) if(ocpdA<=a) return sz; return EGC[EGC.length-1][1]; }
function conduitFor(areaIn2){ for(const [name,a] of EMT) if(a>=areaIn2) return name; return 'over 4": more than one raceway'; }
function kcmilOf(name){ return (E.WIRE.find(w=>w.name===name)||{}).kcmil||null; }
function egcUpsized(egcName,minKcmil,usedKcmil){ // 250.122(B): phase conductors upsized → EGC area up in proportion
  if(!minKcmil||!usedKcmil||usedKcmil<=minKcmil*1.001) return egcName; const need=Math.min(kcmilOf(egcName)*usedKcmil/minKcmil,usedKcmil); const w=E.WIRE.find(w=>w.kcmil>=need-1e-9); return w?w.name:egcName; }   // 250.122(A): never larger than the circuit conductors
function install(o){
  // o: {Itable, phases, V, len, Ilr, pfLr, ambientC, others, wires (WIRE_OPTS list from the code minimum), kelvinName, ocpdA, Isc_kA, aic_kA, Q (motor kvar at rated), Pin, pfRated, drive, cableFt}
  const af=ambientFactor(o.ambientC), cf=countFactor((o.phases===3?3:2)+(o.others||0)); const need=1.25*o.Itable;
  let der=null; for(const w of E.WIRE_OPTS){ if(w.amp*af*cf>=need){ der=w; break; } }
  const codeMin=o.wires[0]; const nc=o.phases===3?3:2;
  const egc=egcFor(o.ocpdA); const egcK=egcUpsized(egc,codeMin.base.kcmil,(o.kelvin&&o.kelvin.base)?o.kelvin.base.kcmil:codeMin.base.kcmil);
  const pipe=(w,eg)=>{ const a=nc*w.sets*(AREA[w.base.name]||0)+(AREA[eg]||0); return {area:a,size:conduitFor(a/0.40)}; };
  const dip=w=>{ const th=Math.acos(Math.min(1,o.pfLr)); const kv=o.phases===3?Math.sqrt(3):2; return kv*o.Ilr*o.len/1000*(w.R*Math.cos(th)+(o.phases===0?0:w.X*Math.sin(th))); };
  const Vln=o.phases===3?o.V/Math.sqrt(3):o.V; const Zs=o.Isc_kA>0?Vln/(o.Isc_kA*1000):0;
  const faultEnd=w=>{ const kv=o.phases===3?1:2; const Zw=Math.hypot(w.R,o.phases===0?0:w.X)*o.len/1000*kv; return Vln/(Zs+Zw); };
  const motorContrib=o.Ilr;  // first-cycle contribution of a running induction motor to an upstream fault ≈ its locked-rotor current
  return {af,cf,need,derated:der,codeMin,egc,egcK,pipeMin:pipe(codeMin,egc),pipeKelvin:o.kelvin?pipe(o.kelvin,egcK):null,
    dipMin:dip(codeMin),dipKelvin:o.kelvin?dip(o.kelvin):null,faultEndMin:faultEnd(codeMin),faultEndKelvin:o.kelvin?faultEnd(o.kelvin):null,motorContrib,
    aicOk:o.aic_kA>=o.Isc_kA, cap460: o.Q>0? {Icorr:(o.Pin)/((o.phases===3?Math.sqrt(3):1)*o.V), I95:Math.hypot(o.Pin,o.Pin*Math.tan(Math.acos(0.95)))/((o.phases===3?Math.sqrt(3):1)*o.V)}:null};
}
Object.assign(E,{EGC,AREA,EMT,ambientFactor,countFactor,egcFor,conduitFor,install});
})(typeof module!=='undefined'?module.exports:MotorEngine);
