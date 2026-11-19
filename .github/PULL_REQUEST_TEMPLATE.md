## Summary
<!-- Briefly describe what this PR changes and why -->

## Type of Change
- [ ] Email roster / `config/contacts.json` update
- [ ] Visual template / asset update (`scripts/render_designs.py`, `assets/`)
- [ ] Content curation / deduplication / caption logic
- [ ] Workflow / Docker / CI configuration
- [ ] Documentation

## Pre-Merge Checklist
- [ ] No secrets or `.env` files are included in this PR
- [ ] Tested locally with `--no-commit` (no accidental live emails sent)
- [ ] If `config/contacts.json` changed, verified `To`/`Cc` resolution via `resolve_recipients()`
- [ ] If base logos/template changed, regenerated `assets/base_cover_frame.png` and `assets/base_inner_frame.png`
