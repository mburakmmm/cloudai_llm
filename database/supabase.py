from supabase import create_client, Client
import os
from dotenv import load_dotenv
from typing import Optional, List, Dict, Any
import json

load_dotenv()

class SupabaseManager:
    def __init__(self):
        self.url: str = os.getenv("SUPABASE_URL")
        self.key: str = os.getenv("SUPABASE_KEY")
        self.client: Client = create_client(self.url, self.key)
        
    async def sign_up(self, email: str, password: str, username: str) -> Dict:
        """Yeni kullanıcı kaydı"""
        try:
            # Önce auth kaydı oluştur
            auth_response = self.client.auth.sign_up({
                "email": email,
                "password": password,
                "options": {
                    "data": {
                        "username": username
                    }
                }
            })
            
            if auth_response.user:
                # Kullanıcı profilini oluştur
                profile_data = {
                    "id": auth_response.user.id,
                    "username": username,
                    "email": email
                }
                
                await self.client.table("profiles").insert(profile_data).execute()
                
                return {
                    "success": True,
                    "user": auth_response.user,
                    "profile": profile_data
                }
                
        except Exception as e:
            return {"success": False, "error": str(e)}
            
    async def sign_in(self, email: str, password: str) -> Dict:
        """Kullanıcı girişi"""
        try:
            response = await self.client.auth.sign_in_with_password({
                "email": email,
                "password": password
            })
            return {"success": True, "session": response.session}
        except Exception as e:
            return {"success": False, "error": str(e)}
            
    async def create_memory(self, memory_data: Dict, user_id: str) -> Dict:
        """Yeni hafıza kaydı oluştur"""
        try:
            memory_data["user_id"] = user_id
            response = await self.client.table("memories").insert(memory_data).execute()
            return {"success": True, "data": response.data}
        except Exception as e:
            return {"success": False, "error": str(e)}
            
    async def get_memories(self, user_id: str, limit: int = 100, offset: int = 0) -> Dict:
        """Kullanıcının hafıza kayıtlarını getir"""
        try:
            response = await self.client.table("memories")\
                .select("*")\
                .eq("user_id", user_id)\
                .order("created_at", desc=True)\
                .limit(limit)\
                .offset(offset)\
                .execute()
            return {"success": True, "data": response.data}
        except Exception as e:
            return {"success": False, "error": str(e)}
            
    async def update_memory(self, memory_id: int, memory_data: Dict, user_id: str) -> Dict:
        """Hafıza kaydını güncelle"""
        try:
            response = await self.client.table("memories")\
                .update(memory_data)\
                .eq("id", memory_id)\
                .eq("user_id", user_id)\
                .execute()
            return {"success": True, "data": response.data}
        except Exception as e:
            return {"success": False, "error": str(e)}
            
    async def delete_memory(self, memory_id: int, user_id: str) -> Dict:
        """Hafıza kaydını sil"""
        try:
            response = await self.client.table("memories")\
                .delete()\
                .eq("id", memory_id)\
                .eq("user_id", user_id)\
                .execute()
            return {"success": True, "data": response.data}
        except Exception as e:
            return {"success": False, "error": str(e)}
            
    async def share_memory(self, memory_id: int, shared_with_id: str, can_edit: bool, user_id: str) -> Dict:
        """Hafıza kaydını paylaş"""
        try:
            share_data = {
                "memory_id": memory_id,
                "shared_with_id": shared_with_id,
                "shared_by_id": user_id,
                "can_edit": can_edit
            }
            response = await self.client.table("shared_memories").insert(share_data).execute()
            return {"success": True, "data": response.data}
        except Exception as e:
            return {"success": False, "error": str(e)}
            
    async def get_shared_memories(self, user_id: str) -> Dict:
        """Kullanıcı ile paylaşılan hafıza kayıtlarını getir"""
        try:
            response = await self.client.table("shared_memories")\
                .select("*, memories(*)")\
                .eq("shared_with_id", user_id)\
                .execute()
            return {"success": True, "data": response.data}
        except Exception as e:
            return {"success": False, "error": str(e)}
            
    async def search_memories(self, query: str, user_id: str) -> Dict:
        """Hafıza kayıtlarında arama yap"""
        try:
            response = await self.client.rpc(
                'search_memories',
                {
                    'search_query': query,
                    'user_id': user_id
                }
            ).execute()
            return {"success": True, "data": response.data}
        except Exception as e:
            return {"success": False, "error": str(e)}

# Singleton instance
supabase = SupabaseManager() 