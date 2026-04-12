# Responsible for: capturing audio from mic, transcribing with Whisper
import os

import numpy as np
import sounddevice as sd
from faster_whisper import WhisperModel

SAMPLE_RATE = 16000  # higher rates = better quality but more CPU usage
DURATION = 10  # seconds

# Default "base" keeps the loop responsive on CPU. Use WHISPER_MODEL=small if you want accuracy over speed.
_WHISPER_NAME = os.environ.get("WHISPER_MODEL", "tiny").strip() or "base"
# "en" fixes language; use WHISPER_LANGUAGE=auto to let Whisper detect (e.g. Finnish + English).
_wh_lang = os.environ.get("WHISPER_LANGUAGE", "en").strip().lower()
WHISPER_LANGUAGE = None if _wh_lang in ("auto", "detect", "") else _wh_lang

# Optional vocabulary hint for accented English (slight extra decode cost). Off by default for speed.
_WHISPER_PROMPT = os.environ.get("WHISPER_INITIAL_PROMPT", "").strip()

model = WhisperModel(_WHISPER_NAME, device="cpu", compute_type="int8")


def record_audio():
    """Record audio from microphone and return as numpy array."""
    print("Listening...")
    frames = int(DURATION * SAMPLE_RATE)
    try:
        audio = sd.rec(frames, samplerate=SAMPLE_RATE, channels=1, dtype="float32")
        sd.wait()
    except sd.PortAudioError as e:
        print(f"Microphone error: {e}")
        return np.zeros((frames, 1), dtype=np.float32)
    return audio


def transcribe(audio: np.ndarray) -> str:
    """Transcribe audio array to text using Whisper."""
    audio = audio.squeeze()
    if audio.size == 0 or float(np.max(np.abs(audio))) < 1e-6:
        return ""

    kwargs: dict = {"beam_size": 5, "vad_filter": False}
    if _WHISPER_PROMPT:
        kwargs["initial_prompt"] = _WHISPER_PROMPT
    if WHISPER_LANGUAGE is not None:
        kwargs["language"] = WHISPER_LANGUAGE

    segments, _info = model.transcribe(audio, **kwargs)
    return " ".join(segment.text for segment in segments).strip()


def listen() -> str:
    """Full pipeline: record then transcribe. Returns text string."""
    try:
        audio = record_audio()
        text = transcribe(audio)
    except Exception as e:
        print(f"Listen error: {e}")
        return ""
    print(f"You said: {text}")
    return text
