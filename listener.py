# Responsible for: capturing audio from mic, transcribing with Whisper
import sounddevice as sd
import numpy as np
from faster_whisper import WhisperModel

SAMPLE_RATE = 16000 #higher rates = better quality but more CPU usage
DURATION = 10  # seconds 
model = WhisperModel("base", device="cpu", compute_type="int8")

# Functions to capture and transcribe audio. In a real app, you'd want to handle edge cases, errors, and maybe do some VAD to only capture when someone is speaking.
def record_audio():
    """Record audio from microphone and return as numpy array."""
    print("Listening...")
    audio = sd.rec(int(DURATION * SAMPLE_RATE), samplerate=SAMPLE_RATE, channels=1, dtype='float32')
    sd.wait()
    return audio

def transcribe(audio: np.ndarray) -> str:
    """Transcribe audio array to text using Whisper."""
    audio = audio.squeeze()
    segments, info = model.transcribe(audio, language="en")
    return " ".join(segment.text for segment in segments)

def listen() -> str:
    """Full pipeline: record then transcribe. Returns text string."""
    audio = record_audio()
    text = transcribe(audio)
    print(f"You said: {text}")
    return text