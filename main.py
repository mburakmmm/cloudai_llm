# main.py
import streamlit as st
import logging
import httpx
import json
from datetime import datetime
from components.chat_panel import ChatPanel
from components.memory_list_panel import MemoryListPanel
from components.trainer_panel import TrainerPanel
from components.cleanup_panel import CleanupPanel
from components.settings_panel import SettingsPanel
from components.intent_analytics_panel import IntentAnalyticsPanel
from components.ai_intent_group_panel import AIIntentGroupPanel
from components.export_panel import ExportPanel
from components.login_panel import LoginPanel
import os
from dotenv import load_dotenv
from supabase import create_client, Client
import asyncio
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
import uvicorn

# Loglama ayarları
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# .env dosyasını yükle
load_dotenv()

# FastAPI uygulaması oluştur
app = FastAPI()

# Statik dosyalar için mount
app.mount("/static", StaticFiles(directory="static"), name="static")

class CloudLLMApp:
    def __init__(self):
        # .env dosyasını yükle
        load_dotenv()
        
        # Supabase URL ve API key'i kontrol et
        self.supabase_url = os.getenv("SUPABASE_URL")
        self.supabase_key = os.getenv("SUPABASE_KEY")
        
        if not self.supabase_url or not self.supabase_key:
            logging.error("SUPABASE_URL veya SUPABASE_KEY bulunamadı!")
            raise ValueError("Lütfen .env dosyasında SUPABASE_URL ve SUPABASE_KEY değerlerini tanımlayın.")
            
        try:
            # API key'i temizle
            self.supabase_key = self.supabase_key.strip()
            if self.supabase_key.endswith('%'):
                self.supabase_key = self.supabase_key[:-1]
                
            logging.info(f"Supabase URL: {self.supabase_url}")
            logging.info(f"Supabase Key: {self.supabase_key[:20]}...")
                
            # Supabase istemcisini oluştur
            self.supabase: Client = create_client(
                supabase_url=self.supabase_url,
                supabase_key=self.supabase_key
            )
            self.supabase_manager = self.supabase
            logging.info("Supabase istemcisi oluşturuldu")
            
            # Bağlantıyı test et
            self.test_supabase_connection()
            
        except Exception as e:
            logging.error(f"Supabase bağlantı hatası: {str(e)}")
            raise ConnectionError(f"Supabase bağlantısı kurulamadı: {str(e)}")
            
        self.token = None
        self.user_id = None
        self.language = "tr"
        self.tts_enabled = True
        self.stt_enabled = True
        
        # Panelleri oluştur
        self.panels = [
            ChatPanel(self),
            MemoryListPanel(self),
            TrainerPanel(self),
            CleanupPanel(self),
            SettingsPanel(self),
            IntentAnalyticsPanel(self),
            AIIntentGroupPanel(self),
            ExportPanel(self),
        ]

    def test_supabase_connection(self):
        """Supabase bağlantısını test et"""
        try:
            # Basit bir sorgu dene
            response = self.supabase.table('profiles').select("count").execute()
            logging.info("Supabase bağlantı testi başarılı!")
            return True
        except Exception as e:
            logging.error(f"Supabase bağlantı testi başarısız: {str(e)}")
            raise ConnectionError(f"Supabase bağlantı testi başarısız: {str(e)}")
        
    async def login(self, email: str, password: str):
        """Supabase'e giriş yap ve token al"""
        try:
            # E-posta ve şifreyi temizle
            email = email.strip()
            password = password.strip()
            
            logging.info(f"Giriş denemesi: {email}")
            
            # Giriş yap
            auth_response = self.supabase.auth.sign_in_with_password({
                "email": email,
                "password": password
            })
            
            logging.info(f"Auth yanıtı: {auth_response}")
            
            if auth_response and hasattr(auth_response.user, 'id'):
                self.token = auth_response.session.access_token
                self.user_id = auth_response.user.id
                
                # Kullanıcı profilini al
                profile = self.supabase.from_('profiles').select('*').eq('id', self.user_id).single().execute()
                
                if profile and profile.data:
                    logging.info(f"Profil bilgisi: {profile.data}")
                    self.show_success(f"Hoş geldiniz, {profile.data.get('full_name', '')}!")
                else:
                    self.show_success("Başarıyla giriş yapıldı!")
                    
                return True
                
            self.show_error("Giriş başarısız. E-posta veya şifre hatalı.")
            return False
            
        except Exception as e:
            error_msg = str(e)
            logging.error(f"Giriş hatası detayı: {error_msg}")
            
            if "Invalid API key" in error_msg:
                logging.error(f"Supabase API key: {self.supabase_key}")
                self.show_error("Supabase API anahtarı geçersiz. Lütfen sistem yöneticisi ile iletişime geçin.")
            elif "Invalid login credentials" in error_msg:
                self.show_error("Giriş bilgileri geçersiz. Lütfen e-posta ve şifrenizi kontrol edin.")
            elif "Email not confirmed" in error_msg:
                self.show_error("E-posta adresiniz henüz doğrulanmamış. Lütfen e-postanızı kontrol edin.")
            else:
                self.show_error(f"Giriş yapılırken bir hata oluştu: {error_msg}")
            return False
            
    async def register(self, email: str, password: str, full_name: str):
        """Yeni kullanıcı kaydı"""
        try:
            # Verileri temizle
            email = email.strip()
            password = password.strip()
            full_name = full_name.strip()
            
            logging.info(f"Kayıt denemesi: {email}")
            
            # Kayıt ol
            auth_response = self.supabase.auth.sign_up({
                "email": email,
                "password": password,
                "options": {
                    "data": {
                        "full_name": full_name
                    }
                }
            })
            
            logging.info(f"Kayıt yanıtı: {auth_response}")
            
            if auth_response and hasattr(auth_response.user, 'id'):
                self.show_success("Kayıt başarılı! Lütfen e-posta adresinizi doğrulayın.")
                return True
                
            self.show_error("Kayıt başarısız.")
            return False
            
        except Exception as e:
            error_msg = str(e)
            logging.error(f"Kayıt hatası detayı: {error_msg}")
            
            if "User already registered" in error_msg:
                self.show_error("Bu e-posta adresi zaten kayıtlı.")
            else:
                self.show_error(f"Kayıt olurken bir hata oluştu: {error_msg}")
            return False
            
    def render(self):
        """Ana sayfayı göster"""
        # CSS stilleri
        st.markdown("""
            <style>
            .main-container {
                max-width: 1200px;
                margin: 0 auto;
                padding: 2rem;
            }
            .header {
                display: flex;
                align-items: center;
                justify-content: space-between;
                margin-bottom: 2rem;
            }
            .title {
                font-size: 2rem;
                font-weight: bold;
                color: #1E88E5;
            }
            .nav-container {
                display: flex;
                gap: 1rem;
                margin-bottom: 2rem;
            }
            .nav-button {
                padding: 0.5rem 1rem;
                border-radius: 5px;
                background-color: #E3F2FD;
                color: #1E88E5;
                border: none;
                cursor: pointer;
            }
            .nav-button:hover {
                background-color: #BBDEFB;
            }
            .nav-button.active {
                background-color: #1E88E5;
                color: white;
            }
            </style>
        """, unsafe_allow_html=True)

        # Ana container
        with st.container():
            st.markdown('<div class="main-container">', unsafe_allow_html=True)
            
            # Header
            st.markdown('<div class="header">', unsafe_allow_html=True)
            st.markdown('<h1 class="title">☁️ Cloud AI</h1>', unsafe_allow_html=True)
            
            # Giriş/çıkış butonu
            if self.token:
                if st.button("Çıkış Yap"):
                    self.token = None
                    self.user_id = None
                    st.rerun()
            else:
                if st.button("Giriş Yap"):
                    st.session_state.show_login = True
                    st.rerun()
            
            st.markdown('</div>', unsafe_allow_html=True)
            
            # Giriş paneli
            if not self.token:
                login_panel = LoginPanel(self)
                login_panel.render()
                return
                
            # Navigasyon
            st.markdown('<div class="nav-container">', unsafe_allow_html=True)
            
            # Sekmeler
            tabs = st.tabs([
                "Sohbet", "Hafıza", "Eğitici", "Temizle",
                "Ayarlar", "İstatistikler", "Intent Grupları",
                "Dışa Aktar"
            ])
            
            st.markdown('</div>', unsafe_allow_html=True)
            
            # Seçilen sekmeyi göster
            if 'selected_tab' not in st.session_state:
                st.session_state.selected_tab = 0
                
            # Sekme değişikliğini dinle
            for i, tab in enumerate(tabs):
                if tab.button("", key=f"tab_{i}"):
                    st.session_state.selected_tab = i
                    st.rerun()
                    
            # Seçilen paneli göster
            if 0 <= st.session_state.selected_tab < len(self.panels):
                self.panels[st.session_state.selected_tab].render()
            
            st.markdown('</div>', unsafe_allow_html=True)

    def toggle_tts(self):
        """TTS'yi aç/kapat"""
        self.tts_enabled = not self.tts_enabled
        st.success(f"TTS {'açıldı' if self.tts_enabled else 'kapandı'}")
        
    def show_error(self, message):
        """Hata mesajı göster"""
        st.error(message)
        
    def show_success(self, message):
        """Başarı mesajı göster"""
        st.success(message)

    async def get_response(self, message):
        """Kullanıcı mesajına yanıt ver"""
        try:
            if not self.token or not self.user_id:
                return "Lütfen önce giriş yapın."

            # Supabase'den en uygun yanıtı bul
            response = self.supabase.table("memories").select("*").execute()
            
            if not response.data:
                return "Henüz hafızamda kayıtlı yanıt yok."
                
            # En basit eşleştirme: Aynı prompt'u ara
            for memory in response.data:
                if message.lower() in memory["prompt"].lower():
                    # Kullanım sayısını artır
                    self.supabase.table("memories").update(
                        {"usage_count": memory["usage_count"] + 1}
                    ).eq("id", memory["id"]).execute()
                    
                    return memory["response"]
                    
            return "Bu konuda henüz bir bilgim yok."
            
        except Exception as e:
            logging.error(f"Yanıt alma hatası: {str(e)}")
            return "Bağlantı hatası. Lütfen internet bağlantınızı kontrol edin."

# FastAPI endpoint'leri
@app.get("/")
async def root():
    return {"message": "Cloud AI API"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    # Streamlit uygulamasını başlat
    cloud_app = CloudLLMApp()
    cloud_app.render()
    
    # FastAPI uygulamasını başlat
    uvicorn.run(app, host="0.0.0.0", port=8000)
