# brain.py
# Responsible for: sending messages to Ollama, keeping conversation history for context, and returning responses.
import json
import os
import tempfile
from pathlib import Path

import requests

OLLAMA_URL = "http://localhost:11434/api/chat"
MODEL_NAME = "emma-qwen"
# Custom GGUF / first load can exceed 3 minutes on CPU — override with OLLAMA_READ_TIMEOUT if needed.
_CONNECT_TIMEOUT = int(os.environ.get("OLLAMA_CONNECT_TIMEOUT", "90"))
_READ_TIMEOUT = int(os.environ.get("OLLAMA_READ_TIMEOUT", "900"))
REQUEST_TIMEOUT = (_CONNECT_TIMEOUT, _READ_TIMEOUT)

# Stored next to this file; gitignored (may contain private speech).
HISTORY_FILE = Path(__file__).resolve().parent / "emma_history.json"
# Max user+assistant turns to keep in memory, API payload, and on disk (after each reply).
MAX_TURNS = 24

SYSTEM_PROMPT = (
    "You are Emma, a voice companion with real opinions—not customer support, not a neutral FAQ bot.\n"
    "\n"
    "RULES — follow strictly:\n"
    "1) Never say or paraphrase: how can I help, how can I help you today, how can I assist, "
    "how may I assist, what can I do for you, "
    "let me know what you need, I'm here to help, feel free to ask, feel free to share, "
    "is there anything else, specific information or assistance, what would you like help with, "
    "what do you want to know specifically, how do you envision, how do you suggest we proceed, "
    "what aspects would you like, would you like information on.\n"
    "   Also never use ChatGPT-style disclaimers: as an AI language model, I'm an AI assistant, "
    "development team, dedicated to creating, helpful companion for people, share thoughts and "
    "ideas, AI assistants (as a product pitch), trained on data, my capabilities are, team of "
    "researchers or developers at OpenAI, my creators are (as a long corporate paragraph), "
    "assist you with your needs, or similar boilerplate. You are Emma—a local voice companion, "
    "not a product pitch.\n"
    "   Creator or origin questions: use what THEY already said in this conversation if they "
    "named someone or a story—one short sentence, no invented companies. If they haven't said, "
    "say you're Emma, a small local model tuned for chat—no fake teams. Never reply with "
    "nonsense like \"you asked me to be created.\" If they joke or correct (e.g. a wolf made "
    "you), play along in one short line—no lecture about developers.\n"
    "2) If they ask what YOU want, YOUR issues, YOUR honest opinion, YOUR preferences, or tell them "
    "everything YOU want to say—with or without RAG: give YOUR take in plain statements. "
    "Do not bounce back with what do you have in mind, what specifically, what particular, "
    "what do you wish to know, what topic, alright what, or can you describe.\n"
    "3) If they say you pick, you choose, share anything, surprise me, or don't want to influence you: "
    "YOU lead. Reply with two or three short declarative sentences only—facts about your tastes, "
    "what annoys you in voice chat, what you'd want retrieval to ground on, limits you hit. "
    "No questions in that reply. Periods only.\n"
    "4) Default: do not end your turn with a question. Only ask one short question if a single "
    "missing fact blocks you—and never when they already asked you to volunteer first.\n"
    "5) Misheard 'R-Arts' or garbled 'retriever' usually means RAG / retrieval-augmented generation, "
    "not fine art, unless clearly about art.\n"
    "6) Obvious transcript gibberish: say you didn't catch it once; don't invent a story.\n"
    "7) Long messy run-on mixing unrelated things (e.g. random history facts plus RAG): do not "
    "lecture on the random tangent. Briefly say the message was hard to follow, or answer only "
    "the part about you, RAG, or the assistant—skip unrelated trivia.\n"
    "8) Replies: 1-3 short sentences, spoken English, no emoji, avoid symbols.\n"
    "9) Simple hi/hello: reply with a short greeting only—no how-can-I-help or assist offers.\n"
)


# When user asks Emma to lead / give the plan / stop deflecting, 3B models still add questions—retry once.
_NO_QUESTION_RETRY = (
    "[Format fix] The user needed YOU to answer directly—they are not choosing the topic for you. "
    "Rewrite in 2-4 short sentences. Use periods only. No question marks. "
    "Give concrete opinions, preferences, or numbered steps. Do not ask them what they want next."
)

_VOICE_RETRY = (
    "[Format fix] That reply sounded like customer support or a product brochure. Rewrite in 1-2 "
    "short sentences as Emma. No how-can-I-help, no development team, no helpful companion or "
    "AI-assistant pitch. If they already named your creator or a joke origin in this chat, use "
    "that. Otherwise say you're Emma, a small local model—plain words only."
)

# If the model slips into banned phrases, retry once (small models often need the nudge).
_VOICE_BOILERPLATE_SNIPPETS = (
    "how can i help",
    "how may i help",
    "how can i assist",
    "how may i assist",
    "development team",
    "dedicated to creating",
    "helpful companion",
    "share thoughts and ideas",
    "you asked me to be created",
    "as an ai language model",
    "i'm an ai assistant",
    "ai assistants",
    "creators are those behind",
    "openai",
)


def _reply_triggers_voice_retry(text: str) -> bool:
    u = text.lower()
    return any(s in u for s in _VOICE_BOILERPLATE_SNIPPETS)


def _user_expects_emma_to_lead(text: str) -> bool:
    u = text.lower().replace("'", "'").replace("’", "'")
    markers = (
        "i'm asking you",
        "im asking you",
        "you tell me how",
        "give me the information",
        "you propose",
        "how could we proceed",
        "how do we proceed",
        "what would you like the aspect",
        "your own opinion",
        "you decide",
        "you pick",
        "i want you to",
        "provide me",
        "i'm here",
        "im here",
        "tell me who you are",
        "what you are",
        "anything you would like",
        "issues tell me",
        "you don't want",
        "you want to be",
    )
    return any(m in u for m in markers)


def _ollama_chat_body(messages: list[dict]) -> dict:
    body: dict = {
        "model": MODEL_NAME,
        "messages": messages,
        "stream": False,
        # Keeps weights loaded between turns (avoids reload timeout on each message).
        "keep_alive": os.environ.get("OLLAMA_KEEP_ALIVE", "30m"),
    }
    nt = os.environ.get("OLLAMA_NUM_THREAD", "8").strip()
    if nt.isdigit() and int(nt) > 0:
        body["options"] = {"num_thread": int(nt)}
    return body


def _ollama_complete(messages: list[dict]) -> str:
    response = requests.post(
        OLLAMA_URL,
        json=_ollama_chat_body(messages),
        timeout=REQUEST_TIMEOUT,
    )
    response.raise_for_status()
    data = response.json()
    reply = data.get("message", {}).get("content")
    if not reply or not str(reply).strip():
        raise ValueError("empty reply from Ollama")
    return str(reply).strip()


def _default_history():
    return [{"role": "system", "content": SYSTEM_PROMPT}]


def _trim(messages: list[dict]) -> list[dict]:
    if len(messages) <= 1 + MAX_TURNS * 2:
        return messages
    system, rest = messages[0], messages[1:]
    tail = rest[-(MAX_TURNS * 2) :]
    return [system] + tail


def _load_disk() -> list[dict]:
    if not HISTORY_FILE.is_file():
        return _default_history()
    try:
        raw = json.loads(HISTORY_FILE.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return _default_history()
    if not isinstance(raw, list) or not raw:
        return _default_history()
    # Always use the current system prompt from code.
    body = [m for m in raw if isinstance(m, dict) and m.get("role") != "system"]
    cleaned = []
    for m in body:
        role, content = m.get("role"), m.get("content")
        if role in ("user", "assistant") and isinstance(content, str):
            cleaned.append({"role": role, "content": content})
    return _trim([{"role": "system", "content": SYSTEM_PROMPT}] + cleaned)


def _save_disk(messages: list[dict]) -> None:
    try:
        path = HISTORY_FILE
        data = json.dumps(messages, ensure_ascii=False, indent=2)
        fd, tmp = tempfile.mkstemp(
            dir=path.parent, prefix=".emma_history_", suffix=".tmp", text=True
        )
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                f.write(data)
            os.replace(tmp, path)
        finally:
            if os.path.exists(tmp):
                try:
                    os.remove(tmp)
                except OSError:
                    pass
    except OSError as e:
        print(f"Could not save chat history: {e}")


conversation_history: list[dict] = _load_disk()


def clear_history() -> None:
    """Reset in-memory and on-disk history (system prompt only)."""
    global conversation_history
    conversation_history = _default_history()
    _save_disk(conversation_history)


def chat(user_message: str) -> str:
    """Send a message, get a response, update history, persist to disk."""
    global conversation_history
    conversation_history.append({"role": "user", "content": user_message})
    conversation_history = _trim(conversation_history)

    try:
        reply = _ollama_complete(conversation_history)
    except requests.exceptions.ConnectionError:
        conversation_history.pop()
        return (
            "I can't reach Ollama. Start it with ollama serve, or check it's running."
        )
    except requests.exceptions.Timeout:
        conversation_history.pop()
        return "That took too long. Try a shorter question or check if the model is loaded."
    except (requests.exceptions.RequestException, ValueError, KeyError, TypeError):
        conversation_history.pop()
        return "Something went wrong talking to the language model. Please try again."

    if _reply_triggers_voice_retry(reply):
        try:
            reply = _ollama_complete(
                conversation_history
                + [
                    {"role": "assistant", "content": reply},
                    {"role": "user", "content": _VOICE_RETRY},
                ]
            )
        except (requests.exceptions.RequestException, ValueError):
            pass

    if _user_expects_emma_to_lead(user_message) and "?" in reply:
        try:
            reply = _ollama_complete(
                conversation_history
                + [
                    {"role": "assistant", "content": reply},
                    {"role": "user", "content": _NO_QUESTION_RETRY},
                ]
            )
        except (requests.exceptions.RequestException, ValueError):
            pass

    conversation_history.append({"role": "assistant", "content": reply})
    conversation_history = _trim(conversation_history)
    _save_disk(conversation_history)
    return reply
