# SECOND PASS — lane A (items needing a human)

| item | what is needed | why it needs a human | where |
|------|----------------|---------------------|-------|
| A4 | Fold the four cbt-* operations into default_catalogue (src/ectt/api/catalogue.py) so they publish through the engine's hello negotiation like every other operation, and give the catalogue generator per-command argument metadata (today build_parser only emits --target-id, so the four commands carry their own parser in ectt.cli.commands) | ectt.api is outside this item's allowed paths; the published operation surface and the parser-generation design are owner territory | src/ectt/cli/commands.py (cbt_catalogue_extensions, build_cbt_parser) |
