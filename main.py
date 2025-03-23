from fastapi import FastAPI, WebSocket, HTTPException
from fastapi.responses import HTMLResponse
import os
import glob
from datetime import datetime
import whisper

app = FastAPI()
HISTORY_DIR = "history"
MAX_HISTORY = 5

from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

model = whisper.load_model("base")

def init_history():
    if not os.path.exists(HISTORY_DIR):
        os.makedirs(HISTORY_DIR)

def log_transcription(text: str):
    log_message = f"{text}\n"
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

@app.post("/clear")
async def clear_transcriptions():
    try:
        archive_session()
        return {"status": "История сохранена, текущая сессия очищена"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/")
async def get():
    return HTMLResponse("""
        <html>
            <body>
                <button onclick="startRecording()" id="startBtn">Start</button>
                <button onclick="stopRecording()" id="stopBtn" disabled>Stop</button>
                <button onclick="clearHistory()">Clear</button>
                
                <div id="history" style="margin: 20px; border: 1px solid #ccc; padding: 10px;">
                    <h3>Последние 5 записей:</h3>
                    <div id="historyList"></div>
                </div>
                
                <div id="output" style="margin: 20px;"></div>

                <script>
                    let ws;
                    let mediaRecorder;
                    let audioStream;

                    async function updateHistory() {
                        const res = await fetch("/history");
                        const history = await res.json();
                        document.getElementById("historyList").innerHTML = history
                            .map(file => `<div>${file}</div>`)
                            .join("");
                    }

                    async function startRecording() {
                        try {
                            // Запрос доступа к микрофону
                            audioStream = await navigator.mediaDevices.getUserMedia({ audio: true });
                            
                            document.getElementById("startBtn").disabled = true;
                            document.getElementById("stopBtn").disabled = false;
                            
                            ws = new WebSocket("ws://" + window.location.host + "/ws");
                            
                            ws.onmessage = (event) => {
                                document.getElementById("output").innerHTML += event.data + "<br>";
                                updateHistory();
                            };

                            mediaRecorder = new MediaRecorder(audioStream);
                            mediaRecorder.ondataavailable = (e) => {
                                if (e.data.size > 0 && ws.readyState === WebSocket.OPEN) {
                                    // Отправляем бинарные данные на сервер
                                    ws.send(e.data);
                                }
                            };
                            
                            mediaRecorder.start(500);
                        } catch (err) {
                            alert("Разрешите доступ к микрофону!");
                        }
                    }

                    function stopRecording() {
                        // Останавливаем запись и отправляем специальное сообщение "STOP"
                        mediaRecorder?.stop();
                        audioStream?.getTracks().forEach(track => track.stop());
                        if (ws && ws.readyState === WebSocket.OPEN) {
                            ws.send("STOP");
                        }
                        document.getElementById("startBtn").disabled = false;
                        document.getElementById("stopBtn").disabled = true;
                    }

                    async function clearHistory() {
                        await fetch("/clear", { method: "POST" });
                        updateHistory();
                        document.getElementById("output").innerHTML = "";
                    }

                    // Загружаем историю при старте
                    updateHistory();
                </script>
            </body>
        </html>
    """)

@app.get("/history")
async def get_history():
    files = sorted(glob.glob(f"{HISTORY_DIR}/*.txt"), reverse=True)[:MAX_HISTORY]
    return [os.path.basename(f).split(".")[0] for f in files]

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    init_history()
    audio_buffer = bytearray()
    try:
        while True:
            message = await websocket.receive()
            if "text" in message:
                if message["text"] == "STOP":
                    break
            elif "bytes" in message:
                audio_buffer.extend(message["bytes"])
    except Exception as e:
        print(f"Ошибка приема данных: {e}")
    finally:
        temp_filename = "temp_recording.wav"
        try:
            with open(temp_filename, "wb") as f:
                f.write(audio_buffer)
            try:
                result = model.transcribe(temp_filename)
                transcription = result.get("text", "").strip()
            except Exception as e:
                transcription = f"Ошибка распознавания: {e}"
            await websocket.send_text(transcription)
            log_transcription(transcription)
        finally:
            if os.path.exists(temp_filename):
                os.remove(temp_filename)
            await websocket.close()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
