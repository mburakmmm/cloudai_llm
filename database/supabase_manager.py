import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from supabase import Client

class SupabaseManager:
    def __init__(self, supabase: Client):
        self.supabase = supabase
        self.logger = logging.getLogger(__name__)

    async def get_memories(self, user_id: str, page: int = 1, per_page: int = 20) -> List[Dict[str, Any]]:
        """Kullanıcının hafızalarını getir"""
        try:
            start = (page - 1) * per_page
            response = self.supabase.table("memories").select("*") \
                .eq("user_id", user_id) \
                .order("created_at", desc=True) \
                .range(start, start + per_page - 1) \
                .execute()
            return response.data
        except Exception as e:
            self.logger.error(f"Hafıza getirme hatası: {str(e)}")
            return []

    async def create_memory(self, memory_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Yeni hafıza oluştur"""
        try:
            response = self.supabase.table("memories").insert(memory_data).execute()
            return response.data[0] if response.data else None
        except Exception as e:
            self.logger.error(f"Hafıza oluşturma hatası: {str(e)}")
            return None

    async def update_memory(self, memory_id: str, memory_data: Dict[str, Any]) -> bool:
        """Hafızayı güncelle"""
        try:
            response = self.supabase.table("memories").update(memory_data) \
                .eq("id", memory_id).execute()
            return bool(response.data)
        except Exception as e:
            self.logger.error(f"Hafıza güncelleme hatası: {str(e)}")
            return False

    async def delete_memory(self, memory_id: str) -> bool:
        """Hafızayı sil"""
        try:
            response = self.supabase.table("memories").delete().eq("id", memory_id).execute()
            return bool(response.data)
        except Exception as e:
            self.logger.error(f"Hafıza silme hatası: {str(e)}")
            return False

    async def get_memory_stats(self, user_id: str) -> Dict[str, Any]:
        """Hafıza istatistiklerini getir"""
        try:
            response = self.supabase.table("memories").select("*") \
                .eq("user_id", user_id).execute()
            memories = response.data

            stats = {
                "total_memories": len(memories),
                "total_usage": sum(m.get("usage_count", 0) for m in memories),
                "by_intent": {},
                "by_priority": {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
            }

            for memory in memories:
                intent = memory.get("intent", "belirsiz")
                priority = memory.get("priority", 1)
                
                if intent in stats["by_intent"]:
                    stats["by_intent"][intent] += 1
                else:
                    stats["by_intent"][intent] = 1
                    
                stats["by_priority"][priority] = stats["by_priority"].get(priority, 0) + 1

            return stats
        except Exception as e:
            self.logger.error(f"İstatistik getirme hatası: {str(e)}")
            return {
                "total_memories": 0,
                "total_usage": 0,
                "by_intent": {},
                "by_priority": {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
            }

    async def bulk_delete_by_intent(self, user_id: str, intent: str) -> int:
        """Intent'e göre toplu silme"""
        try:
            response = self.supabase.table("memories") \
                .delete() \
                .eq("user_id", user_id) \
                .eq("intent", intent) \
                .execute()
            return len(response.data) if response.data else 0
        except Exception as e:
            self.logger.error(f"Toplu silme hatası: {str(e)}")
            return 0

    async def merge_intents(self, user_id: str, source_intents: List[str], target_intent: str) -> bool:
        """Intent'leri birleştir"""
        try:
            for source in source_intents:
                self.supabase.table("memories") \
                    .update({"intent": target_intent}) \
                    .eq("user_id", user_id) \
                    .eq("intent", source) \
                    .execute()
            return True
        except Exception as e:
            self.logger.error(f"Intent birleştirme hatası: {str(e)}")
            return False

    async def get_important_learnings(self, user_id: str, limit: int = 20) -> List[Dict[str, Any]]:
        """Önemli öğrenmeleri getir"""
        try:
            response = self.supabase.table("memories").select("*") \
                .eq("user_id", user_id) \
                .order("priority", desc=True) \
                .order("usage_count", desc=True) \
                .limit(limit) \
                .execute()
            return response.data
        except Exception as e:
            self.logger.error(f"Önemli öğrenme getirme hatası: {str(e)}")
            return []

    async def cleanup_memories(self, user_id: str, age_days: int, min_usage: int, min_priority: int) -> int:
        """Belirli kriterlere göre hafızaları temizle"""
        try:
            threshold_date = (datetime.now() - timedelta(days=age_days)).isoformat()
            
            response = self.supabase.table("memories") \
                .delete() \
                .eq("user_id", user_id) \
                .lt("created_at", threshold_date) \
                .lt("usage_count", min_usage) \
                .lt("priority", min_priority) \
                .execute()
                
            return len(response.data) if response.data else 0
        except Exception as e:
            self.logger.error(f"Hafıza temizleme hatası: {str(e)}")
            return 0

    async def export_memories(self, user_id: str) -> List[Dict[str, Any]]:
        """Kullanıcının tüm hafızalarını dışa aktar"""
        try:
            response = self.supabase.table("memories").select("*") \
                .eq("user_id", user_id) \
                .execute()
            return response.data
        except Exception as e:
            self.logger.error(f"Hafıza dışa aktarma hatası: {str(e)}")
            return [] 