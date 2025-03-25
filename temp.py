import speech_recognition as sr

recognizer = sr.Recognizer()
with sr.Microphone() as source:
    print("Say something...")
    audio = recognizer.listen(source, timeout=5)
    print("Captured audio. Processing...")

try:
    text = recognizer.recognize_google(audio)
    print(f"You said: {text}")
except sr.UnknownValueError:
    print("Could not understand audio.")
except sr.RequestError:
    print("Could not request results. Check internet connection.")
