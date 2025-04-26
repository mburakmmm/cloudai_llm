# intent_optimizer.py
import numpy as np
from typing import Dict, List, Tuple
import logging
from datetime import datetime
from sentence_transformers import SentenceTransformer, util
from collections import defaultdict
from memory_sqlite import SQLiteMemoryManager

logger = logging.getLogger(__name__)

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

class IntentOptimizer:
    def __init__(self):
        self.intent_stats = {}
        self.transition_matrix = {}
        self.success_rates = {}
        
    def update_intent_stats(self, intent: str, success: bool):
        """İstek istatistiklerini güncelle"""
        if intent not in self.intent_stats:
            self.intent_stats[intent] = {
                "total": 0,
                "success": 0,
                "last_used": None,
                "avg_success_rate": 0.0
            }
            
        stats = self.intent_stats[intent]
        stats["total"] += 1
        if success:
            stats["success"] += 1
        stats["last_used"] = datetime.now().isoformat()
        stats["avg_success_rate"] = stats["success"] / stats["total"]
        
    def update_transition(self, from_intent: str, to_intent: str):
        """İstek geçişlerini güncelle"""
        if from_intent not in self.transition_matrix:
            self.transition_matrix[from_intent] = {}
            
        if to_intent not in self.transition_matrix[from_intent]:
            self.transition_matrix[from_intent][to_intent] = 0
            
        self.transition_matrix[from_intent][to_intent] += 1
        
    def get_next_intent_probability(self, current_intent: str) -> Dict[str, float]:
        """Sonraki olası isteklerin olasılıklarını hesapla"""
        if current_intent not in self.transition_matrix:
            return {}
            
        transitions = self.transition_matrix[current_intent]
        total = sum(transitions.values())
        
        return {intent: count/total for intent, count in transitions.items()}
        
    def optimize_intent_library(self, intent_library: Dict[str, List[str]]) -> Dict[str, List[str]]:
        """İstek kütüphanesini optimize et"""
        optimized_library = {}
        
        for intent, examples in intent_library.items():
            if intent in self.intent_stats:
                stats = self.intent_stats[intent]
                
                # Başarı oranına göre örnekleri filtrele
                if stats["avg_success_rate"] > 0.7:
                    optimized_library[intent] = examples
                else:
                    # Sadece başarılı örnekleri al
                    successful_examples = examples[:int(len(examples) * stats["avg_success_rate"])]
                    optimized_library[intent] = successful_examples
            else:
                optimized_library[intent] = examples
                
        return optimized_library
        
    def get_intent_suggestions(self, current_intent: str, top_k: int = 3) -> List[Tuple[str, float]]:
        """En olası sonraki istekleri öner"""
        probabilities = self.get_next_intent_probability(current_intent)
        
        # Olasılıkları sırala
        sorted_intents = sorted(probabilities.items(), key=lambda x: x[1], reverse=True)
        
        # En yüksek olasılıklı top_k istekleri döndür
        return sorted_intents[:top_k]
        
    def get_intent_stats(self) -> Dict[str, Dict]:
        """İstek istatistiklerini getir"""
        return self.intent_stats
        
    def get_transition_matrix(self) -> Dict[str, Dict[str, int]]:
        """Geçiş matrisini getir"""
        return self.transition_matrix
