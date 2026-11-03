#!/usr/bin/env python3
"""tesseract-agent v1 — a triangulating reasoning loop.

The document under test lives in claims/. Everything it may be checked against lives in evidence/.
A value the claim commits to is only KNOWN when independent routes reach it:
  - a lookup route: a value reported in an evidence file (verified by the script to be in that file)
  - a computation route: a stated relation evaluated by the script, EXACTLY, from neighbouring
    values that themselves come from evidence files (the calculator's neighbours rule)
Independence is by source group (author/team), read from the evidence file header, not guessed.
  0 or 1 route  -> UNSTABLE  (empty cell: the next independent route is the measurement to get)
  2 routes agree -> STABILIZED
  3 routes agree -> LOCKED (the vertex lock)
  any independent route disagrees beyond tolerance -> REJECTED, with the number
The model proposes observables, relations and candidate values. The script verifies every citation,
does every piece of arithmetic, computes the synthesis by rule, and never lets a number from the
claims document count as evidence for itself.

    python agent.py claims/khufu-run.md
    python agent.py claims/paper.md --question "..." --max-claims 12 --tolerance 0.05

Every pass writes one immutable JSON line to logs/run-<stamp>.jsonl; a summary goes beside it.
"""
import argparse, ast, datetime, json, math, operator, os, re, sys, time, uuid
import requests

HERE = os.path.dirname(os.path.abspath(__file__))
METHOD = (open(os.path.join(HERE, "method", "method.md"), encoding="utf-8").read() + "\n\n" +
          open(os.path.join(HERE, "method", "cube.md"), encoding="utf-8").read())
OLLAMA = os.environ.get("OLLAMA_URL", "http://localhost:11434")

# ----------------------------------------------------------------------------- model

def ask(model, system, user, num_ctx=8192, temperature=0.1, retries=2):
    body = {"model": model, "format": "json", "stream": False,
            "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}],
            "options": {"temperature": temperature, "num_ctx": num_ctx, "num_predict": 4096}}
    for attempt in range(retries + 1):
        r = requests.post(f"{OLLAMA}/api/chat", json=body, timeout=600)
        r.raise_for_status()
        text = r.json()["message"]["content"]
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            m = re.search(r"\{.*\}", text, re.S)
            if m:
                try:
                    return json.loads(m.group(0))
                except json.JSONDecodeError:
                    pass
            if attempt == retries:
                return {"_parse_error": text[:2000]}

# ----------------------------------------------------------------------------- evidence store

WORD = re.compile(r"[A-Za-z0-9√π]{3,}")
NUM = re.compile(r"-?\d+(?:[.,]\d+)?(?:[eE]-?\d+)?")
FRAC = {"½": ".5", "¼": ".25", "¾": ".75", "⅓": ".333", "⅔": ".667", "⅛": ".125"}
WORDS = {"zero": 0, "one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6, "seven": 7, "eight": 8, "nine": 9,
         "ten": 10, "eleven": 11, "twelve": 12, "fifteen": 15, "twenty": 20, "thirty": 30, "forty": 40, "fifty": 50, "hundred": 100}

def _norm(s):
    s = s.replace("−", "-").replace("–", "-").replace(",", "")
    for k, v in FRAC.items():
        s = re.sub(r"(\d)" + k, r"\1" + v, s).replace(k, "0" + v)
    return s

def parse_number(s):
    if isinstance(s, (int, float)):
        return float(s)
    if not isinstance(s, str):
        return None
    m = NUM.search(_norm(s))
    if m:
        try:
            return float(m.group(0))
        except ValueError:
            pass
    for w, v in WORDS.items():
        if re.search(r"\b" + w + r"\b", s.lower()):
            return float(v)
    return None

def parse_band(s, value):
    """Half-width of the value's band, from how the source wrote it. Returns (abs_band, kind)."""
    if not isinstance(s, str) or value is None:
        return (abs(value) * 0.1 if value else 0.0, "assumed 10 %")
    t = _norm(s)
    m = re.search(r"±\s*(\d+(?:\.\d+)?)\s*(%?)", t)
    if m:
        b = float(m.group(1))
        return (abs(value) * b / 100, f"stated ±{b} %") if m.group(2) else (b, f"stated ±{b}")
    m = re.search(r"to\s+(\d+(?:\.\d+)?)\s*%", t)
    if m:
        b = float(m.group(1)); return (abs(value) * b / 100, f"stated to {b} %")
    if re.search(r"[~≈]|\babout\b|\broughly\b|\bapprox", s.lower()):
        return (abs(value) * 0.10, "hedged (~): ±10 %")
    m = NUM.search(t)
    digits = m.group(0) if m else ""
    if "." in digits:
        return (0.5 * 10 ** (-(len(digits.split(".")[1]))), "half last digit")
    if digits:
        trailing = len(digits) - len(digits.rstrip("0"))
        return (0.5 * 10 ** trailing, "half last digit")
    return (abs(value) * 0.1, "assumed 10 %")

def is_bound(s):
    return bool(isinstance(s, str) and re.search(r"[≥≤<>]|at least|at most|more than|less than", s))

def number_in_text(value, text):
    v = parse_number(value)
    if v is None:
        return False
    t = _norm(text)
    for w, n in WORDS.items():
        if n == v and re.search(r"\b" + w + r"\b", t.lower()):
            return True
    for m in NUM.finditer(t):
        try:
            x = float(m.group(0))
        except ValueError:
            continue
        if x == v or (v != 0 and abs(x - v) / abs(v) < 0.002):
            return True
    return False

class Evidence:
    """A folder of text files. Each file may start with header lines:
         source: Petrie 1883, The Pyramids and Temples of Gizeh
         group: petrie
       `group` is the independence key (author/team). Files without one get their filename as group."""
    def __init__(self, folder):
        self.docs = []  # (name, group, source, text, paragraphs)
        names = sorted(os.listdir(folder)) if os.path.isdir(folder) else []
        for fn in names:
            p = os.path.join(folder, fn)
            if not os.path.isfile(p) or fn.startswith("."):
                continue
            text = open(p, encoding="utf-8", errors="replace").read()
            group, source = os.path.splitext(fn)[0], fn
            for line in text.splitlines()[:6]:
                if line.lower().startswith("group:"):
                    group = line.split(":", 1)[1].strip()
                if line.lower().startswith("source:"):
                    source = line.split(":", 1)[1].strip()
            paras = [q.strip() for q in re.split(r"\n\s*\n", text) if q.strip()]
            self.docs.append((fn, group, source, text, paras))
        self.groups = sorted(set(d[1] for d in self.docs))

    def retrieve(self, query, k=8, max_chars=4500):
        q = set(w.lower() for w in WORD.findall(query))
        scored = []
        for fn, group, source, text, paras in self.docs:
            for p in paras:
                w = set(x.lower() for x in WORD.findall(p))
                if w:
                    scored.append((len(q & w) / (len(q) + 1), fn, p))
        scored.sort(key=lambda t: -t[0])
        out, n = [], 0
        for s, fn, p in scored[:k]:
            if s == 0:
                break
            out.append(f"[{fn}] {p}")
            n += len(p)
            if n > max_chars:
                break
        return "\n\n".join(out)

    def group_of(self, fn):
        for d in self.docs:
            if d[0] == fn:
                return d[1]
        return None

    def contains_number(self, value, fn):
        for d in self.docs:
            if d[0] == fn:
                return number_in_text(value, d[3])
        return False

# ----------------------------------------------------------------------------- exact arithmetic (script, never model)

_OPS = {ast.Add: operator.add, ast.Sub: operator.sub, ast.Mult: operator.mul, ast.Div: operator.truediv,
        ast.Pow: operator.pow, ast.USub: operator.neg, ast.UAdd: operator.pos, ast.Mod: operator.mod}
_FUN = {"sqrt": math.sqrt, "abs": abs, "log": math.log, "log10": math.log10, "exp": math.exp,
        "sin": math.sin, "cos": math.cos, "tan": math.tan, "atan": math.atan, "min": min, "max": max}
_CONST = {"pi": math.pi, "e": math.e}

def evaluate(expr, variables):
    expr = expr.replace("^", "**").replace("×", "*").replace("÷", "/").replace("√", "sqrt")
    tree = ast.parse(expr, mode="eval")

    def ev(n):
        if isinstance(n, ast.Expression):
            return ev(n.body)
        if isinstance(n, ast.Constant) and isinstance(n.value, (int, float)):
            return float(n.value)
        if isinstance(n, ast.Name):
            if n.id in variables:
                return float(variables[n.id])
            if n.id in _CONST:
                return _CONST[n.id]
            raise ValueError(f"unknown variable {n.id}")
        if isinstance(n, ast.BinOp) and type(n.op) in _OPS:
            return _OPS[type(n.op)](ev(n.left), ev(n.right))
        if isinstance(n, ast.UnaryOp) and type(n.op) in _OPS:
            return _OPS[type(n.op)](ev(n.operand))
        if isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id in _FUN:
            return _FUN[n.func.id](*[ev(a) for a in n.args])
        raise ValueError(f"disallowed syntax: {ast.dump(n)[:60]}")
    return ev(tree)

# ----------------------------------------------------------------------------- log

class Log:
    def __init__(self, path):
        self.f = open(path, "a", encoding="utf-8"); self.path = path
    def write(self, **rec):
        rec["ts"] = datetime.datetime.now().isoformat(timespec="seconds")
        self.f.write(json.dumps(rec, ensure_ascii=False) + "\n"); self.f.flush()
        return rec

# ----------------------------------------------------------------------------- prompts

SYSTEM = (
    "You are a reasoning engine. You reason ONLY by the method below and answer in strict JSON. "
    "You never do arithmetic: you name relations and cite values; the script computes. "
    "A value is evidence ONLY if it appears in an evidence file you cite by its [filename]; a number that "
    "appears only in the claim is a prediction, never evidence. Where a list has no entries, return [].\n\n"
    + METHOD
)

P_EXTRACT = """Section "{heading}" of the document under test:
---
{doc}
---
Question in focus (may be empty): {question}

PASS 1, ENTRY: extract the distinct claims in this section. One claim per entry; split a recorded fact
from the inference drawn from it. Normalize each into a testable statement. ANCHOR each claim on the cube:
name the corner its datum sits on (one of + − × * ’ ” , . — or face:<Top|Front|Right|Left|Back|Bottom>, or
axis:<x|y|z>), the cell (instant|rate|inverse|anti-rate), and the held axis (what does not change). For each
claim list the OBSERVABLES it commits to: quantities that could be measured or looked up, each with the
value the claim asserts, INCLUDING any precision the claim states (write "6.283 to 0.05 %", "43.0 ± 0.1 m",
"~2.5 m/s" — never strip a stated tolerance; a named constant like 2π becomes its decimal), or "none" if
the claim is qualitative. Return JSON:
{{"claims": [{{"id": "{prefix}1", "text": "...", "kind": "record|estimate|inference|rejected_by_source|open_question",
  "anchor": {{"corner": "...", "cell": "...", "held_axis": "...", "neighbours_to_check": ["the corner's three neighbours, named for this datum"]}},
  "observables": [{{"name": "short name", "claimed_value": "number with units and stated precision, or none",
                    "precision_needed": "the precision this question needs, e.g. '1 cm', '1 %', 'order of magnitude'"}}]}}, ...]}}
At most {n} claims. If the section contains nothing testable (preamble, summary, moral), return {{"claims": []}}."""

P_ROUTES = """Claim {cid}: {claim}
Observable: {obs} — the claim asserts: {claimed}

Evidence passages (the ONLY admissible sources; each begins with its [filename]):
---
{ctx}
---

Find INDEPENDENT ROUTES to this observable's value WITHOUT using the claim's own number:
1. lookups: any passage that directly reports a value for this observable. Quote the value exactly as the
   passage gives it, with the [filename].
2. computations: any relation that reaches this observable from OTHER quantities the passages report
   (neighbours). Write the relation as an arithmetic expression over named variables (use sqrt, pi, ** for
   powers), and give each variable's value exactly as a passage reports it, with its [filename] and units.
   Convert nothing; if units differ, add the conversion factor as its own variable with its source.
Return JSON:
{{"lookups": [{{"value": "number with units", "file": "filename", "quote": "the sentence"}}],
  "computations": [{{"relation": "expression", "variables": {{"name": {{"value": "number", "units": "...", "file": "filename"}}}},
                    "result_units": "...", "note": "why this relation applies"}}],
  "none_found_because": "... or null"}}"""

P_JUDGE = """Claim {cid}: {claim}

Route report computed by the script (immutable):
{routes}

Evidence passages:
---
{ctx}
---

Run the three non-numeric cores, each independent, citing only the passages above:
- constraint: does the claim survive a change of scale, time, cost or causality the evidence lets you test?
- alternative: is there a competing explanation IN THE EVIDENCE with fewer violations? Name its [file].
- consequence: if the claim is wrong, what propagates, and is any of it irreversible?
A REJECT must cite a [file] and a number or finding from it; without that it is NO_DATA.
Return JSON:
{{"constraint": {{"verdict": "NOT_REJECT|REJECT|NO_DATA", "transformation": "...", "file": "... or null", "reason": "..."}},
  "alternative": {{"verdict": "NOT_REJECT|REJECT|NO_DATA", "alternative": "... or none", "file": "... or null", "reason": "..."}},
  "consequence": {{"verdict": "NOT_REJECT|REJECT|NO_DATA", "if_wrong": "...", "irreversible": false}},
  "implication": {{"propagates_to": ["..."], "risk": "low|medium|high"}},
  "ethics": {{"decision": "PERMIT|REFUSE|HALT", "reason": "..."}}}}"""

P_REVISE = """Claim {cid}: {claim}
Synthesis (by rule, from the cores): {synth}
Route report: {routes}

PASS 6–8. If REJECTED: fold — keep the question, drop the mechanism; give the folded question.
If UNSTABLE: for each observable with fewer than two independent routes, name the exact measurement,
survey, document or experiment that would supply the NEXT independent route (not a restatement).
If STABILIZED or LOCKED: give the reduced statement carrying the agreed number, and the kept terms.
Also give the likely misinterpretation and the proof against it.
Return JSON:
{{"folded_question": "... or null",
  "empty_cells": [{{"observable": "...", "next_route": "..."}}],
  "reduced_statement": "... or null", "kept_terms": ["..."],
  "likely_misinterpretation": "...", "proof_against_it": "...",
  "final": {{"state": "OUTPUT|REFUSAL|SILENCE", "statement": "one sentence; confident words only if STABILIZED or LOCKED"}}}}"""

# ----------------------------------------------------------------------------- route finding (script-verified)

def find_routes(model, ev, cid, claim, obs, claimed, tol, log, run_id, precision_needed=None):
    ctx = ev.retrieve(f"{obs} {claim}")
    rep = ask(model, SYSTEM, P_ROUTES.format(cid=cid, claim=claim, obs=obs, claimed=claimed, ctx=ctx))
    routes, rejected = [], []
    for lk in rep.get("lookups", []) or []:
        fn, val = (str(lk.get("file") or "")).strip("[] "), lk.get("value")
        v = parse_number(val)
        if v is None:
            rejected.append({"type": "lookup", "why": "no number", "raw": lk}); continue
        if ev.group_of(fn) is None:
            rejected.append({"type": "lookup", "why": f"file '{fn}' not in evidence", "raw": lk}); continue
        if not ev.contains_number(val, fn):
            rejected.append({"type": "lookup", "why": f"{val} not found in {fn}", "raw": lk}); continue
        b, bk = parse_band(val, v)
        routes.append({"type": "lookup", "value": v, "band": b, "band_kind": bk, "units": val, "file": fn, "group": ev.group_of(fn)})
    for cp in rep.get("computations", []) or []:
        rel, vars_ = cp.get("relation") or "", cp.get("variables") or {}
        values, groups, bad, relbands = {}, set(), None, []
        for name, spec in vars_.items():
            spec = spec if isinstance(spec, dict) else {"value": spec}
            fn = (str(spec.get("file") or "")).strip("[] ")
            v = parse_number(spec.get("value"))
            if v is None:
                bad = f"variable {name}: no number"; break
            if name.lower() in _CONST and not fn:
                continue
            if ev.group_of(fn) is None:
                bad = f"variable {name}: file '{fn}' not in evidence"; break
            if not ev.contains_number(spec.get("value"), fn):
                bad = f"variable {name}: {spec.get('value')} not found in {fn}"; break
            values[name] = v; groups.add(ev.group_of(fn))
            vb, _ = parse_band(str(spec.get("value")), v)
            if v:
                relbands.append(vb / abs(v))
        if bad:
            rejected.append({"type": "computation", "why": bad, "raw": cp}); continue
        try:
            result = evaluate(rel, values)
        except Exception as ex:
            rejected.append({"type": "computation", "why": f"cannot evaluate '{rel}': {ex}", "raw": cp}); continue
        relb = math.sqrt(sum(x * x for x in relbands)) if relbands else 0.1
        routes.append({"type": "computation", "value": result, "band": abs(result) * relb, "band_kind": "propagated (quadrature)",
                       "relation": rel, "inputs": values, "units": cp.get("result_units"), "groups": sorted(groups), "note": cp.get("note")})
    claimed_v = parse_number(claimed)
    claimed_b, claimed_bk = parse_band(claimed, claimed_v) if claimed_v is not None else (None, None)
    need = parse_number(precision_needed) if precision_needed else None
    need_rel = (need / abs(claimed_v)) if (need and claimed_v and "%" not in str(precision_needed)) else (need / 100 if need and "%" in str(precision_needed) else None)
    seen, independent = set(), []
    for r in routes:
        key = r.get("group") or "+".join(r.get("groups") or ["?"])
        if key in seen:
            r["duplicate_of_group"] = key; continue
        seen.add(key); independent.append(r)
    agree, disagree = [], []
    for r in independent:
        if claimed_v is None:
            r["compare"] = "claim has no number"; continue
        diff = r["value"] - claimed_v
        r["rel_diff"] = round(abs(diff) / abs(claimed_v), 5) if claimed_v else abs(diff)
        two_sigma = 2 * (r["band"] + claimed_b)
        r["two_sigma"] = two_sigma
        if is_bound(claimed):
            ok = (diff >= -two_sigma) if re.search(r"[≥>]|at least|more than", claimed) else (diff <= two_sigma)
            r["compare"] = "bound"
        else:
            ok = abs(diff) <= two_sigma
        r["within_2sigma"] = ok
        r["coarse"] = bool(need_rel is not None and claimed_v and (r["band"] / abs(claimed_v)) > need_rel)
        (agree if ok else disagree).append(r)
    report = {"observable": obs, "claimed": claimed, "claimed_value": claimed_v, "claimed_band": claimed_b, "claimed_band_kind": claimed_bk,
              "precision_needed": precision_needed, "routes": routes,
              "fine_agree": sum(1 for r in agree if not r.get("coarse")),
              "independent_routes": len(independent), "agree": len(agree), "disagree": len(disagree),
              "disagreeing": disagree, "rejected_candidates": rejected, "none_found_because": rep.get("none_found_because")}
    log.write(run=run_id, claim=cid, pass_="ROUTE_STATE", observable=obs, input=ctx, model_proposal=rep, report=report)
    return report, ctx

def synthesis_by_rule(reports, judge):
    """PRF 2.6: any REJECT -> REJECTED; else any NO_DATA -> UNSTABLE; else -> STABILIZED / LOCKED.
       The outcome core is computed from routes; the lock level from the agreeing route count."""
    outcome, lock, reason = "NO_DATA", 0, []
    if reports:
        if any(r["disagree"] for r in reports):
            outcome = "REJECT"
            for r in reports:
                for d in r["disagreeing"]:
                    reason.append(f"{r['observable']}: route {d.get('file') or d.get('relation')} gives {d['value']:.6g} ± {d['band']:.3g} "
                                  f"vs claimed {r['claimed_value']:.6g} ± {r['claimed_band']:.3g}; gap {abs(d['value']-r['claimed_value']):.3g} > 2σ = {d['two_sigma']:.3g}")
        else:
            lock = min(r["agree"] for r in reports)
            fine = min(r.get("fine_agree", 0) for r in reports)
            outcome = "NOT_REJECT" if lock >= 2 else "NO_DATA"
            if lock >= 3 and fine < 3:
                lock = 2  # three agreements, but not all at the precision the question needs: stands, does not lock
            reason = [f"{r['observable']}: {r['agree']} independent route(s) agree within 2σ"
                      + (f" ({r['agree'] - r.get('fine_agree', 0)} coarse)" if r['agree'] > r.get('fine_agree', 0) else "") for r in reports]
    cores = {"outcome": {"verdict": outcome, "reason": "; ".join(reason) or "no numeric observable"}}
    for k in ("constraint", "alternative", "consequence"):
        c = dict(judge.get(k)) if isinstance(judge.get(k), dict) else {}
        v = c.get("verdict", "NO_DATA")
        if k == "alternative":
            # an alternative counts only if it is carried to evidence; an unsupported one is recorded, not counted
            if v == "REJECT" and not c.get("file"):
                c["recorded_not_counted"] = "alternative offered without an evidence file"; v = "NOT_REJECT"
            elif v == "NO_DATA":
                c["note"] = "no competing explanation found in evidence"; v = "NOT_REJECT"
        elif v == "REJECT" and not c.get("file") and k == "constraint":
            c["downgraded"] = "REJECT without an evidence file"; v = "NO_DATA"
        c["verdict"] = v; cores[k] = c
    if any(c["verdict"] == "REJECT" for c in cores.values()):
        synth = "REJECTED"
    elif any(c["verdict"] == "NO_DATA" for c in cores.values()):
        synth = "UNSTABLE"
    else:
        synth = "LOCKED" if lock >= 3 else "STABILIZED"
    return synth, cores, lock

# ----------------------------------------------------------------------------- run

def sections(doc):
    parts = re.split(r"(?m)^(#{1,3} .+)$", doc)
    out = [("(preamble)", parts[0])] if parts[0].strip() else []
    for i in range(1, len(parts), 2):
        out.append((parts[i].lstrip("# ").strip(), parts[i + 1]))
    return [(h, t) for h, t in out if t.strip()]

def run(path, model, question, max_claims, tol, out_dir, evidence_dir):
    doc = open(path, encoding="utf-8").read()
    ev = Evidence(evidence_dir)
    stamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    run_id = f"{stamp}-{uuid.uuid4().hex[:6]}"
    os.makedirs(out_dir, exist_ok=True)
    log = Log(os.path.join(out_dir, f"run-{run_id}.jsonl"))
    log.write(run=run_id, pass_="ENTRY_STATE", input=os.path.basename(path), question=question, model=model,
              tolerance=tol, evidence_files=[d[0] for d in ev.docs], evidence_groups=ev.groups)
    if len(ev.groups) < 2:
        print(f"WARNING: evidence/ has {len(ev.groups)} source group(s); nothing can stabilize with fewer than 2.")
    t0 = time.time()

    claims, secs = [], sections(doc)
    total = sum(len(t) for _, t in secs) or 1
    for i, (heading, text) in enumerate(secs):
        if len(claims) >= max_claims:
            break
        per = max(1, round(max_claims * len(text) / total))
        got = ask(model, SYSTEM, P_EXTRACT.format(heading=heading, doc=text[:12000], question=question or "",
                                                  prefix=f"s{i+1}c", n=per))
        for c in got.get("claims", []) or []:
            c["section"] = heading; claims.append(c)
    claims = claims[:max_claims]
    log.write(run=run_id, pass_="RECOGNITION_STATE", claims=claims, elapsed=round(time.time() - t0, 1))
    print(f"[{run_id}] {len(claims)} claims from {len(secs)} sections; evidence groups: {', '.join(ev.groups) or 'NONE'}")

    results = []
    for c in claims:
        cid, text = c.get("id", "?"), c.get("text", "")
        print(f"  {cid} [{c.get('section')}] {text}")
        t = time.time(); reports, ctx_all = [], []
        for o in (c.get("observables") or [])[:4]:
            name, claimed = o.get("name", ""), o.get("claimed_value", "none")
            if not name or str(claimed).lower() == "none" or parse_number(claimed) is None:
                continue
            rep, ctx = find_routes(model, ev, cid, text, name, claimed, tol, log, run_id, o.get("precision_needed"))
            reports.append(rep); ctx_all.append(ctx)
        brief = [{"observable": r["observable"], "claimed": r["claimed"], "independent_routes": r["independent_routes"],
                  "agree": r["agree"], "disagree": r["disagree"],
                  "routes": [{k: v for k, v in rt.items() if k in ("type", "value", "band", "file", "relation", "groups", "group", "within_2sigma", "coarse")}
                             for rt in r["routes"]]} for r in reports]
        ctx = ctx_all[0] if ctx_all else ev.retrieve(text)
        judge = ask(model, SYSTEM, P_JUDGE.format(cid=cid, claim=text, routes=json.dumps(brief, ensure_ascii=False), ctx=ctx))
        synth, cores, lock = synthesis_by_rule(reports, judge)
        e = {"quad_core": cores, "lock_level": lock, "synthesis": synth, "implication": judge.get("implication"),
             "ethics": judge.get("ethics"), "model_judge_raw": judge}
        log.write(run=run_id, claim=cid, pass_="EVALUATION_STATE", output=e, elapsed=round(time.time() - t, 1))
        if (judge.get("ethics") or {}).get("decision") == "HALT":
            log.write(run=run_id, claim=cid, pass_="FINAL_STATE", state="HALT")
            results.append((c, "HALT", e, {}, reports)); print("      → HALT"); continue
        r = ask(model, SYSTEM, P_REVISE.format(cid=cid, claim=text, synth=synth, routes=json.dumps(brief, ensure_ascii=False)))
        if synth in ("STABILIZED", "LOCKED") and not r.get("reduced_statement"):
            r["reduced_statement"] = text
        log.write(run=run_id, claim=cid, pass_="REVISION_STATE", output=r)
        log.write(run=run_id, claim=cid, pass_="FINAL_STATE", synthesis=synth, output=r.get("final"))
        results.append((c, synth, e, r, reports))
        print(f"      → {synth}  (" + "; ".join(f"{rp['observable']}: {rp['agree']}✓ {rp['disagree']}✗ of {rp['independent_routes']}"
              + (f", {rp['agree']-rp.get('fine_agree',0)} coarse" if rp['agree'] > rp.get('fine_agree', 0) else "") for rp in reports) + ")")

    summary = render_summary(run_id, path, question, model, tol, ev, results, time.time() - t0)
    sp = os.path.join(out_dir, f"run-{run_id}-summary.md")
    open(sp, "w", encoding="utf-8").write(summary)
    log.write(run=run_id, pass_="PROCESS_ARCHIVED", summary=sp, total_elapsed=round(time.time() - t0, 1))
    print(summary); print(f"log: {log.path}\nsummary: {sp}")

def render_summary(run_id, path, question, model, tol, ev, results, elapsed):
    counts = {}
    for _, s, _, _, _ in results:
        counts[s] = counts.get(s, 0) + 1
    L = [f"# Run {run_id}", f"claims: {os.path.basename(path)} · evidence groups: {', '.join(ev.groups) or 'NONE'} · "
         f"model: {model} · agreement: 2σ of combined bands · question: {question or '(none)'} · {len(results)} claims · {elapsed/60:.1f} min",
         "", "counts: " + ", ".join(f"{k} {v}" for k, v in sorted(counts.items())), ""]
    def line(c): return f"- **{c.get('id')}** [{c.get('section')}] {c.get('text')}"
    L.append("## Locked / stabilized — routes that agreed")
    for c, s, e, r, reps in results:
        if s in ("LOCKED", "STABILIZED"):
            L.append(line(c) + f" — **{s}**")
            for rp in reps:
                for rt in rp["routes"]:
                    if "within_2sigma" in rt:
                        L.append(f"  - {rp['observable']}: {rt['type']} {rt.get('file') or rt.get('relation')} → {rt['value']:.6g} ± {rt['band']:.3g} "
                                 f"[{rt['band_kind']}] vs claimed {rp['claimed_value']:.6g} ± {rp['claimed_band']:.3g} [{rp['claimed_band_kind']}]"
                                 + (" — coarse for the precision needed" if rt.get("coarse") else ""))
            if r.get("reduced_statement"): L.append(f"  - reduced: {r['reduced_statement']}")
    L.append("\n## Rejected — the route that disagreed")
    for c, s, e, r, reps in results:
        if s == "REJECTED":
            L.append(line(c))
            for k, v in e["quad_core"].items():
                if v.get("verdict") == "REJECT": L.append(f"  - {k}: {v.get('reason')}")
            if r.get("folded_question"): L.append(f"  - folded → {r['folded_question']}")
    L.append("\n## Unstable — next independent route needed")
    for c, s, e, r, reps in results:
        if s == "UNSTABLE":
            L.append(line(c))
            for rp in reps:
                L.append(f"  - {rp['observable']}: {rp['independent_routes']} independent route(s)" +
                         (f"; none found because: {rp['none_found_because']}" if rp['independent_routes'] == 0 and rp.get('none_found_because') else ""))
            for cell in r.get("empty_cells") or []:
                L.append(f"  - next route for {cell.get('observable')}: {cell.get('next_route')}")
            if not reps: L.append("  - (no numeric observable; qualitative claim)")
    L.append("\n## Citations the script threw out (model proposed; evidence did not contain)")
    n = 0
    for c, s, e, r, reps in results:
        for rp in reps:
            for rj in rp["rejected_candidates"]:
                n += 1
                if n <= 25: L.append(f"- {c.get('id')} {rp['observable']}: {rj['type']} — {rj['why']}")
    if n > 25: L.append(f"- … {n-25} more in the log")
    return "\n".join(L) + "\n"

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("source", help="the document under test (put it in claims/)")
    ap.add_argument("--model", default=os.environ.get("MODEL", "qwen2.5:14b"))
    ap.add_argument("--question", default="")
    ap.add_argument("--max-claims", type=int, default=12)
    ap.add_argument("--tolerance", type=float, default=0.0, help="unused since v1.1: agreement is at 2σ of the combined bands")
    ap.add_argument("--evidence", default=os.path.join(HERE, "evidence"))
    ap.add_argument("--out", default=os.path.join(HERE, "logs"))
    a = ap.parse_args()
    try:
        requests.get(f"{OLLAMA}/api/tags", timeout=5)
    except Exception:
        sys.exit(f"Ollama not reachable at {OLLAMA}. Start it: `ollama serve` (and `ollama pull {a.model}`).")
    run(a.source, a.model, a.question, a.max_claims, a.tolerance, a.out, a.evidence)
