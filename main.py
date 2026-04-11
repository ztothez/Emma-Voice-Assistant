# The loop. Start here to test each piece as you build it.
from listener import listen
from brain import chat
from speaker import speak

if __name__ == "__main__":
    speak("Hello! I'm your assistant. How can I help you today?")
    goodbye_phrases = ["goodbye", "good bye", "exit", "quit"]
    while True:
        user_message = listen()
        if not user_message.strip():
            continue
        if any(phrase in user_message.lower().replace(" ", "") for phrase in goodbye_phrases):
            speak("Goodbye!")
            break
        response = chat(user_message)
        speak(response)