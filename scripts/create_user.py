import asyncio
from database.supabase import supabase
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def create_user(email: str, password: str, username: str):
    """Supabase'de yeni kullanıcı oluştur"""
    try:
        result = await supabase.sign_up(email, password, username)
        
        if result["success"]:
            logger.info(f"Kullanıcı başarıyla oluşturuldu: {result['user'].id}")
            return result["user"].id
        else:
            logger.error(f"Kullanıcı oluşturulamadı: {result['error']}")
            return None
            
    except Exception as e:
        logger.error(f"Hata: {str(e)}")
        return None

if __name__ == "__main__":
    # Kullanıcı bilgileri
    EMAIL = "mburakmemiscy@gmail.com"  # E-posta adresinizi girin
    PASSWORD = "Quartz.2828"   # Şifrenizi girin
    USERNAME = "mburakmemiscy"       # Kullanıcı adınızı girin
    
    user_id = asyncio.run(create_user(EMAIL, PASSWORD, USERNAME))
    
    if user_id:
        print(f"\nKullanıcı ID: {user_id}")
        print("Bu ID'yi migrate_to_supabase.py scriptinde kullanabilirsiniz.") 