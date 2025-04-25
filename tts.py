# tts.py
import pyttsx3
from settings import settings

engine = pyttsx3.init()
engine.setProperty('rate', 150)
engine.setProperty('volume', 1.0)

# Türkçe destekleyen bir ses bul ve uygula
for voice in engine.getProperty('voices'):
    if "tr" in voice.id or "turkish" in voice.name.lower():
        engine.setProperty('voice', voice.id)
        break

def speak(text):
    # Hem metin hem ses çıktısı veriyoruz
    print("🤖:", text)
    if settings.get("VOICE_ENABLED", False):
        engine.say(text)
        engine.runAndWait()
