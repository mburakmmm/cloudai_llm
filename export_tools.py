# export_tools.py
import json
import csv
from memory_sqlite import SQLiteMemoryManager

def export_training_json(path="training_export.json"):
    db = SQLiteMemoryManager()
    memory = db.load_memory()
    with open(path, "w", encoding="utf-8") as f:
        json.dump(memory, f, indent=4, ensure_ascii=False)

def export_training_csv(path="training_export.csv"):
    db = SQLiteMemoryManager()
    memory = db.load_memory()
    if memory:
        keys = list(memory[0].keys())
        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=keys)
            writer.writeheader()
            writer.writerows(memory)
