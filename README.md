# Algae Carbon Credit MRV Platform

Hackathon project: monitor algae farms with **IoT sensors + imagery**, verify carbon sequestration, and list credits for investors.

| Part | Status | Location |
|---|---|---|
| **Backend (your role)** | Done | [`backend/`](./backend) |
| Frontend | Spec provided — not built here | — |

## Backend quick start

```bash
cd backend
python -m venv .venv
.\.venv\Scripts\activate          # Windows
pip install -r requirements.txt
copy .env.example .env
uvicorn app.main:app --reload --port 8000
```

Open http://localhost:8000/docs

Demo password for all seeded users: `password123`

See [`backend/README.md`](./backend/README.md) for API map and how to plug in the two AI models when training finishes.
