import io
import wave
import numpy as np
import sounddevice as sd
from piper import PiperVoice

MODEL_PATH = "en_US-amy-medium.onnx"
voice = PiperVoice.load(MODEL_PATH)

def speak(text: str):
    buffer = io.BytesIO()
    with wave.open(buffer, "wb") as wav_out:
        voice.synthesize_wav(text, wav_out)
    buffer.seek(0)
    with wave.open(buffer, "rb") as wav_file:
        sample_rate = wav_file.getframerate()
        frames = wav_file.readframes(wav_file.getnframes())
    audio_data = np.frombuffer(frames, dtype=np.int16)
    sd.play(audio_data, sample_rate)
    sd.wait()