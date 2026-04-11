# brain.py
# Responsible for: sending messages to Ollama, keeping conversation history for context, and returning responses.
import requests
import json

OLLAMA_URL = "http://localhost:11434/api/chat"
MODEL_NAME = "qwen2.5:3b-instruct"

SYSTEM_PROMPT = (
    "You are a voice assistant called Emma. "
    "Keep responses within 1-3 sentences and do not repeat yourself or overexplain things. "
    "Do not use filler phrases or unnecessary introductions. "
    "Ensure responses are suitable for spoken output. "
    "Use English only. "
    "Be helpful and friendly, but prioritize clarity and efficiency. "
    "Respond in a natural, conversational manner. "
    "If you don't know the answer, say you don't know."
)

#conversation history keeps context across turns
conversation_history = [
    {"role": "system", "content": SYSTEM_PROMPT}
]

def chat(user_message: str) -> str:
    """Send a message, get a response, update history."""
    conversation_history.append({"role": "user", "content": user_message})

    payload = {
        "model": MODEL_NAME,
        "messages": conversation_history,
        "stream": False
    }

    response = requests.post(OLLAMA_URL, json=payload)
    reply = response.json()["message"]["content"]
    conversation_history.append({"role": "assistant", "content": reply})
    return reply