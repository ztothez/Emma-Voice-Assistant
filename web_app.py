"""
Emma web UI — serves a small frontend and proxies chat to Ollama via brain.py.

Run (from project root, venv active):
  uvicorn web_app:app --host 127.0.0.1 --port 8765

Open: http://127.0.0.1:8765
Call mode needs ffmpeg on PATH (browser sends webm; server decodes + Whisper + Piper).
"""
import subprocess
from pathlib import Path

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.concurrency import run_in_threadpool
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, Response
from pydantic import BaseModel, Field

from brain import chat, clear_history, conversation_history
from server_stt import transcribe_uploaded_audio
from speaker import synthesize_wav_bytes

STATIC = Path(__file__).resolve().parent / "static"

app = FastAPI(title="Emma")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class ChatIn(BaseModel):
    message: str = Field(..., min_length=1, max_length=8000)


class TTSIn(BaseModel):
    text: str = Field(..., min_length=1, max_length=8000)


@app.get("/")
async def index():
    path = STATIC / "index.html"
    if not path.is_file():
        raise HTTPException(404, "static/index.html missing")
    return FileResponse(path)


@app.post("/api/chat")
async def api_chat(body: ChatIn):
    text = body.message.strip()
    if not text:
        raise HTTPException(400, "empty message")
    reply = await run_in_threadpool(chat, text)
    return {"reply": reply}


@app.post("/api/history/clear")
async def api_clear():
    await run_in_threadpool(clear_history)
    return {"ok": True}


@app.get("/api/history")
async def api_history():
    return {"messages": list(conversation_history)}


def _transcribe_job(raw: bytes, filename: str | None) -> str:
    return transcribe_uploaded_audio(raw, filename)


@app.post("/api/transcribe")
async def api_transcribe(file: UploadFile = File(...)):
    raw = await file.read()
    if len(raw) < 64:
        raise HTTPException(400, "audio too short")
    try:
        text = await run_in_threadpool(_transcribe_job, raw, file.filename)
    except subprocess.CalledProcessError:
        raise HTTPException(400, "could not decode audio (try recording again)")
    except RuntimeError as e:
        raise HTTPException(503, str(e))
    return {"text": text}


@app.post("/api/tts")
async def api_tts(body: TTSIn):
    def _tts():
        return synthesize_wav_bytes(body.text)

    try:
        wav = await run_in_threadpool(_tts)
    except Exception as e:
        raise HTTPException(500, f"tts failed: {e}") from e
    if not wav:
        raise HTTPException(400, "empty text")
    return Response(content=wav, media_type="audio/wav")
