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
        st.rerun()
        
    def _type_message_slowly(self, text: str, delay: float = 0.1):
        """Mesajı yavaşça yaz"""
        placeholder = st.empty()
        full_text = ""
        for char in text:
            full_text += char
            placeholder.markdown(f'''
                <div class="message cloud-message">
                    <div class="cloud-icon">🤖</div>
                    <div class="message-content">
                        <div class="username">Cloud AI</div>
                        {full_text}
                    </div>
                </div>
            ''', unsafe_allow_html=True)
            time.sleep(delay)

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
        
        /* Düşünme animasyonu */
        .thinking-container {
            display: flex;
            align-items: center;
            padding: 8px 16px;
            background: #f0f2f5;
            border-radius: 12px;
            margin: 8px 0;
            border: 1px solid #e4e6eb;
        }
        
        .typing-animation {
            display: inline-block;
            margin-left: 4px;
            color: #65676b;
        }
        
        .typing-animation::after {
            content: '...';
            animation: typing 1.5s infinite;
        }
        
        @keyframes typing {
            0% { content: '.'; }
            33% { content: '..'; }
            66% { content: '...'; }
            100% { content: '.'; }
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
        }
        
        .clear-button:hover {
            background: #e4e6eb !important;
        }
        </style>
        """, unsafe_allow_html=True)

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

        # Mesaj girişi ve butonlar
        st.markdown("<div class='main-container'>", unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns([4, 1, 1])
        with col1:
            user_input = st.text_input("Mesajınızı yazın...", key="user_input")
        with col2:
            if st.button("Gönder", use_container_width=True):
                if user_input and not st.session_state.is_processing:
                    self._process_user_input(user_input)
        with col3:
            if st.button("Temizle", use_container_width=True, key="clear_button"):
                self.clear_messages()
                
        st.markdown("</div>", unsafe_allow_html=True)
                
    def _process_user_input(self, user_input: str):
        """Kullanıcı mesajını işle"""
        try:
            st.session_state.is_processing = True
            
            # Kullanıcı mesajını ekle
            st.session_state.messages.append({"role": "user", "content": user_input})
            
            # Düşünme animasyonu göster
            thinking = st.empty()
            thinking.markdown(f'''
            <div class="thinking-container">
                <div class="cloud-icon">🤖</div>
                <div class="message-content">
                    <div class="username">Cloud AI</div>
                    Düşünüyorum<span class="typing-animation"></span>
                </div>
            </div>
            ''', unsafe_allow_html=True)
            
            # AI yanıtını al
            response, confidence = self.cloud_ai.sync_process_message(user_input)
            
            # Düşünme animasyonunu kaldır
            thinking.empty()
            
            # AI yanıtını yavaşça yaz
            self._type_message_slowly(response)
            
            # Mesajı session state'e ekle
            st.session_state.messages.append({"role": "assistant", "content": response})
            
        except Exception as e:
            logger.error(f"Mesaj işleme hatası: {str(e)}")
            st.error("Mesaj işlenirken bir hata oluştu. Lütfen tekrar deneyin.")
        finally:
            st.session_state.is_processing = False
            st.rerun()