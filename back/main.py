from fastapi import FastAPI, WebSocket, HTTPException
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import os
from datetime import datetime
import logging
from pathlib import Path

app = FastAPI()

# Настройка CORS (для разработки)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Пути к статическим файлам React
BASE_DIR = Path(__file__).parent
STATIC_DIR = BASE_DIR / "static"

app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/", StaticFiles(directory="static", html=True), name="root")

FILE = "transcriptions.txt"
logging.basicConfig(level=logging.INFO)

def log_transcription(text: str):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_message = f"[{timestamp}] {text}\n"
    logging.info(log_message.strip())
    with open(FILE, "a", encoding="utf-8") as f:
        f.write(log_message)

@app.get("/", response_class=HTMLResponse)
async def serve_index():
    return FileResponse(STATIC_DIR / "index.html")

@app.post("/clear")
async def clear_transcriptions():
    try:
        if os.path.exists(FILE):
            os.remove(FILE)
        return {"status": "История очищена"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    
    try:
        while True:
            audio_data = await websocket.receive_bytes()
            text = f"Транскрибированный текст: {datetime.now().strftime('%H:%M:%S')}"
            await websocket.send_text(text)
            log_transcription(text)
                
    except Exception as e:
        logging.error(f"WebSocket error: {e}")
    finally:
        await websocket.close()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)