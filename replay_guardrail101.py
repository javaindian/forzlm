#!/usr/bin/env python3
"""
replay_guardrail101.py — v31 WS2: rebuild the unknown-identifier list
=====================================================================

Replays the 101 guardrail-refused questions (audit export 2026-09-20)
against the local llama.cpp endpoint and runs every generated SQL through
the REAL guardrail (pipeline/guardrail.py), capturing WHICH tables/columns
get rejected. The aggregate list feeds:
  - vocab/synonyms.json + guardrail whitelist expansion (v31 WS3)
  - new HINT_MAP entries (wrong-identifier -> correct-path hints)
  - the v31 negative / out-of-schema training examples (v31 WS4)

HOW TO RUN (on the server):
  1. Copy this file into the chalo_chatbot project root — the folder that
     contains pipeline/  (it imports pipeline.schema_knowledge for the exact
     runtime system prompt and pipeline.guardrail for the real validator).
  2. Make sure llama.cpp is up and the secretary is IDLE (llama.cpp serves
     one generation at a time; the replay will queue with live users).
  3. Pilot first, then the full run:
       python3 replay_guardrail101.py --limit 10
       python3 replay_guardrail101.py
     Serial timing: ~35-60s per question -> 101 questions is roughly 1-1.5h.

OUTPUT: replay_results.csv (resumable — re-running skips done ids), plus a
final on-screen ranking of the unknown identifiers.
"""

import argparse
import csv
import json
import re
import sys
import time
import urllib.request
from collections import Counter
from pathlib import Path

# ── the 101 guardrail-refused questions: [audit_id, question] ───────────────
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


def load_runtime_pieces():
    """Import the runtime prompt builder + guardrail from the project root."""
    here = str(Path(__file__).resolve().parent)
    if here not in sys.path:
        sys.path.insert(0, here)
    from pipeline.schema_knowledge import build_system_prompt
    from pipeline.guardrail import validate_sql
    from pipeline.llm_client import clean_sql
    return build_system_prompt(), validate_sql, clean_sql


def generate(url, system_prompt, question, temperature, max_tokens, timeout):
    """One chat completion — same shape as pipeline/llm_client.py."""
    payload = {
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": question},
        ],
        "temperature": temperature,
        "max_tokens": max_tokens,
        "repeat_penalty": 1.1,
    }
    req = urllib.request.Request(
        url, data=json.dumps(payload).encode("utf-8"), method="POST",
        headers={"Content-Type": "application/json", "Accept": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=timeout) as r:
        resp = json.loads(r.read().decode("utf-8"))
    choice = resp["choices"][0]
    return choice["message"]["content"], choice.get("finish_reason", "")


REFUSAL_SHAPE = re.compile(r"SELECT\s+'", re.IGNORECASE)


def extract_idents(issues):
    """Turn guardrail issues into (unknown_tables, unknown_table.column) sets."""
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
        else:  # sensitive_table / sensitive_column — keep visible
            pairs.add("[" + i.kind + "] " + d[:80])
    return sorted(tables), sorted(pairs)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--url", default=DEFAULT_URL)
    ap.add_argument("--limit", type=int, default=0, help="pilot: only the first N")
    ap.add_argument("--out", default="replay_results.csv")
    ap.add_argument("--temperature", type=float, default=0.1)
    ap.add_argument("--max-tokens", type=int, default=512)
    ap.add_argument("--timeout", type=int, default=240)
    args = ap.parse_args()

    try:
        system_prompt, validate_sql, clean_sql = load_runtime_pieces()
    except Exception as e:
        sys.exit("Could not import the runtime pieces: " + str(e) +
                 "\nCopy this script into the chalo_chatbot project root (next to pipeline/).")
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

    fields = ["audit_id", "gen_s", "finish_reason", "verdict",
              "unknown_tables", "unknown_columns", "issues", "sql", "question"]
    newfile = not out.exists()
    fh = open(out, "a", newline="", encoding="utf-8")
    w = csv.writer(fh)
    if newfile:
        w.writerow(fields)
        fh.flush()

    stats = Counter()
    tbl_c = Counter()
    col_c = Counter()
    t_all = []
    try:
        for n, (aid, q) in enumerate(todo, 1):
            t0 = time.time()
            try:
                raw, finish = generate(args.url, system_prompt, q,
                                       args.temperature, args.max_tokens, args.timeout)
            except Exception as e:
                w.writerow([aid, "", "LLM_ERROR:" + type(e).__name__, "LLM_ERROR",
                            "", "", str(e)[:200], "", q])
                fh.flush()
                stats["LLM_ERROR"] += 1
                print("[" + str(n) + "/" + str(len(todo)) + "] id=" + str(aid)
                      + " LLM_ERROR (" + type(e).__name__ + ")")
                continue
            gen_s = round(time.time() - t0, 1)
            t_all.append(gen_s)
            sql = clean_sql(raw)

            if finish == "length":
                verdict = "TRUNCATED"
                tables, pairs, issues_s = "", "", "cut off by max_tokens"
            elif not sql.strip():
                verdict = "EMPTY"
                tables, pairs, issues_s = "", "", "model returned nothing usable"
            elif REFUSAL_SHAPE.search(sql[:200]) and re.search(r"\bAS\s+Message\b", sql, re.I):
                verdict = "REFUSAL_SQL"
                tables, pairs = "", ""
                issues_s = "model self-refused (SELECT '...' AS Message)"
            else:
                res = validate_sql(sql)
                if res.is_valid:
                    verdict, tables, pairs, issues_s = "PASS", "", "", ""
                else:
                    verdict = "FAIL"
                    tables, pairs = extract_idents(res.issues)
                    issues_s = " | ".join("[" + i.kind + "] " + i.detail
                                          for i in res.issues)[:1000]

            # normalize: tables/pairs are lists (FAIL path) or "" (other paths)
            tbl_list = tables if isinstance(tables, list) else ([tables] if tables else [])
            col_list = pairs if isinstance(pairs, list) else ([pairs] if pairs else [])
            w.writerow([aid, gen_s, finish, verdict,
                        "; ".join(tbl_list), "; ".join(col_list),
                        issues_s, sql.replace("\n", " "), q])
            fh.flush()
            stats[verdict] += 1
            for t in tbl_list:
                tbl_c[t] += 1
            for p in col_list:
                col_c[p] += 1
            first = (tbl_list or col_list or ["-"])[0][:70]
            print("[" + str(n) + "/" + str(len(todo)) + "] id=" + str(aid)
                  + " " + verdict.ljust(11) + " " + str(gen_s).rjust(6) + "s  " + first)
    finally:
        fh.close()

    print("\n=== DONE: " + str(dict(stats)) + " ===")
    if t_all:
        t_all.sort()
        print("gen time: p50=" + str(t_all[len(t_all) // 2]) + "s max=" + str(t_all[-1]) + "s")
    if tbl_c:
        print("\nTOP UNKNOWN TABLES (vocab + HINT_MAP input):")
        for t, n in tbl_c.most_common(30):
            print("  " + str(n).rjust(3) + "  " + t)
    if col_c:
        print("\nTOP UNKNOWN COLUMNS (table.column):")
        for c, n in col_c.most_common(30):
            print("  " + str(n).rjust(3) + "  " + c)
    print("\nfull rows -> " + str(out))


if __name__ == "__main__":
    main()
