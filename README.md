# 🎭 InsightFace – Face Recognition & Anti-Spoofing System

A real-time face recognition server built with **FastAPI** + **InsightFace**, featuring **liveness detection (anti-spoofing)** to prevent photo/video attacks.

---

## ✨ Features

- 🔍 **Face Recognition** – Identify registered faces in real time via webcam
- 🛡️ **Anti-Spoofing (Liveness Detection)** – Detect fake faces from photos or screens
- 📝 **Face Registration** – Register new faces directly through the browser
- 📊 **Log Viewer** – Access recent server logs via REST API
- 🌐 **Web UI** – Browser-based interface, no app installation required

---

## 📋 Requirements

| Requirement | Version |
|---|---|
| Python | 3.9+ |
| OS | Windows / Linux / macOS |
| Camera | Required for web UI |

---

## 🚀 Installation

### 1. Clone the repository

```bash
git clone https://github.com/cristwayden/insightface.git
cd insightface
```

### 2. Create a virtual environment (recommended)

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

> **Note:** `torch` and `torchvision` may take several minutes to download. For GPU support, install the appropriate CUDA version of PyTorch from [pytorch.org](https://pytorch.org/).

---

## ▶️ Starting the Server

### Option A – Using PowerShell script (Windows, recommended)

The script automatically kills any process occupying port 8000 before starting:

```powershell
.\start_server.ps1
```

### Option B – Run directly with Python

```bash
python server.py
```

Once started, the server listens at:

```
http://0.0.0.0:8000
```

You will see output similar to:

```
============================================================
FACE RECOGNITION API SYSTEM STARTING
============================================================
Loading InsightFace AI model, please wait...
✅ InsightFace model loaded successfully
Loading Anti-Spoofing model...
✅ Anti-Spoofing model loaded successfully
--- SERVER SYSTEM READY ---
Port: 8000 | Address: 0.0.0.0
```

---

## 🌐 Web Interface

Open the HTML files in your browser **after** the server is running:

| File | Description |
|---|---|
| `index.html` | **Face Scanner** – scan faces via webcam in real time |
| `register.html` | **Face Registration** – register new faces into the database |

> **Tip:** If accessing from a different device on the same network, replace `127.0.0.1` in the browser URL with the server machine's IP address (e.g., `http://192.168.1.x:8000`).

### Face Scanner (`index.html`)

1. Open `index.html` in your browser
2. Allow camera access when prompted
3. Click **"Quét Khuôn Mặt"** (Scan Face)
4. The result will display:
   - ✅ **Green** – Recognized person (real face)
   - 🔴 **Red** – Spoofing detected (fake/photo face)
   - 🟠 **Orange** – No face found

### Face Registration (`register.html`)

1. Open `register.html` in your browser
2. Enter the person's name in the input field
3. Look directly at the camera
4. Click **"Chụp & Đăng Ký"** (Capture & Register)
5. A success message confirms the face was saved

---

## 📁 Project Structure

```
InsightFace/
├── server.py               # FastAPI server – main application
├── start_server.ps1        # PowerShell startup script (Windows)
├── requirements.txt        # Python dependencies
├── index.html              # Web UI – face scanner
├── register.html           # Web UI – face registration
│
├── data/                   # Face database (auto-created)
│   ├── database.json       # Stored face embeddings & names
│   └── *.jpg               # Registered face images
│
├── logs/                   # Server log files (auto-created)
│   └── server.log          # Rotating log (5 MB × 3 backups)
│
├── resources/
│   ├── anti_spoof_models/  # Anti-spoofing model weights
│   └── detection_model/    # Face detection model weights
│
└── src/
    ├── anti_spoof_predict.py
    ├── generate_patches.py
    └── utility.py
```

---

## 🔌 REST API Reference

Base URL: `http://localhost:8000`

### `GET /`

Health check – confirms the server is running.

**Response:**
```json
{
  "message": "Face Recognition API system is running. Send POST to /recognize to scan."
}
```

---

### `POST /recognize`

Detect and recognize faces in an uploaded image.

**Request:** `multipart/form-data`

| Field | Type | Description |
|---|---|---|
| `file` | File | Image file (JPEG/PNG) |

**Response:**
```json
{
  "status": "success",
  "faces": [
    {
      "name": "Nguyen Van A",
      "score": 0.92,
      "bbox": [120, 80, 300, 320],
      "is_real": true,
      "liveness_score": 0.97
    }
  ]
}
```

| Field | Description |
|---|---|
| `name` | Recognized name, or `"Stranger"` if not in database |
| `score` | Similarity score (0–1). Higher = more confident match |
| `bbox` | Bounding box `[x1, y1, x2, y2]` |
| `is_real` | `true` = real face, `false` = spoofing detected |
| `liveness_score` | Anti-spoofing confidence (0–1) |

---

### `POST /register`

Register a new face into the database.

**Request:** `multipart/form-data`

| Field | Type | Description |
|---|---|---|
| `name` | String | Name to associate with the face |
| `file` | File | Image file containing the face |

**Response:**
```json
{
  "status": "success",
  "message": "Successfully registered: Nguyen Van A"
}
```

---

### `GET /logs`

Retrieve the last 100 lines from the server log.

**Response:**
```json
{
  "total_lines": 250,
  "recent_logs": ["2026-07-21 10:00:00 | INFO     | ...", "..."]
}
```

---

## 🗄️ Database Management

The face database is automatically managed:

- **Location:** `data/database.json`
- **Auto-load:** On startup, the server loads all registered faces
- **Auto-build:** If `database.json` doesn't exist, the server scans the `data/` folder for any `.jpg`/`.png` images and auto-registers them using the filename as the person's name

**To pre-populate the database manually:**

1. Place image files named after the person (e.g., `john_doe.jpg`) into the `data/` folder
2. Restart the server – it will auto-register all images and create `database.json`

---

## 📝 Logging

Logs are stored in the `logs/` directory with automatic rotation:

- **File:** `logs/server.log`
- **Max size:** 5 MB per file
- **Backups:** 3 files retained
- **Console:** INFO level and above
- **File:** DEBUG level and above (more verbose)

---

## 🛠️ Troubleshooting

| Problem | Solution |
|---|---|
| `Port 8000 already in use` | Run `.\start_server.ps1` – it auto-kills the blocking process |
| `No face found` during registration | Ensure good lighting, look directly at the camera, and use a clear photo |
| `Spoofing detected` on a real face | Try better lighting or increase camera quality |
| Camera not opening in browser | Ensure you are accessing via `http://` (not `file://`) when on a remote device |
| Models not loading | Verify the `resources/anti_spoof_models/` and `resources/detection_model/` directories contain the required model files |

---

## 📄 License

This project is for research and educational purposes.