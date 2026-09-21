
ubuntu@chalo-ai-secretary:/opt/chalo-ai-secretary/chalo_chatbot$ sudo python3 replay_with_retry101_rev2.py --limit 5                         system prompt: 6776 chars | endpoint: http://localhost:8080/v1/chat/completions
to run: 5 questions

[1/5] id=611 REFUSED_DOMAIN 9.7s  asset and maintenance tracking
[2/5] id=609 REFUSED_DOMAIN 26.3s  inventory receipt/issue transactions
[3/5] id=607 REFUSED_DOMAIN 11.4s  the library module
[4/5] id=604 REFUSED_DOMAIN 17.0s  asset and maintenance tracking
[5/5] id=603 FAIL_BOTH      hints=1  15.0+14.3s

=== FINAL OUTCOMES (patched pipeline simulation) ===
  REFUSED_DOMAIN           4  (80%)
  FAIL_BOTH                1  (20%)

attempt-2 verdicts among retried: {'FAIL': 1}
gen1: p50=15.0s max=26.3s
gen2 (retried=1): p50=14.3s  total GPU s=94
hint coverage on FAILs: 1/1

full rows -> replay_retry_results.csv
