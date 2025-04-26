# memory_sqlite.py
import sqlite3
import numpy as np
import logging
from typing import Optional, Tuple, List, Dict, Any
import os
from datetime import datetime
import json

# Debug logları için ayarlar
logger = logging.getLogger(__name__)

class SQLiteMemoryManager:
    def __init__(self, db_path="memory.db"):
        self.db_path = db_path
        logger.debug(f"Initializing SQLiteMemoryManager with db_path: {db_path}")
        self._init_db()
        
    def _init_db(self):
        logger.debug("Creating/checking database tables")
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS memories (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        prompt TEXT NOT NULL,
                        response TEXT NOT NULL,
                        embedding BLOB,
                        tags TEXT,
                        priority INTEGER DEFAULT 1,
                        intent TEXT DEFAULT 'genel',
                        context_message TEXT,
                        category TEXT DEFAULT 'genel',
                        emotion TEXT DEFAULT 'neutral',
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        usage_count INTEGER DEFAULT 0,
                        last_used TIMESTAMP,
                        avg_match_score REAL DEFAULT 0
                    )
                ''')
                
                # Embedding sütunu var mı kontrol et
                cursor.execute("PRAGMA table_info(memories)")
                columns = [column[1] for column in cursor.fetchall()]
                
                if 'embedding' not in columns:
                    cursor.execute('ALTER TABLE memories ADD COLUMN embedding BLOB')
                
                if 'emotion' not in columns:
                    cursor.execute('ALTER TABLE memories ADD COLUMN emotion TEXT DEFAULT "neutral"')
                
                conn.commit()
                logger.debug("Database tables created/checked successfully")
        except Exception as e:
            logger.error(f"Error in _init_db: {str(e)}")
            raise

    def add_memory(self, memory_data: Dict[str, Any]) -> int:
        logger.debug(f"Adding memory: {memory_data}")
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Embedding'i numpy array'den BLOB'a dönüştür
                embedding_blob = None
                if "embedding" in memory_data and memory_data["embedding"] is not None:
                    try:
                        if isinstance(memory_data["embedding"], np.ndarray):
                            embedding_blob = memory_data["embedding"].astype(np.float32).tobytes()
                        else:
                            logger.warning(f"Embedding geçerli bir numpy array değil: {type(memory_data['embedding'])}")
                    except Exception as e:
                        logger.error(f"Embedding dönüştürme hatası: {str(e)}")
                        embedding_blob = None
                
                # Duygu analizi sonuçlarını işle
                emotion_data = memory_data.get("emotion", {})
                if isinstance(emotion_data, dict):
                    emotion = emotion_data.get("emotion", "neutral")
                else:
                    emotion = str(emotion_data)
                
                cursor.execute("""
                    INSERT INTO memories (prompt, response, embedding, intent, emotion)
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    str(memory_data["prompt"]),
                    str(memory_data["response"]),
                    embedding_blob,
                    str(memory_data.get("intent", "genel")),
                    str(emotion)
                ))
                conn.commit()
                last_id = cursor.lastrowid
                logger.debug(f"Successfully added memory with ID: {last_id}")
                return last_id
        except Exception as e:
            logger.error(f"Error in add_memory: {str(e)}")
            raise

    def load_memory(self) -> List[Dict[str, Any]]:
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM memories")
                rows = cursor.fetchall()
                return [{
                    "id": row["id"],
                    "prompt": row["prompt"],
                    "response": row["response"],
                    "tags": json.loads(row["tags"]) if row["tags"] else [],
                    "priority": row["priority"],
                    "intent": row["intent"],
                    "context_message": row["context_message"],
                    "category": row["category"],
                    "created_at": row["created_at"],
                    "usage_count": row["usage_count"],
                    "last_used": row["last_used"],
                    "avg_match_score": row["avg_match_score"]
                } for row in rows]
        except Exception as e:
            logger.error(f"Error in load_memory: {str(e)}")
            return []

    def update_usage_stats(self, memory_id: int, match_score: float = None):
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                if match_score is not None:
                    cursor.execute("""
                        UPDATE memories 
                        SET usage_count = usage_count + 1,
                            last_used = CURRENT_TIMESTAMP,
                            avg_match_score = ((avg_match_score * usage_count) + ?) / (usage_count + 1)
                        WHERE id = ?
                    """, (match_score, memory_id))
                else:
                    cursor.execute("""
                        UPDATE memories 
                        SET usage_count = usage_count + 1,
                            last_used = CURRENT_TIMESTAMP
                        WHERE id = ?
                    """, (memory_id,))
                conn.commit()
        except Exception as e:
            logger.error(f"Error in update_usage_stats: {str(e)}")

    def delete_memory(self, memory_id: int) -> bool:
        """ID'ye göre hafıza kaydını siler"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM memories WHERE id = ?", (memory_id,))
                conn.commit()
                return cursor.rowcount > 0
        except Exception as e:
            logger.error(f"Error in delete_memory: {str(e)}")
            return False

    def update_memory(self, memory_id: int, new_data: Dict[str, Any]) -> bool:
        """ID'ye göre hafıza kaydını günceller"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Güncellenecek alanları ve değerleri hazırla
                update_fields = []
                params = []
                
                for key, value in new_data.items():
                    if key in ["prompt", "response", "intent", "priority", "tags"]:
                        if key == "tags":
                            value = json.dumps(value)
                        update_fields.append(f"{key} = ?")
                        params.append(value)
                
                if update_fields:
                    params.append(memory_id)  # WHERE id = ? için
                    query = f"""
                        UPDATE memories 
                        SET {', '.join(update_fields)}
                        WHERE id = ?
                    """
                    cursor.execute(query, params)
                    conn.commit()
                    return cursor.rowcount > 0
                return False
        except Exception as e:
            logger.error(f"Error in update_memory: {str(e)}")
            return False

    def delete_by_intent(self, intent: str) -> int:
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM memories WHERE intent = ?", (intent,))
                deleted = cursor.rowcount
                conn.commit()
                return deleted
        except Exception as e:
            logger.error(f"Error in delete_by_intent: {str(e)}")
            return 0

    def clear_all(self) -> bool:
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM memories")
                conn.commit()
                return True
        except Exception as e:
            logger.error(f"Error in clear_all: {str(e)}")
            return False

    def remove_duplicates(self) -> int:
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    DELETE FROM memories 
                    WHERE id NOT IN (
                        SELECT MIN(id)
                        FROM memories 
                        GROUP BY prompt, response
                    )
                """)
                deleted = cursor.rowcount
                conn.commit()
                return deleted
        except Exception as e:
            logger.error(f"Error in remove_duplicates: {str(e)}")
            return 0

    def find_best_response(self, query_embedding: np.ndarray) -> Tuple[Optional[str], float]:
        """En iyi yanıtı bul"""
        try:
            if query_embedding is None:
                logger.error("query_embedding None olamaz")
                return None, 0.0

            if not isinstance(query_embedding, np.ndarray):
                logger.error(f"query_embedding numpy array olmalı, şu an: {type(query_embedding)}")
                return None, 0.0

            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Tüm bellekleri getir
                cursor.execute("SELECT id, embedding, response FROM memories WHERE embedding IS NOT NULL")
                memories = cursor.fetchall()
                
                if not memories:
                    logger.warning("Veritabanında hiç bellek bulunamadı")
                    return None, 0.0
                    
                # Benzerlik skorlarını hesapla
                similarities = []
                for memory in memories:
                    try:
                        memory_id, memory_embedding_blob, response = memory
                        
                        if memory_embedding_blob is None:
                            logger.debug(f"ID {memory_id} için embedding verisi yok")
                            continue
                            
                        memory_embedding = np.frombuffer(memory_embedding_blob, dtype=np.float32)
                        
                        # Boyut kontrolü
                        if memory_embedding.shape != query_embedding.shape:
                            logger.warning(f"Embedding boyutları uyuşmuyor: {memory_embedding.shape} != {query_embedding.shape}")
                            continue
                        
                        # Normalize et
                        memory_embedding_norm = np.linalg.norm(memory_embedding)
                        query_embedding_norm = np.linalg.norm(query_embedding)
                        
                        if memory_embedding_norm == 0 or query_embedding_norm == 0:
                            logger.warning(f"Sıfır norm tespit edildi - Memory: {memory_embedding_norm}, Query: {query_embedding_norm}")
                            continue
                            
                        # Kosinüs benzerliği hesapla
                        similarity = np.dot(query_embedding, memory_embedding) / (memory_embedding_norm * query_embedding_norm)
                        
                        logger.debug(f"ID {memory_id} için benzerlik skoru: {similarity}")
                        similarities.append((response, similarity, memory_id))
                        
                    except Exception as e:
                        logger.error(f"Bellek {memory[0]} için benzerlik hesaplama hatası: {str(e)}")
                        continue
                
                if not similarities:
                    logger.warning("Hiç geçerli benzerlik skoru hesaplanamadı")
                    return None, 0.0
                    
                # En yüksek benzerlik skoruna sahip yanıtı bul
                best_response, best_similarity, best_memory_id = max(similarities, key=lambda x: x[1])
                
                logger.info(f"En iyi yanıt bulundu - ID: {best_memory_id}, Benzerlik: {best_similarity}")
                
                # Benzerlik skoru çok düşükse None döndür
                if best_similarity < 0.5:  # Eşik değerini düşürdüm
                    logger.warning(f"En iyi benzerlik skoru çok düşük: {best_similarity}")
                    return None, best_similarity
                
                # Kullanım istatistiklerini güncelle
                self.update_usage_stats(best_memory_id, best_similarity)
                
                return best_response, best_similarity
                
        except Exception as e:
            logger.error(f"find_best_response hatası: {str(e)}")
            return None, 0.0

    def get_all_memories(self) -> List[dict]:
        """Tüm bellekleri getir"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT id, prompt, response, intent, created_at 
                FROM memories 
                ORDER BY created_at DESC
            """)
            
            memories = []
            for row in cursor.fetchall():
                memories.append({
                    "id": row[0],
                    "prompt": row[1],
                    "response": row[2],
                    "intent": row[3],
                    "created_at": row[4]
                })
            
            conn.close()
            return memories
            
        except Exception as e:
            logger.error(f"Bellek getirme hatası: {str(e)}")
            return []

    def analyze_emotion(self, text: str) -> dict:
        try:
            # Cümle yapısı analizi
            sentence_score = 0
            text_lower = text.lower()
            
            # Noktalama işaretleri analizi
            if "!" in text:
                sentence_score += 0.2
            if "..." in text:
                sentence_score -= 0.1
            
            # Kelime bazlı analiz
            word_scores = []
            for emotion, data in self.emotion_lexicon.items():
                emotion_score = 0
                for word in data["words"]:
                    if word in text_lower:
                        emotion_score += data["intensity"]
                    
                if emotion_score != 0:
                    word_scores.append({
                        "emotion": emotion,
                        "score": emotion_score
                    })
            
            # Bağlam analizi
            context_score = 0
            if len(self.emotion_history["emotion_timeline"]) > 0:
                last_emotion = self.emotion_history["emotion_timeline"][-1]["emotion"]
                if last_emotion != "neutral":
                    context_score = self.emotion_lexicon[last_emotion]["intensity"] * 0.3
            
            # Toplam skor hesaplama
            final_scores = []
            for score in word_scores:
                final_score = score["score"] + sentence_score + context_score
                final_scores.append({
                    "emotion": score["emotion"],
                    "score": final_score
                })
            
            # En yüksek skorlu duyguyu seç
            if final_scores:
                max_score = max(final_scores, key=lambda x: abs(x["score"]))
                current_emotion = max_score["emotion"]
                intensity = max_score["score"]
            else:
                current_emotion = "neutral"
                intensity = 0.0
            
            # Duygu geçmişini güncelle
            self.emotion_history["current_emotion"] = current_emotion
            self.emotion_history["emotion_intensity"] = intensity
            self.emotion_history["emotion_timeline"].append({
                "emotion": current_emotion,
                "intensity": intensity,
                "timestamp": datetime.now().isoformat()
            })
            
            return {
                "emotion": current_emotion,
                "intensity": intensity,
                "emoji": self.emotion_lexicon[current_emotion]["emojis"][0],
                "confidence": abs(intensity) / 2  # 0-1 arası güven skoru
            }
            
        except Exception as e:
            logger.error(f"Gelişmiş duygu analizi hatası: {str(e)}")
            return {"emotion": "neutral", "intensity": 0.0, "emoji": "😐", "confidence": 0.0}
