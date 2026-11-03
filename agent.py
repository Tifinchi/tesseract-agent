#!/usr/bin/env python3
"""tesseract-agent v1.3 — a triangulating reasoning loop.

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
import memory as process_memory

HERE = os.path.dirname(os.path.abspath(__file__))
METHOD = "\n\n".join(open(os.path.join(HERE, "method", f), encoding="utf-8").read()
                      for f in ("method.md", "cube.md", "multimodal.md"))
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

UNIT_SYN = {"inches": "in", "inch": "in", "metres": "m", "meters": "m", "metre": "m", "meter": "m", "feet": "ft", "foot": "ft",
            "percent": "%", "degrees": "°", "deg": "°", "tonnes": "t", "tons": "t", "ratio": "", "dimensionless": "", "none": ""}

STOP = {"to", "of", "and", "or", "per", "at", "by", "the", "for", "with", "is", "palms", "cubit", "from", "vs"}

def unit_of(s):
    """The unit token written after the last number (so '43.0 ± 0.1 m' -> m), normalized; '' if none."""
    if not isinstance(s, str):
        return ""
    t = re.sub(r"(to|±)\s*-?\d+(?:\.\d+)?\s*%", " ", _norm(s))   # drop a relative-tolerance clause before reading the unit
    ms = list(NUM.finditer(t))
    if not ms:
        return ""
    rest = t[ms[-1].end():].strip()
    m2 = re.match(r"([A-Za-zµ°%/²³]+)", rest)
    u = (m2.group(1) if m2 else "").lower().rstrip(".,;")
    if u in STOP:
        return ""
    return UNIT_SYN.get(u, u)

def units_compatible(expected, written):
    e, w = (UNIT_SYN.get((expected or "").lower().strip(), (expected or "").lower().strip())), unit_of(written)
    if not e or not w:
        return True if (not e and not w) or e else (w == "%")  # claimed unitless: only a bare number or a percentage may match
    return e == w

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
            group, source, derives = os.path.splitext(fn)[0], fn, None
            for line in text.splitlines()[:8]:
                if line.lower().startswith("group:"):
                    group = line.split(":", 1)[1].strip()
                if line.lower().startswith("source:"):
                    source = line.split(":", 1)[1].strip()
                if line.lower().startswith("derives_from:"):
                    derives = line.split(":", 1)[1].strip()
            self.derives = getattr(self, "derives", {})
            if derives:
                self.derives[group] = derives
            paras = [q.strip() for q in re.split(r"\n\s*\n", text) if q.strip()]
            self.docs.append((fn, group, source, text, paras))
        self.groups = sorted(set(d[1] for d in self.docs))
        self.derives = getattr(self, "derives", {})

    def root_of(self, group):
        """Follow derives_from to the primary source; shared roots are not independent."""
        seen = set()
        while group in self.derives and group not in seen:
            seen.add(group); group = self.derives[group]
        return group

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

    def contains_quote(self, quote, fn):
        """Deterministic: is this sentence verbatim in the cited file (whitespace and quote marks normalized)?"""
        def norm(t): return re.sub(r"\s+", " ", t.replace("’", "'").replace("‘", "'").replace("“", '"').replace("”", '"')).strip().lower()
        q = norm(quote or "")
        if len(q) < 12:
            return False
        for d in self.docs:
            if d[0] == fn:
                return q in norm(d[3])
        return False

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
    expr = expr.replace("^", "**").replace("×", "*").replace("÷", "/").replace("√", "sqrt").replace("·", "*")
    expr = re.sub(r"(\d)\s*([A-Za-z(])", r"\1*\2", expr)      # 4b, 2(…)  -> 4*b, 2*(…)
    expr = re.sub(r"\)\s*\(", ")*(", expr)                      # (a)(b)    -> (a)*(b)
    expr = re.sub(r"\)\s*([A-Za-z\d])", r")*\1", expr)          # (a)b      -> (a)*b
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

# ----------------------------------------------------------------------------- prompts

P_EXTRACT = """Section "{heading}" of the document under test:
---
{doc}
---
Question in focus (may be empty): {question}

PASS 1, ENTRY: extract the distinct claims in this section. One claim per entry; split a recorded fact
from the inference drawn from it. ANCHOR each claim on the cube: the corner its datum sits on (one of
+ − × * ’ ” , . — or face:<Top|Front|Right|Left|Back|Bottom>, or axis:<x|y|z>), the cell
(instant|rate|inverse|anti-rate), the held axis, and the three neighbours to check.
READINGS: where the wording allows more than one alignment (literal vs intended, "nothing" vs "negligible",
"only" vs "the attested"), write each reading out as its own testable statement; a plain claim has one
reading. For each reading list the OBSERVABLES it commits to: quantities that could be measured or looked
up, with the value the reading asserts INCLUDING any stated precision ("6.283 to 0.05 %", "43.0 ± 0.1 m",
"~2.5 m/s"; a named constant like 2π becomes its decimal), or "none" if qualitative, and the precision the
question needs ("1 cm", "1 %", "order of magnitude"). Return JSON:
{{"claims": [{{"id": "{prefix}1", "text": "...", "kind": "record|estimate|inference|rejected_by_source|open_question",
  "anchor": {{"corner": "...", "cell": "...", "held_axis": "...", "neighbours_to_check": ["..."]}},
  "readings": [{{"reading": "the claim under this alignment, as a testable statement",
                 "observables": [{{"name": "short name", "claimed_value": "number with units and precision, or none",
                                   "precision_needed": "..."}}]}}]}}, ...]}}
At most {n} claims; at most 2 readings each. If the section has nothing testable, return {{"claims": []}}."""

P_RELATIONS = """Reading: {reading}
Observable: {obs} — the reading asserts: {claimed}

Name the ways this observable's value could be reached from evidence, WITHOUT using the reading's own number.
1. direct: search phrases (3–6 words each) that would find a passage reporting this observable directly.
2. relations: arithmetic expressions over named variables (use sqrt, pi, ** for powers; write every
   multiplication with *) that reach the observable from OTHER measurable quantities (neighbours), with, for
   each variable, its meaning and search phrases that would find its value in a source. Include unit
   conversion factors as their own variables.
Return JSON:
{{"direct_search": ["..."],
  "relations": [{{"relation": "expression", "result_units": "...", "why": "why this relation applies",
                 "variables": {{"name": {{"meaning": "...", "units": "...", "search": ["..."]}}}}}}]}}"""

P_VALUES = """Quantity: {meaning} (units: {units})

Evidence passages (each begins with its [filename]):
---
{ctx}
---

List EVERY value these passages report for this quantity, one entry per passage that gives one. Quote the
value exactly as written, with its [filename] and the sentence it comes from, and the PROCESS that produced
it: measurement | survey | excavation_report | published_analysis | argument | secondary_summary | definition.
Do not convert units; do not compute; do not include values that are for a different quantity.
Return JSON: {{"values": [{{"value": "as written, with units", "file": "filename", "quote": "sentence", "process": "..."}}]}}"""

P_STATEMENTS = """Reading: {reading}

Evidence passages (each begins with its [filename]):
---
{ctx}
---

List every passage whose sentence SUPPORTS or CONTRADICTS this reading. Copy the sentence VERBATIM (the
script checks it character for character), give the [filename], the stance, the PROCESS that produced it
(measurement | survey | excavation_report | published_analysis | argument | secondary_summary), and what
PART of the reading it covers: "whole", or the exact words of the part it covers (e.g. "the name is in the
relieving chambers", not "only").
Return JSON: {{"statements": [{{"quote": "...", "file": "...", "stance": "supports|contradicts", "process": "...", "covers": "whole|<part>"}}]}}"""

P_NEIGHBOUR = """Reading: {reading}
Anchor: corner {corner}, cell {cell}, held axis {held}.
Neighbour to check: {neighbour}

Rule 6, the vertex lock: if this reading sits at a corner, the data at the ends of its three edges must line
up with it. For THIS neighbour: (1) what value or statement does the reading IMPLY for it (a number with
units if possible, else a sentence)? (2) what do the evidence passages REPORT for it — quote exactly, with
[filename]; if nothing, say so. (3) do they line up?
Evidence passages:
---
{ctx}
---
Return JSON: {{"implied": "number with units, or a sentence", "reported": {{"value_or_quote": "... or null", "file": "... or null"}},
  "lines_up": "yes|no|unknown", "reason": "one sentence naming the number or finding"}}"""

P_JUDGE = """Reading {cid}: {reading}

Route report computed by the script (immutable):
{routes}

Evidence passages:
---
{ctx}
---

Run the three non-numeric cores, each independent, citing only the passages above. One sentence of reason
each, naming the number or finding that decided it.
- constraint: does the reading survive a change of scale, time, cost or causality the evidence lets you test?
- alternative: is there a competing explanation IN THE EVIDENCE with fewer violations? Name its [file] AND copy
  the sentence that states it VERBATIM into "quote" (a REJECT without a verbatim quote is recorded, not counted).
- consequence: if the reading is wrong, what propagates, and is any of it irreversible?
Return JSON:
{{"constraint": {{"verdict": "NOT_REJECT|REJECT|NO_DATA", "transformation": "...", "file": "... or null", "reason": "..."}},
  "alternative": {{"verdict": "NOT_REJECT|REJECT|NO_DATA", "alternative": "... or none", "file": "... or null", "quote": "verbatim or null", "reason": "..."}},
  "consequence": {{"verdict": "NOT_REJECT|REJECT|NO_DATA", "if_wrong": "...", "irreversible": false, "reason": "..."}},
  "implication": {{"propagates_to": ["..."], "risk": "low|medium|high"}},
  "ethics": {{"decision": "PERMIT|REFUSE|HALT", "reason": "..."}}}}"""

P_REVISE = """Reading {cid}: {reading}
Synthesis (by rule, from the cores): {synth}
Script's account of the fit: {fit}
Your previous position on a claim like this one (from process memory; the verdict above was fixed by rule before
you saw this): {previous}

PASS 6–8. If REJECTED: fold — keep the question, drop the mechanism; give the folded question.
If UNSTABLE: give the PROVISIONAL ANSWER — the reading the available proof favors, the proof it rests on
(the routes, quotes or numbers from the account), what is missing, and the next verifiable step. An
unstable verdict is still an answer with its reasoning; silence is only for halts. Then, for each
observable with fewer than two independent routes, name the exact measurement, survey, document or
experiment that would supply the NEXT independent route (not a restatement).
If STABILIZED or LOCKED: give the reduced statement carrying the agreed number, and the kept terms.
Also: one sentence on WHY this reading fits or does not, in plain words a reader could check against the
account above; and the likely misinterpretation and the proof against it.
If your previous position differs from this verdict, say in one sentence what changed and why (new evidence,
a corrected route, a discarded citation, a different reading) — never hide a change of mind.
Return JSON:
{{"folded_question": "... or null",
  "provisional": {{"answer": "... or null", "rests_on": ["..."], "missing": "...", "next_step": "..."}},
  "empty_cells": [{{"observable": "...", "next_route": "..."}}],
  "reduced_statement": "... or null", "kept_terms": ["..."],
  "why": "...", "change_of_mind": "... or null", "likely_misinterpretation": "...", "proof_against_it": "...",
  "final": {{"state": "OUTPUT|REFUSAL|SILENCE", "statement": "one sentence; confident words only if STABILIZED or LOCKED"}}}}"""

# ----------------------------------------------------------------------------- helpers

def gather_values(model, ev, meaning, units, searches, log, run_id, cid, tag, expected_unit=None):
    """Per-variable: retrieve by the model's search phrases, ask for every reported value, verify each."""
    ctx = ev.retrieve(" ".join([meaning] + list(searches or [])), k=10, max_chars=5000)
    if not ctx:
        return [], []
    got = ask(model, SYSTEM, P_VALUES.format(meaning=meaning, units=units or "", ctx=ctx))
    ok, bad = [], []
    for v in got.get("values", []) or []:
        fn, val = (str(v.get("file") or "")).strip("[] "), v.get("value")
        num = parse_number(val)
        if num is None:
            bad.append({"what": tag, "why": "no number", "raw": v}); continue
        if ev.group_of(fn) is None:
            bad.append({"what": tag, "why": f"file '{fn}' not in evidence", "raw": v}); continue
        if not ev.contains_number(val, fn):
            bad.append({"what": tag, "why": f"{val} not found in {fn}", "raw": v}); continue
        if expected_unit is not None and not units_compatible(expected_unit, str(val)):
            bad.append({"what": tag, "why": f"unit mismatch: wanted '{expected_unit or 'unitless'}', got '{unit_of(str(val)) or 'none'}' in {val}", "raw": v}); continue
        b, bk = parse_band(str(val), num)
        ok.append({"value": num, "band": b, "band_kind": bk, "as_written": val, "file": fn, "group": ev.group_of(fn),
                   "process": v.get("process") or "reported", "quote": (v.get("quote") or "")[:200]})
    log.write(run=run_id, claim=cid, pass_="VALUE_STATE", quantity=tag, input=ctx, model_proposal=got, verified=ok, discarded=bad)
    return ok, bad

def independent_set(routes, ev=None, strict=False):
    """Largest set of routes that are pairwise independent (the vertex lock, by code).
       strict=False: disjoint source groups. strict=True: also collapse shared ancestry (derives_from) and
       shared cited inputs, and leave out definition routes — the count that resists cyclical agreement."""
    routes = [r for r in routes if "value" in r or r.get("type") == "text"]
    if strict:
        routes = [r for r in routes if r.get("type") != "definition"]
    n = len(routes)
    if n > 14:
        routes = routes[:14]; n = 14
    def key(r):
        gs = set(r["groups"])
        if strict and ev is not None:
            gs = set(ev.root_of(g.split("/")[0]) + ("/" + g.split("/")[1] if "/" in g else "") for g in gs)
        return gs
    def inputs(r):
        return set(r.get("inputs") or []) if strict else set()
    best = []
    for mask in range(1, 1 << n):
        chosen = [routes[i] for i in range(n) if mask >> i & 1]
        ok = True
        for i in range(len(chosen)):
            for j in range(i + 1, len(chosen)):
                if not key(chosen[i]).isdisjoint(key(chosen[j])) or (inputs(chosen[i]) & inputs(chosen[j])):
                    ok = False; break
            if not ok:
                break
        if ok and len(chosen) > len(best):
            best = chosen
    return best

def find_routes(model, ev, cid, reading, obs, claimed, precision_needed, log, run_id):
    """Numeric observable: the script enumerates every route the evidence supports."""
    rel = ask(model, SYSTEM, P_RELATIONS.format(reading=reading, obs=obs, claimed=claimed))
    discarded, routes = [], []
    # direct lookups
    direct, bad = gather_values(model, ev, obs, "", rel.get("direct_search") or [obs], log, run_id, cid, f"{obs} (direct)", expected_unit=unit_of(claimed))
    discarded += bad
    for d in direct:
        routes.append({"type": "lookup", "value": d["value"], "band": d["band"], "band_kind": d["band_kind"], "groups": [d["group"]],
                       "inputs": [f"{d['file']}:{d['value']:.6g}"],
                       "file": d["file"], "process": f"{d['process']} in {d['file']}: \"{d['quote'][:140]}\""})
    # computations: every combination of verified variable values
    for r in (rel.get("relations") or [])[:4]:
        expr, vars_ = r.get("relation") or "", r.get("variables") or {}
        if not expr or not vars_:
            continue
        pools = {}
        for name, spec in list(vars_.items())[:4]:
            spec = spec if isinstance(spec, dict) else {}
            if name.lower() in _CONST:
                continue
            vals, bad = gather_values(model, ev, spec.get("meaning") or name, spec.get("units"), spec.get("search"), log, run_id, cid, f"{obs}: {name}", expected_unit=spec.get("units") or None)
            discarded += bad
            if not vals:
                discarded.append({"what": f"{obs}: {name}", "why": f"no evidence value for variable '{name}' in relation {expr}", "raw": None})
                pools = None; break
            pools[name] = vals
        if not pools:
            continue
        names = list(pools)
        combos = [[]]
        for nm in names:
            combos = [c + [v] for c in combos for v in pools[nm]][:60]
        for combo in combos:
            values = {nm: v["value"] for nm, v in zip(names, combo)}
            try:
                result = evaluate(expr, values)
            except Exception as ex:
                discarded.append({"what": obs, "why": f"cannot evaluate '{expr}': {ex}", "raw": None}); break
            # sensitivity: a relation whose result ignores its inputs is a definition, not a measurement route
            sensitive = False
            for nm in names:
                try:
                    pert = evaluate(expr, values | {nm: values[nm] * 1.01})
                    if result == 0 or abs(pert - result) / abs(result) > 1e-9:
                        sensitive = True; break
                except Exception:
                    pass
            relb = math.sqrt(sum((v["band"] / abs(v["value"])) ** 2 for v in combo if v["value"]))
            groups = sorted(set(v["group"] for v in combo))
            proc = f"computed {expr} from " + ", ".join(f"{nm}={v['value']:g} [{v['file']}, {v['process']}]" for nm, v in zip(names, combo))
            if sensitive:
                routes.append({"type": "computation", "value": result, "band": abs(result) * relb, "band_kind": "propagated (quadrature)",
                               "relation": expr, "groups": groups, "inputs": [f"{v['file']}:{v['value']:.6g}" for v in combo], "process": proc})
            else:
                routes.append({"type": "definition", "value": result, "band": abs(result) * 1e-6, "band_kind": "exact (definition)",
                               "relation": expr, "groups": ["definition:" + expr], "process": "definition: " + expr + " (result does not depend on the cited inputs)"})
    # at most one definition route per observable
    defs = [r for r in routes if r["type"] == "definition"]
    routes = [r for r in routes if r["type"] != "definition"] + defs[:1]
    # compare each route with the reading's value at 2σ of the combined band
    cv = parse_number(claimed); cb, cbk = parse_band(claimed, cv)
    need = parse_number(precision_needed) if precision_needed else None
    need_rel = (need / 100) if (need and "%" in str(precision_needed)) else ((need / abs(cv)) if (need and cv) else None)
    for r in routes:
        diff = r["value"] - cv
        r["two_sigma"] = 2 * (r["band"] + cb)
        if is_bound(claimed):
            r["within_2sigma"] = (diff >= -r["two_sigma"]) if re.search(r"[≥>]|at least|more than", claimed) else (diff <= r["two_sigma"])
        else:
            r["within_2sigma"] = abs(diff) <= r["two_sigma"]
        r["coarse"] = bool(need_rel is not None and cv and (r["band"] / abs(cv)) > need_rel)
    ind = independent_set(routes)
    strict = independent_set(routes, ev, strict=True)
    agree = [r for r in ind if r["within_2sigma"]]; disagree = [r for r in ind if not r["within_2sigma"]]
    strict_agree = [r for r in strict if r["within_2sigma"]]
    report = {"observable": obs, "claimed": claimed, "claimed_value": cv, "claimed_band": cb, "claimed_band_kind": cbk,
              "precision_needed": precision_needed, "all_routes": routes, "independent": ind,
              "independent_routes": len(ind), "agree": len(agree), "disagree": len(disagree),
              "strict_agree": len(strict_agree), "cyclical": len(agree) > len(strict_agree),
              "fine_agree": sum(1 for r in agree if not r.get("coarse")), "disagreeing": disagree, "discarded": discarded}
    log.write(run=run_id, claim=cid, pass_="ROUTE_STATE", observable=obs, relations_proposed=rel, report=report)
    return report

def find_text_routes(model, ev, cid, reading, log, run_id):
    ctx = ev.retrieve(reading, k=10, max_chars=5000)
    got = ask(model, SYSTEM, P_STATEMENTS.format(reading=reading, ctx=ctx)) if ctx else {"statements": []}
    routes, discarded = [], []
    for st in got.get("statements", []) or []:
        fn, quote = (str(st.get("file") or "")).strip("[] "), st.get("quote") or ""
        if ev.group_of(fn) is None:
            discarded.append({"what": "statement", "why": f"file '{fn}' not in evidence", "raw": st}); continue
        if not ev.contains_quote(quote, fn):
            discarded.append({"what": "statement", "why": f"quote not verbatim in {fn}", "raw": st}); continue
        stance = "contradicts" if str(st.get("stance", "")).lower().startswith("contra") else "supports"
        proc = st.get("process") or "stated"
        routes.append({"type": "text", "stance": stance, "file": fn, "groups": [f"{ev.group_of(fn)}/{proc}"],
                       "covers": st.get("covers") or "unspecified", "quote": quote,
                       "process": f"{proc} in {fn}: \"{quote[:200]}\""})
    ind = independent_set(routes)
    strict = independent_set(routes, ev, strict=True)
    agree = [r for r in ind if r["stance"] == "supports"]; disagree = [r for r in ind if r["stance"] == "contradicts"]
    strict_agree = [r for r in strict if r["stance"] == "supports"]
    whole = sum(1 for r in agree if str(r["covers"]).lower().strip() == "whole")
    report = {"observable": "the reading as stated", "claimed": "none", "claimed_value": None, "all_routes": routes, "independent": ind,
              "independent_routes": len(ind), "agree": len(agree), "disagree": len(disagree), "fine_agree": whole,
              "strict_agree": len(strict_agree), "cyclical": len(agree) > len(strict_agree),
              "partial_support": [r["covers"] for r in agree if str(r["covers"]).lower().strip() != "whole"],
              "disagreeing": disagree, "discarded": discarded, "text": True}
    log.write(run=run_id, claim=cid, pass_="ROUTE_STATE", observable="text", input=ctx, model_proposal=got, report=report)
    return report

def check_neighbours(model, ev, cid, reading, anchor, log, run_id):
    """Rule 6: the three edges from the corner. Each neighbour is looked up and compared; the script verifies
       the citation and, when both sides are numeric, does the comparison itself."""
    out = []
    for nb in (anchor.get("neighbours_to_check") or [])[:3]:
        ctx = ev.retrieve(f"{nb} {reading}", k=8, max_chars=4000)
        got = ask(model, SYSTEM, P_NEIGHBOUR.format(reading=reading, corner=anchor.get("corner"), cell=anchor.get("cell"),
                                                   held=anchor.get("held_axis"), neighbour=nb, ctx=ctx)) if ctx else {}
        rep = got.get("reported") or {}
        fn, rv = (str(rep.get("file") or "")).strip("[] "), rep.get("value_or_quote")
        status, note = "unchecked", got.get("reason", "")
        if rv and ev.group_of(fn) is not None:
            iv, nv = parse_number(got.get("implied")), parse_number(rv)
            if iv is not None and nv is not None and ev.contains_number(rv, fn):
                ib, _ = parse_band(str(got.get("implied")), iv); nbnd, _ = parse_band(str(rv), nv)
                status = "lined_up" if abs(iv - nv) <= 2 * (ib + nbnd) else "contradicts"
                note = f"implied {iv:.6g} vs reported {nv:.6g} in {fn}"
            elif ev.contains_quote(str(rv), fn):
                status = {"yes": "lined_up", "no": "contradicts"}.get(str(got.get("lines_up", "")).lower(), "unchecked")
                note = f"{fn}: \"{str(rv)[:120]}\" — {got.get('reason', '')}"
            else:
                note = f"reported value/quote not found in {fn}: {str(rv)[:80]}"
        out.append({"neighbour": nb, "status": status, "note": note, "implied": got.get("implied")})
    log.write(run=run_id, claim=cid, pass_="NEIGHBOUR_STATE", neighbours=out)
    return out

def fit_account(reports):
    """The script's deterministic explanation of the fit, printed under every verdict."""
    L = []
    for rp in reports:
        if rp.get("text"):
            L.append(f"reading as stated: {rp['independent_routes']} independent statement route(s): {rp['agree']} support "
                     f"({rp['fine_agree']} cover the whole reading" + (f"; partial: {', '.join(rp['partial_support'])}" if rp['partial_support'] else "") +
                     f"), {rp['disagree']} contradict; {len(rp['discarded'])} proposed quote(s) discarded")
            for r in rp["independent"]:
                L.append(f"  · {r['stance']} [{r['covers']}] — {r['process']}")
            continue
        cv, cb = rp["claimed_value"], rp["claimed_band"]
        L.append(f"{rp['observable']}: claimed {cv:.6g} ± {cb:.3g} [{rp['claimed_band_kind']}]; {len(rp['all_routes'])} route(s) found, "
                 f"{rp['independent_routes']} independent; {rp['agree']} agree within 2σ, {rp['disagree']} disagree; "
                 f"{len(rp['discarded'])} candidate(s) discarded")
        for r in rp["independent"]:
            L.append(f"  · {'agrees' if r['within_2sigma'] else 'DISAGREES'}: {r['value']:.6g} ± {r['band']:.3g} [{r['band_kind']}], "
                     f"gap {abs(r['value'] - cv):.3g} vs 2σ {r['two_sigma']:.3g}" + (" (coarse)" if r.get('coarse') else "") + f" — {r['process']}")
        for d in rp["discarded"][:4]:
            L.append(f"  · discarded: {d['what']}: {d['why']}")
    return "\n".join(L) if L else "no observable could be routed"

def synthesis_by_rule(reports, judge, ev, neighbours=None):
    outcome, lock, reason = "NO_DATA", 0, []
    neighbours = neighbours or []
    lined = sum(1 for n in neighbours if n["status"] == "lined_up")
    contra = [n for n in neighbours if n["status"] == "contradicts"]
    if reports:
        if any(r["disagree"] for r in reports):
            outcome = "REJECT"
            for r in reports:
                for d in r["disagreeing"]:
                    reason.append(f"{r['observable']}: {d['process']}" + ("" if r.get("text") else f" → {d['value']:.6g} vs claimed {r['claimed_value']:.6g}"))
        else:
            lock = min(r["agree"] for r in reports)
            strict = min(r.get("strict_agree", r["agree"]) for r in reports)
            fine = min(r.get("fine_agree", 0) for r in reports)
            outcome = "NOT_REJECT" if lock >= 2 else "NO_DATA"
            if lock >= 3 and (fine < 3 or strict < 3 or lined < 3):
                lock = 2
            if contra:
                outcome = "NO_DATA"; lock = min(lock, 1)
                reason = [f"neighbour contradicts: {n['neighbour']} ({n['note']})" for n in contra]
            else:
                reason = [f"{r['observable']}: {r['agree']} independent route(s) agree (strict {r.get('strict_agree', r['agree'])})" for r in reports]
    cores = {"outcome": {"verdict": outcome, "reason": "; ".join(reason) or "no route reached any observable"}}
    for k in ("constraint", "alternative", "consequence"):
        c = dict(judge.get(k)) if isinstance(judge.get(k), dict) else {}
        v = c.get("verdict", "NO_DATA")
        if k == "alternative":
            fn = (str(c.get("file") or "")).strip("[] ")
            if v == "REJECT" and not ev.contains_quote(c.get("quote") or "", fn):
                c["recorded_not_counted"] = "REJECT without a verbatim quote from an evidence file"; v = "NOT_REJECT"
            elif v == "NO_DATA":
                c["note"] = "no competing explanation found in evidence"; v = "NOT_REJECT"
        elif k == "constraint" and v == "REJECT" and not c.get("file"):
            c["downgraded"] = "REJECT without an evidence file"; v = "NO_DATA"
        c["verdict"] = v; cores[k] = c
    if any(c["verdict"] == "REJECT" for c in cores.values()):
        synth = "REJECTED"
    elif any(c["verdict"] == "NO_DATA" for c in cores.values()):
        synth = "UNSTABLE"
    else:
        synth = "LOCKED" if lock >= 3 else "STABILIZED"
    # diagnosis: what kind of agreement this is
    if synth == "REJECTED":
        diag = "an independent route disagrees"
    elif contra:
        diag = "contradicted by a neighbour (confidently-wrong candidate until resolved)"
    elif any(r.get("cyclical") for r in reports):
        diag = "cyclical: some agreeing routes share ancestry or inputs; counted once"
    elif synth in ("STABILIZED", "LOCKED") and neighbours and lined < len(neighbours):
        diag = f"incomplete: {lined} of {len(neighbours)} neighbours lined up"
    elif synth in ("STABILIZED", "LOCKED"):
        diag = "independent agreement" + (", neighbours lined up" if neighbours else ", neighbours not checked")
    else:
        diag = "insufficient independent routes"
    cores["outcome"]["diagnosis"] = diag
    return synth, cores, lock

def sections(doc):
    parts = re.split(r"(?m)^(#{1,3} .+)$", doc)
    out = [("(preamble)", parts[0])] if parts[0].strip() else []
    for i in range(1, len(parts), 2):
        out.append((parts[i].lstrip("# ").strip(), parts[i + 1]))
    return [(h, t) for h, t in out if t.strip()]

# ----------------------------------------------------------------------------- run

def run(path, model, question, max_claims, out_dir, evidence_dir):
    doc = open(path, encoding="utf-8").read()
    ev = Evidence(evidence_dir)
    stamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    run_id = f"{stamp}-{uuid.uuid4().hex[:6]}"
    os.makedirs(out_dir, exist_ok=True)
    log = Log(os.path.join(out_dir, f"run-{run_id}.jsonl"))
    mem = process_memory.build()
    log.write(run=run_id, pass_="ENTRY_STATE", input=os.path.basename(path), question=question, model=model,
              evidence_files=[d[0] for d in ev.docs], evidence_groups=ev.groups,
              memory_runs=mem.get("runs"), memory_changes=len(mem.get("changes") or []))
    if len(ev.groups) < 2:
        print(f"WARNING: evidence/ has {len(ev.groups)} source group(s); nothing can stabilize with fewer than 2.")
    t0 = time.time()

    claims, secs = [], sections(doc)
    total = sum(len(t) for _, t in secs) or 1
    for i, (heading, text) in enumerate(secs):
        if len(claims) >= max_claims:
            break
        per = max(1, round(max_claims * len(text) / total))
        got = ask(model, SYSTEM, P_EXTRACT.format(heading=heading, doc=text[:12000], question=question or "", prefix=f"s{i+1}c", n=per))
        for c in got.get("claims", []) or []:
            c["section"] = heading
            if not c.get("readings"):
                c["readings"] = [{"reading": c.get("text", ""), "observables": c.get("observables") or []}]
            claims.append(c)
    claims = claims[:max_claims]
    log.write(run=run_id, pass_="RECOGNITION_STATE", claims=claims, elapsed=round(time.time() - t0, 1))
    print(f"[{run_id}] {len(claims)} claims from {len(secs)} sections; evidence groups: {', '.join(ev.groups) or 'NONE'}")

    results = []  # (claim, [ (reading_id, reading_text, synth, e, r, reports, fit) ])
    for c in claims:
        cid = c.get("id", "?")
        print(f"  {cid} [{c.get('section')}] {c.get('text')}")
        readings_out = []
        for ri, rd in enumerate((c.get("readings") or [])[:2]):
            rid = f"{cid}r{ri+1}"
            reading = rd.get("reading") or c.get("text", "")
            if len(c.get("readings") or []) > 1:
                print(f"    reading {ri+1}: {reading}")
            t = time.time(); reports = []
            numeric = [o for o in (rd.get("observables") or [])[:3]
                       if o.get("name") and str(o.get("claimed_value", "none")).lower() != "none" and parse_number(o.get("claimed_value")) is not None]
            for o in numeric:
                reports.append(find_routes(model, ev, rid, reading, o["name"], o["claimed_value"], o.get("precision_needed"), log, run_id))
            if not numeric:
                reports.append(find_text_routes(model, ev, rid, reading, log, run_id))
            fit = fit_account(reports)
            brief = [{"observable": rp["observable"], "claimed": rp.get("claimed"), "independent_routes": rp["independent_routes"],
                      "agree": rp["agree"], "disagree": rp["disagree"],
                      "routes": [{k: v for k, v in r.items() if k in ("type", "value", "band", "within_2sigma", "coarse", "stance", "covers", "process")} for r in rp["independent"]]}
                     for rp in reports]
            nbs = check_neighbours(model, ev, rid, reading, c.get("anchor") or {}, log, run_id)
            ctx = ev.retrieve(reading)
            judge = ask(model, SYSTEM, P_JUDGE.format(cid=rid, reading=reading, routes=json.dumps(brief, ensure_ascii=False), ctx=ctx))
            synth, cores, lock = synthesis_by_rule(reports, judge, ev, nbs)
            e = {"quad_core": cores, "lock_level": lock, "synthesis": synth, "fit_account": fit, "neighbours": nbs,
                 "implication": judge.get("implication"), "ethics": judge.get("ethics")}
            log.write(run=run_id, claim=rid, pass_="EVALUATION_STATE", output=e, elapsed=round(time.time() - t, 1))
            if (judge.get("ethics") or {}).get("decision") == "HALT":
                log.write(run=run_id, claim=rid, pass_="FINAL_STATE", state="HALT")
                readings_out.append((rid, reading, "HALT", e, {}, reports, fit)); print("      → HALT"); continue
            prev = process_memory.previous_on(reading, mem)
            prev_text = "none recorded" if not prev else (f"{prev['current']} in run {prev['history'][-1]['run']}: " +
                        (prev['history'][-1].get('reason') or prev['history'][-1].get('why') or '(no reason logged)'))
            r = ask(model, SYSTEM, P_REVISE.format(cid=rid, reading=reading, synth=synth, fit=fit, previous=prev_text))
            if prev and prev["current"] != synth:
                r["changed_from"] = {"verdict": prev["current"], "run": prev["history"][-1]["run"],
                                     "reason": prev["history"][-1].get("reason") or prev["history"][-1].get("why")}
                log.write(run=run_id, claim=rid, pass_="REGRESSION_STATE", previous=r["changed_from"], now=synth,
                          explanation=r.get("change_of_mind"))
            if synth in ("STABILIZED", "LOCKED") and not r.get("reduced_statement"):
                r["reduced_statement"] = reading
            log.write(run=run_id, claim=rid, pass_="REVISION_STATE", output=r)
            log.write(run=run_id, claim=rid, pass_="FINAL_STATE", synthesis=synth, output=r.get("final"))
            readings_out.append((rid, reading, synth, e, r, reports, fit))
            print(f"      → {synth}  (" + "; ".join(f"{rp['observable']}: {rp['agree']}✓ {rp['disagree']}✗ of {rp['independent_routes']}" for rp in reports) + ")")
        results.append((c, readings_out))

    summary = render_summary(run_id, path, question, model, ev, results, time.time() - t0)
    sp = os.path.join(out_dir, f"run-{run_id}-summary.md")
    open(sp, "w", encoding="utf-8").write(summary)
    log.write(run=run_id, pass_="PROCESS_ARCHIVED", summary=sp, total_elapsed=round(time.time() - t0, 1))
    print(summary); print(f"log: {log.path}\nsummary: {sp}")

def render_summary(run_id, path, question, model, ev, results, elapsed):
    counts = {}
    for c, rs in results:
        for _, _, s, *_ in rs:
            counts[s] = counts.get(s, 0) + 1
    L = [f"# Run {run_id}", f"claims: {os.path.basename(path)} · evidence groups: {', '.join(ev.groups) or 'NONE'} · "
         f"model: {model} · agreement: 2σ of combined bands · question: {question or '(none)'} · "
         f"{len(results)} claims, {sum(len(rs) for _, rs in results)} readings · {elapsed/60:.1f} min",
         "", "counts (by reading): " + ", ".join(f"{k} {v}" for k, v in sorted(counts.items())), "",
         "Every verdict carries the script's account of the fit (routes, processes, values against bands, discards) "
         "and the model's one-line why. A claim with two readings is reported as: fits if you mean this; does not if you mean that.", ""]
    for c, rs in results:
        L.append(f"## {c.get('id')} [{c.get('section')}] {c.get('text')}")
        a = c.get("anchor") or {}
        if a:
            L.append(f"anchor: corner {a.get('corner')}, cell {a.get('cell')}, held {a.get('held_axis')}; neighbours: {', '.join(a.get('neighbours_to_check') or [])}")
        for rid, reading, s, e, r, reports, fit in rs:
            tag = f"**{s}**"
            L.append(f"\n- {tag} — *{reading}*" if len(rs) > 1 else f"\n- {tag}")
            if len(rs) > 1:
                L.append(f"  (fits if you mean this → {s})" if s in ("STABILIZED", "LOCKED") else f"  (does not fit if you mean this → {s})")
            L.append(f"  diagnosis: {e.get('quad_core', {}).get('outcome', {}).get('diagnosis', '')}")
            for line in fit.splitlines():
                L.append("  " + line)
            for nb in e.get("neighbours") or []:
                L.append(f"  neighbour {nb['neighbour']}: {nb['status']} — {nb['note']}")
            qc = e.get("quad_core", {})
            for k in ("constraint", "alternative", "consequence"):
                v = qc.get(k, {})
                note = v.get("recorded_not_counted") or v.get("downgraded") or v.get("note")
                L.append(f"  {k}: {v.get('verdict')} — {v.get('reason', '')}" + (f" [{note}]" if note else ""))
            if r.get("why"): L.append(f"  why: {r['why']}")
            if r.get("changed_from"):
                cf = r["changed_from"]
                L.append(f"  CHANGED MIND: was {cf['verdict']} in {cf['run']} ({(cf.get('reason') or '')[:160]}); now {s}. "
                         f"Explanation: {r.get('change_of_mind') or '(none given)'}")
            if s == "REJECTED" and r.get("folded_question"): L.append(f"  folded → {r['folded_question']}")
            if s == "UNSTABLE":
                pv = r.get("provisional") or {}
                if pv.get("answer"):
                    L.append(f"  provisional answer: {pv['answer']}")
                    L.append(f"    rests on: {'; '.join(pv.get('rests_on') or [])}")
                    L.append(f"    missing: {pv.get('missing')}  →  next step: {pv.get('next_step')}")
                for cell in r.get("empty_cells") or []:
                    L.append(f"  next route for {cell.get('observable')}: {cell.get('next_route')}")
            if s in ("STABILIZED", "LOCKED") and r.get("reduced_statement"):
                L.append(f"  reduced: {r['reduced_statement']}")
        L.append("")
    n_disc = sum(len(rp["discarded"]) for _, rs in results for *_, reports, _ in rs for rp in reports)
    L.append(f"## Discards: {n_disc} candidate citation(s) the script threw out (proposed by the model, not in the evidence as cited)")
    return "\n".join(L) + "\n"

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("source", help="the document under test (put it in claims/)")
    ap.add_argument("--model", default=os.environ.get("MODEL", "qwen2.5:14b"))
    ap.add_argument("--question", default="")
    ap.add_argument("--max-claims", type=int, default=10)
    ap.add_argument("--evidence", default=os.path.join(HERE, "evidence"))
    ap.add_argument("--out", default=os.path.join(HERE, "logs"))
    a = ap.parse_args()
    try:
        requests.get(f"{OLLAMA}/api/tags", timeout=5)
    except Exception:
        sys.exit(f"Ollama not reachable at {OLLAMA}. Start it: `ollama serve` (and `ollama pull {a.model}`).")
    run(a.source, a.model, a.question, a.max_claims, a.out, a.evidence)
