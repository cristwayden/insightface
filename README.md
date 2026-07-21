# 🎭 InsightFace – Hệ thống Nhận diện Khuôn mặt & Chống Giả mạo

Máy chủ nhận diện khuôn mặt thời gian thực, xây dựng trên nền **FastAPI** + **InsightFace**, tích hợp **Anti-Spoofing (MiniFASNet)** để phát hiện tấn công bằng ảnh/video. Kiến trúc phân tầng rõ ràng, dễ mở rộng và bảo trì.

---

## ✨ Tính năng

| Tính năng | Mô tả |
|---|---|
| 🔍 **Nhận diện khuôn mặt** | Xác định người đã đăng ký qua webcam theo thời gian thực |
| 🛡️ **Anti-Spoofing** | Phát hiện khuôn mặt giả (ảnh in, màn hình, video phát lại) |
| 📝 **Đăng ký khuôn mặt** | Thêm người mới trực tiếp qua trình duyệt |
| 📊 **Log Viewer API** | Xem log server qua REST API |
| 🌐 **Giao diện Web** | Frontend HTML sẵn có, không cần cài ứng dụng |
| ⚙️ **Cấu hình linh hoạt** | Toàn bộ tham số đọc từ file `.env` |
| 🔑 **API Key (tùy chọn)** | Bảo vệ endpoint bằng API Key header |

---

## 📋 Yêu cầu hệ thống

| Thành phần | Phiên bản |
|---|---|
| Python | 3.9+ |
| OS | Windows / Linux / macOS |
| Camera | Bắt buộc để dùng Web UI |

---

## 🚀 Cài đặt

### 1. Clone repository

```bash
git clone https://github.com/cristwayden/insightface.git
cd insightface
```

### 2. Tạo môi trường ảo (khuyến nghị)

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Linux / macOS
source venv/bin/activate
```

### 3. Cài dependencies

```bash
pip install -r requirements.txt
```

> **Lưu ý:** `torch` và `torchvision` có thể mất vài phút để tải. Để dùng GPU, cài PyTorch phiên bản CUDA phù hợp tại [pytorch.org](https://pytorch.org/).

### 4. Cấu hình môi trường

```bash
# Sao chép file mẫu
copy .env.example .env   # Windows
cp .env.example .env     # Linux/macOS
```

Chỉnh sửa `.env` theo nhu cầu (xem phần [Cấu hình](#%EF%B8%8F-cấu-hình) bên dưới).

---

## ▶️ Khởi chạy Server

### Cách A — Script PowerShell (Windows, khuyến nghị)

Tự động kill process đang chiếm port 8000 trước khi khởi động:

```powershell
.\start_server.ps1
```

### Cách B — Chạy trực tiếp

```bash
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

Server sẽ khởi động tại `http://0.0.0.0:8000` và hiển thị:

```
============================================================
INSIGHTFACE API — ĐANG KHỞI ĐỘNG
============================================================
✅ InsightFace model tải xong.
✅ Anti-Spoofing model tải xong.
✅ SERVER SẴN SÀNG — Port: 8000 | Host: 0.0.0.0
============================================================
```

---

## 🌐 Giao diện Web

| URL | Mô tả |
|---|---|
| `http://localhost:8000/static/index.html` | **Máy quét** – nhận diện khuôn mặt qua webcam |
| `http://localhost:8000/static/register.html` | **Đăng ký** – thêm khuôn mặt mới vào hệ thống |
| `http://localhost:8000/docs` | **Swagger UI** – thử nghiệm API trực tiếp |

> **Truy cập từ thiết bị khác (cùng mạng LAN):** Thay `localhost` bằng IP máy chủ, ví dụ: `http://192.168.1.x:8000/static/index.html`

### Máy quét khuôn mặt

1. Mở `http://localhost:8000/static/index.html`
2. Cho phép truy cập camera
3. Nhấn **"Quét Khuôn Mặt"**
4. Kết quả hiển thị:
   - 🟢 **Xanh** – Người đã đăng ký, khuôn mặt thật
   - 🔴 **Đỏ** – Phát hiện giả mạo (ảnh/video)
   - 🟠 **Cam** – Không tìm thấy khuôn mặt

### Đăng ký khuôn mặt

1. Mở `http://localhost:8000/static/register.html`
2. Nhập tên nhân viên
3. Nhìn thẳng vào camera
4. Nhấn **"Chụp & Đăng Ký"**

---

## 📁 Cấu trúc Project

```
insightface/
├── app/
│   ├── main.py                        # Entry point FastAPI (Lifespan, CORS, Routes)
│   ├── api/
│   │   ├── deps.py                    # Dependency Injection providers
│   │   └── v1/
│   │       ├── router.py              # Gộp tất cả route v1
│   │       └── endpoints/
│   │           ├── recognize.py       # POST /api/v1/recognize
│   │           ├── register.py        # POST /api/v1/register
│   │           └── logs.py            # GET  /api/v1/logs
│   ├── core/
│   │   ├── config.py                  # Đọc .env (pydantic-settings)
│   │   ├── logging.py                 # RotatingFileHandler tập trung
│   │   └── security.py                # API Key authentication
│   ├── services/
│   │   ├── face_engine.py             # Singleton AI (InsightFace + Anti-Spoof)
│   │   └── db_service.py              # Thread-safe JSON database
│   └── schemas/
│       ├── recognize.py               # Pydantic response models
│       └── register.py                # Pydantic response models
│
├── static/
│   ├── index.html                     # Giao diện Nhận diện
│   └── register.html                  # Giao diện Đăng ký
│
├── data/                              # Dữ liệu khuôn mặt (tự tạo khi chạy)
│   ├── database.json                  # Embeddings đã lưu
│   └── *.jpg                          # Ảnh backup nhân viên
│
├── logs/                              # Log files (tự tạo khi chạy)
│   └── server.log                     # Rotating log (5 MB × 3 bản)
│
├── resources/
│   ├── anti_spoof_models/             # Weights MiniFASNet
│   └── detection_model/               # Weights face detection
│
├── src/                               # Anti-Spoofing library (Minivision)
│   ├── anti_spoof_predict.py
│   ├── generate_patches.py
│   └── utility.py
│
├── .env                               # Biến môi trường (không commit Git)
├── .env.example                       # Template cấu hình
├── requirements.txt
├── start_server.ps1                   # Script khởi động (Windows)
└── README.md
```

---

## 🔌 REST API

**Base URL:** `http://localhost:8000`  
**Swagger UI:** `http://localhost:8000/docs`

---

### `GET /`

Health check — kiểm tra server đang hoạt động.

**Response:**
```json
{
  "message": "InsightFace API đang hoạt động.",
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

Nhận diện khuôn mặt trong ảnh upload.

**Request:** `multipart/form-data`

| Trường | Kiểu | Mô tả |
|---|---|---|
| `file` | File | Ảnh JPEG/PNG chứa khuôn mặt |

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

| Trường | Mô tả |
|---|---|
| `name` | Tên người, hoặc `"Stranger"` nếu không khớp |
| `score` | Điểm tương đồng cosine (0–1) |
| `bbox` | Bounding box `[x1, y1, x2, y2]` |
| `is_real` | `true` = khuôn mặt thật, `false` = phát hiện giả mạo |
| `liveness_score` | Điểm Anti-Spoofing (0–1) |

---

### `POST /api/v1/register`

Đăng ký khuôn mặt mới vào hệ thống.

**Request:** `multipart/form-data`

| Trường | Kiểu | Mô tả |
|---|---|---|
| `name` | String | Tên nhân viên cần đăng ký |
| `file` | File | Ảnh chân dung |

**Response:**
```json
{
  "status": "success",
  "message": "Đăng ký thành công: Nguyen Van A"
}
```

---

### `GET /api/v1/logs`

Xem N dòng log gần nhất.

**Query params:**

| Tham số | Mặc định | Mô tả |
|---|---|---|
| `lines` | `100` | Số dòng log muốn lấy (1–5000) |

**Ví dụ:** `GET /api/v1/logs?lines=50`

**Response:**
```json
{
  "total_lines": 350,
  "returned_lines": 50,
  "log_file": "D:/InsightFace/logs/server.log",
  "recent_logs": ["2026-07-21 10:00:00 | INFO | ..."]
}
```

> **Backward compatibility:** Các URL cũ `/recognize`, `/register`, `/logs` vẫn hoạt động và sẽ tự động redirect sang `/api/v1/...`.

---

## ⚙️ Cấu hình

Chỉnh sửa file `.env` để thay đổi cấu hình mà không cần sửa code:

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
DET_SIZE=640             # Kích thước detection (pixel)
SIMILARITY_THRESHOLD=0.45  # Ngưỡng nhận diện (0.0 – 1.0)

# Bảo mật (để trống = không bắt API key)
# API_KEY=your_secret_key_here
```

### Bật API Key

Khi `API_KEY` được đặt trong `.env`, tất cả endpoint yêu cầu header:

```http
X-API-Key: your_secret_key_here
```

---

## 🗄️ Quản lý Database

Database được quản lý tự động:

- **Vị trí:** `data/database.json`
- **Auto-load:** Tải tất cả khuôn mặt đã đăng ký khi server khởi động
- **Auto-bootstrap:** Nếu `database.json` chưa tồn tại, server tự quét thư mục `data/` để đăng ký từ ảnh có sẵn (tên file = tên người)

**Nạp dữ liệu thủ công:**

1. Đặt ảnh vào thư mục `data/` với tên file là tên người (vd: `nguyen_van_a.jpg`)
2. Khởi động lại server — hệ thống tự đăng ký và tạo `database.json`

**Cập nhật khuôn mặt:** Đăng ký lại cùng tên sẽ **ghi đè** embedding cũ.

---

## 📝 Logging

| Thuộc tính | Giá trị |
|---|---|
| Vị trí | `logs/server.log` |
| Kích thước tối đa | 5 MB / file |
| Số bản lưu | 3 file |
| Console | INFO trở lên |
| File | DEBUG trở lên (chi tiết hơn) |

---

## 🛠️ Xử lý sự cố

| Vấn đề | Giải pháp |
|---|---|
| `uvicorn not recognized` | Dùng `python -m uvicorn ...` thay vì gọi trực tiếp |
| `ModuleNotFoundError: pydantic_settings` | Chạy `pip install pydantic-settings python-dotenv` |
| `Port 8000 already in use` | Chạy `.\start_server.ps1` — tự động kill process đang chiếm port |
| Không nhận diện được khuôn mặt | Tăng ánh sáng, nhìn thẳng camera, giảm `SIMILARITY_THRESHOLD` trong `.env` |
| `Spoofing detected` với mặt thật | Cải thiện ánh sáng hoặc chất lượng camera |
| Camera không mở trên trình duyệt | Truy cập qua `http://` (không phải `file://`) |
| Model không load | Kiểm tra `resources/anti_spoof_models/` và `resources/detection_model/` có đầy đủ file weight |

---

## 📄 License

Dự án phục vụ mục đích nghiên cứu và giáo dục.