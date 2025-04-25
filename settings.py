# settings.py
import json
import os

SETTINGS_FILE = "settings.json"

# Varsayılan ayarlar
DEFAULT_SETTINGS = {
    "TTS_ENABLED": False,
    "STT_ENABLED": False,
    "THEME_MODE": "dark",
    "LANGUAGE": "tr",
    "DEBUG_MODE": False,
    "LOGGING_LEVEL": "WARNING",
    "TTS_VOICE": "tr-TR-Standard-A",  # Google Cloud TTS sesi
    "TTS_PITCH": 0,  # Normal pitch
    "TTS_SPEAKING_RATE": 1.0,  # Normal hız
}

# Ayarları yükle
def load_settings():
    try:
        if os.path.exists(SETTINGS_FILE):
            with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                return {**DEFAULT_SETTINGS, **json.load(f)}
        return DEFAULT_SETTINGS.copy()
    except Exception as e:
        print(f"Ayarlar yüklenirken hata oluştu: {str(e)}")
        return DEFAULT_SETTINGS.copy()

# Ayarları kaydet
def save_settings():
    try:
        with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
            json.dump(settings, f, indent=4, ensure_ascii=False)
    except Exception as e:
        print(f"Ayarlar kaydedilirken hata oluştu: {str(e)}")

# Global settings nesnesi
settings = load_settings()
