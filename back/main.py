from fastapi import FastAPI, WebSocket, HTTPException
from fastapi.websockets import WebSocketDisconnect, WebSocketState
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import os
import glob
from datetime import datetime
import whisper

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:8000", "http://localhost:8000"],  # Укажите адреса фронтенда
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

# Загрузка модели Whisper
model = whisper.load_model("base")

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
    audio_buffer = bytearray()

    try:
        while True:
            print("start")
            message = await websocket.receive()
            
            if "text" in message:
                print(message["text"])
                if message["text"] == "STOP":
                    break
            elif "bytes" in message:
                audio_buffer.extend(message["bytes"])
    except WebSocketDisconnect:
        print("WebSocket был отключен.")
    except Exception as e:
        print(f"Ошибка приема данных: {e}")
    finally:
        temp_filename = "temp_recording.wav"
        try:
            # Сохраняем аудио во временный файл
            with open(temp_filename, "wb") as f:
                f.write(audio_buffer)
            
            # Транскрибируем аудио с помощью Whisper
            try:
                result = model.transcribe(temp_filename)
                transcription = result.get("text", "").strip()
            except Exception as e:
                transcription = f"Ошибка распознавания: {e}"

            # Отправляем результат клиенту, если соединение все еще открыто
            if websocket.client_state == WebSocketState.CONNECTED:
                await websocket.send_text(transcription)
                log_transcription(transcription)
        except Exception as e:
            print(f"Ошибка при обработке аудио: {e}")
        finally:
            # Удаляем временный файл
            if os.path.exists(temp_filename):
                os.remove(temp_filename)
            # Пробуем закрыть соединение только если оно еще открыто
            if websocket.client_state == WebSocketState.CONNECTED:
                await websocket.close()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)