import io
import os
import wave

import numpy as np
import sounddevice as sd
from piper import PiperVoice

MODEL_PATH = "en_US-amy-medium.onnx"
if not os.path.isfile(MODEL_PATH):
    raise FileNotFoundError(
        f"Missing Piper voice model: {MODEL_PATH!r} (need .onnx in project root)"
    )
voice = PiperVoice.load(MODEL_PATH)


def synthesize_wav_bytes(text: str) -> bytes:
    """Return a full WAV file as bytes (for HTTP responses). Empty input -> empty bytes."""
    if not text or not str(text).strip():
        return b""
    buffer = io.BytesIO()
    with wave.open(buffer, "wb") as wav_out:
        voice.synthesize_wav(text.strip(), wav_out)
    return buffer.getvalue()


def speak(text: str):
    if not text or not str(text).strip():
        return
    try:
        raw = synthesize_wav_bytes(text)
        if not raw:
            return
        bio = io.BytesIO(raw)
        with wave.open(bio, "rb") as wav_file:
            sample_rate = wav_file.getframerate()
            frames = wav_file.readframes(wav_file.getnframes())
        audio_data = np.frombuffer(frames, dtype=np.int16)
        sd.play(audio_data, sample_rate)
        sd.wait()
    except sd.PortAudioError as e:
        print(f"Speaker error: {e}")
    except Exception as e:
        print(f"Speech output failed: {e}")