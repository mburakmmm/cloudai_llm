import sqlite3
import asyncio
from database.supabase import supabase
import json
from sentence_transformers import SentenceTransformer
import numpy as np
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Embedding modeli
model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')

async def migrate_to_supabase(sqlite_path: str, user_id: str):
    """SQLite veritabanından Supabase'e veri aktarımı"""
    try:
        # SQLite bağlantısı
        conn = sqlite3.connect(sqlite_path)
        cursor = conn.cursor()
        
        # Tüm hafıza kayıtlarını al
        cursor.execute("""
            SELECT id, prompt, response, intent, tags, priority, 
                   usage_count, context_message, category, created_at
            FROM memories
        """)
        memories = cursor.fetchall()
        
        logger.info(f"Toplam {len(memories)} kayıt bulundu")
        
        # Her kayıt için
        for memory in memories:
            try:
                # Veriyi hazırla
                memory_data = {
                    "prompt": memory[1],
                    "response": memory[2],
                    "intent": memory[3],
                    "tags": json.loads(memory[4]) if memory[4] else [],
                    "priority": memory[5],
                    "usage_count": memory[6],
                    "context_message": memory[7],
                    "category": memory[8],
                    "created_at": memory[9],
                    "user_id": user_id
                }
                
                # Embedding oluştur
                embedding = model.encode(memory[1])  # prompt'tan embedding oluştur
                memory_data["embedding"] = embedding.tolist()
                
                # Supabase'e kaydet
                result = await supabase.create_memory(memory_data, user_id)
                
                if result["success"]:
                    logger.info(f"Kayıt başarıyla aktarıldı: {memory[0]}")
                else:
                    logger.error(f"Kayıt aktarılamadı: {memory[0]} - Hata: {result['error']}")
                
            except Exception as e:
                logger.error(f"Kayıt işlenirken hata: {str(e)}")
                continue
        
        logger.info("Veri aktarımı tamamlandı")
        
    except Exception as e:
        logger.error(f"Genel hata: {str(e)}")
    finally:
        conn.close()

if __name__ == "__main__":
    # Kullanıcı bilgileri
    SQLITE_PATH = "memory.db"  # SQLite dosya yolu
    USER_ID = "mburakmemiscy"  # Supabase kullanıcı ID'si
    
    asyncio.run(migrate_to_supabase(SQLITE_PATH, USER_ID)) 