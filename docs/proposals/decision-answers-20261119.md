# Owner decision answers (2026-11-19)

Recorded from the owner's answers to the decision memos in `decision-memos-20261117.md`. Each answer below takes the memo's recommended option. The owner gave these answers in chat on 2026-11-19. They are recorded here, but the decision register and the requirement, design and licence files have not been changed yet. Applying them is a separate, reviewed change.

| Decision | Owner answer | Memo option | What applying it changes (not yet applied) |
|---|---|---|---|
| D-01 Licence posture (ADR-005, T-01, WP-PKG-07, WP-PKG-08) | Apache-2.0 | (b) | `LICENSE` and the licence badge in the repository. `TOOL-LIC-010` stays as written. Confirm the patent-grant and licensee wording with the owner before the file is replaced. |
| D-02 Identity model (T-04, T-14, WP-TCM-02) | Stable ids plus content digests | (a) | `design/SDD-003-data-model.md` sections 6 and 7, and one sentence in SDD-002 S2/S3. |
| D-03 Platform order (T-05, WP-CORE-03, WP-GUI-01) | Windows first, Linux CI kept green | (a) | Priority edits to `TOOL-NFR-010` and `TOOL-NFR-020` in `SRS-001-requirements.md`. This is a requirement change, so it goes through the change process. |
| D-04 NFR calibration (T-06, WP-CORE-05) | Defer to post-pilot; mark provisional | (a) | `[PROVISIONAL]` markers on `TOOL-NFR-030`, `TOOL-NFR-040` and `TOOL-NFR-150` in the SRS. Calibrate before WP-CORE-05 exits P2. |

## Still open (not answered in this round)

- ADR-003, ADR-004, ADR-005 (record and its file location), ADR-007.
- SRS-Q2 and SRS-Q9.

Items blocked only by those decisions stay held.

## Next step

Apply the four answers as one reviewed change. It touches the licence file, the SRS and SDD text, and the decision state. Confirm before applying, because the licence change is hard to reverse once it is public.
