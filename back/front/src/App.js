import React from "react";
import VoiceRecorder from "./components/VoiceRecorder";
import "./App.css"; // Подключите CSS

function App() {
  return (
    <div className="App">
      <div className="App-header">
        <div className="title-container">
          <h1 className="title-text">Voice Recorder</h1>
        </div>
        <VoiceRecorder />
      </div>
    </div>
  );
}

export default App;