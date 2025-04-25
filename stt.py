import sounddevice as sd
import numpy as np
import queue
import sys
import json

MODEL_PATH = "vosk_models/tr/vosk-model-small-tr-0.3"

def listen_and_transcribe():
    # Vosk modelini devre dışı bırakıp sadece metin girişi kullanıyoruz
    print("Lütfen mesajınızı yazın (çıkmak için 'q' yazın):")
    text = input("> ")
    if text.lower() == 'q':
        sys.exit(0)
    return text