import cv2
import numpy as np
from fastapi import FastAPI, File, UploadFile, Form, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from insightface.app import FaceAnalysis
import io
import json
from PIL import Image
import os
import warnings
import logging
import logging.handlers
from datetime import datetime

from src.anti_spoof_predict import AntiSpoofPredict
from src.generate_patches import CropImage
from src.utility import parse_model_name

warnings.filterwarnings('ignore')

# ============================================================
# LOGGING SYSTEM CONFIGURATION
# ============================================================
LOG_DIR = "logs"
LOG_FILE = os.path.join(LOG_DIR, "server.log")

if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR)

# Log format
log_formatter = logging.Formatter(
    fmt="%(asctime)s | %(levelname)-8s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

# Handler to write to FILE (rotating: 5MB per file, keep 3 backups)
file_handler = logging.handlers.RotatingFileHandler(
    LOG_FILE, maxBytes=5 * 1024 * 1024, backupCount=3, encoding="utf-8"
)
file_handler.setFormatter(log_formatter)
file_handler.setLevel(logging.DEBUG)

# Handler to print to CONSOLE
console_handler = logging.StreamHandler()
console_handler.setFormatter(log_formatter)
console_handler.setLevel(logging.INFO)

# Main logger
logger = logging.getLogger("InsightFace")
logger.setLevel(logging.DEBUG)
logger.addHandler(file_handler)
logger.addHandler(console_handler)
# ============================================================

app_api = FastAPI(title="Face Recognition API")

logger.info("="*60)
logger.info("FACE RECOGNITION API SYSTEM STARTING")
logger.info(f"Log file: {os.path.abspath(LOG_FILE)}")
logger.info("="*60)

# Configure CORS so Web/App can call the API without being blocked
app_api.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Allow all origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 1. Initialize InsightFace model
logger.info("Loading InsightFace AI model, please wait...")
app_insight = FaceAnalysis(name='buffalo_l', providers=['CPUExecutionProvider'])
app_insight.prepare(ctx_id=0, det_size=(640, 640))
logger.info("✅ InsightFace model loaded successfully")

# Initialize Anti-Spoofing model
logger.info("Loading Anti-Spoofing model...")
anti_spoof_model = AntiSpoofPredict(device_id=0)
image_cropper = CropImage()
logger.info("✅ Anti-Spoofing model loaded successfully")

# 2. Simulated database list to store information
known_face_embeddings = []
known_face_names = []

def register_user(name, image_path):
    """Register a user's face information"""
    img = cv2.imread(image_path)
    if img is None:
        print(f"❌ Image not found at: {image_path}")
        return
    
    faces = app_insight.get(img)
    if len(faces) == 0:
        print(f"❌ No face found in image: {image_path}")
    else:
        embedding = faces[0].embedding
        known_face_embeddings.append(embedding)
        known_face_names.append(name)
        print(f"✅ Face registered successfully for: {name}")

data_dir = "data"
db_file = os.path.join(data_dir, "database.json")

def load_database():
    global known_face_embeddings, known_face_names
    if os.path.exists(db_file):
        logger.info(f"Loading data from {db_file}...")
        with open(db_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            known_face_names = data.get("names", [])
            known_face_embeddings = [np.array(emb, dtype=np.float32) for emb in data.get("embeddings", [])]
        logger.info(f"✅ Loaded {len(known_face_names)} faces from database.")
        return True
    return False

def save_database():
    with open(db_file, 'w', encoding='utf-8') as f:
        data = {
            "names": known_face_names,
            "embeddings": [emb.tolist() for emb in known_face_embeddings]
        }
        json.dump(data, f, ensure_ascii=False, indent=4)

# --- AUTO LOAD DATA ---
if not os.path.exists(data_dir):
    os.makedirs(data_dir)

if not load_database():
    logger.warning(f"No database file found. Scanning '{data_dir}' directory to create new one...")
    for filename in os.listdir(data_dir):
        if filename.lower().endswith(('.png', '.jpg', '.jpeg')):
            name = os.path.splitext(filename)[0]
            image_path = os.path.join(data_dir, filename)
            register_user(name, image_path)
    if len(known_face_names) > 0:
        save_database()

def compute_similarity(emb1, emb2):
    return np.dot(emb1, emb2) / (np.linalg.norm(emb1) * np.linalg.norm(emb2))

def match_face(target_embedding, threshold=0.45):
    if len(known_face_embeddings) == 0:
        return "Stranger", 0.0

    similarities = [compute_similarity(target_embedding, db_emb) for db_emb in known_face_embeddings]
    max_idx = np.argmax(similarities)
    max_score = float(similarities[max_idx])

    if max_score >= threshold:
        return known_face_names[max_idx], max_score
    return "Stranger", max_score

@app_api.post("/recognize")
async def recognize_face(request: Request, file: UploadFile = File(...)):
    client_ip = request.client.host
    start_time = datetime.now()
    logger.info(f"[RECOGNIZE] Request from IP: {client_ip} | File: {file.filename}")

    try:
        # Read image data sent by client
        contents = await file.read()
        image = Image.open(io.BytesIO(contents)).convert('RGB')
        img_np = np.array(image)
        # Convert RGB to BGR for cv2 / InsightFace
        img_bgr = img_np[:, :, ::-1].copy()

        # Recognition
        faces = app_insight.get(img_bgr)
        logger.debug(f"[RECOGNIZE] Detected {len(faces)} face(s) in image")
        
        results = []
        for face in faces:
            bbox = face.bbox.astype(int).tolist()
            embedding = face.embedding
            name, score = match_face(embedding)
            
            # Check Liveness (Anti-Spoofing)
            image_bbox = [bbox[0], bbox[1], bbox[2] - bbox[0], bbox[3] - bbox[1]] # convert [x1, y1, x2, y2] to [x, y, w, h]
            prediction = np.zeros((1, 3))
            models_dir = "resources/anti_spoof_models"
            model_names = os.listdir(models_dir)
            for model_name in model_names:
                h_input, w_input, model_type, scale = parse_model_name(model_name)
                param = {
                    "org_img": img_bgr,
                    "bbox": image_bbox,
                    "scale": scale,
                    "out_w": w_input,
                    "out_h": h_input,
                    "crop": True,
                }
                if scale is None:
                    param["crop"] = False
                img_crop = image_cropper.crop(**param)
                prediction += anti_spoof_model.predict(img_crop, os.path.join(models_dir, model_name))
            
            label = np.argmax(prediction)
            value = prediction[0][label] / len(model_names) # Average score
            is_real = bool(label == 1)

            # Log result for each face
            liveness_tag = "REAL" if is_real else "⚠ FAKE"
            logger.info(
                f"[RECOGNIZE] IP: {client_ip} | Name: {name} | "
                f"Match: {score:.4f} | Liveness: {value:.4f} | Status: {liveness_tag}"
            )
            if not is_real:
                logger.warning(
                    f"[SECURITY] SPOOFING DETECTED! IP: {client_ip} | "
                    f"Fake name: {name} | Liveness: {value:.4f}"
                )
            
            results.append({
                "name": name,
                "score": float(score),
                "bbox": bbox, # [x1, y1, x2, y2]
                "is_real": is_real,
                "liveness_score": float(value)
            })

        if len(faces) == 0:
            logger.info(f"[RECOGNIZE] IP: {client_ip} | No faces found")

        elapsed = (datetime.now() - start_time).total_seconds()
        logger.debug(f"[RECOGNIZE] Completed in {elapsed:.3f}s")

        return JSONResponse(content={"status": "success", "faces": results})
        
    except Exception as e:
        logger.error(f"[RECOGNIZE] ERROR from IP {client_ip}: {str(e)}", exc_info=True)
        return JSONResponse(content={"status": "error", "message": str(e)}, status_code=500)

@app_api.post("/register")
async def register_new_face(request: Request, name: str = Form(...), file: UploadFile = File(...)):
    client_ip = request.client.host
    logger.info(f"[REGISTER] Registration request from IP: {client_ip} | Name: '{name}'")

    try:
        contents = await file.read()
        image = Image.open(io.BytesIO(contents)).convert('RGB')
        img_np = np.array(image)
        img_bgr = img_np[:, :, ::-1].copy()

        faces = app_insight.get(img_bgr)
        if len(faces) == 0:
            logger.warning(f"[REGISTER] IP: {client_ip} | Name: '{name}' | FAILED: no face found")
            return JSONResponse(content={"status": "error", "message": "No face found in the image for registration"})
        
        # Take only the largest or first face
        embedding = faces[0].embedding
        known_face_embeddings.append(embedding)
        known_face_names.append(name)
        
        # Update JSON database file
        save_database()
        
        # Save image to data directory for future runs
        if not os.path.exists(data_dir):
            os.makedirs(data_dir)
        save_path = os.path.join(data_dir, f"{name}.jpg")
        cv2.imwrite(save_path, img_bgr)

        total = len(known_face_names)
        logger.info(f"[REGISTER] ✅ Registration successful | Name: '{name}' | IP: {client_ip} | Total DB: {total} person(s)")
        
        return JSONResponse(content={"status": "success", "message": f"Successfully registered: {name}"})
        
    except Exception as e:
        logger.error(f"[REGISTER] ERROR from IP {client_ip} | Name: '{name}' | {str(e)}", exc_info=True)
        return JSONResponse(content={"status": "error", "message": str(e)}, status_code=500)

@app_api.get("/")
def read_root():
    return {"message": "Face Recognition API system is running. Send POST to /recognize to scan."}

@app_api.get("/logs")
def get_log_summary():
    """Return the last 100 log lines"""
    if not os.path.exists(LOG_FILE):
        return {"logs": []}
    with open(LOG_FILE, "r", encoding="utf-8") as f:
        lines = f.readlines()
    return {"total_lines": len(lines), "recent_logs": lines[-100:]}

if __name__ == "__main__":
    logger.info("--- SERVER SYSTEM READY ---")
    logger.info("Port: 8000 | Address: 0.0.0.0")
    uvicorn.run(app_api, host="0.0.0.0", port=8000)
