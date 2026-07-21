# 🎭 InsightFace – Face Recognition & Anti-Spoofing System

Real-time face recognition server, built on **FastAPI** + **InsightFace**, integrated with **Anti-Spoofing (MiniFASNet)** to detect photo/video spoofing attacks. Clear layered architecture, easy to scale and maintain.

---

## ✨ Features

| Feature | Description |
|---|---|
| 🔍 **Face Recognition** | Identify registered users via webcam in real-time |
| 🛡️ **Anti-Spoofing** | Detect fake faces (printed photos, screens, replayed videos) |
| 📝 **Face Registration** | Add new users directly via browser |
| 📊 **Log Viewer API** | View server logs via REST API |
| 🌐 **Web Interface** | Built-in HTML frontend, no app installation required |
| ⚙️ **Flexible Configuration** | All parameters read from `.env` file |
| 🔑 **API Key (Optional)** | Protect endpoints with an API Key header |

---

## 📋 System Requirements

| Component | Version |
|---|---|
| Python | 3.9+ |
| OS | Windows / Linux / macOS |
| Camera | Required for Web UI |

---

## 🚀 Installation

### 1. Clone the repository

```bash
git clone https://github.com/cristwayden/insightface.git
cd insightface
```

### 2. Create a virtual environment (Recommended)

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Linux / macOS
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

> **Note:** `torch` and `torchvision` might take a few minutes to download. To use GPU, install the appropriate PyTorch CUDA version from [pytorch.org](https://pytorch.org/).

### 4. Configure environment

```bash
# Copy the template file
copy .env.example .env   # Windows
cp .env.example .env     # Linux/macOS
```

Edit `.env` according to your needs (see [Configuration](#%EF%B8%8F-configuration) below).

---

## ▶️ Start the Server

### Option A — PowerShell Script (Windows, recommended)

Automatically kills any process using port 8000 before starting:

```powershell
.\start_server.ps1
```

### Option B — Run directly

```bash
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

The server will start at `http://0.0.0.0:8000` and output:

```
============================================================
INSIGHTFACE API — STARTING UP
============================================================
✅ InsightFace model loaded.
✅ Anti-Spoofing model loaded.
✅ SERVER READY — Port: 8000 | Host: 0.0.0.0
============================================================
```

---

## 🌐 Web Interface

| URL | Description |
|---|---|
| `http://localhost:8000/static/index.html` | **Scanner** – recognize faces via webcam |
| `http://localhost:8000/static/register.html` | **Registration** – add new faces to the system |
| `http://localhost:8000/docs` | **Swagger UI** – test APIs directly |

> **Accessing from another device (same LAN):** Replace `localhost` with the server's IP, e.g., `http://192.168.1.x:8000/static/index.html`

### Face Scanner

1. Open `http://localhost:8000/static/index.html`
2. Allow camera access
3. Click **"Scan Face"**
4. Results:
   - 🟢 **Green** – Registered user, real face
   - 🔴 **Red** – Spoofing detected (photo/video)
   - 🟠 **Orange** – No face found

### Face Registration

1. Open `http://localhost:8000/static/register.html`
2. Enter the employee's name or ID
3. Look straight into the camera
4. Click **"Capture & Register"**

---

## 📁 Project Structure

```
insightface/
├── app/
│   ├── main.py                        # FastAPI entry point (Lifespan, CORS, Routes)
│   ├── api/
│   │   ├── deps.py                    # Dependency Injection providers
│   │   └── v1/
│   │       ├── router.py              # Aggregates all v1 routes
│   │       └── endpoints/
│   │           ├── recognize.py       # POST /api/v1/recognize
│   │           ├── register.py        # POST /api/v1/register
│   │           └── logs.py            # GET  /api/v1/logs
│   ├── core/
│   │   ├── config.py                  # Read .env (pydantic-settings)
│   │   ├── logging.py                 # Centralized RotatingFileHandler
│   │   └── security.py                # API Key authentication
│   ├── services/
│   │   ├── face_engine.py             # AI Singleton (InsightFace + Anti-Spoof)
│   │   └── db_service.py              # Thread-safe JSON database
│   └── schemas/
│       ├── recognize.py               # Pydantic response models
│       └── register.py                # Pydantic response models
│
├── static/
│   ├── index.html                     # Recognition UI
│   └── register.html                  # Registration UI
│
├── data/                              # Face data (auto-created at runtime)
│   ├── database.json                  # Saved embeddings
│   └── *.jpg                          # Employee backup images
│
├── logs/                              # Log files (auto-created at runtime)
│   └── server.log                     # Rotating log (5 MB × 3 backups)
│
├── resources/
│   ├── anti_spoof_models/             # MiniFASNet weights
│   └── detection_model/               # Face detection weights
│
├── src/                               # Anti-Spoofing library (Minivision)
│   ├── anti_spoof_predict.py
│   ├── generate_patches.py
│   └── utility.py
│
├── .env                               # Environment variables (ignored by Git)
├── .env.example                       # Configuration template
├── requirements.txt
├── start_server.ps1                   # Startup script (Windows)
└── README.md
```

---

## 🔌 REST API

**Base URL:** `http://localhost:8000`  
**Swagger UI:** `http://localhost:8000/docs`

---

### `GET /`

Health check — verify if the server is running.

**Response:**
```json
{
  "message": "InsightFace API is running.",
  "version": "2.0.0",
  "endpoints": {
    "recognize": "POST /api/v1/recognize",
    "register":  "POST /api/v1/register",
    "logs":      "GET  /api/v1/logs",
    "frontend":  "GET  /static/index.html"
  }
}
```

---

### `POST /api/v1/recognize`

Recognize faces in an uploaded image.

**Request:** `multipart/form-data`

| Field | Type | Description |
|---|---|---|
| `file` | File | JPEG/PNG image containing faces |

**Response:**
```json
{
  "status": "success",
  "faces": [
    {
      "name": "Nguyen Van A",
      "score": 0.923,
      "bbox": [120, 80, 300, 320],
      "is_real": true,
      "liveness_score": 0.971
    }
  ]
}
```

| Field | Description |
|---|---|
| `name` | Person's name, or `"Stranger"` if no match |
| `score` | Cosine similarity score (0–1) |
| `bbox` | Bounding box `[x1, y1, x2, y2]` |
| `is_real` | `true` = real face, `false` = spoofing detected |
| `liveness_score` | Anti-Spoofing score (0–1) |

---

### `POST /api/v1/register`

Register a new face into the system.

**Request:** `multipart/form-data`

| Field | Type | Description |
|---|---|---|
| `name` | String | Employee name or ID to register |
| `file` | File | Portrait image |

**Response:**
```json
{
  "status": "success",
  "message": "Registration successful: Nguyen Van A"
}
```

---

### `GET /api/v1/logs`

View the most recent N lines of logs.

**Query params:**

| Parameter | Default | Description |
|---|---|---|
| `lines` | `100` | Number of log lines to retrieve (1–5000) |

**Example:** `GET /api/v1/logs?lines=50`

**Response:**
```json
{
  "total_lines": 350,
  "returned_lines": 50,
  "log_file": "D:/InsightFace/logs/server.log",
  "recent_logs": ["2026-07-21 10:00:00 | INFO | ..."]
}
```

> **Backward compatibility:** Legacy URLs (`/recognize`, `/register`, `/logs`) still work and will automatically redirect to `/api/v1/...`.

---

## ⚙️ Configuration

Edit the `.env` file to change configuration without modifying code:

```env
# Server
APP_HOST=0.0.0.0
APP_PORT=8000

# Logging
LOG_LEVEL=DEBUG          # DEBUG | INFO | WARNING | ERROR

# Paths
DATA_DIR=data
RESOURCES_DIR=resources
ANTI_SPOOF_MODELS_DIR=resources/anti_spoof_models
DB_FILE=data/database.json

# Face Recognition
INSIGHTFACE_MODEL=buffalo_l
DET_SIZE=640             # Detection size (pixels)
SIMILARITY_THRESHOLD=0.45  # Recognition threshold (0.0 – 1.0)

# Security (leave empty = no API key required)
# API_KEY=your_secret_key_here
```

### Enabling API Key

When `API_KEY` is set in `.env`, all endpoints will require a header:

```http
X-API-Key: your_secret_key_here
```

---

## 🗄️ Database Management

The database is managed automatically:

- **Location:** `data/database.json`
- **Auto-load:** Loads all registered faces when the server starts
- **Auto-bootstrap:** If `database.json` does not exist, the server automatically scans the `data/` directory to register available images (filename = person's name)

**Manual Data Entry:**

1. Place an image in the `data/` directory with the filename as the person's name (e.g., `nguyen_van_a.jpg`)
2. Restart the server — the system will automatically register it and create `database.json`

**Updating a Face:** Re-registering with the same name will **overwrite** the old embedding.

---

## 📝 Logging

| Property | Value |
|---|---|
| Location | `logs/server.log` |
| Max Size | 5 MB / file |
| Backups | 3 files |
| Console | INFO and above |
| File | DEBUG and above (more detailed) |

---

## 🛠️ Troubleshooting

| Issue | Solution |
|---|---|
| `uvicorn not recognized` | Use `python -m uvicorn ...` instead of calling it directly |
| `ModuleNotFoundError: pydantic_settings` | Run `pip install pydantic-settings python-dotenv` |
| `Port 8000 already in use` | Run `.\start_server.ps1` — it automatically kills the process using the port |
| Cannot recognize face | Increase lighting, look straight into the camera, reduce `SIMILARITY_THRESHOLD` in `.env` |
| `Spoofing detected` on a real face | Improve lighting or camera quality |
| Camera doesn't open in browser | Access via `http://` (not `file://`) |
| Model fails to load | Check if `resources/anti_spoof_models/` and `resources/detection_model/` contain all weight files |

---

## 📄 License
