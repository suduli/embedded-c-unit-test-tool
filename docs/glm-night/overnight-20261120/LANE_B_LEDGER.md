| item | state | commit | est tokens | cumulative | notes |
|---|---|---|---|---|---|
| FIX-REP | DONE | 3e68e96 | 110k | 110k | executor: Claude; 1465 passed |
| FIX-TXN | DONE | PENDING | 120k | 230k | executor: Claude; Project.transaction (journal+rollback+cancellation) and token on save_file/save; write_analysis_model runs in OutputRoot.transaction, joining a caller |
