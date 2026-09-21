# forzlm — AI Secretary work repo

Single input/output channel between the owner (VPS `chalo-ai-secretary`) and the agent.
Branch for all work: **`sandbox-outputs`**.

## Layout

| Path | Contents | Written by |
|------|----------|------------|
| `patch/` | schema patch scripts (`patch_hintmap_vX_Y.py`) | agent |
| `replay/` | measurement instruments (`replay_with_retry101_revN.py`) | agent |
| `results/` | run outputs from the VPS (`replay_retry_results.csv`, logs) | owner |
| `docs/` | per-artifact CHANGELOGs + notes | agent |
| `superseded/` | superseded versions, archived under original names | both |
| `baseline/` | reference snapshots from the live tree | owner |

## The loop

1. Agent pushes deliverables to `sandbox-outputs`.
2. Owner pulls on the VPS, applies (patch + service restart / replay run).
3. Owner pushes run artifacts (CSVs, logs) back to `results/`.
4. Agent pulls, analyzes, next iteration (v_next patch / instrument revision / v31 dataset).

## Versioning protocol (STANDING RULE — owner directive 2026-09-21)

1. Every revision → **new filename** (`_v<maj>_<min>.py` or `_revN`).
2. Superseded file moves to `superseded/` under its original name — never overwritten in place.
3. Exact delta documented in `<artifact>_CHANGELOG.md` **at revision time** — no manual diffing, ever.
4. Internal self-references and all doc pointers updated in the same pass.

## Reading the replay summary (rev2 semantics)

- `PASS_FIRST` — correct on attempt 1 (no patch involvement)
- `REFUSED_DOMAIN` — every hallucinated table belongs to a domain the ERP doesn't store → canonical refusal, 0 retry GPU (patch Part C)
- `PASS_RETRY` — guardrail caught attempt 1, HINT_MAP-guided retry succeeded (Part A)
- `FAIL_BOTH` — retry failed → classify from the row: new identifier (→ next HINT_MAP batch), same identifier repeated (→ hint phrasing), new domain-absent variant (→ DOMAIN_ABSENT_TABLES)

## State log

- 2026-09-21 (later): owner restored all artifacts lost in the sandbox reset (flat upload, then agent-filed
  into layout). Verified: patch v2.1 (79 entries, IEM + Part B v2.1 block, py_compile OK) · replay rev2
  (tally fix present, 101 questions, py_compile OK) · v1 replay_results.csv (101 rows) · guardrail101
  worklist + live-tree zip in baseline/. Awaiting: full-101 replay_retry_results.csv in results/.
- 2026-09-21: repo workflow established. Agent sandbox reset to ~Sep 15 checkpoint lost local copies of
  `patch_hintmap_v2_1.py` (79 HINT_MAP entries + domain-absent refusal, applied & pilot-verified on VPS)
  and `replay_with_retry101_rev2.py` (retry-path instrument, tally fix; 5-row pilot done).
  Canonical copies to be committed from the VPS. v2.2 candidate entries already identified from pilot
  id=603: `("InventoryItem_Master", "InventoryTypeID")` and `("InventoryType_Master", None)` — both point
  to `ItemCategory_ID` → `InventoryCategory_Master(Id, Name)`. v2.2 ships as ONE batch after the full
  101 replay CSV lands in `results/`.
- 2026-09-21 (final): full-101 rev2 run analyzed (tools/analyze_retry_results.py -> docs/retry101_analysis.md
  + results/retry_identifier_frequency.csv). Outcomes: 8 PASS_FIRST / 15 PASS_RETRY / 16 REFUSED_DOMAIN /
  62 FAIL_BOTH. Key finding: hints fix 83% of hinted identifiers, but attempt-2 spawns 65 fresh
  hallucinations (95 distinct) and 77 attempt-2 identifiers had no v2.1 hint. Single-retry is the
  bottleneck -> v2.2 batch + multi-retry ceiling measurement (rev3) next.
