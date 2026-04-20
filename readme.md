# Emma: local AI voice assistant

A **fully local** voice assistant: microphone → speech-to-text → LLM → text-to-speech, without sending your speech to a cloud API.

## Pipeline

```
Microphone → Whisper (STT) → Ollama (LLM) → Piper (TTS) → speakers
```

## Components

| Piece | File | Role |
|--------|------|------|
| Listener | [listener.py](listener.py) | Records mic audio, transcribes with faster-whisper |
| Brain | [brain.py](brain.py) | Calls Ollama’s chat API, persona rules, optional retry logic |
| Speaker | [speaker.py](speaker.py) | Piper TTS; plays audio (CLI loop) or exposes WAV bytes |
| Main loop | [main.py](main.py) | CLI conversation loop |
| Web UI | [web_app.py](web_app.py) | FastAPI + static UI; text chat and optional browser mic (needs **ffmpeg**) |
| Server STT | [server_stt.py](server_stt.py) | Decodes uploaded audio for the web UI |

Default Ollama model name is **`emma-qwen`** (set in `brain.py`). Use a **Qwen2.5 Instruct**–compatible GGUF plus the correct **Ollama `TEMPLATE`** (see below).

## Requirements

- **Python 3.10+**
- **[Ollama](https://ollama.com)** running locally (`ollama serve`)
- A **Piper** voice: `en_US-amy-medium.onnx` (+ matching `.onnx.json`) in the **project root** (or change `MODEL_PATH` in [speaker.py](speaker.py))
- For **web call mode**: **ffmpeg** on your `PATH`

## Install

```bash
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

## Ollama model (`emma-qwen`)

1. Put your **GGUF** next to a text **Modelfile** (example name `Emma.ModelFile`).

2. The Modelfile must include the **same `TEMPLATE` block** as the matching base instruct model, or chat formatting will be wrong. For Qwen2.5 1.5B instruct, copy the `TEMPLATE """ ... """` section from:

   ```bash
   ollama show qwen2.5:1.5b-instruct --modelfile
   ```

   Keep your own `FROM` (path to GGUF), `PARAMETER` lines, and `SYSTEM` for Emma.

3. Create / refresh the model:

   ```bash
   ollama create emma-qwen -f Emma.ModelFile
   ```

To try **stock** Qwen without a custom GGUF, pull e.g. `qwen2.5:1.5b-instruct` and temporarily set `MODEL_NAME` in [brain.py](brain.py) to that tag.

### Useful environment variables (optional)

| Variable | Purpose |
|----------|---------|
| `OLLAMA_READ_TIMEOUT` | Seconds for Ollama response (default `900`; first load on CPU can be slow) |
| `OLLAMA_CONNECT_TIMEOUT` | Connect timeout (default `90`) |
| `OLLAMA_KEEP_ALIVE` | e.g. `30m` — keeps the model loaded between turns |
| `OLLAMA_NUM_THREAD` | Thread count passed to Ollama |
| `WHISPER_MODEL` | Whisper size: `tiny` (default), `base`, `small`, … |
| `WHISPER_LANGUAGE` | `en` (default) or `auto` for detection |

## Piper voice

Download a voice from the [Piper samples](https://rhasspy.github.io/piper-samples/) page. Place **`en_US-amy-medium.onnx`** and **`en_US-amy-medium.onnx.json`** in the project root unless you change `MODEL_PATH` in [speaker.py](speaker.py).

## Run

**CLI (mic + speakers):**

```bash
python main.py
```

**Web UI:**

```bash
uvicorn web_app:app --host 127.0.0.1 --port 8765
```

Open [http://127.0.0.1:8765](http://127.0.0.1:8765).

## Using Emma

- Each listen window is **10 seconds** (see `DURATION` in [listener.py](listener.py)).
- Say **goodbye**, **exit**, or **quit** to stop the CLI loop.
- Say **clear memory**, **forget everything**, **start fresh**, or **new conversation** to wipe chat history (in-memory and `emma_history.json`).

Conversation context is stored in **`emma_history.json`** next to `brain.py` (gitignored).

## Fine-tuning / dataset (optional)

Training data should be JSON: a list of objects with a **`messages`** array of `{ "role": "system"|"user"|"assistant", "content": "..." }` turns (chat template compatible with Qwen2.5).

- See **[emma_dataset.example.json](emma_dataset.example.json)** for the shape.
- Full **`emma_dataset.json`**, **`*.gguf`**, and similar artifacts are listed in **`.gitignore`** so they are not committed by default.

Regenerate a dataset locally (if you keep a generator script under `scripts/`, that folder is typically ignored—run the script from your machine only).

## Dependencies (`requirements.txt`)

| Package | Role |
|---------|------|
| `faster-whisper` | Speech-to-text |
| `sounddevice` | Mic capture / playback |
| `numpy` | Audio buffers |
| `piper-tts` | Text-to-speech |
| `requests` | Ollama HTTP API |
| `fastapi`, `uvicorn`, `python-multipart` | Web UI and uploads |
