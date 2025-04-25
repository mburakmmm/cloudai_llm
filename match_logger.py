# match_logger.py
import json
import os
from datetime import datetime

LOG_FILE = "logs/match_log.json"

def log_match(memory_id, user_input):
    if not os.path.exists("logs"):
        os.makedirs("logs")

    log = []
    if os.path.exists(LOG_FILE):
        try:
            with open(LOG_FILE, "r", encoding="utf-8") as f:
                log = json.load(f)
        except json.JSONDecodeError:
            log = []

    log.append({
        "id": memory_id,
        "matched_input": user_input,
        "timestamp": datetime.now().isoformat()
    })

    with open(LOG_FILE, "w", encoding="utf-8") as f:
        json.dump(log, f, indent=4, ensure_ascii=False)

def get_matches_for_id(memory_id):
    if not os.path.exists(LOG_FILE):
        return []
    with open(LOG_FILE, "r", encoding="utf-8") as f:
        all_logs = json.load(f)
    return [entry for entry in all_logs if entry["id"] == memory_id]
