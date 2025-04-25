# intent_optimizer.py
from sentence_transformers import SentenceTransformer, util
from collections import defaultdict
from memory_sqlite import SQLiteMemoryManager

model = SentenceTransformer("all-MiniLM-L6-v2")

# Gruplar = benzer intent'e sahip kayıtlar

def suggest_intent_clusters(threshold=0.8):
    db = SQLiteMemoryManager()
    memory = db.load_memory()
    groups = []
    used = set()

    for i, item_i in enumerate(memory):
        if item_i['intent'] in used:
            continue
        current_group = [item_i['intent']]
        emb_i = model.encode(item_i['intent'], convert_to_tensor=True)

        for j in range(i + 1, len(memory)):
            item_j = memory[j]
            if item_j['intent'] in used or item_j['intent'] == item_i['intent']:
                continue
            emb_j = model.encode(item_j['intent'], convert_to_tensor=True)
            sim = float(util.pytorch_cos_sim(emb_i, emb_j))
            if sim >= threshold:
                current_group.append(item_j['intent'])
                used.add(item_j['intent'])

        if len(current_group) > 1:
            used.update(current_group)
            groups.append(current_group)

    return groups
