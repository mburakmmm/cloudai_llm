# database.py
import sqlite3
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
import json
from models import Memory, Intent, Emotion, User

logger = logging.getLogger(__name__)

class Database:
    def __init__(self, db_path: str = "app.db"):
        self.db_path = db_path
        self._init_db()
        
    def _init_db(self):
        """Veritabanı tablolarını oluştur"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Memories tablosu
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS memories (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        prompt TEXT NOT NULL,
                        response TEXT NOT NULL,
                        embedding BLOB,
                        intent TEXT,
                        tags TEXT,
                        priority INTEGER DEFAULT 1,
                        category TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        usage_count INTEGER DEFAULT 0,
                        last_used TIMESTAMP,
                        avg_match_score REAL DEFAULT 0
                    )
                ''')
                
                # Intents tablosu
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS intents (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT UNIQUE NOT NULL,
                        examples TEXT,
                        success_rate REAL DEFAULT 0,
                        usage_count INTEGER DEFAULT 0,
                        last_used TIMESTAMP
                    )
                ''')
                
                # Emotions tablosu
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS emotions (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT NOT NULL,
                        intensity REAL,
                        emoji TEXT,
                        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        trigger TEXT
                    )
                ''')
                
                # Users tablosu
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS users (
                        id TEXT PRIMARY KEY,
                        email TEXT UNIQUE NOT NULL,
                        preferences TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        last_active TIMESTAMP,
                        interaction_count INTEGER DEFAULT 0,
                        favorite_topics TEXT
                    )
                ''')
                
                conn.commit()
                logger.info("Veritabanı tabloları başarıyla oluşturuldu")
                
        except Exception as e:
            logger.error(f"Veritabanı başlatma hatası: {str(e)}")
            raise
            
    def add_memory(self, memory: Memory) -> int:
        """Yeni bellek ekle"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO memories (
                        prompt, response, embedding, intent, tags,
                        priority, category, created_at, usage_count,
                        last_used, avg_match_score
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    memory.prompt,
                    memory.response,
                    memory.embedding.tobytes() if memory.embedding is not None else None,
                    memory.intent,
                    json.dumps(memory.tags),
                    memory.priority,
                    memory.category,
                    memory.created_at.isoformat(),
                    memory.usage_count,
                    memory.last_used.isoformat() if memory.last_used else None,
                    memory.avg_match_score
                ))
                conn.commit()
                return cursor.lastrowid
        except Exception as e:
            logger.error(f"Bellek ekleme hatası: {str(e)}")
            raise
            
    def get_memory(self, memory_id: int) -> Optional[Memory]:
        """ID'ye göre bellek getir"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM memories WHERE id = ?", (memory_id,))
                row = cursor.fetchone()
                
                if row:
                    return Memory.from_dict(dict(row))
                return None
                
        except Exception as e:
            logger.error(f"Bellek getirme hatası: {str(e)}")
            return None
            
    def update_memory(self, memory: Memory) -> bool:
        """Bellek güncelle"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE memories SET
                        prompt = ?,
                        response = ?,
                        embedding = ?,
                        intent = ?,
                        tags = ?,
                        priority = ?,
                        category = ?,
                        usage_count = ?,
                        last_used = ?,
                        avg_match_score = ?
                    WHERE id = ?
                """, (
                    memory.prompt,
                    memory.response,
                    memory.embedding.tobytes() if memory.embedding is not None else None,
                    memory.intent,
                    json.dumps(memory.tags),
                    memory.priority,
                    memory.category,
                    memory.usage_count,
                    memory.last_used.isoformat() if memory.last_used else None,
                    memory.avg_match_score,
                    memory.id
                ))
                conn.commit()
                return cursor.rowcount > 0
                
        except Exception as e:
            logger.error(f"Bellek güncelleme hatası: {str(e)}")
            return False
            
    def delete_memory(self, memory_id: int) -> bool:
        """Bellek sil"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM memories WHERE id = ?", (memory_id,))
                conn.commit()
                return cursor.rowcount > 0
                
        except Exception as e:
            logger.error(f"Bellek silme hatası: {str(e)}")
            return False
            
    def get_all_memories(self) -> List[Memory]:
        """Tüm bellekleri getir"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM memories ORDER BY created_at DESC")
                return [Memory.from_dict(dict(row)) for row in cursor.fetchall()]
                
        except Exception as e:
            logger.error(f"Bellekleri getirme hatası: {str(e)}")
            return []
            
    def add_intent(self, intent: Intent) -> bool:
        """Yeni istek ekle"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO intents (
                        name, examples, success_rate,
                        usage_count, last_used
                    ) VALUES (?, ?, ?, ?, ?)
                """, (
                    intent.name,
                    json.dumps(intent.examples),
                    intent.success_rate,
                    intent.usage_count,
                    intent.last_used.isoformat() if intent.last_used else None
                ))
                conn.commit()
                return True
                
        except Exception as e:
            logger.error(f"İstek ekleme hatası: {str(e)}")
            return False
            
    def get_all_intents(self) -> List[Intent]:
        """Tüm istekleri getir"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM intents")
                return [Intent.from_dict(dict(row)) for row in cursor.fetchall()]
                
        except Exception as e:
            logger.error(f"İstekleri getirme hatası: {str(e)}")
            return []
            
    def add_emotion(self, emotion: Emotion) -> bool:
        """Yeni duygu ekle"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO emotions (
                        name, intensity, emoji,
                        timestamp, trigger
                    ) VALUES (?, ?, ?, ?, ?)
                """, (
                    emotion.name,
                    emotion.intensity,
                    emotion.emoji,
                    emotion.timestamp.isoformat(),
                    emotion.trigger
                ))
                conn.commit()
                return True
                
        except Exception as e:
            logger.error(f"Duygu ekleme hatası: {str(e)}")
            return False
            
    def get_emotions(self, limit: int = 100) -> List[Emotion]:
        """Son duyguları getir"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT * FROM emotions ORDER BY timestamp DESC LIMIT ?",
                    (limit,)
                )
                return [Emotion.from_dict(dict(row)) for row in cursor.fetchall()]
                
        except Exception as e:
            logger.error(f"Duyguları getirme hatası: {str(e)}")
            return []
            
    def add_user(self, user: User) -> bool:
        """Yeni kullanıcı ekle"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO users (
                        id, email, preferences,
                        created_at, last_active,
                        interaction_count, favorite_topics
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    user.id,
                    user.email,
                    json.dumps(user.preferences),
                    user.created_at.isoformat(),
                    user.last_active.isoformat(),
                    user.interaction_count,
                    json.dumps(user.favorite_topics)
                ))
                conn.commit()
                return True
                
        except Exception as e:
            logger.error(f"Kullanıcı ekleme hatası: {str(e)}")
            return False
            
    def get_user(self, user_id: str) -> Optional[User]:
        """Kullanıcı getir"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
                row = cursor.fetchone()
                
                if row:
                    return User.from_dict(dict(row))
                return None
                
        except Exception as e:
            logger.error(f"Kullanıcı getirme hatası: {str(e)}")
            return None
            
    def update_user(self, user: User) -> bool:
        """Kullanıcı güncelle"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE users SET
                        email = ?,
                        preferences = ?,
                        last_active = ?,
                        interaction_count = ?,
                        favorite_topics = ?
                    WHERE id = ?
                """, (
                    user.email,
                    json.dumps(user.preferences),
                    user.last_active.isoformat(),
                    user.interaction_count,
                    json.dumps(user.favorite_topics),
                    user.id
                ))
                conn.commit()
                return cursor.rowcount > 0
                
        except Exception as e:
            logger.error(f"Kullanıcı güncelleme hatası: {str(e)}")
            return False 