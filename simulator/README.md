# OS4CSAPI UAV Data Simulator

A real-time UAV flythrough simulator that generates Line-of-Bearing (LOB)
observations, runs Weighted Least-Squares (WLS) triangulation, and publishes
location estimates to a [CSAPI](https://ogcapi.ogc.org/connectedsystems/)-compliant
server (e.g. [OpenSensorHub](https://opensensorhub.org/)).

## What It Does

The simulator models a small UAS flying a 14-waypoint route through a network
of three ground-based sensor nodes (MA-1, MA-2, MA-3). As the UAV enters each
node's detection envelope, the simulator:

1. **Publishes LOB observations** — bearing, std-dev, classification — to each
   detecting node's datastream.
2. **Runs a localizer** — polls the latest LOBs, correlates by classification
   and timestamp, computes a WLS bearing intersection, and publishes a
   location estimate (lat/lon, CEP50, contributing LOBs).
3. **Seeds detection ranges** — ensures each node's detection-capabilities
   datastream has a valid observation so map rings render correctly.

## Architecture

```
┌──────────────┐      POST /observations       ┌──────────────┐
│  Simulation  │ ─────────────────────────────► │              │
│  Worker      │   LOBs per detecting node      │   CSAPI      │
└──────────────┘                                │   Server     │
                                                │   (OSH)      │
┌──────────────┐      POST /observations       │              │
│  Localizer   │ ─────────────────────────────► │              │
│  Worker      │   location estimates           │              │
└──────────┬───┘                                └──────────────┘
           │  GET latest LOBs                          ▲
           └───────────────────────────────────────────┘

┌──────────────┐
│  FastAPI      │  /health  /status  /start  /stop  /clear  /reset
│  REST API     │
└──────────────┘
```

## Quick Start

### Prerequisites

- Python 3.12+
- A running CSAPI server with admin credentials
- The MA sensor nodes and localizer bootstrapped on the server
  (see `scripts/bootstrap_uas.py` and `scripts/bootstrap_localizer.py`)

### 1. Configure

```bash
cd simulator
cp .env.example .env
# Edit .env with your server details
```

### 2. Install Dependencies

```bash
python -m venv .venv
source .venv/bin/activate   # Linux/macOS
# .venv\Scripts\activate    # Windows

pip install -r requirements.txt
```

### 3. Run

```bash
# Source env vars
export $(grep -v '^#' .env | xargs)

# Start the API server
uvicorn main:app --host 127.0.0.1 --port 8000
```

The server starts at `http://127.0.0.1:8000`. Use the REST API to control
the simulation (see [API Endpoints](#api-endpoints) below).

### 4. Run (Docker)

```bash
docker build -t csapi-simulator .

docker run -d \
  -e OSH_ADDRESS=my-osh-server.example.com \
  -e OSH_USER=admin \
  -e OSH_PASS=secret \
  -p 8080:8080 \
  csapi-simulator
```

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/health` | Health check — returns server URL |
| `GET` | `/status` | Live telemetry snapshot (tick, UAV position, detecting nodes, counts) |
| `POST` | `/start` | Start simulation (accepts optional JSON body, see below) |
| `POST` | `/stop` | Stop a running simulation |
| `POST` | `/clear` | Delete sim/localizer observations (preserves detection ranges & SENREPs) |
| `POST` | `/reset` | Full demo reset — clears sim data, SENREPs, and track sampling features |

### POST /start — Request Body

All fields are optional with sensible defaults:

```json
{
  "duration_s": 3600,
  "interval_s": 5.0,
  "speed_kmh": 12.0,
  "start_offset_s": 0.0
}
```

| Field | Default | Description |
|-------|---------|-------------|
| `duration_s` | `3600` | How long the simulation runs (10–86400 s) |
| `interval_s` | `5.0` | Tick interval — time between LOB publications (1–60 s) |
| `speed_kmh` | `12.0` | UAV ground speed (1–100 km/h) |
| `start_offset_s` | `0.0` | Skip into route — start partway through the trajectory |

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `OSH_ADDRESS` | **Yes** | Server hostname, e.g. `my-osh-server.example.com` (no scheme, no path) |
| `OSH_USER` | **Yes** | SensorHub API username |
| `OSH_PASS` | **Yes** | SensorHub API password |

The simulator will **fail-fast on startup** if any of these are missing.

## Files

| File | Purpose |
|------|---------|
| `engine.py` | Core simulation logic — server config, geo math, HTTP helpers, observation & estimate builders, datastream discovery, WLS triangulation |
| `main.py` | FastAPI wrapper — `SimState`, simulation/localizer workers, observation clearing, REST endpoints |
| `Dockerfile` | Container build (Python 3.12-slim, uvicorn on port 8080) |
| `fly.toml` | Fly.io deployment config |
| `.env.example` | Environment variable template |
| `requirements.txt` | Python dependencies (FastAPI, uvicorn, pydantic) |

## Simulation Phases

The 14-waypoint trajectory is designed to exercise all detection states:

| Phase | Waypoints | Detecting Nodes |
|-------|-----------|-----------------|
| 1 — SW approach | 1–2 | None (outside all envelopes) |
| 2 — Enter MA-1 | 3–4 | MA-1 only |
| 3 — Dual detection | 5–6 | MA-1 + MA-2 |
| 4 — Triple detection | 7–9 | MA-1 + MA-2 + MA-3 |
| 5 — Exit MA-1 | 10–11 | MA-2 + MA-3 |
| 6 — Exit & clear | 12–14 | MA-3 → None |

The localizer begins producing location fixes in Phase 3 (≥ 2 bearings).

## Clearing Strategy

The simulator maintains a tiered clearing approach to protect data:

- **`/clear`** (Tier 2) — Deletes LOB and localizer observations only.
  Detection ranges are re-seeded. SENREPs and bootstrap data are untouched.
- **`/reset`** (Tier 3) — Full demo reset. Clears sim data plus all SENREP
  observations and track sampling features. Detection ranges are re-seeded.
- **Never touched** — ISS, NWS, NDBC, CO-OPS, and all other publisher data.

## Deployment

### systemd (Linux VM)

```ini
[Unit]
Description=CSAPI Data Simulator
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/simulator
Environment=OSH_ADDRESS=my-osh-server.example.com
Environment=OSH_USER=admin
Environment=OSH_PASS=secret
ExecStart=/home/ubuntu/simulator-venv/bin/uvicorn main:app --host 127.0.0.1 --port 8000
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

### Fly.io

Secrets are set via the Fly CLI:

```bash
fly secrets set OSH_ADDRESS=my-osh-server.example.com OSH_USER=admin OSH_PASS=secret
fly deploy
```

## Notes

- The simulator uses **stdlib `urllib`** only — no `requests` or `httpx` dependency.
- SSL verification is disabled (`CERT_NONE`) to support self-signed certs.
- HTTP requests include automatic retry with exponential backoff (5 attempts).
- The localizer embeds `contributingLobsJson` in each estimate so map
  consumers can render the exact bearing lines with zero temporal mismatch.
