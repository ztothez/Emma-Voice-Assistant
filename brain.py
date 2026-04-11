# brain.py
# Responsible for: sending messages to Ollama, keeping conversation history

import requests
import json

OLLAMA_URL = "http://localhost:11434/api/chat"
MODEL_NAME = "qwen2.5:3b-instruct"

# conversation history keeps context across turns
# Ollama expects a list of {"role": "...", "content": "..."} dicts
conversation_history = [
    {"role": "system", "content": "You are a voice assistant."}
]

SYSTEM_PROMPT = (
    "You are a voice assistant called Emma. Keep responses within a few sentences and dont repeat yourself or overexplain things, "
    "suitable for spoken output. Use english language only for the conversations. Always be helpful and friendly towards the user. "
    "Respond to the user's queries in a conversational manner. If you don't know the answer, say you don't know."
)


def chat(user_message: str) -> str:
    """Send a message, get a response, update history."""
    conversation_history.append({"role": "user", "content": user_message})

    # TODO: build the request payload
    # hint: Ollama /api/chat expects:
    # {"model": MODEL_NAME, "messages": [...], "stream": False}
    # prepend your SYSTEM_PROMPT as {"role": "system", "content": ...}
    payload = # build this dict

    # TODO: POST to OLLAMA_URL, parse the response
    # hint: response.json()["message"]["content"] is the reply text
    response = pass

    # TODO: append assistant response to conversation_history
    # TODO: return the response text string
    pass