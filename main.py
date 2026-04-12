# The loop. Start here to test each piece as you build it.
from listener import listen
from brain import chat, clear_history
from speaker import speak

if __name__ == "__main__":
    speak("Hi, I'm Emma.")
    goodbye_phrases = ["goodbye", "good bye", "exit", "quit"]
    reset_phrases = ["clear memory", "forget everything", "start fresh", "new conversation"]
    while True:
        user_message = listen()
        if not user_message.strip():
            continue
        compact = user_message.lower().replace(" ", "")
        if any(p.lower().replace(" ", "") in compact for p in goodbye_phrases):
            speak("Goodbye!")
            break
        if any(p.lower().replace(" ", "") in compact for p in reset_phrases):
            clear_history()
            speak("Okay, I've forgotten our earlier chat.")
            continue
        response = chat(user_message)
        speak(response)

        