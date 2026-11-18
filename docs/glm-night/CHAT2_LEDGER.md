# Chat 2 ledger

| WP | state | commit | tests | notes |
|---|---|---|---|---|
| WP-SPIKE-01 | DONE | 00af0f7 | spike tests 7 passed; suite 399/4 | 7.5x floor, 0 parse errors, no CFG construct; evidence chain in analysis note |
| WP-SPIKE-03 | PARTIAL | bc9fce5 | suite 399/4 | local-build PASS verified; clean-VM endpoint-security step open (manual, owner) |
| WP-SPIKE-02 | DONE | bf84c1b | spike tests 12 passed; suite 399/4 | 5/5 checklist, 242ms cold start; human app.py pass advisory |
| WP-CORE-01 | DONE | 0f3825c | 130 passed/1 skipped (symlink priv) x3; suite 399/4 | all 3 criterion elements evidenced; cross-machine run is owner step |
| WP-CORE-02 | PARTIAL | 1fb8290 | test_errors 16 passed; suite 399/4 | mechanisms verified; CLI exit-code + op adoption open |
| WP-API-01 | DONE | 427c319 | 20 new api tests; suite 419/4 | AC-1..6 from SRS+SDD-002; transport deferred to WP-API-02 |
| WP-CLI-01 | DONE | 0b19151 | 13 new cli tests; suite 432/4 | catalogue-generated parser; exit codes deferred to WP-CLI-02 |
| WP-CLI-02 | DONE | 9335003 | 11 new exit-code tests; suite 443/4 | 4 categories distinct+documented; 0/1/2/10/11 |
| WP-CLI-03 | PARTIAL | 3bb0df2 | 4 new container tests; suite 447/4 | execution contract pinned; real image = WP-PKG-05 |
| WP-PRJ-01 | DONE | 6a9ff96 | prj 79 passed/2 skips; suite 447/4 | 5 reqs evidenced; companion inspection note cited |
| WP-ING-01 | DONE | 18304a0 | ing 83 passed/0 skip; suite 447/4 | 4 reqs evidenced incl. real cmake scratch-configure |
| WP-ANA-01 | DONE | 28427d2 | ana 128 passed/0 skip; suite 447/4 | PAR-010/020 evidenced vs real libclang |
| WP-ANA-02 | DONE | 0a9dbfa | ana 128 passed/0 skip; suite 447/4 | PAR-030/040/050 evidenced incl closure termination |
| WP-ANA-04 | DONE | 0ad9eba | persist+schema 41 passed; suite 447/4 | 5.4 criterion met in full; PAR-100 row added |
| WP-ANA-08 | DONE | e531ad8 | ana suite green; suite 447/4 | PAR-150: inventory presence/status/fail-closed evidenced |
| WP-ANA-09 | DONE | e531ad8 | ana suite green; suite 447/4 | PAR-160: round-trip + optional-absence evidenced |
| WP-ANA-07 | PARTIAL | 2adfafd | ana 128 passed; suite 447/4 | PAR-130 done; PAR-140 inventory unpopulated + no multi-file driver |
