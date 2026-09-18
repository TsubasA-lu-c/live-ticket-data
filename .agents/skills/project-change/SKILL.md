---
name: project-change
description: Modify production live-ticket delivery data in this repository. Use for adding, changing, removing, validating, or promoting data; do not use for read-only inspection.
---

1. Read `README.md` and only the data files relevant to the requested change.
2. Confirm the change is explicitly intended for production; Dev approval is not production approval.
3. Preserve unrelated existing IDs and records. Never invent missing facts.
4. Keep this repository data-only; collector logic belongs elsewhere.
5. Validate JSON structure and manifest consistency with the established collector workflow when available.
6. Report exactly what changed and any unresolved source or validation risk.
