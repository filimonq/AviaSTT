import { useState, useRef, useEffect } from "react";
import { Button } from "./ui/button";
import { Card, CardContent } from "./ui/card";
import { Mic, Square } from "lucide-react";
import "./VoiceRecorder.css";

export default function VoiceRecorder() {
  const [isRecording, setIsRecording] = useState(false);
  const [logs, setLogs] = useState([]);
  const [history, setHistory] = useState([]);
  const mediaRecorderRef = useRef(null);
  const audioStreamRef = useRef(null);
  const websocketRef = useRef(null);

  // Fetch history data from the server
  const fetchHistory = async () => {
    try {
      const res = await fetch("http://localhost:8000/history");
      const data = await res.json();
      setHistory(data);
    } catch (err) {
      console.error("Error fetching history:", err);
    }
  };

  useEffect(() => {
    fetchHistory();
    return () => {
      // Clean up on unmount
      if (websocketRef.current) {
        websocketRef.current.close();
      }
      if (audioStreamRef.current) {
        audioStreamRef.current.getTracks().forEach((track) => track.stop());
      }
    };
  }, []);

  // Start recording and opening websocket connection
  const startRecording = async () => {
    try {
      audioStreamRef.current = await navigator.mediaDevices.getUserMedia({ audio: true });

      websocketRef.current = new WebSocket("ws://localhost:8000/ws");

      websocketRef.current.onopen = () => {
        console.log("WebSocket connected");
      };

      websocketRef.current.onmessage = (event) => {
        setLogs((prevLogs) => [...prevLogs, event.data]);
        fetchHistory(); // This can be optimized to avoid unnecessary fetching
      };

      websocketRef.current.onerror = (error) => {
        console.error("WebSocket error:", error);
      };

      websocketRef.current.onclose = () => {
        console.log("WebSocket connection closed");
        setIsRecording(false); // Останавливаем запись при закрытии соединения
      };

      mediaRecorderRef.current = new MediaRecorder(audioStreamRef.current);
      mediaRecorderRef.current.ondataavailable = (event) => {
        if (event.data.size > 0 && websocketRef.current?.readyState === WebSocket.OPEN) {
          websocketRef.current.send(event.data);
        }
      };

      mediaRecorderRef.current.onstop = () => {
        if (websocketRef.current?.readyState === WebSocket.OPEN) {
          websocketRef.current.send("STOP"); // Отправляем сообщение о завершении записи
        }
      };

      mediaRecorderRef.current.start(1000); // Start recording with chunks of 1 second
      setIsRecording(true);
    } catch (error) {
      console.error("Error accessing microphone:", error);
      alert("Please allow microphone access.");
    }
  };

  // Stop recording and close connections
  const stopRecording = () => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop();
    }
    if (audioStreamRef.current) {
      audioStreamRef.current.getTracks().forEach((track) => track.stop());
    }
    setIsRecording(false);
  };

  // Clear data endpoint call
  const clearData = async () => {
    try {
      const response = await fetch("http://localhost:8000/clear", { method: "POST" });
      if (response.ok) {
        setLogs([]);
        fetchHistory();
      } else {
        console.error("Error clearing data");
      }
    } catch (err) {
      console.error("Error clearing data:", err);
    }
  };

  return (
    <Card className="card">
      <CardContent className="card-content">
        <div className="recorder-container">
          <div className="recorder-circle">
            <div className={`recorder-circle-background ${isRecording ? "recording" : "idle"}`}></div>
            <Button
              variant={isRecording ? "destructive" : "default"}
              size="icon"
              className="recorder-button"
              onClick={isRecording ? stopRecording : startRecording}
            >
              {isRecording ? <Square className="h-6 w-6" /> : <Mic className="h-6 w-6" />}
            </Button>
          </div>
        </div>
        <div className={`recorder-status ${isRecording ? "recording" : "idle"}`}>
          {isRecording ? "Recording..." : "Press the microphone to start recording"}
        </div>
        <div style={{ marginTop: "20px" }}>
          <Button onClick={clearData} className="save-button">Clear Data (Save to History)</Button>
        </div>
        <div style={{ marginTop: "20px" }}>
          <h3>Logs:</h3>
          <div style={{ border: "1px solid #ccc", padding: "10px", height: "150px", overflowY: "auto" }}>
            {logs.map((log, idx) => (
              <div key={idx}>{log}</div>
            ))}
          </div>
        </div>
        <div style={{ marginTop: "20px" }}>
          <h3>History (Last 5):</h3>
          <ul>
            {history.map((item, idx) => (
              <li key={idx}>{item}</li>
            ))}
          </ul>
        </div>
      </CardContent>
    </Card>
  );
}