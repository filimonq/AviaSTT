from fastapi import FastAPI, WebSocket, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import os
import glob
from datetime import datetime

app = FastAPI()

# Настройка CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Монтирование статических файлов
app.mount("/static", StaticFiles(directory="static"), name="static")

# Инициализация папок
HISTORY_DIR = "history"
AUDIO_DIR = "audio"
MAX_HISTORY = 5

def init_dirs():
    if not os.path.exists(HISTORY_DIR):
        os.makedirs(HISTORY_DIR)
    if not os.path.exists(AUDIO_DIR):
        os.makedirs(AUDIO_DIR)

def log_transcription(text: str):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_message = f"[{timestamp}] {text}\n"
    print(log_message, end='')
    with open("current_session.txt", "a", encoding="utf-8") as f:
        f.write(log_message)

def archive_session():
    if os.path.exists("current_session.txt"):
        session_id = int(datetime.now().timestamp())
        os.rename("current_session.txt", f"{HISTORY_DIR}/{session_id}.txt")
    
    files = sorted(glob.glob(f"{HISTORY_DIR}/*.txt"), key=os.path.getctime)
    while len(files) > MAX_HISTORY:
        os.remove(files.pop(0))

def save_audio(data: bytes):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    file_path = f"{AUDIO_DIR}/{timestamp}.wav"
    with open(file_path, "wb") as f:
        f.write(data)
    return file_path

@app.get("/", response_class=HTMLResponse)
async def serve_index():
    try:
        with open("static/index.html", "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Index.html not found")

@app.post("/clear")
async def clear_transcriptions():
    try:
        archive_session()
        return {"status": "История сохранена, текущая сессия очищена"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/history")
async def get_history():
    init_dirs()
    files = sorted(glob.glob(f"{HISTORY_DIR}/*.txt"), reverse=True)[:MAX_HISTORY]
    return [os.path.basename(f).split(".")[0] for f in files]

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    init_dirs()
    
    try:
        while True:
            audio_chunk = await websocket.receive_bytes()
            file_path = save_audio(audio_chunk)
            text = f"Аудио сохранено: {file_path}"
            await websocket.send_text(text)
            log_transcription(text)
    except Exception as e:
        print(f"Ошибка: {e}")
    finally:
        await websocket.close()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)