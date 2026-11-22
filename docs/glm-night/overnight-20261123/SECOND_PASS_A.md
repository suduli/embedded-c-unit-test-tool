# SECOND PASS — lane A (items needing a human)

| item | what is needed | why it needs a human | where |
|------|----------------|---------------------|-------|
| A3 | Release signing for the SBOM (signature field + key management) | signing needs keys only the owner holds; the mechanism (which keys, where stored, who signs) is an owner decision per the security policy | src/ectt/sec/sbom.py (SIGNING_NOT_CONFIGURED marker; the document carries no signature field) |
