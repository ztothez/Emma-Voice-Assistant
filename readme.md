# AI Voice Assistant

A local, fully offline voice assistant named **Emma**. Speak to her, she listens, thinks, and talks back all running on your machine.

## How it works

```
Microphone → Whisper (STT) → Ollama / qwen2.5 (LLM) → Piper (TTS) → Speakers
```

| Module | File | Responsibility |
|---|---|---|
| Listener | [listener.py](listener.py) | Records mic audio and transcribes it with Whisper |
| Brain | [brain.py](brain.py) | Sends transcribed text to Ollama and maintains conversation history |
| Speaker | [speaker.py](speaker.py) | Synthesizes the response to audio with Piper TTS and plays it |
| Main loop | [main.py](main.py) | Ties everything together in a continuous conversation loop |

## Requirements

- [Ollama](https://ollama.com) running locally with the `qwen2.5:3b-instruct` model pulled
- A Piper TTS voice model (`.onnx` + `.onnx.json`) in the project root
- Python 3.10+

## Setup

1. **Install dependencies**

   ```bash
   pip install -r requirements.txt
   ```

2. **Pull the Ollama model**

   ```bash
   ollama pull qwen2.5:3b-instruct
   ```

3. **Download a Piper voice model**

   Get a voice from the [Piper samples page](https://rhasspy.github.io/piper-samples/) and place the `.onnx` and `.onnx.json` files in the project root. The default voice is `en_US-amy-medium`.

   To use a different voice, update `MODEL_PATH` in [speaker.py](speaker.py).

4. **Run**

   ```bash
   python main.py
   ```

## Usage

- Emma greets you on startup
- Speak during the 10-second recording window
- Say **"goodbye"**, **"exit"**, or **"quit"** to end the session
- Conversation history is kept in memory for context across turns

## Dependencies

| Package | Purpose |
|---|---|
| `faster-whisper` | Speech-to-text transcription |
| `sounddevice` | Mic recording and audio playback |
| `numpy` | Audio buffer handling |
| `piper-tts` | Text-to-speech synthesis |
| `requests` | HTTP calls to the Ollama API |
