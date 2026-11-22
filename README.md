# SOLE — Bits & Bytes Social Media Automation

[![Offline Cron Status](https://github.com/yashagrawall/bits-bytes-automation/actions/workflows/bits-bytes-offline-cron.yml/badge.svg)](https://github.com/yashagrawall/bits-bytes-automation/actions/workflows/bits-bytes-offline-cron.yml)
[![CI Validation](https://github.com/yashagrawall/bits-bytes-automation/actions/workflows/ci-validate.yml/badge.svg)](https://github.com/yashagrawall/bits-bytes-automation/actions/workflows/ci-validate.yml)
![Python 3.12](https://img.shields.io/badge/Python-3.12-3776AB?logo=python&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?logo=docker&logoColor=white)
![Cost](https://img.shields.io/badge/Subscription_Cost-$0%2Fmo-2EA043)

Automated, zero-cost, offline-capable content curation, 1080×1350 carousel design rendering, Instagram caption drafting, and email packaging for **SOLE (Society Of Literary Enthusiasts) — Bits & Bytes** at **IGIT Sarang** (`@sole_igit`).

> **Human-in-the-loop & Instagram-only by design:** This system never auto-posts to Instagram and generates no LinkedIn content. It emails ready-to-publish carousels (dated PDF + 1080×1350 JPG slides), Instagram captions, and source tables to the Design & Social Media leads one evening ahead of each post day.

---

## Weekly Schedule (`Asia/Kolkata`)

Runs automatically via **GitHub Actions** even when no local machine is powered on:

| Day & Time (IST) | Content Type | Target Post Day | Carousel PDF Name | Output |
| :--- | :--- | :--- | :--- | :--- |
| **Tuesday, 6:00 PM** | Random Fact of the Week | Wednesday | `<DateCode>_Random_Fact.pdf` | 4-slide 1080×1350 carousel + Instagram caption |
| **Wednesday, 6:00 PM** | Random Vocabulary / Thesaurus | Thursday | `<DateCode>_Random_Vocabulary.pdf` | 4-slide 1080×1350 carousel + Instagram caption |
| **Saturday, 6:00 PM** | Weekly News Highlights | Sunday | `<DateCode>_Weekly_News_Highlights.pdf` | 8-slide 1080×1350 carousel + Top 10 source table + Instagram caption |

---

## Key Features

- **Zero Subscriptions ($0/mo):** Built with Python, Pillow, GitHub Actions, Docker Compose, and Gmail SMTP App Passwords.
- **Exact Day/Time & Idempotency Guards:** GitHub Actions maps each cron schedule explicitly (`facts` / `vocab` / `news`), `--type auto` skips non-mail days instead of misfiring, and same-day idempotency blocks duplicate emails (override with `--force`).
- **Pre-Baked HD Static Assets:** Transparent HD SOLE & IGIT logos (`assets/*_logo_hd.png`) and pre-baked 1080×1350 cover/inner frames (`assets/base_*_frame.png`) cut carousel rendering to ~1.3s–2.5s.
- **Consistent Format Everywhere:** Single canonical HTML + clean plain-text email builder (`scripts/package_and_deliver.py`), deterministic `/GHOST` Instagram captions (single unified hashtag block, zero raw Markdown), and dated carousel PDFs.
- **Persistent Deduplication:** Tracks every sent news story, fact, and word in `data/published_history.json` (auto-committed with `git pull --rebase` after each scheduled run) so content never repeats.
- **Anti-Spam Email Delivery:** Sends RFC-5322 compliant `multipart/alternative` (clean plain text + light HTML with inline HD logos) via Gmail TLS SMTP (`smtp.gmail.com:587` STARTTLS) with retry protection.

---

## Quick Start

### 1. Offline Cloud Automation (GitHub Actions — Primary)
1. Fork or clone this repository.
2. Add the following **Repository Secrets** under `Settings → Secrets and variables → Actions`:
   - `GMAIL_USER` — Sender Gmail address
   - `GMAIL_APP_PASSWORD` — 16-character Google App Password (requires 2-Step Verification)
   - `CONTACTS_JSON` — Full JSON content of your private `config/contacts.json` (keeps member emails & phones out of the public repo)
   - `GEMINI_API_KEY` *(optional)* — Optional LLM caption enrichment (only when `ENABLE_LLM_CAPTIONS=true`)
3. Enable GitHub Actions. The cron workflow (`.github/workflows/bits-bytes-offline-cron.yml`) runs every Tue/Wed/Sat at 6:00 PM IST, or can be triggered manually via **Actions → Run workflow** (with optional `force` toggle).

### 2. Local CLI (Dry-Run & Testing)
```bash
# Install dependencies
pip install Pillow

# Copy environment template for local email testing
cp .env.example .env

# Dry-run without sending mail or mutating history
python3 scripts/standalone_engine.py --type news --no-commit
python3 scripts/standalone_engine.py --type facts --no-commit
python3 scripts/standalone_engine.py --type vocab --no-commit

# Send a combined test sample to a single address (without burning ledger items)
python3 scripts/standalone_engine.py --type combined-sample --send-mail --no-commit --to-override your@email.com

# Force-resend a live email if already sent today
python3 scripts/standalone_engine.py --type news --send-mail --force
```

### 3. Local Docker Container (`bits-bytes-engine`)
```bash
cp .env.example .env   # Fill in GMAIL_USER and GMAIL_APP_PASSWORD
docker compose up -d --build
```
- **Health Endpoint:** `http://127.0.0.1:8765/health`
- **No Split-Brain Duplicates:** `ENABLE_DAEMON_SCHEDULER=false` by default in `docker-compose.yml` so GitHub Actions stays the sole mailer. If you disable GitHub Actions and set `ENABLE_DAEMON_SCHEDULER=true`, the Docker daemon polls every 60s and triggers strictly on Tue/Wed/Sat at **18:00 IST**.

---

## Documentation, Sample Email & Guides

- **[docs/sample_email.html](docs/sample_email.html)** / **[docs/sample_email.txt](docs/sample_email.txt)** — Redacted sample outgoing email (HTML + clean plain-text format).
- **[DOCUMENTATION.md](DOCUMENTATION.md)** — Full architecture, design system specs, asset pipeline, anti-spam setup, audit history, and operations guide.
- **[CONTRIBUTING.md](CONTRIBUTING.md)** — Handover guide for future SOLE / Bits & Bytes reps (updating `config/contacts.json`, editing templates, and opening PRs).

---

## License

Released under the [MIT License](LICENSE). Maintained by **SOLE — Bits & Bytes, IGIT Sarang**.
