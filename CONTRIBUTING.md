# Contributing to SOLE — Bits & Bytes Automation

Thank you for helping maintain the **Bits & Bytes** social media automation for **SOLE, IGIT Sarang**!

## Common Maintainer Tasks

### 1. Updating the Email Roster (`To` / `Cc`)
Copy `config/contacts.example.json` to `config/contacts.json` (gitignored), edit `recipients.to` / `recipients.cc`, and update the `CONTACTS_JSON` GitHub Actions repository secret. Verify locally without sending mail:
```bash
python3 -c "import sys; sys.path.insert(0, 'scripts'); from package_and_deliver import load_contacts, resolve_recipients; to, cc = resolve_recipients(load_contacts()); print('TO:', to); print('CC:', cc)"
```

### 2. Updating Logos or Base Template Frames
If you replace `assets/bits_n_bytes_template.jpg` or the HD logos (`assets/sole_logo_hd.png`, `assets/igit_logo_hd.png`), regenerate the pre-baked static frames before committing:
```bash
python3 scripts/build_static_assets.py
```

### 3. Testing Changes Safely (No Live Emails)
Always run a dry-run before pushing or opening a PR:
```bash
python3 scripts/standalone_engine.py --type news --no-commit
python3 scripts/standalone_engine.py --type facts --no-commit
python3 scripts/standalone_engine.py --type vocab --no-commit
```
If you need to inspect an actual email in your inbox, use `--to-override` so you do not spam the entire team:
```bash
python3 scripts/standalone_engine.py --type combined-sample --send-mail --no-commit --to-override your_email@gmail.com
```

## Rules Before Opening a PR
- **Never commit `.env` or `config/contacts.json`** (personal emails, phone numbers, App Passwords, or API keys).
- **Do not commit ephemeral `output/` files** (already ignored in `.gitignore`).
- **Keep `data/published_history.json` intact** so previously published topics are not repeated.
- **Preserve brand guidelines:** Instagram-only (`@sole_igit`), Week Edition badge present, `WEEKLY NEWS HIGHLIGHTS` title, no slide number markers, and no relevance/source clutter on graphic cards.
