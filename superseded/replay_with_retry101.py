#!/usr/bin/env python3
"""
replay_with_retry101.py — v2 instrument: measures the PATCHED pipeline
======================================================================
Per question: attempt #1 like production; if guardrail fails, do exactly
what the patched orchestrator does (domain-absent refusal, else one
hint-guided retry + Branch_Id auto-repair) and record the final outcome.

RUN (server, chalo_chatbot project root, llama.cpp idle):
    python3 replay_with_retry101.py --limit 5     # pilot
    python3 replay_with_retry101.py               # full ~40-70 min
OUTPUT: replay_retry_results.csv (resumable). final outcomes:
  PASS_FIRST | PASS_RETRY | REFUSED_DOMAIN | FAIL_BOTH |
  NO_RETRY_TRUNCATED / NO_RETRY_EMPTY / NO_RETRY_REFUSAL_SQL |
  LLM_ERROR / LLM_ERROR2
"""
import argparse, csv, json, re, sys, time, urllib.request
from collections import Counter
from pathlib import Path

QUESTIONS = [
 [
  611,
  "How many smart boards, projectors, or tablets are currently under maintenance or non-functional?"
 ],
 [
  609,
  "Which vendor has supplied the most inventory this year, and what is their pending payment status?"
 ],
 [
  607,
  "How many library books are currently marked as lost or overdue by students?"
 ],
 [
  604,
  "What is the total current value of fixed assets (computers, lab equipment, furniture) registered in the ERP?"
 ],
 [
  603,
  "How many textbooks and notebooks are available in the school store for the next term?"
 ],
 [
  602,
  "What is the current stock level of school uniforms, and which sizes are running low?"
 ],
 [
  600,
  "What is the total maintenance and repair cost incurred for the fleet in the last quarter?"
 ],
 [
  597,
  "How many GPS tracking alerts (e.g., overspeeding, route deviation, unauthorized stops) were triggered this week?"
 ],
 [
  595,
  "What is the average monthly fuel consumption and cost per vehicle?"
 ],
 [
  594,
  "Which bus routes have the highest number of parent complaints or delays this month?"
 ],
 [
  591,
  "How many new staff background verification checks are pending completion?"
 ],
 [
  590,
  "Can you list staff members whose recent performance appraisal scores are below the expected threshold?"
 ],
 [
  589,
  "What is the total amount of staff advance or salary loan pending recovery?"
 ],
 [
  587,
  "Are there any discrepancies between biometric attendance and approved leave applications this month?"
 ],
 [
  584,
  "What is the average years of experience of the teaching faculty in the senior secondary wing?"
 ],
 [
  583,
  "Which staff members have not completed their mandatory POSH or child safety (POCSO) training?"
 ],
 [
  579,
  "What is the staff attrition or turnover rate for the current academic year?"
 ],
 [
  578,
  "How many teaching and non-teaching staff members are on leave today?"
 ],
 [
  577,
  "What is the current teacher-to-student ratio across the school?"
 ],
 [
  576,
  "What is the rate of re-evaluation or re-checking requests for the recent board exams?"
 ],
 [
  575,
  "How many students have opted for each subject combination in Class 11 (Science, Commerce, Arts/Humanities)?"
 ],
 [
  573,
  "What is the academic performance comparison between the morning and evening shifts (if applicable)?"
 ],
 [
  572,
  "How many practical exam marks are pending submission for the science departments?"
 ],
 [
  571,
  "What is the average time taken by teachers to grade and publish exam results after the test?"
 ],
 [
  569,
  "What is the syllabus completion rate for each class as per teacher logs in the ERP?"
 ],
 [
  568,
  "How many students are currently enrolled in remedial or extra coaching classes?"
 ],
 [
  566,
  "What is the average GPA/CGPA trend across the school over the last 3 years?"
 ],
 [
  559,
  "How many students are marked present in class but have not swiped their RFID/ID cards at the gate?"
 ],
 [
  555,
  "What is the daily average attendance trend compared to the same month last year?"
 ],
 [
  553,
  "How many medical leave requests were submitted by students this month?"
 ],
 [
  549,
  "Can you list students who have been absent for more than 3 consecutive days?"
 ],
 [
  546,
  "Can you provide a list of students whose Aadhaar or UDISE+ details are missing or incomplete?"
 ],
 [
  544,
  "How many students transferred out mid-session, and what were the primary reasons recorded?"
 ],
 [
  543,
  "What is the geographical distribution (pincode-wise) of our current student base?"
 ],
 [
  541,
  "Are there any classes where the student strength exceeds the CBSE/State Board prescribed limit?"
 ],
 [
  539,
  "How many students are currently on the waiting list for Nursery and KG admissions?"
 ],
 [
  538,
  "From which sources (website, referrals, walk-ins, social media ads) are we getting the most admissions?"
 ],
 [
  536,
  "How many students were admitted under the RTE quota this academic year?"
 ],
 [
  534,
  "Which class has the highest number of vacant seats for the upcoming academic session?"
 ],
 [
  525,
  "What is the average time taken by parents to clear dues after the due date?"
 ],
 [
  524,
  "How many fee concession or scholarship requests are currently pending management approval?"
 ],
 [
  520,
  "How much RTE (Right to Education) reimbursement is currently pending from the government?"
 ],
 [
  514,
  "how many students eligible for board exam registration"
 ],
 [
  510,
  "how many students from outside city or hostel"
 ],
 [
  508,
  "give me list of students with single parent"
 ],
 [
  505,
  "which class is full and which has vacant seats"
 ],
 [
  499,
  "stock that is not moving since long time"
 ],
 [
  498,
  "which vendor we buy most from"
 ],
 [
  497,
  "items pending for purchase approval"
 ],
 [
  496,
  "what all we purchased this month for school"
 ],
 [
  495,
  "furniture count classroom wise"
 ],
 [
  493,
  "books issued but not returned list"
 ],
 [
  492,
  "how many computers working vs not working"
 ],
 [
  491,
  "sports equipment inventory show me"
 ],
 [
  490,
  "which items expired or damaged in store"
 ],
 [
  487,
  "how many uniforms sold this year"
 ],
 [
  485,
  "which items are low in stock need to order"
 ],
 [
  484,
  "how many books left in stock in library"
 ],
 [
  483,
  "vehicle documents insurance puc expiry status all buses"
 ],
 [
  481,
  "which driver has most complaints"
 ],
 [
  478,
  "students waiting for transport allocation"
 ],
 [
  477,
  "any bus due for servicing or fitness expiry"
 ],
 [
  474,
  "fuel expense this month for transport"
 ],
 [
  460,
  "staff whose contract expiring soon"
 ],
 [
  457,
  "how many female vs male staff"
 ],
 [
  452,
  "teachers without any qualification updated in system"
 ],
 [
  438,
  "how many students absent without informing today"
 ],
 [
  432,
  "which teacher not marking attendance regularly"
 ],
 [
  426,
  "students who came late today"
 ],
 [
  412,
  "average marks trend for class 8 whole year"
 ],
 [
  410,
  "which stream science commerce arts best result class 11"
 ],
 [
  408,
  "top 3 students in each subject class 12"
 ],
 [
  406,
  "performance of RTE students in exams overall"
 ],
 [
  404,
  "marks entry pending teacher wise show me"
 ],
 [
  390,
  "how many exam papers still not evaluated"
 ],
 [
  388,
  "class 11 commerce vs science average marks"
 ],
 [
  382,
  "result not entered for which classes yet?"
 ],
 [
  377,
  "how many reappear or supplementary cases this exam"
 ],
 [
  376,
  "average attendance of toppers vs failures any pattern?"
 ],
 [
  375,
  "students scoring less than 33 in science"
 ],
 [
  374,
  "class 6 result summary quick"
 ],
 [
  371,
  "which teacher's class scored best in her subject"
 ],
 [
  365,
  "how many absent in the last unit test"
 ],
 [
  362,
  "which section performed better in science 10A or 10B"
 ],
 [
  361,
  "result analysis of class 12 science stream"
 ],
 [
  355,
  "how many students failed in any subject class 8"
 ],
 [
  350,
  "how much money in fees we wrote off as bad debt"
 ],
 [
  347,
  "how much second installment is due this month total"
 ],
 [
  346,
  "fee concession category wise breakup staff sibling rte merit"
 ],
 [
  342,
  "how many reminders sent and how many paid after that"
 ],
 [
  333,
  "total security deposit collected and refundable"
 ],
 [
  316,
  "how much transport fee pending route wise"
 ],
 [
  315,
  "any concession given without approval? i want to check"
 ],
 [
  300,
  "how many siblings getting sibling discount and total amount"
 ],
 [
  299,
  "total fees waived off due to rte"
 ],
 [
  292,
  "how many students on installment plan currently"
 ],
 [
  291,
  "total tuition fee collection excluding transport"
 ],
 [
  289,
  "how much discount we have given in total, is it too much?"
 ],
 [
  286,
  "how much admission fee collected for new admissions this year"
 ],
 [
  278,
  "is there any student paid extra by mistake, refund pending?"
 ],
 [
  277,
  "how much scholarship amount we given this year"
 ]
]
DEFAULT_URL = "http://localhost:8080/v1/chat/completions"
REFUSAL_SHAPE = re.compile(r"SELECT\s+'", re.IGNORECASE)

# ── Branch_Id auto-repair: verbatim from pipeline/orchestrator.py ───────────
_RE_BRANCH_ID_BARE = re.compile(
    r"(SELECT\s+)(Branch_Id)(\s+FROM\s+UserAccountRoleDetails\b)", re.IGNORECASE)
_RE_BRANCH_ID_QUALIFIED = re.compile(
    r"\b([A-Za-z_][A-Za-z0-9_]*)\.Branch_Id\b", re.IGNORECASE)
_RE_ALIAS_BOUND_UARD = re.compile(
    r"\b(?:FROM|JOIN)\s+UserAccountRoleDetails\s+(?:AS\s+)?([A-Za-z_][A-Za-z0-9_]*)\b",
    re.IGNORECASE)

def _auto_repair_branch_id(sql):
    if not sql or "branch_id" not in sql.lower():
        return sql
    fixed = _RE_BRANCH_ID_BARE.sub(lambda m: f"{m.group(1)}BranchID{m.group(3)}", sql)
    bound = {a.upper() for a in _RE_ALIAS_BOUND_UARD.findall(fixed)}
    if bound:
        def _alias_fix(m):
            return f"{m.group(1)}.BranchID" if m.group(1).upper() in bound else m.group(0)
        fixed = _RE_BRANCH_ID_QUALIFIED.sub(_alias_fix, fixed)
    return fixed

def load_runtime_pieces():
    here = str(Path(__file__).resolve().parent)
    if here not in sys.path:
        sys.path.insert(0, here)
    from pipeline.schema_knowledge import build_system_prompt
    from pipeline.guardrail import validate_sql
    from pipeline.llm_client import clean_sql
    try:
        from pipeline.semantic_rules import lookup_hints, lookup_domain_absent
    except Exception:
        try:
            from semantic_rules import lookup_hints, lookup_domain_absent
        except Exception:
            lookup_hints = lookup_domain_absent = None
    if lookup_domain_absent is None:
        print("WARNING: lookup_hints/lookup_domain_absent not importable - "
              "apply patch_hintmap_v2.py first; running WITHOUT patch logic.")
    return build_system_prompt(), validate_sql, clean_sql, lookup_hints, lookup_domain_absent

def generate(url, system_prompt, question, temperature, max_tokens, timeout):
    payload = {"messages": [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": question}],
        "temperature": temperature, "max_tokens": max_tokens, "repeat_penalty": 1.1}
    req = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"),
                                 method="POST",
                                 headers={"Content-Type": "application/json",
                                          "Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        resp = json.loads(r.read().decode("utf-8"))
    choice = resp["choices"][0]
    return choice["message"]["content"], choice.get("finish_reason", "")

def extract_idents(issues):
    tables, pairs = set(), set()
    for i in issues:
        d = i.detail
        if i.kind == "unknown_table":
            m = re.search(r"Table '([^']+)' does not exist", d)
            if m:
                tables.add(m.group(1))
        elif i.kind == "unknown_column":
            m = re.search(r"Column '([^']+)' does not exist on table '([^']+)'", d)
            if m:
                pairs.add(m.group(2) + "." + m.group(1))
        else:
            pairs.add("[" + i.kind + "] " + d[:80])
    return sorted(tables), sorted(pairs)

def judge(sql, finish, validate_sql, clean_sql):
    """-> (verdict, tables, pairs, issues_s, sql)"""
    if finish == "length":
        return "TRUNCATED", [], [], "cut off by max_tokens", sql
    if not sql.strip():
        return "EMPTY", [], [], "model returned nothing usable", sql
    if REFUSAL_SHAPE.search(sql[:200]) and re.search(r"\bAS\s+Message\b", sql, re.I):
        return "REFUSAL_SQL", [], [], "model self-refused (SELECT '...' AS Message)", sql
    res = validate_sql(sql)
    if res.is_valid:
        return "PASS", [], [], "", sql
    tables, pairs = extract_idents(res.issues)
    issues_s = " | ".join("[" + i.kind + "] " + i.detail for i in res.issues)[:1000]
    return "FAIL", tables, pairs, issues_s, sql

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--url", default=DEFAULT_URL)
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--out", default="replay_retry_results.csv")
    ap.add_argument("--temperature", type=float, default=0.1)
    ap.add_argument("--max-tokens", type=int, default=512)
    ap.add_argument("--timeout", type=int, default=240)
    args = ap.parse_args()

    system_prompt, validate_sql, clean_sql, lookup_hints, lookup_domain_absent = \
        load_runtime_pieces()
    print("system prompt: " + str(len(system_prompt)) + " chars | endpoint: " + args.url)

    done = set()
    out = Path(args.out)
    if out.exists():
        with open(out, encoding="utf-8") as f:
            done = {int(r["audit_id"]) for r in csv.DictReader(f) if r.get("audit_id")}
        print("resuming: " + str(len(done)) + " already done")
    todo = [(i, q) for i, q in QUESTIONS if i not in done]
    if args.limit:
        todo = todo[: args.limit]
    print("to run: " + str(len(todo)) + " questions\n")

    fields = ["audit_id", "gen1_s", "verdict1", "n_hints", "gen2_s", "verdict2",
              "final", "unknown_tables_1", "unknown_columns_1",
              "unknown_tables_2", "unknown_columns_2", "sql2", "question"]
    newfile = not out.exists()
    fh = open(out, "a", newline="", encoding="utf-8")
    w = csv.writer(fh)
    if newfile:
        w.writerow(fields)
        fh.flush()

    finals, v2c = Counter(), Counter()
    hint_hits = 0
    g1_all, g2_all = [], []

    def write(aid, g1, v1, nh, g2, v2, final, t1, p1, t2, p2, sql2, q):
        w.writerow([aid, g1, v1, nh, g2, v2, final,
                    "; ".join(t1), "; ".join(p1), "; ".join(t2), "; ".join(p2),
                    (sql2 or "").replace("\n", " ")[:800], q])
        fh.flush()

    try:
        for n, (aid, q) in enumerate(todo, 1):
            t0 = time.time()
            try:
                raw, finish = generate(args.url, system_prompt, q,
                                       args.temperature, args.max_tokens, args.timeout)
            except Exception as e:
                write(aid, "", "LLM_ERROR", "", "", "", "LLM_ERROR",
                      [], [], [], [], "", q)
                finals["LLM_ERROR"] += 1
                print("[" + str(n) + "/" + str(len(todo)) + "] id=" + str(aid)
                      + " LLM_ERROR (" + type(e).__name__ + ")")
                continue
            g1 = round(time.time() - t0, 1)
            g1_all.append(g1)
            v1, t1, p1, iss1, sql1 = judge(clean_sql(raw), finish, validate_sql, clean_sql)

            if v1 == "PASS":
                write(aid, g1, v1, 0, "", "", "PASS_FIRST", t1, p1, [], [], "", q)
                finals["PASS_FIRST"] += 1
                print("[" + str(n) + "/" + str(len(todo)) + "] id=" + str(aid)
                      + " PASS_FIRST " + str(g1) + "s")
                continue

            if v1 != "FAIL":
                write(aid, g1, v1, 0, "", "", "NO_RETRY_" + v1, t1, p1, [], [], sql1, q)
                finals["NO_RETRY_" + v1] += 1
                print("[" + str(n) + "/" + str(len(todo)) + "] id=" + str(aid)
                      + " NO_RETRY_" + v1)
                continue

            # ── patched production path ──
            if lookup_domain_absent is not None:
                try:
                    da = lookup_domain_absent(sql1)
                except Exception:
                    da = []
                if da:
                    write(aid, g1, v1, 0, "", "", "REFUSED_DOMAIN", t1, p1, [], [], sql1, q)
                    finals["REFUSED_DOMAIN"] += 1
                    print("[" + str(n) + "/" + str(len(todo)) + "] id=" + str(aid)
                          + " REFUSED_DOMAIN " + str(g1) + "s  " + " / ".join(sorted(set(da))))
                    continue

            hints = []
            if lookup_hints is not None:
                try:
                    hints = lookup_hints(sql1)
                except Exception:
                    hints = []
            nh = len(hints)
            hint_hits += 1 if nh else 0
            issue_lines = iss1.replace(" | ", "\n- ")
            issue_lines = "-" + issue_lines if issue_lines else "- (schema mismatch)"
            hint_lines = "\n".join("- Hint: " + h for h in hints)
            retry_q = (q + "\n\nNote: a previous attempt at this query used a table or "
                       "column that does not exist in the real schema:\n" + issue_lines + "\n")
            if hint_lines:
                retry_q += "The correct approach for the issues above:\n" + hint_lines + "\n"
            retry_q += "Write the correct T-SQL query using only real tables and columns."

            t1c = time.time()
            try:
                raw2, finish2 = generate(args.url, system_prompt, retry_q,
                                         args.temperature, args.max_tokens, args.timeout)
            except Exception as e:
                write(aid, g1, v1, nh, "", "LLM_ERROR", "LLM_ERROR2", t1, p1, [], [], "", q)
                finals["LLM_ERROR2"] += 1
                print("[" + str(n) + "/" + str(len(todo)) + "] id=" + str(aid)
                      + " LLM_ERROR2 (" + type(e).__name__ + ")")
                continue
            g2 = round(time.time() - t1c, 1)
            g2_all.append(g2)
            sql2 = _auto_repair_branch_id(clean_sql(raw2))
            v2, t2, p2, iss2, _ = judge(sql2, finish2, validate_sql, clean_sql)
            v2c[v2] += 1
            final = "PASS_RETRY" if v2 == "PASS" else ("FAIL_BOTH" if v2 == "FAIL" else v2 + "2")
            write(aid, g1, v1, nh, g2, v2, final, t1, p1, t2, p2, sql2, q)
            print("[" + str(n) + "/" + str(len(todo)) + "] id=" + str(aid)
                  + " " + final.ljust(14) + " hints=" + str(nh)
                  + "  " + str(g1) + "+" + str(g2) + "s")
    finally:
        fh.close()

    N = sum(finals.values()) or 1
    print("\n=== FINAL OUTCOMES (patched pipeline simulation) ===")
    for k, c in finals.most_common():
        print("  " + k.ljust(22) + str(c).rjust(4) + "  (" + str(round(c / N * 100)) + "%)")
    print("\nattempt-2 verdicts among retried: " + str(dict(v2c)))
    if g1_all:
        g1_all.sort()
        print("gen1: p50=" + str(g1_all[len(g1_all) // 2]) + "s max=" + str(g1_all[-1]) + "s")
    if g2_all:
        g2_all.sort()
        retried = len(g2_all)
        print("gen2 (retried=" + str(retried) + "): p50=" + str(g2_all[retried // 2])
              + "s  total GPU s=" + str(round(sum(g1_all) + sum(g2_all))))
        print("hint coverage on FAILs: " + str(hint_hits) + "/" + str(retried))
    print("\nfull rows -> " + str(out))

if __name__ == "__main__":
    main()
