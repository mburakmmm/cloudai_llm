import os
from dotenv import load_dotenv
import streamlit as st

# .env dosyasını yükle (eğer varsa)
load_dotenv()

def get_env(key: str, default=None):
    """
    Ortam değişkenini .env veya Streamlit secrets'dan alır
    """
    # Önce Streamlit secrets'dan dene
    try:
        return st.secrets[key]
    except:
        # Eğer Streamlit secrets yoksa .env'den al
        return os.getenv(key, default)

# Supabase Credentials
SUPABASE_URL = get_env("SUPABASE_URL")
SUPABASE_KEY = get_env("SUPABASE_KEY")

# Model Settings
MODEL_PATH = get_env("MODEL_PATH", "models/")
MODEL_NAME = get_env("MODEL_NAME", "cloud_llm")
CONFIDENCE_THRESHOLD = float(get_env("CONFIDENCE_THRESHOLD", "0.7"))
MAX_CONTEXT_LENGTH = int(get_env("MAX_CONTEXT_LENGTH", "2000"))

# Logging
LOG_LEVEL = get_env("LOG_LEVEL", "INFO")

# Backup Settings
AUTO_BACKUP = get_env("AUTO_BACKUP", "True").lower() == "true"
BACKUP_FREQUENCY = get_env("BACKUP_FREQUENCY", "Günlük")

# Optional Settings
TTS_ENABLED = get_env("TTS_ENABLED", "False").lower() == "true"
DARK_MODE = get_env("DARK_MODE", "False").lower() == "true" 