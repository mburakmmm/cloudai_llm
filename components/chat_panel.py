import streamlit as st
import logging
import time
from typing import Optional
from datetime import datetime
from cloud import CloudAI

logger = logging.getLogger(__name__)

class ChatPanel:
    def __init__(self, cloud_ai):
        self.cloud_ai = cloud_ai
        if "messages" not in st.session_state:
            st.session_state.messages = []
        if "is_processing" not in st.session_state:
            st.session_state.is_processing = False
            
    def clear_messages(self):
        """Mesaj geçmişini temizle"""
        st.session_state.messages = []
        st.session_state.user_input = ""  # Input alanını da temizle
        st.success("Mesaj geçmişi temizlendi!")
        st.rerun()
        
    def render(self):
        st.title("Cloud AI Chat")
        
        # CSS stilleri
        st.markdown("""
        <style>
        /* Ana container */
        .main-container {
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
            height: calc(100vh - 200px);
            display: flex;
            flex-direction: column;
        }
        
        /* Mesaj balonları */
        .message {
            padding: 12px 16px;
            margin: 8px 0;
            border-radius: 12px;
            max-width: 80%;
            line-height: 1.5;
            font-size: 16px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            position: relative;
            word-wrap: break-word;
        }
        
        /* Kullanıcı mesajı */
        .user-message {
            margin-left: auto;
            background: linear-gradient(135deg, #4A90E2, #357ABD);
            color: white;
            border: none;
        }
        
        /* AI mesajı */
        .cloud-message {
            margin-right: auto;
            background: #f0f2f5;
            color: #1c1e21;
            border: 1px solid #e4e6eb;
        }
        
        /* Mesaj içeriği */
        .message-content {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
        }
        
        /* Kullanıcı adı */
        .username {
            font-weight: 600;
            margin-bottom: 4px;
            font-size: 14px;
            color: rgba(255,255,255,0.9);
        }
        
        .cloud-message .username {
            color: #65676b;
        }
        
        /* Input alanı */
        .stTextInput > div > div > input {
            background-color: #f0f2f5 !important;
            color: #1c1e21 !important;
            border: 1px solid #e4e6eb;
            border-radius: 12px;
            padding: 12px;
            font-size: 16px;
            transition: all 0.2s ease;
            width: 100%;
        }
        
        .stTextInput > div > div > input:focus {
            border-color: #4A90E2;
            box-shadow: 0 0 0 2px rgba(74, 144, 226, 0.2);
        }
        
        /* Butonlar */
        .stButton > button {
            background: linear-gradient(135deg, #4A90E2, #357ABD);
            color: white;
            border: none;
            padding: 12px 24px;
            border-radius: 12px;
            font-weight: 600;
            transition: all 0.2s ease;
            width: 100%;
        }
        
        .stButton > button:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 8px rgba(0,0,0,0.1);
        }
        
        /* Temizle butonu */
        .clear-button {
            background: #f0f2f5 !important;
            color: #1c1e21 !important;
            border: 1px solid #e4e6eb !important;
            margin-left: 8px !important;
        }
        
        .clear-button:hover {
            background: #e4e6eb !important;
            transform: translateY(-2px);
        }
        
        /* Mobil uyumluluk */
        @media (max-width: 768px) {
            .main-container {
                padding: 10px;
                height: calc(100vh - 150px);
            }
            
            .message {
                max-width: 90%;
                font-size: 14px;
                padding: 10px 14px;
            }
            
            .stTextInput > div > div > input {
                padding: 10px;
                font-size: 14px;
            }
            
            .stButton > button {
                padding: 10px 20px;
                font-size: 14px;
            }
            
            .username {
                font-size: 12px;
            }
        }
        
        /* Mesaj alanı için yeni stiller */
        .message-area {
            flex: 1;
            overflow-y: auto;
            padding: 20px;
            margin-bottom: 20px;
        }
        
        /* Input container için yeni stiller */
        .input-container {
            position: fixed;
            bottom: 0;
            left: 0;
            right: 0;
            background: white;
            padding: 20px;
            border-top: 1px solid #e4e6eb;
            z-index: 1000;
        }
        </style>
        """, unsafe_allow_html=True)

        # Ana container
        st.markdown("<div class='main-container'>", unsafe_allow_html=True)
        
        # Mesaj alanı
        st.markdown("<div class='message-area'>", unsafe_allow_html=True)
        
        # Mesaj geçmişini göster
        for message in st.session_state.messages:
            if message["role"] == "user":
                st.markdown(f'''
                <div class="message user-message">
                    <div class="message-content">
                        <div class="username">Siz</div>
                        {message["content"]}
                    </div>
                </div>
                ''', unsafe_allow_html=True)
            else:
                st.markdown(f'''
                <div class="message cloud-message">
                    <div class="cloud-icon">🤖</div>
                    <div class="message-content">
                        <div class="username">Cloud AI</div>
                        {message["content"]}
                    </div>
                </div>
                ''', unsafe_allow_html=True)
        
        st.markdown("</div>", unsafe_allow_html=True)
        
        # Input container
        st.markdown("<div class='input-container'>", unsafe_allow_html=True)
        
        # Form oluştur
        with st.form(key="message_form", clear_on_submit=True):
            col1, col2, col3 = st.columns([4, 1, 1])
            with col1:
                user_input = st.text_input(
                    "Mesajınızı yazın...",
                    key="user_input"
                )
            with col2:
                submit_button = st.form_submit_button("Gönder")
            with col3:
                clear_button = st.form_submit_button("Temizle")
            
            if submit_button and user_input and not st.session_state.is_processing:
                self._process_user_input(user_input)
            
            if clear_button:
                self.clear_messages()
        
        st.markdown("</div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    def _process_user_input(self, message: str):
        """Kullanıcı mesajını işle"""
        try:
            st.session_state.is_processing = True
            
            # Kullanıcı mesajını ekle
            st.session_state.messages.append({"role": "user", "content": message})
            
            # AI yanıtını al
            response, confidence = self.cloud_ai.sync_process_message(message)
            
            if response:
                # Yanıtı session state'e ekle
                st.session_state.messages.append({"role": "assistant", "content": response})
                
                # Input alanını temizle
                st.session_state.user_input = ""
            
        except Exception as e:
            logger.error(f"Mesaj işleme hatası: {str(e)}")
            st.error("Yanıt oluşturulurken bir hata oluştu. Lütfen tekrar deneyin.")
        finally:
            st.session_state.is_processing = False
            st.rerun()