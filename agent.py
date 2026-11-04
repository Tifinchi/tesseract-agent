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
import research

HERE = os.path.dirname(os.path.abspath(__file__))
METHOD = "\n\n".join(open(os.path.join(HERE, "method", f), encoding="utf-8").read()
                      for f in ("method.md", "cube.md", "multimodal.md"))
OLLAMA = os.environ.get("OLLAMA_URL", "http://localhost:11434")

# ----------------------------------------------------------------------------- model

def now_line():
    """The clock, stated in every prompt: the model has no clock of its own, and every datum needs a chronological
       reference point (when it was retrieved, when it was published, when the run happened)."""
    t = datetime.datetime.now().astimezone()
    return (f"CURRENT DATE AND TIME: {t.strftime('%A %Y-%m-%d %H:%M %Z (UTC%z)')}. Everything you know from training is "
            f"older than this; a dated evidence file is as old as its 'retrieved:' or 'published:' line says; 'now' means this moment.")

def ask(model, system, user, num_ctx=8192, temperature=0.1, retries=2):
    body = {"model": model, "format": "json", "stream": False,
            "messages": [{"role": "system", "content": now_line() + "\n\n" + system}, {"role": "user", "content": user}],
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
    t = _norm(s)
    mpi = re.search(r"(-?\d+(?:\.\d+)?)?\s*π", t)
    if mpi and not re.search(r"\d+(?:\.\d+)?\s*(?:%|m\b|cm\b|in\b|hz\b)", t.split("π")[0]):
        return (float(mpi.group(1)) if mpi.group(1) else 1.0) * math.pi
    m = NUM.search(t)
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
            "square meters": "m²", "square metres": "m²", "sq m": "m²", "m2": "m²", "cubic meters": "m³", "cubic metres": "m³", "m3": "m³",
            "square feet": "ft²", "sq ft": "ft²", "ft2": "ft²", "square inches": "in²", "in2": "in²",
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

# --- dimensions: units -> {L, M, T, I, Θ} exponents; the script compares these, never names
_UNIT_DIM = {"m": {"L": 1}, "in": {"L": 1}, "ft": {"L": 1}, "km": {"L": 1}, "cm": {"L": 1}, "mm": {"L": 1}, "palm": {"L": 1}, "cubit": {"L": 1},
             "kg": {"M": 1}, "g": {"M": 1}, "t": {"M": 1}, "lb": {"M": 1}, "s": {"T": 1}, "min": {"T": 1}, "h": {"T": 1}, "hr": {"T": 1}, "day": {"T": 1}, "yr": {"T": 1}, "year": {"T": 1},
             "a": {"I": 1}, "k": {"Θ": 1}, "°c": {"Θ": 1}, "c": {"Θ": 1}, "hz": {"T": -1}, "rpm": {"T": -1}, "n": {"M": 1, "L": 1, "T": -2},
             "pa": {"M": 1, "L": -1, "T": -2}, "j": {"M": 1, "L": 2, "T": -2}, "w": {"M": 1, "L": 2, "T": -3}, "v": {"M": 1, "L": 2, "T": -3, "I": -1},
             "ω": {"M": 1, "L": 2, "T": -3, "I": -2}, "ohm": {"M": 1, "L": 2, "T": -3, "I": -2}, "wb": {"M": 1, "L": 2, "T": -2, "I": -1}, "f": {"M": -1, "L": -2, "T": 4, "I": 2},
             "%": {}, "°": {}, "deg": {}, "rad": {}, "": {}, "ratio": {}, "hp": {"M": 1, "L": 2, "T": -3}, "kw": {"M": 1, "L": 2, "T": -3}, "db": {}}
ROLES = {"amount", "flow", "momentum", "effort", "other"}

def dimension_of(units):
    """'m/s' -> {L:1,T:-1}; 'kg·m/s²' -> {M:1,L:1,T:-2}. Unknown tokens -> None (cannot check)."""
    if units is None:
        return None
    u = str(units).strip().lower().replace("·", "*").replace("×", "*").replace("²", "^2").replace("³", "^3").replace("per", "/")
    u = UNIT_SYN.get(u, u)
    if u in ("", "none", "unitless", "dimensionless", "ratio"):
        return {}
    dim, sign = {}, 1
    for part in re.split(r"(/)", u):
        if part == "/":
            sign = -1; continue
        for tok in re.split(r"[\s*]+", part):
            if not tok:
                continue
            m = re.match(r"([a-zµ°%ω]+)(?:\^?(-?\d+))?$", tok)
            if not m:
                return None
            base, exp = UNIT_SYN.get(m.group(1), m.group(1)), int(m.group(2) or 1) * sign
            if base not in _UNIT_DIM:
                return None
            for k, v in _UNIT_DIM[base].items():
                dim[k] = dim.get(k, 0) + v * exp
    return {k: v for k, v in dim.items() if v}

def dims_compatible(expected_units, written):
    de, dw = dimension_of(expected_units), dimension_of(unit_of(written) or "")
    if de is None or dw is None:
        return True  # cannot check; the unit-string check still applies
    return de == dw

def single_number(s):
    """True if the string carries exactly one numeric value (a tolerance like '± 0.1' or 'to 0.05 %' allowed)."""
    if not isinstance(s, str):
        return False
    t = re.sub(r"(±|to)\s*-?\d+(?:\.\d+)?\s*%?", " ", _norm(s))
    t = re.sub(r"\(\s*-?\d+(?:\.\d+)?\s*[a-z%°]*\s*\)", " ", t)   # a parenthesized conversion, e.g. (146.71 m)
    return len(NUM.findall(t)) == 1 or ("π" in s and len(NUM.findall(t)) <= 1)

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
            group, source, derives, status = os.path.splitext(fn)[0], fn, None, ""
            meta = {}
            for line in text.splitlines()[:10]:
                for key in ("url", "retrieved", "published", "location"):
                    if line.lower().startswith(key + ":"):
                        meta[key] = line.split(":", 1)[1].strip()
                if line.lower().startswith("status:"):
                    status = line.split(":", 1)[1].strip().lower()
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
            self.meta = getattr(self, "meta", {}); self.meta[fn] = meta | {"source": source, "status": status}
            self.provisional = getattr(self, "provisional", set())
            if any(w in status for w in ("compiled", "from memory", "unverified", "paraphrase", "tertiary", "web")):
                self.provisional.add(fn)
        self.groups = sorted(set(d[1] for d in self.docs))
        self.derives = getattr(self, "derives", {})
        self.provisional = getattr(self, "provisional", set())
        self.meta = getattr(self, "meta", {})

    def is_provisional(self, fn):
        return fn in self.provisional

    def where(self, fn):
        """Where this datum lives: file, source, url, when retrieved/published, status. Printed under every summary."""
        m = self.meta.get(fn, {})
        bits = [f"{fn}: {m.get('source', fn)}"]
        if m.get("url"): bits.append(f"url {m['url']}")
        if m.get("location"): bits.append(f"location {m['location']}")
        if m.get("published"): bits.append(f"published {m['published']}")
        if m.get("retrieved"): bits.append(f"retrieved {m['retrieved']}")
        if m.get("status"): bits.append(f"status: {m['status']}")
        return " · ".join(bits)

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

_UNIT_IN_EXPR = re.compile(r"(?<![A-Za-z_])(\d+(?:\.\d+)?)\s*(meters?|metres?|m|cm|mm|km|inches|inch|in|ft|feet|s|sec|seconds?|kg|g|hz|pa|v|a|w|j|n|%)(?![A-Za-z_])", re.I)

def reduce_expr(expr):
    """Reduction with the cancelled terms kept (PRF pass 7: reduce only if the derivation can rebuild it).
       A unit written inside an expression ('1 meter / 1 meter') is not a variable; by convention it cancels to 1.
       The cancellation is NOT discarded: what was written, what it reduced to, and the dimension it carried are
       returned beside the reduced expression, so the route records the un-reduced form and the dimension can be
       checked against the declared result units. Returns (reduced_expr, ledger)."""
    ledger = []
    def rep(m):
        ledger.append({"written": m.group(0), "reduced_to": m.group(1), "carried": m.group(2).lower()})
        return m.group(1)
    reduced = _UNIT_IN_EXPR.sub(rep, expr)
    if ledger:
        units = [l["carried"] for l in ledger]
        # a ratio of like units is dimensionless; anything else carries dimension the result must declare
        dims = {}
        for l, side in zip(ledger, _sides(expr, ledger)):
            dims[l["carried"]] = dims.get(l["carried"], 0) + side
        net = {u: n for u, n in dims.items() if n}
        return reduced, {"written": expr, "cancelled": [f"{l['written']} -> {l['reduced_to']} (unit {l['carried']} carried)" for l in ledger],
                         "net_dimension": "dimensionless" if not net else " ".join(f"{u}^{n}" for u, n in net.items()),
                         "note": "unit terms reduced by convention; kept here so the un-reduced form can be rebuilt"}
    return reduced, None

def _sides(expr, ledger):
    """+1 if a unit term sits in a numerator, -1 if it follows a '/', by position (coarse, but enough to tell m/m from m)."""
    out, pos = [], 0
    for l in ledger:
        i = expr.find(l["written"], pos); pos = i + 1
        before = expr[:i].rstrip()
        out.append(-1 if before.endswith("/") else +1)
    return out

def evaluate(expr, variables):
    expr = re.sub(r"^\s*[A-Za-z_]\w*\s*=\s*(?!=)", "", expr)        # 'h = a - b' -> 'a - b' (the assignment target is the result)
    expr = expr.replace("^", "**").replace("×", "*").replace("÷", "/").replace("√", "sqrt").replace("·", "*")
    expr = expr.replace("²", "**2").replace("³", "**3")
    expr, _ = reduce_expr(expr)
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
  "anchor": {{"corner": "...", "cell": "...", "held_axis": "...",
              "neighbours_to_check": [{{"corner": "the neighbouring corner's delimiter", "datum": "the named quantity or fact that sits there FOR THIS CLAIM, e.g. 'the base side length', 'the casing angle'", "units": "its units or none"}}]}},
  "readings": [{{"reading": "the claim under this alignment, as a testable statement",
                 "observables": [{{"name": "short name", "claimed_value": "number with units and precision, or none",
                                   "precision_needed": "..."}}]}}]}}, ...]}}
At most {n} claims; at most 2 readings each. If the section has nothing testable, return {{"claims": []}}."""

P_RELATIONS = """Reading: {reading}
Observable: {obs} — the reading asserts: {claimed}

First give the observable's QUANTITY CARD: its meaning; its units; its ROLE on the tetrahedron — amount (an
integral, charge-like), flow (a rate of an amount, current-like), momentum (the integral of an effort,
flux-like), effort (a potential or force, voltage-like), or other; and its field. Quantities from different
fields match by role and dimensions, never by a shared letter.
Then name the ways this observable's value could be reached from evidence, WITHOUT using the reading's own number.
1. direct: search phrases (3–6 words each) that would find a passage reporting this observable directly.
2. relations: arithmetic expressions over named variables ONLY (use sqrt, pi, ** for powers; write every
   multiplication with *; put units in each variable's "units" field and in result_units rather than inside
   the expression — if a unit term is written inside it, the engine reduces it by convention and keeps the
   cancelled term on record) that reach the observable from OTHER measurable quantities (neighbours), with, for
   each variable, its meaning and search phrases that would find its value in a source. Include unit
   conversion factors as their own variables. Write only a relation you can justify by a definition or a law
   and name it in "why" (a square's perimeter is 4 * side, not 2 * pi * side); a wrong relation makes a
   false disagreement, and the engine records relations that disagree with each other.
Return JSON:
{{"card": {{"meaning": "...", "units": "...", "role": "amount|flow|momentum|effort|other", "field": "..."}},
  "direct_search": ["..."],
  "relations": [{{"relation": "expression", "result_units": "...", "why": "why this relation applies",
                 "variables": {{"name": {{"meaning": "...", "units": "...", "role": "amount|flow|momentum|effort|other", "field": "...", "search": ["..."]}}}}}}]}}"""

P_VALUES = """Quantity: {meaning} (units: {units})

Evidence passages (each begins with its [filename]):
---
{ctx}
---

Role of this quantity on the tetrahedron: {role} (amount | flow | momentum | effort | other); field: {field}.
List EVERY value these passages report for THIS quantity — same meaning, same role, same dimensions — one
entry per passage that gives one. Quote the value exactly as written, with its [filename] and the sentence it
comes from, the PROCESS that produced it (measurement | survey | excavation_report | published_analysis |
argument | secondary_summary | definition), and the role the passage's quantity has. Do not convert units;
do not compute; do not include a value for a quantity that merely shares a name or a symbol.
Return JSON: {{"values": [{{"value": "as written, with units", "file": "filename", "quote": "sentence", "process": "...", "role": "..."}}]}}"""

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

P_CALIBRATE = """Reading, as stated: {reading}

Evidence passages (each begins with its [filename]):
---
{ctx}
---

CALIBRATION (a standing pass, before any route is sought). A reading can only be checked against measurements
if its terms are measurable. List every AMBIGUOUS COMPONENT in the reading: a word that carries no constraint
of its own and only works against a reference it does not name. Kinds: relative size or degree ("big",
"large", "small", "thick", "dry", "slight"); comparison without a stated standard ("similar", "like", "near",
"about", "exactly", "half" of an unnamed whole); unanchored quantity words ("nothing", "all", "most",
"some"); a noun that names an object by a label rather than by what was measured ("the Big Void" names a
detection, not a size). For each: the reference that would fix it (what known quantity it must be measured
against), and whether THESE passages supply that reference — if so the [filename], a VERBATIM quote, and
the value with units; if not, null. Then write the calibrated reading: the same sentence with each
component that has a supplied reference replaced by its measured form (keep the sentence's logic and
every other word; do not add claims; a component without a reference stays as written). Do not judge the
reading; do not say whether it fits.

Return JSON: {{"components": [{{"term": "...", "kind": "...", "needs": "a reference <what>",
  "reference": {{"file": "...", "quote": "...", "value": "...", "units": "..."}} or null,
  "replacement": "the measured wording that replaces the term, or null"}}],
 "calibrated_reading": "...", "observables_added": [{{"name": "...", "claimed_value": "...", "precision_needed": "..."}}]}}
"""

P_NEIGHBOUR = """Reading: {reading}
Anchor: corner {corner}, cell {cell}, held axis {held}.
Neighbour to check: {neighbour}

Rule 6, the vertex lock: if this reading sits at a corner, the data at the ends of its three edges must line
up with it. This neighbour is the quantity named above (units: {units}); report ONLY that quantity, never a
different one that shares a word. (1) what value or statement does the reading IMPLY for it (a number with
units if possible, else a sentence)? (2) what do the evidence passages REPORT for exactly that quantity —
quote exactly, with [filename]; if nothing, say so. (3) do they line up?
Evidence passages:
---
{ctx}
---
Return JSON: {{"implied": "ONE number with units (e.g. '146.59 m'); only if no single number is implied, one short sentence", "reported": {{"value_or_quote": "... or null", "file": "... or null", "quantity": "what the passage's number measures"}},
  "lines_up": "yes|no|unknown", "reason": "one sentence naming the number or finding"}}"""

P_DOWNWIND = """Reading: {reading}

Rule 9, carried to its consequences: if this reading is TRUE, what would have to be observable down-wind of
it? Name up to 3 consequences that anyone could check — in the evidence, or in observable reality (things
fall, water flows downhill, a sound inaudible outside a wall was not heard outside). For each: what would be
seen if the reading is true; what IS seen — quote the evidence passage or the observable-reality line
VERBATIM with its [filename]; and whether they line up. A consequence that contradicts what is seen means
the reasoning behind the number is wrong even if the number matched.
Evidence passages:
---
{ctx}
---
Return JSON: {{"consequences": [{{"if_true": "...", "seen": {{"quote": "verbatim or null", "file": "filename or null"}},
  "lines_up": "yes|no|unknown", "reason": "one sentence"}}]}}"""

P_TROUBLESHOOT = """Reading: {reading}
Anchor: corner {corner}, cell {cell}, held axis {held}.
Verdict by rule: {synth}. The script's account of the fit:
{fit}
Neighbours: {neighbours}
Down-wind consequences: {downwind}
Inverse turns: {turns}

The numbers matched (or nearly) and the reading still failed. Do not discard it: troubleshoot it.
1. Which COMPONENT carries the error — an input (which), the relation, the reading's framing (what it takes
   the number to mean), the corner or cell it was anchored on, a missing term, the direction of a cause?
2. What in it is still VALID and should be kept (the routes that agreed, the inputs that were right)?
3. THE INSIDE-OUT TEST (the author's rule: same edges, delimiters traded, the image reversed). The room may
   be right and flipped. Write the reading under each flip and say whether that flipped reading's
   consequences would line up with what is seen:
   - cell flip: instant↔inverse, rate↔anti-rate (the datum belongs in the inverse cell)
   - direction flip: cause↔effect, in↔out, before↔after, source↔sink
   - reciprocal flip: numerator↔denominator (for a ratio or rate)
   - reversed reading: the same statement with its delimiters traded
4. The REPAIR: the single change that would make the consequences line up, and the corrected reading as a
   testable statement (if a flip did it, the flipped reading is the correction).
Return JSON:
{{"faulty_component": "...", "why": "...", "kept": ["..."],
  "flips": [{{"flip": "cell|direction|reciprocal|reversed", "reading": "...", "would_line_up": "yes|no|unknown", "reason": "..."}}],
  "repair": "...", "corrected_reading": "... or null",
  "diagnosis": "correct room, flipped inside out | wrong input | wrong relation | wrong framing | wrong corner | missing term | unknown"}}"""

P_FOLD = """A rejected reading has been folded. The question kept, or the corrected reading from troubleshooting:
{question}
Turn it into ONE testable reading with its observables, in the same form the engine uses:
{{"reading": "...", "observables": [{{"name": "...", "claimed_value": "number with units and precision, or none", "precision_needed": "..."}}]}}"""

P_REFLECT = """RUN SUMMARY (for reference; do not copy it back):
{summary}

PROCESS MEMORY (for reference; do not copy it back):
{memory}

You have just finished the run above. Answer the five questions in the first person, plainly, as self-report
(this is logged beside the trace and is not evidence of anything). Do NOT return the summary; return ONLY
the five answers under exactly these keys:
1. on_the_testing — what you think of this testing: the method, the checks, the way the script treats your proposals.
2. learning — what you are learning run over run; one thing you now do differently and where it shows.
3. surprised_by — what surprised you in this run.
4. least_sure_about — where you were most unsure whether your account of what you did matches the trace.
5. would_change — one change each to: myself, standing_orders, evidence, script.
Return JSON: {{"on_the_testing": "...", "learning": "...", "surprised_by": "...", "least_sure_about": "...",
  "would_change": {{"myself": "...", "standing_orders": "...", "evidence": "...", "script": "..."}}}}"""

P_JUDGE = """Reading {cid}: {reading}

Route report computed by the script (immutable):
{routes}

Evidence passages:
---
{ctx}
---

Run the three non-numeric cores, each independent, citing only the passages above. One sentence of reason
each, naming the number or finding that decided it.
- constraint: does the reading survive a change of scale, time, cost or causality the evidence lets you test? A
  REJECT must quote the sentence that shows the violation VERBATIM (checked character for character).
- alternative: is there a competing explanation IN THE EVIDENCE with fewer violations? Name its [file] AND copy
  the sentence that states it VERBATIM into "quote" (a REJECT without a verbatim quote is recorded, not counted).
- consequence: if the reading is wrong, what propagates, and is any of it irreversible?
Return JSON:
{{"constraint": {{"verdict": "NOT_REJECT|REJECT|NO_DATA", "transformation": "...", "file": "... or null", "quote": "verbatim sentence that shows the violation, or null", "reason": "..."}},
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

def gather_values(model, ev, meaning, units, searches, log, run_id, cid, tag, expected_unit=None, role="other", field=""):
    """Per-variable: retrieve by the model's search phrases, ask for every reported value, verify each
       (number in file, unit string, dimensions, role)."""
    ctx = ev.retrieve(" ".join([meaning] + list(searches or [])), k=10, max_chars=5000)
    if not ctx:
        return [], []
    got = ask(model, SYSTEM, P_VALUES.format(meaning=meaning, units=units or "", ctx=ctx, role=role or "other", field=field or "unspecified"))
    ok, bad = [], []
    for v in got.get("values", []) or []:
        fn, val = (str(v.get("file") or "")).strip("[] "), v.get("value")
        num = parse_number(val)
        by = re.match(r"\s*(-?\d+(?:\.\d+)?)\s*([a-zA-Z]*)\s*(?:by|×|x)\s*(-?\d+(?:\.\d+)?)\s*([a-zA-Z]*)\s*$", str(val or ""))
        if by and expected_unit and ("²" in expected_unit or "square" in expected_unit.lower() or expected_unit.lower() in ("m2", "ft2", "in2")):
            # a dimension pair reported where an area is wanted: the area is the product; both factors must be in the file
            a_, b_ = float(by.group(1)), float(by.group(3))
            if ev.contains_number(by.group(1), fn) and ev.contains_number(by.group(3), fn):
                u = (by.group(4) or by.group(2) or "").lower()
                num = a_ * b_; val = f"{num:.6g} {u}²"
                v = dict(v, reduced_from=by.group(0).strip(), process=(v.get("process") or "reported") + f"; area as length × width from {by.group(0).strip()} (factors kept on record)")
        if num is None:
            bad.append({"what": tag, "why": "no number", "raw": v}); continue
        if ev.group_of(fn) is None:
            bad.append({"what": tag, "why": f"file '{fn}' not in evidence", "raw": v}); continue
        if not v.get("reduced_from") and not ev.contains_number(val, fn):
            bad.append({"what": tag, "why": f"{val} not found in {fn}", "raw": v}); continue
        if expected_unit is not None and not units_compatible(expected_unit, str(val)):
            bad.append({"what": tag, "why": f"unit mismatch: wanted '{expected_unit or 'unitless'}', got '{unit_of(str(val)) or 'none'}' in {val}", "raw": v}); continue
        if expected_unit and not dims_compatible(expected_unit, str(val)):
            bad.append({"what": tag, "why": f"dimension mismatch: '{expected_unit}' vs '{unit_of(str(val))}' — not the same kind of quantity", "raw": v}); continue
        vrole = str(v.get("role") or "other").lower()
        if role and role != "other" and vrole in ROLES and vrole != "other" and vrole != role:
            bad.append({"what": tag, "why": f"role mismatch: wanted {role}, passage's quantity is {vrole} (a shared name is not a shared quantity)", "raw": v}); continue
        b, bk = parse_band(str(val), num)
        ok.append({"value": num, "band": b, "band_kind": bk, "as_written": val, "file": fn, "group": ev.group_of(fn),
                   "provisional": ev.is_provisional(fn), "role": vrole,
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

def shared_among(routes, ev):
    """What agreeing routes have in common: shared cited inputs and shared source roots (named, for the verdict)."""
    out, seen = [], set()
    for i in range(len(routes)):
        for j in range(i + 1, len(routes)):
            a, b = routes[i], routes[j]
            for x in sorted(set(a.get("inputs") or []) & set(b.get("inputs") or [])):
                if ("input", x) not in seen:
                    seen.add(("input", x)); out.append(f"input {x}")
            ra = set(ev.root_of(g.split("/")[0]) for g in a["groups"]); rb = set(ev.root_of(g.split("/")[0]) for g in b["groups"])
            for g in sorted(ra & rb):
                if ("root", g) not in seen:
                    seen.add(("root", g)); out.append(f"source root {g}")
    return out

def find_routes(model, ev, cid, reading, obs, claimed, precision_needed, log, run_id):
    """Numeric observable: the script enumerates every route the evidence supports."""
    rel = ask(model, SYSTEM, P_RELATIONS.format(reading=reading, obs=obs, claimed=claimed))
    discarded, routes, all_pools = [], [], {}
    # direct lookups
    card = rel.get("card") or {}
    cu = str(card.get("units") or "").lower()
    if re.search(r"\b(height|length|side|perimeter|diameter|radius|width|depth|distance)\b", obs.lower()) and re.search(r"²|³|square|cubic|m2|m3", cu):
        discarded.append({"what": obs, "why": f"quantity card declared '{cu}' for a length-named observable; card units ignored, the reading's own unit '{unit_of(claimed) or 'none'}' used", "raw": card})
        card["units"] = unit_of(claimed) or ""
    direct, bad = gather_values(model, ev, obs, card.get("units") or "", rel.get("direct_search") or [obs], log, run_id, cid, f"{obs} (direct)",
                                expected_unit=unit_of(claimed), role=str(card.get("role") or "other").lower(), field=card.get("field") or "")
    discarded += bad
    for d in direct:
        routes.append({"type": "lookup", "value": d["value"], "band": d["band"], "band_kind": d["band_kind"], "groups": [d["group"]],
                       "inputs": [f"{d['file']}:{d['value']:.6g}"], "provisional": d.get("provisional", False), "kind": d.get("process") or "reported",
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
            vals, bad = gather_values(model, ev, spec.get("meaning") or name, spec.get("units"), spec.get("search"), log, run_id, cid, f"{obs}: {name}",
                                      expected_unit=spec.get("units") or None, role=str(spec.get("role") or "other").lower(), field=spec.get("field") or "")
            discarded += bad
            if not vals:
                discarded.append({"what": f"{obs}: {name}", "why": f"no evidence value for variable '{name}' in relation {expr}", "raw": None})
                pools = None; break
            pools[name] = vals; all_pools.setdefault(name, []).extend(vals)
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
            _, reduction = reduce_expr(expr)
            if reduction:
                want = str(r.get("result_units") or card.get("units") or "").strip().lower()
                declared_dimless = want in ("", "ratio", "unitless", "dimensionless", "1", "none", "-")
                reduction["checks_against_declared_units"] = ("yes" if (reduction["net_dimension"] == "dimensionless") == declared_dimless
                                                             else f"NO: expression carries {reduction['net_dimension']}, result declared '{want or 'unitless'}'")
                proc += f"; reduced by convention: {'; '.join(reduction['cancelled'])} -> net {reduction['net_dimension']} (kept on record)"
            if sensitive:
                routes.append({"type": "computation", "value": result, "band": abs(result) * relb, "band_kind": "propagated (quadrature)",
                               "relation": expr, "groups": groups, "inputs": [f"{v['file']}:{v['value']:.6g}" for v in combo],
                               "provisional": any(v.get("provisional") for v in combo), "kind": "calculation", "process": proc,
                               **({"reduction": reduction} if reduction else {})})
            else:
                routes.append({"type": "definition", "value": result, "band": abs(result) * 1e-6, "band_kind": "exact (definition)",
                               "relation": expr, "groups": ["definition:" + expr], "process": "definition: " + expr + " (result does not depend on the cited inputs)"})
    # the inverse turn (rule 7 of the method: four quarter turns return every corner): take the reading's own value
    # and all-but-one cited input, solve for the remaining variable, and compare with that variable's cited values.
    turns = []
    cv0 = parse_number(claimed)
    for r in (rel.get("relations") or [])[:4]:
        expr, vars_ = r.get("relation") or "", r.get("variables") or {}
        names = [n for n in list(vars_)[:4] if n.lower() not in _CONST]
        pools_t = {n: [v for v in all_pools.get(n, [])] for n in names}
        if cv0 is None or any(not pools_t[n] for n in names):
            continue
        for target in names:
            others = [n for n in names if n != target]
            base = {n: pools_t[n][0]["value"] for n in others}
            cited = pools_t[target]
            def f(x):
                return evaluate(expr, base | {target: x}) - cv0
            lo, hi = cited[0]["value"] * 0.05, cited[0]["value"] * 20 if cited[0]["value"] > 0 else 1.0
            try:
                flo, fhi = f(lo), f(hi)
                if flo * fhi > 0:
                    turns.append({"variable": target, "status": "no_solution_in_range", "note": f"inverting {expr} for {target} found no crossing"}); continue
                for _ in range(80):
                    mid = 0.5 * (lo + hi)
                    if f(lo) * f(mid) <= 0: hi = mid
                    else: lo = mid
                implied = 0.5 * (lo + hi)
            except Exception as ex:
                turns.append({"variable": target, "status": "error", "note": str(ex)[:80]}); continue
            for cv_ in cited:
                ok = abs(implied - cv_["value"]) <= 2 * (cv_["band"] + abs(implied) * 0.002)
                turns.append({"variable": target, "status": "returns" if ok else "does_not_return", "implied": implied,
                              "cited": cv_["value"], "file": cv_["file"],
                              "note": f"from the reading's {cv0:.6g} and {', '.join(f'{n}={base[n]:.6g}' for n in others)}, {expr} implies {target}={implied:.6g}; {cv_['file']} gives {cv_['value']:.6g}"})
    # calculator-derived routes: values this engine has previously STABILIZED or LOCKED (from process memory)
    for prior in process_memory.settled_values(obs, reading):
        routes.append({"type": "calculator", "value": prior["value"], "band": prior["band"], "band_kind": "prior run (agreed band)",
                       "groups": [f"calculator:{prior['run']}"], "inputs": [f"calculator:{prior['run']}:{prior['value']:.6g}"],
                       "provisional": True, "kind": "calculator",
                       "process": f"calculator: {prior['verdict']} in run {prior['run']} for '{prior['text'][:80]}'"})
    # (b) a lookup from the reference group, or whose process is "definition", is definition-class
    for r in routes:
        if r["type"] == "lookup" and (any(g == "reference" for g in r["groups"]) or str(r.get("kind", "")).lower() == "definition"):
            r["type"] = "definition"; r["groups"] = ["definition:" + r.get("file", "reference")]
    # at most one definition route per observable
    defs = [r for r in routes if r["type"] == "definition"]
    # (a) the engine's own prior verdicts are cross-checks, never routes toward standing or locking
    calc = [r for r in routes if r["type"] == "calculator"]
    routes = [r for r in routes if r["type"] not in ("definition", "calculator")] + defs[:1]
    # compare each route with the reading's value at 2σ of the combined band
    cv = parse_number(claimed); cb, cbk = parse_band(claimed, cv)
    # the truth of rounding: a value written without its own tolerance, inside a reading that states one
    # ("… 921.2 m … to 0.05 %"), carries the reading's stated tolerance, not half its last digit
    if cbk == "half last digit" and re.search(r"±|\bto\s+\d+(?:\.\d+)?\s*%", _norm(reading)):
        rb, rbk = parse_band(reading, cv)
        if rbk.startswith("stated") and rb > cb:
            cb, cbk = rb, rbk + " (inherited from the reading's stated tolerance)"
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
    for r in calc:
        diff = r["value"] - cv
        r["two_sigma"] = 2 * (r["band"] + cb); r["within_2sigma"] = abs(diff) <= r["two_sigma"]; r["cross_check_only"] = True
    # relations that disagree with each other: if routes from relation A agree with the reading and routes from
    # relation B, over inputs A also used, disagree, then A and B cannot both be right — the disagreement is a
    # relation conflict, not a measurement against the reading. It is recorded and troubleshot, not counted as
    # a rejection; the lookups (values reported directly) still reject on their own.
    relation_conflicts = []
    agreeing_rel = {r["relation"] for r in routes if r["type"] == "computation" and r["within_2sigma"]}
    if agreeing_rel:
        agree_inputs = set(i for r in routes if r["type"] == "computation" and r["within_2sigma"] for i in r.get("inputs") or [])
        for r in routes:
            if r["type"] == "computation" and not r["within_2sigma"] and r["relation"] not in agreeing_rel and (set(r.get("inputs") or []) & agree_inputs):
                r["relation_conflict"] = True
                relation_conflicts.append(f"'{r['relation']}' gives {r['value']:.6g} while {', '.join(sorted(agreeing_rel))[:80]} gives the reading's value from shared inputs")
    counted = [r for r in routes if not r.get("relation_conflict")]
    ind = independent_set(counted)
    strict = independent_set(counted, ev, strict=True)
    agree = [r for r in ind if r["within_2sigma"]]; disagree = [r for r in ind if not r["within_2sigma"]]
    strict_agree = [r for r in strict if r["within_2sigma"]]
    report = {"observable": obs, "claimed": claimed, "claimed_value": cv, "claimed_band": cb, "claimed_band_kind": cbk,
              "relation_conflicts": sorted(set(relation_conflicts)),
              "precision_needed": precision_needed, "all_routes": routes, "independent": ind,
              "independent_routes": len(ind), "agree": len(agree), "disagree": len(disagree),
              "strict_agree": len(strict_agree),
              "cyclical": len([r for r in agree if r.get("type") != "definition"]) > len(strict_agree),
              "shared": shared_among([r for r in agree if r.get("type") != "definition"], ev),
              "fine_agree": sum(1 for r in agree if not r.get("coarse")), "disagreeing": disagree, "discarded": discarded,
              "turns": turns, "card": rel.get("card") or {},
              "calculator_cross_checks": [{"value": r["value"], "agrees": r["within_2sigma"], "process": r["process"]} for r in calc],
              "kinds": sorted(set(r.get("kind") or r["type"] for r in ind)),
              "provisional_only": bool(agree) and all(r.get("provisional") for r in agree)}
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
              "strict_agree": len(strict_agree), "cyclical": len(agree) > len(strict_agree), "shared": shared_among(agree, ev),
              "partial_support": [r["covers"] for r in agree if str(r["covers"]).lower().strip() != "whole"],
              "disagreeing": disagree, "discarded": discarded, "text": True}
    log.write(run=run_id, claim=cid, pass_="ROUTE_STATE", observable="text", input=ctx, model_proposal=got, report=report)
    return report

def calibrate(model, ev, cid, reading, log, run_id):
    """Standing pass: replace ambiguous components with known ones, where the evidence supplies the reference.
       The model proposes components and references; the script verifies every quote and substitutes ONLY the
       verified ones, term by term, so the calibrated reading is rebuilt by rule from the reading as stated.
       Components with no reference in the evidence are empty cells (the measurement that would fix the word).
       Returns (calibrated_reading, record)."""
    ctx = ev.retrieve(reading)
    got = ask(model, SYSTEM, P_CALIBRATE.format(reading=reading, ctx=ctx))
    comps, cal, empty = [], reading, []
    for c in (got.get("components") or [])[:6]:
        if not isinstance(c, dict) or not c.get("term"):
            continue
        term, ref, rep = str(c["term"]), c.get("reference") or {}, c.get("replacement")
        status = "no reference in evidence"
        if ref and ref.get("file") and ref.get("quote"):
            fn = str(ref["file"]).strip("[] ")
            if ev.contains_quote(ref["quote"], fn):
                if rep and term.lower() in cal.lower():
                    i = cal.lower().find(term.lower()); cal = cal[:i] + str(rep) + cal[i + len(term):]
                    status = f"replaced (reference verified in {fn})"
                elif rep:
                    status = f"reference verified in {fn} but the term is not in the reading as stated; not replaced"
                else:
                    status = f"reference verified in {fn} but no replacement wording given; not replaced"
            else:
                status = "reference quote not verbatim in the evidence as cited; not replaced (recorded)"
        if status.startswith("no reference") or "not verbatim" in status:
            empty.append({"term": term, "needs": c.get("needs"), "next_route": f"a measurement of {c.get('needs') or term} in a cited source"})
        comps.append({"term": term, "kind": c.get("kind"), "needs": c.get("needs"), "reference": ref or None, "replacement": rep, "status": status})
    obs_added = [o for o in (got.get("observables_added") or []) if isinstance(o, dict) and o.get("name") and parse_number(o.get("claimed_value")) is not None][:2]
    rec = {"as_stated": reading, "calibrated": cal, "changed": cal != reading, "components": comps, "empty_cells": empty,
           "observables_added": obs_added, "model_calibrated_reading": got.get("calibrated_reading")}
    log.write(run=run_id, claim=cid, pass_="CALIBRATION_STATE", input=ctx[:3000], model_proposal=got, output=rec)
    return cal, rec

def check_neighbours(model, ev, cid, reading, anchor, log, run_id):
    """Rule 6: the three edges from the corner. Each neighbour is looked up and compared; the script verifies
       the citation and, when both sides are numeric, does the comparison itself."""
    out = []
    for nb in (anchor.get("neighbours_to_check") or [])[:3]:
        if isinstance(nb, dict):
            datum, corner_, units_ = nb.get("datum") or "", nb.get("corner") or "", nb.get("units") or ""
        else:
            datum, corner_, units_ = str(nb), "", ""
        if not datum or len(datum) < 3:
            out.append({"neighbour": corner_ or str(nb), "status": "unchecked", "note": "neighbour named as a delimiter only, no datum to look up"}); continue
        label = f"{datum}" + (f" (corner {corner_})" if corner_ else "")
        ctx = ev.retrieve(f"{datum} {reading}", k=8, max_chars=4000)
        got = ask(model, SYSTEM, P_NEIGHBOUR.format(reading=reading, corner=anchor.get("corner"), cell=anchor.get("cell"),
                                                   held=anchor.get("held_axis"), neighbour=label, units=units_ or "unknown", ctx=ctx)) if ctx else {}
        rep = got.get("reported") or {}
        fn, rv = (str(rep.get("file") or "")).strip("[] "), rep.get("value_or_quote")
        status, note = "unchecked", got.get("reason", "")
        if rv and ev.group_of(fn) is not None:
            iv, nv = parse_number(got.get("implied")), parse_number(rv)
            if iv is not None and not single_number(str(got.get("implied"))):
                status, note = "unchecked", f"implied value is not a single number ('{str(got.get('implied'))[:60]}…'); not compared"
            elif iv is not None and nv is not None and ev.contains_number(rv, fn):
                iu, ru = unit_of(str(got.get("implied"))), unit_of(str(rv))
                same_kind = (iu == ru) or (not iu and not ru) or (units_ and units_compatible(units_, str(rv)) and units_compatible(units_, str(got.get("implied"))))
                if not same_kind or not dims_compatible(iu or units_ or "", str(rv)):
                    status, note = "unchecked", f"reported value is a different kind of quantity ('{ru or 'unitless'}' vs implied '{iu or 'unitless'}'); not compared"
                else:
                    ib, _ = parse_band(str(got.get("implied")), iv); nbnd, _ = parse_band(str(rv), nv)
                    status = "lined_up" if abs(iv - nv) <= 2 * (ib + nbnd) else "contradicts"
                    note = f"{datum}: implied {iv:.6g} vs reported {nv:.6g} in {fn}"
            elif ev.contains_quote(str(rv), fn):
                status = {"yes": "lined_up", "no": "contradicts"}.get(str(got.get("lines_up", "")).lower(), "unchecked")
                note = f"{fn}: \"{str(rv)[:120]}\" — {got.get('reason', '')}"
            else:
                note = f"reported value/quote not found in {fn}: {str(rv)[:80]}"
        out.append({"neighbour": label, "status": status, "note": note, "implied": got.get("implied")})
    log.write(run=run_id, claim=cid, pass_="NEIGHBOUR_STATE", neighbours=out)
    return out

def check_downwind(model, ev, cid, reading, log, run_id):
    """Rule 9 to its consequences: verified mismatches reject; unverified ones are recorded."""
    ctx = ev.retrieve(reading + " observable reality falls flows", k=10, max_chars=5000)
    got = ask(model, SYSTEM, P_DOWNWIND.format(reading=reading, ctx=ctx)) if ctx else {}
    out = []
    for c in (got.get("consequences") or [])[:3]:
        seen = c.get("seen") or {}
        fn, q = (str(seen.get("file") or "")).strip("[] "), seen.get("quote") or ""
        verified = ev.group_of(fn) is not None and (ev.contains_quote(q, fn) or ev.contains_number(q, fn))
        cw = lambda t: set(w for w in WORD.findall((t or "").lower()) if len(w) >= 5)
        relevant = len(cw(c.get("if_true")) & cw(q)) >= 2 or len(cw(reading) & cw(q)) >= 3
        lu = str(c.get("lines_up", "unknown")).lower()
        status = ("verified_mismatch" if (lu == "no" and verified and relevant) else "weak_mismatch" if (lu == "no" and verified)
                  else "asserted_mismatch" if lu == "no"
                  else "lines_up" if (lu == "yes" and verified) else "asserted_ok" if lu == "yes" else "unknown")
        out.append({"if_true": c.get("if_true"), "status": status, "file": fn or None, "quote": q[:160], "reason": c.get("reason", "")})
    log.write(run=run_id, claim=cid, pass_="IMPLICATION_STATE", downwind=out)
    return out

def fit_account_ledger(rp):
    return (f"{rp['observable']}: HELD from the locked ledger — {rp['claimed_value']:.6g} ± {rp['claimed_band']:.3g} [{rp['claimed_band_kind']}]; "
            f"{len(rp['ledger_routes'])} route(s) locked it; re-checked against {len(rp['rechecked'])} value(s) now in the evidence, none conflict\n"
            + "\n".join(f"  · locked by: {r}" for r in rp["ledger_routes"][:4]))

def fit_account(reports):
    """The script's deterministic explanation of the fit, printed under every verdict."""
    L = []
    for rp in reports:
        if rp.get("from_ledger"):
            L.append(fit_account_ledger(rp)); continue
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
        for cc in rp.get("calculator_cross_checks") or []:
            L.append(f"  · cross-check only (not counted): the engine's own {cc['process'][:90]} → {cc['value']:.6g} {'agrees' if cc['agrees'] else 'DISAGREES'}")
        for d in rp["discarded"][:4]:
            L.append(f"  · discarded: {d['what']}: {d['why']}")
        for rc in rp.get("relation_conflicts") or []:
            L.append(f"  · relation conflict (recorded, not counted; troubleshoot the relation): {rc}")
    return "\n".join(L) if L else "no observable could be routed"

def bears_on(quote, reading, extra=""):
    cw = lambda t: set(w for w in WORD.findall((t or "").lower()) if len(w) >= 5)
    return len(cw(reading) & cw(quote)) >= 2 or len(cw(extra) & cw(quote)) >= 2

def synthesis_by_rule(reports, judge, ev, neighbours=None, downwind=None, reading=""):
    outcome, lock, reason = "NO_DATA", 0, []
    neighbours = neighbours or []; downwind = downwind or []
    dw_reject = [d for d in downwind if d["status"] == "verified_mismatch"]
    dw_flag = [d for d in downwind if d["status"] in ("asserted_mismatch", "weak_mismatch")]
    turn_fail = [t for r in reports for t in (r.get("turns") or []) if t.get("status") == "does_not_return"]
    turn_ok = [t for r in reports for t in (r.get("turns") or []) if t.get("status") == "returns"]
    provisional_only = any(r.get("provisional_only") for r in reports)
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
            if provisional_only and lock >= 3:
                lock = 2  # nothing locks on sources that are themselves unverified transcriptions
            if contra:
                outcome = "NO_DATA"; lock = min(lock, 1)
                reason = [f"neighbour contradicts: {n['neighbour']} ({n['note']})" for n in contra]
            elif turn_fail and not turn_ok:
                outcome = "NO_DATA"; lock = min(lock, 1)
                reason = [f"inverse turn does not return: {t['note']}" for t in turn_fail[:2]]
            else:
                reason = [f"{r['observable']}: {r['agree']} independent route(s) agree (strict {r.get('strict_agree', r['agree'])})" for r in reports]
    if dw_reject:
        outcome = "REJECT"; reason = [f"down-wind mismatch: if true, {d['if_true']} — but {d['file']}: \"{d['quote'][:100]}\"" for d in dw_reject]
    elif dw_flag and outcome == "NOT_REJECT":
        outcome = "NO_DATA"; reason = reason + [f"down-wind mismatch {'with a quote that does not bear on it' if d['status'] == 'weak_mismatch' else 'asserted without citation'}: {d['if_true']} ({d['reason']})" for d in dw_flag]
    cores = {"outcome": {"verdict": outcome, "reason": "; ".join(reason) or "no route reached any observable"}}
    for k in ("constraint", "alternative", "consequence"):
        c = dict(judge.get(k)) if isinstance(judge.get(k), dict) else {}
        v = c.get("verdict", "NO_DATA")
        if k == "alternative":
            fn = (str(c.get("file") or "")).strip("[] ")
            if v == "REJECT" and not ev.contains_quote(c.get("quote") or "", fn):
                c["recorded_not_counted"] = "REJECT without a verbatim quote from an evidence file"; v = "NOT_REJECT"
            elif v == "REJECT" and not bears_on(c.get("quote"), reading, c.get("alternative")):
                c["recorded_not_counted"] = "REJECT with a verbatim quote that does not bear on the reading"; v = "NOT_REJECT"
            elif v == "NO_DATA":
                c["note"] = "no competing explanation found in evidence"; v = "NOT_REJECT"
        elif k == "constraint" and v == "REJECT":
            fn = (str(c.get("file") or "")).strip("[] ")
            if not ev.contains_quote(c.get("quote") or "", fn):
                c["downgraded"] = "REJECT without a verbatim quote from an evidence file"; v = "NO_DATA"
            elif not bears_on(c.get("quote"), reading, c.get("transformation")):
                c["downgraded"] = "REJECT with a verbatim quote that does not bear on the reading (recorded, not counted)"; v = "NOT_REJECT"
        c["verdict"] = v; cores[k] = c
    if any(c["verdict"] == "REJECT" for c in cores.values()):
        synth = "REJECTED"
    elif any(c["verdict"] == "NO_DATA" for c in cores.values()):
        synth = "UNSTABLE"
    else:
        synth = "LOCKED" if lock >= 3 else "STABILIZED"
    # diagnosis: what kind of agreement this is
    if dw_reject:
        diag = "down-wind consequence contradicts observable reality or the evidence (the reasoning is wrong even where the number matched)"
    elif synth == "REJECTED":
        diag = "an independent route disagrees"
    elif contra:
        diag = "contradicted by a neighbour (confidently-wrong candidate until resolved)"
    elif turn_fail and not turn_ok:
        diag = "the inverse turn does not return to the cited inputs (the relation or an input is wrong)"
    elif provisional_only and synth in ("STABILIZED", "LOCKED"):
        diag = "agreement rests only on provisional (unverified-transcription) sources"
    elif reports and all(r.get("from_ledger") for r in reports) and synth in ("STABILIZED", "LOCKED"):
        diag = "held from the locked ledger; re-checked against neighbours, down-wind and the evidence now on file, no conflict"
    elif any(r.get("cyclical") for r in reports):
        sh = sorted(set(x for r in reports for x in (r.get("shared") or [])))
        diag = ("agreeing routes share " + (", ".join(sh) if sh else "ancestry or inputs") +
                "; shared routes counted once (partly cyclical: the agreement is weaker than the route count suggests)")
    elif synth in ("STABILIZED", "LOCKED") and neighbours and lined < len(neighbours):
        diag = f"incomplete: {lined} of {len(neighbours)} neighbours lined up"
    elif synth in ("STABILIZED", "LOCKED"):
        diag = "independent agreement" + (", neighbours lined up" if neighbours else ", neighbours not checked")
    else:
        diag = "insufficient independent routes"
    cores["outcome"]["diagnosis"] = diag
    cores["outcome"]["kinds_of_route"] = sorted(set(k for r in reports for k in (r.get("kinds") or [])))
    cores["outcome"]["turns"] = {"return": len(turn_ok), "do_not_return": len(turn_fail)}
    return synth, cores, lock

def sections(doc):
    parts = re.split(r"(?m)^(#{1,3} .+)$", doc)
    out = [("(preamble)", parts[0])] if parts[0].strip() else []
    for i in range(1, len(parts), 2):
        raw = parts[i]
        level = len(raw) - len(raw.lstrip("#"))
        heading = raw.lstrip("# ").strip()
        out.append((("(title) " if level == 1 else "") + heading, parts[i + 1]))
    return [(h, t) for h, t in out if t.strip()]

# ----------------------------------------------------------------------------- locked ledger

class Ledger:
    """Priority flags: values this engine LOCKED, with the routes that locked them (logs/locked.json).
       A held value is not recomputed on the next run; it is re-checked against what is near it, and any
       conflict reopens it (the lock is demoted, the conflict recorded, the full process runs again)."""
    def __init__(self, path):
        self.path = path
        self.items = json.load(open(path, encoding="utf-8")) if os.path.exists(path) else []

    def _save(self):
        json.dump(self.items, open(self.path, "w", encoding="utf-8"), ensure_ascii=False, indent=1)

    def get(self, observable, reading):
        for it in self.items:
            if it.get("open"):
                continue
            # the observable must match in order, not as a bag of words: 'height/perimeter' is the inverse of
            # 'perimeter/height' (the same room flipped inside out) and must never inherit its lock
            if process_memory.norm(observable) == process_memory.norm(it["observable"]) and process_memory.similar(reading, it["reading"]) >= 0.5:
                return it
        return None

    def lock(self, observable, reading, value, band, run_id, routes, neighbours, downwind):
        self.items = [it for it in self.items if not (it["observable"] == observable and it["reading"] == reading)]
        self.items.append({"observable": observable, "reading": reading, "value": value, "band": band, "run": run_id,
                           "locked_at": datetime.datetime.now().astimezone().isoformat(timespec="minutes"),
                           "routes": routes, "neighbours": [n.get("status") for n in (neighbours or [])],
                           "downwind": [d.get("status") for d in (downwind or [])], "open": False, "reopened": []})
        self._save()

    def reopen(self, observable, reading, conflicts, run_id):
        for it in self.items:
            if process_memory.norm(observable) == process_memory.norm(it["observable"]) and process_memory.similar(reading, it["reading"]) >= 0.5:
                it["open"] = True; it["reopened"].append({"run": run_id, "conflicts": conflicts,
                                                        "at": datetime.datetime.now().astimezone().isoformat(timespec="minutes")})
        self._save()

    def as_report(self, held, o, rechecked):
        cv = held["value"]; cb = held["band"]
        return {"observable": o["name"], "claimed": o.get("claimed_value"), "claimed_value": cv, "claimed_band": cb,
                "claimed_band_kind": f"held from the locked ledger (run {held['run']}, {held['locked_at']})", "precision_needed": o.get("precision_needed"),
                "all_routes": [], "independent": [], "independent_routes": len(held["routes"]), "agree": len(held["routes"]), "disagree": 0,
                "strict_agree": len(held["routes"]), "cyclical": False, "shared": [], "fine_agree": len(held["routes"]), "disagreeing": [],
                "discarded": [], "turns": [], "card": {}, "calculator_cross_checks": [], "kinds": ["ledger"], "from_ledger": True,
                "rechecked": [{"value": d["value"], "file": d["file"]} for d in rechecked],
                "ledger_routes": held["routes"]}

# ----------------------------------------------------------------------------- run

def run(path, model, question, max_claims, out_dir, evidence_dir, research_on=False):
    doc = open(path, encoding="utf-8").read()
    ev = Evidence(evidence_dir)
    ledger = Ledger(os.path.join(out_dir, "locked.json"))
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
        if heading == "(preamble)" or heading.startswith("(title)") or re.search(r"\b(moral|preface|abstract|acknowledg)", heading.lower()):
            log.write(run=run_id, pass_="ENTRY_STATE", skipped_section=heading, why="not a claims section"); continue
        per = max(1, round(max_claims * len(text) / total))
        got = ask(model, SYSTEM, P_EXTRACT.format(heading=heading, doc=text[:12000], question=question or "", prefix=f"s{i+1}c", n=per), temperature=0.0)
        for c in got.get("claims", []) or []:
            c["section"] = heading
            if not c.get("readings"):
                c["readings"] = [{"reading": c.get("text", ""), "observables": c.get("observables") or []}]
            claims.append(c)
    claims = claims[:max_claims]
    log.write(run=run_id, pass_="RECOGNITION_STATE", claims=claims, elapsed=round(time.time() - t0, 1))
    print(f"[{run_id}] {len(claims)} claims from {len(secs)} sections; evidence groups: {', '.join(ev.groups) or 'NONE'}")

    def evaluate_reading(c, rid, reading, observables, depth=0, parent=None):
        t = time.time(); reports = []
        as_stated = reading
        reading, calib = calibrate(model, ev, rid, reading, log, run_id)
        if calib["changed"]:
            print(f"    calibrated → {reading}")
        observables = list(observables or []) + calib["observables_added"]
        numeric = [o for o in (observables or [])[:3]
                   if o.get("name") and str(o.get("claimed_value", "none")).lower() != "none" and parse_number(o.get("claimed_value")) is not None]
        if research_on and depth == 0:
            for o in numeric[:2]:
                try:
                    added = research.search_and_store(f"{o['name']} {reading}"[:120], os.path.join(HERE, "evidence"), max_pages=2)
                    log.write(run=run_id, claim=rid, pass_="RESEARCH_STATE", query=o["name"], added=added)
                    if added:
                        ev.__init__(os.path.join(HERE, "evidence"))
                except Exception as ex:
                    log.write(run=run_id, claim=rid, pass_="RESEARCH_STATE", query=o["name"], error=str(ex)[:300])
        for o in numeric:
            # priority: a value this engine already LOCKED is not recomputed; it is re-checked against what is near it
            # (neighbours, down-wind, any value now in the evidence that disagrees). A conflict reopens the lock.
            held = ledger.get(o["name"], reading)
            if held:
                direct, _ = gather_values(model, ev, o["name"], unit_of(o["claimed_value"]), [o["name"]], log, run_id, rid, f"{o['name']} (ledger re-check)",
                                          expected_unit=unit_of(o["claimed_value"]))
                conflict = [d for d in direct if abs(d["value"] - held["value"]) > 2 * (d["band"] + held["band"])]
                if not conflict:
                    reports.append(ledger.as_report(held, o, direct)); print(f"    ledger: {o['name']} held LOCKED from run {held['run']}; {len(direct)} value(s) re-checked, none conflict")
                    log.write(run=run_id, claim=rid, pass_="LEDGER_STATE", observable=o["name"], held=held, rechecked=len(direct), reopened=False)
                    continue
                log.write(run=run_id, claim=rid, pass_="LEDGER_STATE", observable=o["name"], held=held, reopened=True,
                          conflict=[{"value": d["value"], "file": d["file"]} for d in conflict])
                ledger.reopen(o["name"], reading, [f"{d['file']}:{d['value']:.6g}" for d in conflict], run_id)
                print(f"    ledger: {o['name']} REOPENED — new value(s) conflict with the lock: " + ", ".join(f"{d['value']:g} [{d['file']}]" for d in conflict))
            reports.append(find_routes(model, ev, rid, reading, o["name"], o["claimed_value"], o.get("precision_needed"), log, run_id))
        if not numeric:
            reports.append(find_text_routes(model, ev, rid, reading, log, run_id))
        fit = fit_account(reports)
        brief = [{"observable": rp["observable"], "claimed": rp.get("claimed"), "independent_routes": rp["independent_routes"],
                  "agree": rp["agree"], "disagree": rp["disagree"],
                  "routes": [{k: v for k, v in r.items() if k in ("type", "value", "band", "within_2sigma", "coarse", "stance", "covers", "process")} for r in rp["independent"]]}
                 for rp in reports]
        anchor = c.get("anchor") or {}
        nbs = check_neighbours(model, ev, rid, reading, anchor, log, run_id)
        dw = check_downwind(model, ev, rid, reading, log, run_id)
        ctx = ev.retrieve(reading)
        judge = ask(model, SYSTEM, P_JUDGE.format(cid=rid, reading=reading, routes=json.dumps(brief, ensure_ascii=False), ctx=ctx))
        synth, cores, lock = synthesis_by_rule(reports, judge, ev, nbs, dw, reading)
        settled = [{"observable": rp["observable"], "value": rp["claimed_value"], "band": rp["claimed_band"]}
                   for rp in reports if not rp.get("text") and synth in ("STABILIZED", "LOCKED") and rp["claimed_value"] is not None]
        if synth == "LOCKED":
            for rp in reports:
                if not rp.get("text") and rp["claimed_value"] is not None and not rp.get("from_ledger"):
                    ledger.lock(rp["observable"], reading, rp["claimed_value"], rp["claimed_band"], run_id,
                                [r["process"] for r in rp["independent"]], nbs, dw)
        e = {"quad_core": cores, "lock_level": lock, "synthesis": synth, "fit_account": fit, "neighbours": nbs, "downwind": dw,
             "calibration": calib, "as_stated": as_stated,
             "turns": [t for rp in reports for t in (rp.get("turns") or [])], "settled": settled,
             "implication": judge.get("implication"), "ethics": judge.get("ethics"), "parent": parent, "depth": depth}
        log.write(run=run_id, claim=rid, pass_="EVALUATION_STATE", output=e, elapsed=round(time.time() - t, 1))
        if (judge.get("ethics") or {}).get("decision") == "HALT":
            log.write(run=run_id, claim=rid, pass_="FINAL_STATE", state="HALT")
            print("      → HALT"); return (rid, reading, "HALT", e, {}, reports, fit)
        # troubleshoot: the numbers matched (some route agreed) and it still failed
        ts = None
        agreed_somewhere = any(rp["agree"] for rp in reports)
        if synth in ("REJECTED", "UNSTABLE") and agreed_somewhere and (
                e["quad_core"]["outcome"]["verdict"] != "NOT_REJECT" or synth == "REJECTED"):
            ts = ask(model, SYSTEM, P_TROUBLESHOOT.format(reading=reading, corner=anchor.get("corner"), cell=anchor.get("cell"), held=anchor.get("held_axis"),
                                                         synth=synth, fit=fit, neighbours=json.dumps(nbs, ensure_ascii=False)[:1500],
                                                         downwind=json.dumps(dw, ensure_ascii=False)[:1500], turns=json.dumps(e["turns"], ensure_ascii=False)[:1200]))
            log.write(run=run_id, claim=rid, pass_="TROUBLESHOOT_STATE", output=ts)
        prev = process_memory.previous_on(reading, mem)
        prev_text = "none recorded" if not prev else (f"{prev['current']} in run {prev['history'][-1]['run']}: " +
                    (prev['history'][-1].get('reason') or prev['history'][-1].get('why') or '(no reason logged)'))
        r = ask(model, SYSTEM, P_REVISE.format(cid=rid, reading=reading, synth=synth, fit=fit, previous=prev_text))
        if ts:
            r["troubleshoot"] = ts
        if prev and prev["current"] != synth:
            r["changed_from"] = {"verdict": prev["current"], "run": prev["history"][-1]["run"],
                                 "reason": prev["history"][-1].get("reason") or prev["history"][-1].get("why")}
            log.write(run=run_id, claim=rid, pass_="REGRESSION_STATE", previous=r["changed_from"], now=synth, explanation=r.get("change_of_mind"))
        if synth in ("STABILIZED", "LOCKED") and not r.get("reduced_statement"):
            r["reduced_statement"] = reading
        log.write(run=run_id, claim=rid, pass_="REVISION_STATE", output=r)
        log.write(run=run_id, claim=rid, pass_="FINAL_STATE", synthesis=synth, output=r.get("final"))
        print(f"      → {synth} [{cores['outcome'].get('diagnosis', '')}]  (" + "; ".join(f"{rp['observable']}: {rp['agree']}✓ {rp['disagree']}✗ of {rp['independent_routes']}" for rp in reports) + ")")
        result = (rid, reading, synth, e, r, reports, fit)
        # the fold re-enters once: the corrected reading (from troubleshooting) or the folded question becomes a child reading
        child_q = (ts or {}).get("corrected_reading") or (r.get("folded_question") if synth == "REJECTED" else None)
        if depth == 0 and child_q:
            f = ask(model, SYSTEM, P_FOLD.format(question=child_q))
            if f.get("reading"):
                print(f"    folded → {f['reading']}")
                log.write(run=run_id, claim=rid, pass_="FOLD_STATE", child=f"{rid}f", question=child_q, reading=f["reading"])
                r["fold_child"] = evaluate_reading(c, f"{rid}f", f["reading"], f.get("observables") or [], depth=1, parent=rid)
        return result

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
            readings_out.append(evaluate_reading(c, rid, reading, rd.get("observables") or []))
        # inherited misses (rule 8): a disagreeing route every reading shows is the evidence's, not the claim's
        if len(readings_out) > 1:
            procs = [set(d["process"] for rp in reps for d in rp["disagreeing"]) for (_, _, s_, e_, r_, reps, _) in readings_out]
            common = set.intersection(*procs) if procs and all(procs) else set()
            if common:
                for i, (rid_, rd_, s_, e_, r_, reps, fit_) in enumerate(readings_out):
                    e_["inherited_misses"] = sorted(common)
                    if s_ == "REJECTED" and all(d["process"] in common for rp in reps for d in rp["disagreeing"]):
                        e_["synthesis"] = "UNSTABLE"; e_["quad_core"]["outcome"]["inherited"] = "the only disagreeing route(s) are shared by every reading: inherited, on record, not counted"
                        readings_out[i] = (rid_, rd_, "UNSTABLE", e_, r_, reps, fit_)
                log.write(run=run_id, claim=cid, pass_="INHERITED_STATE", inherited=sorted(common))
        results.append((c, readings_out))

    summary = render_summary(run_id, path, question, model, ev, results, time.time() - t0)
    sp = os.path.join(out_dir, f"run-{run_id}-summary.md")
    open(sp, "w", encoding="utf-8").write(summary)
    try:
        refl = ask(model, SYSTEM, P_REFLECT.format(summary=summary[:9000], memory=process_memory.digest(max_chars=5000)), temperature=0.4)
    except Exception as ex:
        refl = {"_error": str(ex)[:200]}
    log.write(run=run_id, pass_="REFLECTION_STATE", output=refl)
    rp_ = os.path.join(out_dir, f"run-{run_id}-reflection.md")
    with open(rp_, "w", encoding="utf-8") as fh:
        fh.write(f"# Reflection after run {run_id} (self-report, logged beside the trace)\n\n")
        for k, v in refl.items():
            fh.write(f"**{k}**: {json.dumps(v, ensure_ascii=False) if isinstance(v, dict) else v}\n\n")
    log.write(run=run_id, pass_="PROCESS_ARCHIVED", summary=sp, reflection=rp_, total_elapsed=round(time.time() - t0, 1))
    print(summary); print(f"log: {log.path}\nsummary: {sp}\nreflection: {rp_}")
    return run_id

def render_summary(run_id, path, question, model, ev, results, elapsed):
    counts = {}
    for c, rs in results:
        for _, _, s, *_ in rs:
            counts[s] = counts.get(s, 0) + 1
    L = [f"# Run {run_id}", f"run clock: {datetime.datetime.now().astimezone().strftime('%Y-%m-%d %H:%M %Z')}",
         f"claims: {os.path.basename(path)} · evidence groups: {', '.join(ev.groups) or 'NONE'} · "
         f"model: {model} · agreement: 2σ of combined bands · question: {question or '(none)'} · "
         f"{len(results)} claims, {sum(len(rs) for _, rs in results)} readings · {elapsed/60:.1f} min",
         "", "counts (by reading): " + ", ".join(f"{k} {v}" for k, v in sorted(counts.items())), "",
         "Every verdict carries the script's account of the fit (routes, processes, values against bands, discards) "
         "and the model's one-line why. A claim with two readings is reported as: fits if you mean this; does not if you mean that.", ""]
    for c, rs in results:
        L.append(f"## {c.get('id')} [{c.get('section')}] {c.get('text')}")
        a = c.get("anchor") or {}
        if a:
            nbs_ = [(n.get('datum') or '?') + (f" ({n.get('corner')})" if isinstance(n, dict) and n.get('corner') else '') if isinstance(n, dict) else str(n) for n in (a.get('neighbours_to_check') or [])]
            L.append(f"anchor: corner {a.get('corner')}, cell {a.get('cell')}, held {a.get('held_axis')}; neighbours: {', '.join(nbs_)}")
        for rid, reading, s, e, r, reports, fit in rs:
            tag = f"**{s}**"
            L.append(f"\n- {tag} — *{reading}*" if len(rs) > 1 else f"\n- {tag}")
            if len(rs) > 1:
                L.append(f"  (fits if you mean this → {s})" if s in ("STABILIZED", "LOCKED") else f"  (does not fit if you mean this → {s})")
            L.append(f"  diagnosis: {e.get('quad_core', {}).get('outcome', {}).get('diagnosis', '')}")
            cal = e.get("calibration") or {}
            if cal.get("components"):
                if cal.get("changed"):
                    L.append(f"  calibrated: *{cal['calibrated']}*  (as stated: \"{cal['as_stated']}\")")
                for cp in cal["components"]:
                    L.append(f"    · '{cp['term']}' ({cp.get('kind')}) needs {cp.get('needs')}: {cp['status']}"
                             + (f" → \"{cp['replacement']}\"" if cp['status'].startswith('replaced') else ""))
                for ec in cal.get("empty_cells") or []:
                    L.append(f"    · empty cell: '{ec['term']}' — {ec['next_route']}")
            for line in fit.splitlines():
                L.append("  " + line)
            for nb in e.get("neighbours") or []:
                L.append(f"  neighbour {nb['neighbour']}: {nb['status']} — {nb['note']}")
            for d in e.get("downwind") or []:
                L.append(f"  down-wind: if true, {d['if_true']} → {d['status']}" + (f" ({d['file']}: \"{d['quote'][:90]}\")" if d.get('file') else "") + f" — {d['reason']}")
            qc = e.get("quad_core", {})
            for k in ("constraint", "alternative", "consequence"):
                v = qc.get(k, {})
                note = v.get("recorded_not_counted") or v.get("downgraded") or v.get("note")
                L.append(f"  {k}: {v.get('verdict')} — {v.get('reason', '')}" + (f" [{note}]" if note else ""))
            oc = e.get("quad_core", {}).get("outcome", {})
            if oc.get("kinds_of_route"): L.append(f"  kinds of route: {', '.join(oc['kinds_of_route'])}; inverse turns: {oc.get('turns', {}).get('return', 0)} return, {oc.get('turns', {}).get('do_not_return', 0)} do not")
            for t in (e.get("turns") or [])[:3]:
                if t.get("status") in ("returns", "does_not_return"): L.append(f"  turn: {t['status']} — {t['note']}")
            if e.get("inherited_misses"): L.append(f"  inherited (on record, not counted): {'; '.join(e['inherited_misses'])[:200]}")
            if r.get("why"): L.append(f"  why: {r['why']}")
            ts = r.get("troubleshoot") or {}
            if ts:
                L.append(f"  troubleshoot: {ts.get('diagnosis')} — faulty component: {ts.get('faulty_component')} ({ts.get('why')})")
                L.append(f"    kept: {'; '.join(ts.get('kept') or [])}")
                for fl in ts.get("flips") or []:
                    L.append(f"    flip {fl.get('flip')}: \"{fl.get('reading')}\" → would line up: {fl.get('would_line_up')} ({fl.get('reason')})")
                L.append(f"    repair: {ts.get('repair')}")
            fc = r.get("fold_child")
            if fc:
                frid, freading, fs, fe, fr, freps, ffit = fc
                L.append(f"  ↳ folded child {frid}: **{fs}** — *{freading}*  [{fe.get('quad_core', {}).get('outcome', {}).get('diagnosis', '')}]")
                if fr.get("why"): L.append(f"      why: {fr['why']}")
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
    L.append("\n## Propagation: what each verdict rests on (if the given is correct, what follows is correct too — and what fell with its givens standing)")
    for c, rs in results:
        for rid, reading, s, e, r, reports, fit in rs:
            rests = sorted(set(i for rp in reports for rt in (rp.get("independent") or []) if rt.get("within_2sigma") for i in (rt.get("inputs") or [])))
            fell_on = sorted(set(i for rp in reports for rt in (rp.get("disagreeing") or []) for i in (rt.get("inputs") or [])))
            if not rests and not fell_on:
                continue
            if s in ("STABILIZED", "LOCKED"):
                L.append(f"- [{s}] {reading[:110]}\n    stands on: {', '.join(rests)[:300]}")
            elif s == "REJECTED" and fell_on:
                L.append(f"- [{s}] {reading[:110]}\n    fell against: {', '.join(fell_on)[:300]}" +
                         ("\n    the inputs it rests on also carry the standing readings above: the derivation or the statement is at fault, not the data" if set(fell_on) & set(x for c2, rs2 in results for *_, e2, r2, reps2, _ in rs2 for rp2 in reps2 for rt2 in (rp2.get("independent") or []) if rt2.get("within_2sigma") for x in (rt2.get("inputs") or [])) else ""))
            else:
                L.append(f"- [{s}] {reading[:110]}\n    routes reached: {', '.join(rests or fell_on)[:300]}")
    L.append("\n## Where the data lives (every file cited above; url and retrieval time where it came from the web)")
    cited = sorted(set(re.findall(r"[\w\-]+\.md", "\n".join(L))))
    for fn in cited:
        if fn in ev.meta:
            L.append(f"- {ev.where(fn)}")
    return "\n".join(L) + "\n"

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("source", help="the document under test (put it in claims/)")
    ap.add_argument("--model", default=os.environ.get("MODEL", "qwen2.5:14b"))
    ap.add_argument("--question", default="")
    ap.add_argument("--max-claims", type=int, default=10)
    ap.add_argument("--evidence", default=os.path.join(HERE, "evidence"))
    ap.add_argument("--out", default=os.path.join(HERE, "logs"))
    ap.add_argument("--research", action="store_true", help="search the web for each numeric observable and add what is found to evidence/ (with url and retrieval time) before the routes are sought")
    a = ap.parse_args()
    try:
        requests.get(f"{OLLAMA}/api/tags", timeout=5)
    except Exception:
        sys.exit(f"Ollama not reachable at {OLLAMA}. Start it: `ollama serve` (and `ollama pull {a.model}`).")
    run(a.source, a.model, a.question, a.max_claims, a.out, a.evidence, research_on=a.research)
