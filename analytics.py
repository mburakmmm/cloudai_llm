# analytics.py
from memory_sqlite import SQLiteMemoryManager
from collections import defaultdict

def get_intent_summary():
    db = SQLiteMemoryManager()
    memory = db.load_memory()
    counter = defaultdict(int)
    for item in memory:
        counter[item.get("intent", "genel")] += 1
    return dict(counter)

def get_important_learnings(top_n=10):
    db = SQLiteMemoryManager()
    memory = db.load_memory()
    sorted_items = sorted(
        memory,
        key=lambda x: (x.get("usage_count", 0) * 2 + x.get("priority", 1)),
        reverse=True
    )
    return sorted_items[:top_n]

def get_unused_high_priority(threshold_priority=3):
    db = SQLiteMemoryManager()
    memory = db.load_memory()
    unused = []
    for item in memory:
        if item.get("priority", 1) >= threshold_priority and item.get("usage_count", 0) == 0:
            unused.append(item)
    return unused
