# SECOND PASS — lane A (items needing a human)

| item | what is needed | why it needs a human | where |
|------|----------------|---------------------|-------|
| A2 | Compile and run the composed generated C (stub unit + protocol runtime + per-case functions) with a real C toolchain to confirm the parse-only verification; render the UUT call body into the per-case call slot (CMP-GEN: needs the analysis model's declared types and comparison semantics) | no C compiler is installed on this machine, so run-time behaviour of the generated C is unverifiable here; the call-body rendering is the CMP-GEN second-pass item and needs the model extension decision | src/ectt/gen/testbody.py (call_lines slot), src/ectt/gen/protocol.py, tests/gen/test_testbody.py |
