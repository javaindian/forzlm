#!/usr/bin/env python3
"""Analyze replay_with_retry101_rev2 full-run output vs the v1 baseline + real schema.

Inputs (relative to repo root):
  results/replay_retry_results.csv          - rev2 full-101 run
  results/replay_results.csv                - v1 one-shot baseline
  patch/patch_hintmap_v2_1.py               - HINT_MAP keys + DOMAIN_ABSENT_TABLES (v2.1)
  baseline/schema_catalog.json              - REAL schema {table: [columns]}

Outputs:
  console summary
  results/retry_identifier_frequency.csv    - attempt-2 identifier worklist for v2.2
  docs/retry101_analysis.md                 - full report
"""
import ast, csv, difflib, json, os, re, sys
from collections import Counter, defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# ------------------------------------------------------------------ real schema
REAL = json.load(open(os.path.join(ROOT, "baseline", "schema_catalog.json")))
TABLES = set(REAL)

# ------------------------------------------------------------------ patch knowledge
patch = open(os.path.join(ROOT, "patch", "patch_hintmap_v2_1.py"), encoding="utf-8").read()
m = re.search(r"A_ENTRIES = \[(.*?)\n\]", patch, re.S)
A_ENTRIES = ast.literal_eval("[" + m.group(1) + "]")
HINT_KEYS = {(tbl, col) for (tbl, col), _txt in A_ENTRIES}

mb = re.search(r"DOMAIN_ABSENT_TABLES:\s*set\s*=\s*\{(.*?)\n\}", patch, re.S)
DA_SET = set(re.findall(r'"([^"]+)"', mb.group(1)))

def hint_for(ident):
    if "." in ident:
        tbl, col = ident.split(".", 1)
        return ("hinted" if (tbl, col) in HINT_KEYS else "no-hint")
    return ("hinted" if (ident, None) in HINT_KEYS else "no-hint")

FAMILIES = [
    ("appraisal", ("Appraisal", "PerformanceParameter", "Performance")),
    ("fuel", ("Fuel",)),
    ("complaint", ("Complaint",)),
    ("library", ("Library", "Book")),
    ("sports", ("Sports",)),
    ("purchase", ("Purchase", "GRN")),
    ("inventory_txn", ("InventoryEntry", "Stock")),
    ("fixed_asset", ("FixedAsset", "Maintenance_Master", "MaintenanceRepair", "Asset")),
    ("item_misc", ("Furniture", "Computer", "Uniform", "Stationary", "Stationery",
                   "Textbook", "Notebook", "Size")),
    ("gps", ("VehicleTracking", "GPS")),
    ("staff_verif", ("StaffVerification",)),
]

def family_of(tbl):
    for fam, kws in FAMILIES:
        if any(k.lower() in tbl.lower() for k in kws):
            return fam
    return None

def classify(ident):
    if "." in ident:
        tbl, col = ident.split(".", 1)
        if tbl not in TABLES:
            return "TABLE_HALLUC"
        if col in REAL[tbl]:
            return "BOTH_REAL_VALIDATOR_MISMATCH"
        return "COL_HALLUC"
    return "TABLE_HALLUC" if ident not in TABLES else "TABLE_REAL_SOLO"

def suggest(ident):
    """Closest real schema target for a hallucinated identifier."""
    if "." in ident:
        tbl, col = ident.split(".", 1)
        if tbl in TABLES:
            cols = difflib.get_close_matches(col, REAL[tbl], n=3, cutoff=0.45)
            return tbl + "." + "/".join(cols) if cols else tbl + " (no similar col)"
        tmatch = difflib.get_close_matches(tbl, sorted(TABLES), n=2, cutoff=0.55)
        return "table? " + "/".join(tmatch) if tmatch else "table? none-close"
    tmatch = difflib.get_close_matches(ident, sorted(TABLES), n=3, cutoff=0.5)
    return "/".join(tmatch) if tmatch else "none-close"

def split_ids(field):
    field = (field or "").strip()
    return [x.strip() for x in field.split(";") if x.strip()] if field else []

# ------------------------------------------------------------------ load runs
rows = list(csv.DictReader(open(os.path.join(ROOT, "results", "replay_retry_results.csv"))))
v1 = {r["audit_id"]: r for r in csv.DictReader(open(os.path.join(ROOT, "results", "replay_results.csv")))}

for r in rows:
    r["u1"] = split_ids(r["unknown_tables_1"]) + split_ids(r["unknown_columns_1"])
    r["u2"] = split_ids(r["unknown_tables_2"]) + split_ids(r["unknown_columns_2"])
    r["rep"] = [x for x in r["u2"] if x in r["u1"]]
    r["fresh"] = [x for x in r["u2"] if x not in r["u1"]]

fb = [r for r in rows if r["final"] == "FAIL_BOTH"]
pr = [r for r in rows if r["final"] == "PASS_RETRY"]
rd = [r for r in rows if r["final"] == "REFUSED_DOMAIN"]
pf = [r for r in rows if r["final"] == "PASS_FIRST"]

L = []  # report lines
def say(s=""):
    print(s)
    L.append(s)

say("# retry-101 full-run analysis (rev2, patched pipeline)")
say("")
say("Run: 101 Q, gen1 p50 15.4s, gen2 p50 21.7s, total GPU ~3462s. Outcomes: "
    f"PASS_FIRST {len(pf)}, PASS_RETRY {len(pr)}, REFUSED_DOMAIN {len(rd)}, FAIL_BOTH {len(fb)}.")
say("")

# 1. transition matrix v1 -> new
say("## 1. Transition vs v1 baseline (92 FAIL / 9 PASS)")
tm = defaultdict(Counter)
for r in rows:
    tm[v1[r["audit_id"]]["verdict"]][r["final"]] += 1
say("")
say("| v1 | " + " | ".join(sorted({r["final"] for r in rows})) + " |")
say("|---|" + "---|" * len({r["final"] for r in rows}))
for vv in sorted(tm):
    row = tm[vv]
    say("| " + vv + " | " + " | ".join(str(row.get(k, 0)) for k in sorted({r["final"] for r in rows})) + " |")
say("")
drop = [r["audit_id"] for r in rows if v1[r["audit_id"]]["verdict"] == "PASS"
        and r["final"] in ("FAIL_BOTH",)]
say(f"v1-PASS now failing (nondeterminism watchlist): {drop or 'none'}")
say("")

# 2. hint-coverage sanity: computed hints vs n_hints column
mism = []
for r in rows:
    computed = sum(1 for x in r["u1"] if hint_for(x) == "hinted")
    if computed != int(r["n_hints"] or 0):
        mism.append((r["audit_id"], r["n_hints"], computed, r["u1"]))
say(f"## 2. HINT_KEYS parse check: n_hints matches computed hint count on "
    f"{len(rows) - len(mism)}/101 rows")
for a, b, c, u in mism:
    say(f"  - id={a}: csv n_hints={b} computed={c} u1={u}")
say("")

# 3. hint efficacy on attempt 1 -> 2
hinted_u1 = [(r, x) for r in fb for x in r["u1"] if hint_for(x) == "hinted"]
fixed = sum(1 for r, x in hinted_u1 if x not in r["u2"])
rep_h = [(r, x) for r, x in hinted_u1 if x in r["u2"]]
say(f"## 3. Hint efficacy on FAIL_BOTH (attempt-1 hinted identifiers: {len(hinted_u1)})")
say(f"- fixed by retry (absent in attempt-2): {fixed}  ({round(100*fixed/max(1,len(hinted_u1)))}%)")
say(f"- repeated despite hint:               {len(rep_h)}  ({round(100*len(rep_h)/max(1,len(hinted_u1)))}%)")
rep_freq = Counter(x for _, x in rep_h)
say("")
say("Top repeated-despite-hint:")
for ident, c in rep_freq.most_common(12):
    say(f"  {c:2d}x  {ident}")
say("")

# 4. attempt-2 identifier classification
u2_all = Counter(x for r in fb for x in r["u2"])
say(f"## 4. Attempt-2 unknowns across FAIL_BOTH: {sum(u2_all.values())} hits, "
    f"{len(u2_all)} distinct")
cls = Counter(classify(x) for x in u2_all)
say("by class: " + ", ".join(f"{k}={v}" for k, v in cls.most_common()))
repeat_n = sum(len(r["rep"]) for r in fb)
fresh_n = sum(len(r["fresh"]) for r in fb)
say(f"repeated-from-attempt-1: {repeat_n} hits | fresh (new hallucinations): {fresh_n} hits")
say("")

# 5. v2.2 worklist: u2 identifiers without a v2.1 hint
work = [(x, c) for x, c in u2_all.items() if hint_for(x) == "no-hint"]
work.sort(key=lambda t: -t[1])
say(f"## 5. v2.2 HINT worklist: {len(work)} distinct unhinted attempt-2 identifiers")
say("")
say("| ident | hits | class | schema verdict / closest real |")
say("|---|---|---|---|")
for x, c in work:
    cl = classify(x)
    extra = ""
    if cl == "TABLE_HALLUC":
        fam = family_of(x.split(".")[0] if "." in x else x)
        extra = f"DA-family:{fam}" if fam else ""
    say(f"| {x} | {c} | {cl} | {suggest(x)} {extra} |")
say("")

# 6. hints=0 rows
say("## 6. Retried with ZERO hint coverage (HINT_MAP gaps on attempt-1)")
for r in rows:
    if r["final"] in ("FAIL_BOTH", "PASS_RETRY") and int(r["n_hints"] or 0) == 0:
        say(f"- id={r['audit_id']} {r['final']}: u1={r['u1'] or ['(none flagged)']} "
            f"u2={r['u2'] or ['(none flagged)']}")
say("")

# 7. domain-absent slip-throughs
say("## 7. Domain-absent candidates not covered by v2.1 DOMAIN_ABSENT_TABLES")
da_miss = Counter()
for r in fb:
    for x in r["u2"]:
        tbl = x.split(".")[0]
        if tbl not in TABLES and tbl not in DA_SET and family_of(tbl):
            da_miss[tbl] += 1
for t, c in da_miss.most_common():
    say(f"  {c:2d}x  {t}  (family: {family_of(t)})")
if not da_miss:
    say("  none")
say("")

# 8. PASS_RETRY profile
say(f"## 8. PASS_RETRY profile ({len(pr)} questions - proof hints work when coverage is complete)")
for r in sorted(pr, key=lambda r: int(r["n_hints"] or 0)):
    say(f"- id={r['audit_id']} hints={r['n_hints']} u1={len(r['u1'])} "
        f"({round(float(r['gen1_s']))}+{round(float(r['gen2_s']))}s)")
say("")

# 9. validator mismatches
mm = [(r, x) for r in fb for x in r["u2"] if classify(x) == "BOTH_REAL_VALIDATOR_MISMATCH"]
say(f"## 9. Attempt-2 identifiers where table AND column both exist (validator mismatch): {len(mm)}")
for r, x in mm:
    say(f"- id={r['audit_id']}: {x}")
say("")

# frequency CSV
with open(os.path.join(ROOT, "results", "retry_identifier_frequency.csv"), "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["identifier", "attempt2_hits", "repeated_from_attempt1", "fresh",
                "class", "has_v21_hint", "suggestion"])
    for x, c in u2_all.most_common():
        rep_c = sum(1 for r in fb if x in r["rep"])
        w.writerow([x, c, rep_c, c - rep_c, classify(x), hint_for(x), suggest(x)])

open(os.path.join(ROOT, "docs", "retry101_analysis.md"), "w").write("\n".join(L) + "\n")
print("\nwrote docs/retry101_analysis.md + results/retry_identifier_frequency.csv")
