# SOLE — Bits & Bytes Social Media Automation

[![Offline Cron Status](https://github.com/yashagrawall/bits-bytes-automation/actions/workflows/bits-bytes-offline-cron.yml/badge.svg)](https://github.com/yashagrawall/bits-bytes-automation/actions/workflows/bits-bytes-offline-cron.yml)
[![CI Validation](https://github.com/yashagrawall/bits-bytes-automation/actions/workflows/ci-validate.yml/badge.svg)](https://github.com/yashagrawall/bits-bytes-automation/actions/workflows/ci-validate.yml)
![Python 3.12](https://img.shields.io/badge/Python-3.12-3776AB?logo=python&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?logo=docker&logoColor=white)
![Cost](https://img.shields.io/badge/Subscription_Cost-$0%2Fmo-2EA043)

Automated, zero-cost, offline-capable content curation, 1080×1350 carousel design rendering, caption drafting, and email packaging for **SOLE (Society Of Literary Enthusiasts) — Bits & Bytes** at **IGIT Sarang** (`@sole_igit`).

> **Human-in-the-loop by design:** This system never auto-posts to Instagram. It emails ready-to-publish carousels (PDF + slides), captions, and source tables to the Design & Social Media leads one evening ahead of each post day.

---

## Weekly Schedule (`Asia/Kolkata`)

Runs automatically via GitHub Actions even when no local machine is powered on:

| Day & Time (IST) | Content Type | Target Post Day | Output |
| :--- | :--- | :--- | :--- |
| **Tuesday, 6:00 PM** | Random Fact of the Week | Wednesday | 4-slide 1080×1350 carousel + Instagram caption |
| **Wednesday, 6:00 PM** | Random Vocabulary / Thesaurus | Thursday | 4-slide 1080×1350 carousel + Instagram caption |
| **Saturday, 6:00 PM** | Weekly News Highlights | Sunday | 8-slide 1080×1350 carousel + Top 10 source table + Instagram caption |

---

## Key Features

- **Zero Subscriptions ($0/mo):** Built with Python, Pillow, GitHub Actions, Docker Compose, and Gmail SMTP App Passwords.
- **Pre-Baked HD Static Assets:** Transparent HD SOLE & IGIT logos (`assets/*_logo_hd.png`) and pre-baked 1080×1350 cover/inner frames (`assets/base_*_frame.png`) cut carousel rendering to ~1.3s–2.5s.
- **Peer-Approved Zine Layout:** Preserves the official `BITS -N- BYTES` torn graph-paper aesthetic with centered, auto-fitted typography that never overlaps or clips.
- **Persistent Deduplication:** Tracks every sent news story, fact, and word in `data/published_history.json` (auto-committed after each scheduled run) so content never repeats.
- **Anti-Spam Email Delivery:** Sends RFC-5322 compliant `multipart/alternative` (plain text + clean HTML with inline HD logos) via Gmail SSL SMTP with retry protection.

---

## Quick Start

### 1. Offline Cloud Automation (GitHub Actions — Recommended)
1. Fork or clone this repository.
2. Add the following **Repository Secrets** under `Settings → Secrets and variables → Actions`:
   - `GMAIL_USER` — Sender Gmail address
   - `GMAIL_APP_PASSWORD` — 16-character Google App Password (requires 2-Step Verification)
   - `GEMINI_API_KEY` *(optional)* — Optional LLM enrichment fallback
3. Enable GitHub Actions. The cron workflow (`.github/workflows/bits-bytes-offline-cron.yml`) runs every Tue/Wed/Sat at 6:00 PM IST, or can be triggered manually via **Actions → Run workflow**.

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

# Send a combined test sample to a single address
python3 scripts/standalone_engine.py --type combined-sample --send-mail --to-override your@email.com
```

### 3. Local Docker Stack (`bits-bytes-engine` + `n8n`)
```bash
cp .env.example .env   # Fill in GMAIL_USER and GMAIL_APP_PASSWORD
docker compose up -d --build
```
- **Engine API:** `http://127.0.0.1:8765`
- **n8n UI:** `http://127.0.0.1:5678`

---

## Documentation & Guides

- **[DOCUMENTATION.md](DOCUMENTATION.md)** — Full architecture, design system specs, asset pipeline, anti-spam setup, troubleshooting history, and operations guide.
- **[CONTRIBUTING.md](CONTRIBUTING.md)** — Handover guide for future SOLE / Bits & Bytes reps (updating `config/contacts.json`, editing templates, and opening PRs).

---

## License

Released under the [MIT License](LICENSE). Maintained by **SOLE — Bits & Bytes, IGIT Sarang**.
