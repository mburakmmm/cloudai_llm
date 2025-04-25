import streamlit as st
import os
from dotenv import load_dotenv
from supabase import create_client, Client
import logging
from datetime import datetime
import asyncio
import nest_asyncio

# Event loop sorununu çöz
nest_asyncio.apply()

# Loglama ayarları
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Panelleri import et
from components.login_panel import LoginPanel
from components.chat_panel import ChatPanel
from components.export_panel import ExportPanel
from components.ai_intent_group_panel import AIIntentGroupPanel
from components.intent_analytics_panel import IntentAnalyticsPanel
from components.settings_panel import SettingsPanel
from components.cleanup_panel import CleanupPanel
from components.memory_list_panel import MemoryListPanel
from components.trainer_panel import TrainerPanel
from components.sidebar import Sidebar

# CloudAI'yı en son import et
from cloud import CloudAI

class CloudLLMApp:
    def __init__(self):
        # .env dosyasını yükle
        load_dotenv()
        
        # Event loop'u başlat
        try:
            self.loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self.loop)
        except Exception as e:
            logger.error(f"Event loop hatası: {str(e)}")
        
        # Session state'i başlat
        self.setup_session_state()
        
        # Supabase bağlantısını başlat
        try:
            self.supabase = create_client(
                os.getenv("SUPABASE_URL"),
                os.getenv("SUPABASE_KEY")
            )
        except Exception as e:
            logger.error(f"Supabase bağlantı hatası: {str(e)}")
            st.error("Veritabanı bağlantısı kurulamadı. Lütfen daha sonra tekrar deneyin.")
            return
        
        # CloudAI nesnesini başlat
        try:
            self.cloud_ai = CloudAI()
        except Exception as e:
            logger.error(f"CloudAI başlatılırken hata: {str(e)}")
            st.error("AI sistemi başlatılamadı. Lütfen daha sonra tekrar deneyin.")
            return
            
        # Panelleri başlat
        try:
            self.login_panel = LoginPanel(self)
            self.chat_panel = ChatPanel(self.cloud_ai)
            self.export_panel = ExportPanel(self)
            self.ai_intent_group_panel = AIIntentGroupPanel(self)
            self.intent_analytics_panel = IntentAnalyticsPanel(self)
            self.settings_panel = SettingsPanel(self)
            self.cleanup_panel = CleanupPanel(self)
            self.memory_list_panel = MemoryListPanel(self)
            self.trainer_panel = TrainerPanel(self)
            self.sidebar = Sidebar()
        except Exception as e:
            logger.error(f"Panel başlatma hatası: {str(e)}")
            st.error("Paneller yüklenemedi. Lütfen sayfayı yenileyin.")
            return

    def setup_session_state(self):
        if 'messages' not in st.session_state:
            st.session_state.messages = []
        if 'selected_panel' not in st.session_state:
            st.session_state.selected_panel = 'chat'
        if 'is_authenticated' not in st.session_state:
            st.session_state.is_authenticated = False
        if 'dark_mode' not in st.session_state:
            st.session_state.dark_mode = False
        if 'token' not in st.session_state:
            st.session_state.token = None
        if 'user_id' not in st.session_state:
            st.session_state.user_id = None

    async def login(self, email: str, password: str):
        """Supabase'e giriş yap"""
        try:
            # Supabase auth işlemi
            auth_response = self.supabase.auth.sign_in_with_password({
                "email": email,
                "password": password
            })
            
            if auth_response and hasattr(auth_response.user, 'id'):
                st.session_state.token = auth_response.session.access_token
                st.session_state.user_id = auth_response.user.id
                st.session_state.is_authenticated = True
                return True
                
            return False
            
        except Exception as e:
            logger.error(f"Giriş hatası: {str(e)}")
            return False

    async def register(self, email: str, password: str, full_name: str):
        """Yeni kullanıcı kaydı"""
        try:
            # Supabase auth işlemi
            auth_response = self.supabase.auth.sign_up({
                "email": email,
                "password": password,
                "options": {
                    "data": {
                        "full_name": full_name
                    }
                }
            })
            
            if auth_response and hasattr(auth_response.user, 'id'):
                return True
                
            return False
            
        except Exception as e:
            logger.error(f"Kayıt hatası: {str(e)}")
            return False

    def run_async(self, coro):
        """Asenkron fonksiyonları çalıştırmak için yardımcı metod"""
        try:
            if not self.loop.is_running():
                return self.loop.run_until_complete(coro)
            else:
                future = asyncio.run_coroutine_threadsafe(coro, self.loop)
                return future.result(timeout=10)  # 10 saniye timeout
        except Exception as e:
            logger.error(f"Asenkron işlem hatası: {str(e)}")
            return None

    def main(self):
        """Ana uygulama"""
        st.set_page_config(page_title="Cloud AI", page_icon="☁️", layout="wide")

        # Karanlık mod CSS'i
        if st.session_state.dark_mode:
            st.markdown("""
                <style>
                /* Ana uygulama arka planı */
                .stApp {
                    background-color: #1E1E1E;
                    color: #FFFFFF;
                }
                
                /* Sidebar */
                [data-testid="stSidebar"] {
                    background-color: #2E2E2E;
                    border-right: 1px solid #3E3E3E;
                }
                
                /* Sidebar başlık */
                [data-testid="stSidebar"] .sidebar-content h1 {
                    color: #FFFFFF;
                }
                
                /* Radio butonlar */
                .stRadio > label {
                    color: #FFFFFF !important;
                }
                
                /* Butonlar */
                .stButton > button {
                    background-color: #3E3E3E !important;
                    color: #FFFFFF !important;
                    border: 1px solid #4E4E4E !important;
                }
                
                /* Text input ve textarea */
                .stTextInput > div > div > input,
                .stTextArea > div > div > textarea {
                    background-color: #2E2E2E !important;
                    color: #FFFFFF !important;
                    border: 1px solid #3E3E3E !important;
                }
                
                /* Expander */
                .streamlit-expanderHeader {
                    background-color: #2E2E2E !important;
                    color: #FFFFFF !important;
                }
                
                /* Container */
                .element-container {
                    background-color: #2E2E2E;
                }
                
                /* Mesaj containerleri */
                .message-container, .memory-item, .input-container {
                    background-color: #2E2E2E !important;
                    color: #FFFFFF !important;
                    border: 1px solid #3E3E3E !important;
                }
                
                /* AI mesajları */
                .ai-message .message-content {
                    background-color: #3E3E3E !important;
                    color: #FFFFFF !important;
                }
                
                /* Kullanıcı mesajları */
                .user-message .message-content {
                    background-color: #0084ff !important;
                    color: #FFFFFF !important;
                }
                
                /* Chat container */
                .chat-container {
                    background-color: #2E2E2E !important;
                    border: 1px solid #3E3E3E !important;
                }
                
                /* Başlıklar */
                h1, h2, h3, h4, h5, h6 {
                    color: #FFFFFF !important;
                }
                </style>
            """, unsafe_allow_html=True)

        # Giriş yapılmamışsa login panelini göster
        if not st.session_state.is_authenticated:
            self.login_panel.render()
            return

        # Ana içerik
        st.title("☁️ Cloud AI")
        
        # Yan menüyü göster
        self.sidebar.render()
        
        # Seçilen paneli göster
        try:
            if st.session_state.selected_panel == "Sohbet":
                self.chat_panel.render()
            elif st.session_state.selected_panel == "Hafıza":
                self.memory_list_panel.render()
            elif st.session_state.selected_panel == "Eğitici":
                self.trainer_panel.render()
            elif st.session_state.selected_panel == "Temizle":
                self.cleanup_panel.render()
            elif st.session_state.selected_panel == "Ayarlar":
                self.settings_panel.render()
            elif st.session_state.selected_panel == "İstatistikler":
                self.intent_analytics_panel.render()
            elif st.session_state.selected_panel == "Intent Grupları":
                self.ai_intent_group_panel.render()
            elif st.session_state.selected_panel == "Dışa Aktar":
                self.export_panel.render()
        except Exception as e:
            st.error(f"Panel yüklenirken hata oluştu: {str(e)}")

if __name__ == "__main__":
    try:
        app = CloudLLMApp()
        app.main()
    except Exception as e:
        st.error(f"Uygulama başlatılırken hata oluştu: {str(e)}") 