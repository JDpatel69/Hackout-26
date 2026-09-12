# Algae Carbon Credit MRV — Backend

FastAPI backend for a **Measurement, Reporting & Verification (MRV)** marketplace focused on **algae-based carbon capture** (hackathon problem: IoT sensors + imagery → verified sequestration).

Built to pair with the glassmorphic multi-role frontend (farm operator, verifier, researcher, investor).

## Features

- JWT auth with 4 roles
- Farms, documents, verification pipeline, carbon credits, marketplace, portfolio
- IoT sensor ingestion (growth rate, CO₂ uptake, water quality, …)
- **Two AI model slots** (stubbed now, swap when training finishes):
  1. **Algae image model** — coverage, biomass, health, species from pond/drone/satellite images
  2. **Sensor verify model** — validates IoT streams, estimates sequestration, anomaly flags
- Dual-AI verify endpoint used before verifier approve
- Cross-role data consistency: approve → creates `CarbonProject` investors can buy

## Quick start

```bash
cd backend
python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS/Linux
# source .venv/bin/activate

pip install -r requirements.txt
copy .env.example .env   # or: cp .env.example .env

uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

- API docs: http://localhost:8000/docs  
- Health: http://localhost:8000/health  

## Demo accounts (password for all: `password123`)

| Role | Email |
|---|---|
| Farm Operator | `amina@greenalgae.co` |
| Farm Operator | `rajesh@aquacarbon.in` |
| Verifier | `elena@ecoaudit.org` |
| Researcher | `marcus@oceanlab.edu` |
| Investor | `sofia@impactvault.io` |

## AI models — how to plug in later

Both models run as **stubs** by default (`AI_*_MODEL_ENABLED=false`).

| Model | Stub class | Trained placeholder | Config flags |
|---|---|---|---|
| Image (algae) | `StubAlgaeImageModel` | `TrainedAlgaeImageModel` / `RemoteAlgaeImageModel` | `AI_IMAGE_MODEL_ENABLED`, `AI_IMAGE_MODEL_PATH`, `AI_IMAGE_MODEL_URL` |
| Sensor verify | `StubSensorVerifyModel` | `TrainedSensorVerifyModel` / `RemoteSensorVerifyModel` | `AI_SENSOR_MODEL_ENABLED`, `AI_SENSOR_MODEL_PATH`, `AI_SENSOR_MODEL_URL` |

**When weights are ready:**

1. Drop artifacts into `models/algae_image_model/` and/or `models/sensor_verify_model/`
2. Implement `load()` + `predict()` in the `Trained*` classes (`app/ai/…`)
3. Set the matching `AI_*_MODEL_ENABLED=true` in `.env`
4. Or point `AI_*_MODEL_URL` at a separate inference microservice

Routes stay the same — only the registry switches implementation.

### Key AI / IoT endpoints

| Method | Path | Purpose |
|---|---|---|
| GET | `/api/ai/status` | Stub vs trained vs remote |
| POST | `/api/iot/sensors` | Ingest one sensor reading |
| POST | `/api/iot/sensors/batch` | Batch ingest |
| GET | `/api/iot/sensors/{farm_id}` | List readings |
| POST | `/api/ai/image/analyze` | **Model 1** — algae image analysis |
| POST | `/api/ai/sensor/verify` | **Model 2** — sensor verification |
| POST | `/api/ai/dual-verify` | Run both + composite score |

## Main API map (frontend-aligned)

| Area | Prefix |
|---|---|
| Auth | `/api/auth/*` |
| Farms | `/api/farms/*` |
| Verifier | `/api/verifier/*` |
| Investor | `/api/investor/*` |
| Researcher | `/api/researcher/*` |
| Notifications | `/api/notifications/*` |
| IoT + AI | `/api/iot/*`, `/api/ai/*` |

## Project layout

```
backend/
├── app/
│   ├── main.py
│   ├── config.py
│   ├── database.py
│   ├── seed.py
│   ├── ai/                 # ← model contracts + stubs + registry
│   ├── api/routes/         # HTTP endpoints
│   ├── models/             # SQLAlchemy
│   ├── schemas/            # Pydantic (camelCase JSON)
│   ├── services/           # AI orchestration, notifications
│   └── utils/
├── models/                 # empty dirs for trained weights
├── requirements.txt
└── .env.example
```

## Frontend CORS

Default allowed origins: `http://localhost:5173`, `http://localhost:3000`  
Edit `CORS_ORIGINS` in `.env` if needed.

## Reset DB

Delete `mrv.db` and restart uvicorn — seed data reloads automatically.
