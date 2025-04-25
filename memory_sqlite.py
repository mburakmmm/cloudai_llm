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
                    embedding_blob = memory_data["embedding"].tobytes()
                
                cursor.execute("""
                    INSERT INTO memories (prompt, response, embedding, tags, priority, intent, context_message, category)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    memory_data["prompt"],
                    memory_data["response"],
                    embedding_blob,
                    json.dumps(memory_data.get("tags", [])),
                    memory_data.get("priority", 1),
                    memory_data.get("intent", "genel"),
                    memory_data.get("context_message", ""),
                    memory_data.get("category", "genel")
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
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Tüm bellekleri getir
            cursor.execute("SELECT id, embedding, response FROM memories WHERE embedding IS NOT NULL")
            memories = cursor.fetchall()
            
            if not memories:
                logger.warning("No memories found with embeddings")
                return None, 0.0
                
            # Benzerlik skorlarını hesapla
            similarities = []
            for memory in memories:
                try:
                    memory_embedding = np.frombuffer(memory[1], dtype=np.float32)
                    similarity = np.dot(query_embedding, memory_embedding) / (
                        np.linalg.norm(query_embedding) * np.linalg.norm(memory_embedding)
                    )
                    similarities.append((memory[2], similarity))
                except Exception as e:
                    logger.error(f"Error processing memory {memory[0]}: {str(e)}")
                    continue
            
            if not similarities:
                logger.warning("No valid similarities calculated")
                return None, 0.0
            
            # En yüksek benzerlik skoruna sahip yanıtı bul
            best_response, best_similarity = max(similarities, key=lambda x: x[1])
            
            conn.close()
            return best_response, float(best_similarity)
            
        except Exception as e:
            logger.error(f"Yanıt bulma hatası: {str(e)}")
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
