# ChatterFix

A maintenance management system (CMMS) built for technicians, not office workers.

[![Deploy](https://github.com/TheGringo-ai/Chatterfix/actions/workflows/deploy.yml/badge.svg)](https://github.com/TheGringo-ai/Chatterfix/actions/workflows/deploy.yml)
[![Security](https://github.com/TheGringo-ai/Chatterfix/actions/workflows/security-scan.yml/badge.svg)](https://github.com/TheGringo-ai/Chatterfix/actions/workflows/security-scan.yml)

**Status:** Live at [chatterfix.com](https://chatterfix.com)

---

## What is ChatterFix?

ChatterFix is a production CMMS platform focused on hands-free maintenance workflows. Voice commands, OCR scanning, and AI assistance reduce manual data entry for technicians working on the floor.

## Why does it exist?

Traditional CMMS systems require typing, clicking through menus, and filling out forms. That doesn't work when you're standing next to broken equipment with dirty hands. ChatterFix captures maintenance data through voice and camera instead.

## What makes it real?

- Live production deployment with CI/CD
- Firebase/Firestore backend with multi-tenant data isolation
- Security auditing with automated vulnerability fixes
- Active commit history of production maintenance
- `AI_STATE.yaml` tracks decisions and project state to maintain continuity

## What problem does it solve?

- Technicians can create work orders, check out parts, and update status by voice
- OCR extracts data from equipment labels and documents automatically
- AI assists with natural language queries about maintenance history and inventory

---

## Quick Start

**Prerequisites:**
- Python 3.11+
- Google Cloud account (Firebase)
- API keys for AI services (Gemini)

```bash
git clone https://github.com/TheGringo-ai/Chatterfix.git
cd Chatterfix
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your API keys
python3 main.py
```

**Local:** http://localhost:8000
**Production:** https://chatterfix.com

---

## Architecture

```
ChatterFix/
├── main.py                 # FastAPI application
├── app/
│   ├── routers/           # API endpoints
│   ├── services/          # Business logic
│   ├── core/              # Database (Firestore)
│   └── templates/         # Jinja2 HTML
├── mobile/                # React Native app
├── AI_STATE.yaml          # Project state and decisions
└── scripts/               # Deployment and utilities
```

**Stack:** Python, FastAPI, Firebase/Firestore, React Native, Google Cloud Run

---

## Key Endpoints

| Endpoint | Description |
|----------|-------------|
| `/ai/voice` | Process voice commands |
| `/ai/chat` | AI assistant |
| `/work-orders` | Work order CRUD |
| `/assets` | Asset management |
| `/inventory/parts` | Parts inventory |

Full API docs at `/docs` when running locally.

---

## Deployment

Push to `main` triggers automatic deployment to Google Cloud Run.

Manual:
```bash
./deploy.sh direct
```

---

## Project State

This repo includes `AI_STATE.yaml` which records human-approved decisions and project state. This prevents rework and maintains continuity across development sessions.

---

## License

Dual license: Community (non-commercial) and Enterprise (commercial). See [LICENSE](LICENSE) for details.

---

## Contact

- Issues: [GitHub Issues](https://github.com/TheGringo-ai/Chatterfix/issues)
- Enterprise: enterprise@chatterfix.com

---

© 2024-2026 Fred Taylor. All Rights Reserved.
