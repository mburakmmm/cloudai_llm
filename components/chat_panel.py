import streamlit as st
import logging
import asyncio
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
            
        if "current_message" not in st.session_state:
            st.session_state.current_message = ""
            
        if "is_typing" not in st.session_state:
            st.session_state.is_typing = False

    def clear_messages(self):
        st.session_state.messages = []
        st.rerun()

    def type_message(self, message: str, speed: float = 0.05) -> str:
        """Mesajı yavaşça yazdırır"""
        if not st.session_state.is_typing:
            st.session_state.is_typing = True
            typed_message = ""
            for char in message:
                typed_message += char
                yield typed_message
                time.sleep(speed)
            st.session_state.is_typing = False

    def render(self):
        # Dark mode kontrolü
        is_dark_mode = st.session_state.get('dark_mode', False)
        
        st.markdown(f"""
        <style>
        /* Genel chat container stili */
        .chat-container {{
            max-width: 800px;
            margin: 0 auto;
            padding: 1rem;
        }}

        /* Mesaj balonları için genel stil */
        .message {{
            padding: 1rem 1.5rem;
            margin: 0.5rem 0;
            border-radius: 15px;
            max-width: 80%;
            line-height: 1.5;
            font-size: 1rem;
            box-shadow: 0 2px 5px {is_dark_mode and 'rgba(0,0,0,0.2)' or 'rgba(0,0,0,0.1)'};
            transition: all 0.3s ease;
        }}

        /* Kullanıcı mesajı stili */
        .user-message {{
            margin-left: auto;
            background: linear-gradient(135deg, #2979FF, #1565C0);
            color: rgba(255, 255, 255, 0.95);
            border: 1px solid {is_dark_mode and '#1E88E5' or '#2962FF'};
        }}

        /* Cloud mesajı stili */
        .cloud-message {{
            display: flex;
            align-items: start;
            margin-right: auto;
            background-color: {is_dark_mode and '#2A2A2A' or '#f8f9fa'};
            border: 1px solid {is_dark_mode and '#3A3A3A' or '#e9ecef'};
            color: {is_dark_mode and '#E0E0E0' or '#212529'};
        }}

        /* Cloud ikonu stili */
        .cloud-icon {{
            font-size: 1.5rem;
            margin-right: 0.75rem;
            color: {is_dark_mode and '#4FC3F7' or '#0084ff'};
            opacity: 0.9;
        }}

        /* Mesaj içeriği stili */
        .message-content {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
        }}

        /* Kullanıcı adı stili */
        .username {{
            font-weight: 600;
            margin-bottom: 0.3rem;
            color: {is_dark_mode and '#E0E0E0' or '#424242'};
            opacity: 0.9;
        }}

        /* Düşünme animasyonu container */
        .thinking-container {{
            display: flex;
            align-items: center;
            padding: 0.5rem 1rem;
            background-color: {is_dark_mode and '#2A2A2A' or '#f8f9fa'};
            border-radius: 10px;
            margin: 0.5rem 0;
            border: 1px solid {is_dark_mode and '#3A3A3A' or '#e9ecef'};
        }}

        /* Düşünme animasyonu */
        .typing-animation {{
            display: inline-block;
            margin-left: 4px;
            color: {is_dark_mode and '#4FC3F7' or '#0084ff'};
        }}

        .typing-animation::after {{
            content: '...';
            animation: typing 1.5s infinite;
        }}

        @keyframes typing {{
            0% {{ content: '.'; }}
            33% {{ content: '..'; }}
            66% {{ content: '...'; }}
            100% {{ content: '.'; }}
        }}

        /* Input container stili */
        .input-container {{
            margin-top: 1rem;
            padding: 1rem;
            background-color: {is_dark_mode and '#2A2A2A' or '#ffffff'};
            border-radius: 10px;
            border: 1px solid {is_dark_mode and '#3A3A3A' or '#e9ecef'};
        }}

        /* Input alanı stili */
        .stTextInput > div > div > input {{
            background-color: {is_dark_mode and '#363636' or '#ffffff'} !important;
            color: {is_dark_mode and '#E0E0E0' or '#212529'} !important;
            border: 1px solid {is_dark_mode and '#4A4A4A' or '#ced4da'};
            border-radius: 8px;
            padding: 0.75rem;
            font-size: 1rem;
            transition: all 0.2s ease;
        }}

        .stTextInput > div > div > input:focus {{
            border-color: {is_dark_mode and '#4FC3F7' or '#0084ff'};
            box-shadow: 0 0 0 2px {is_dark_mode and 'rgba(79, 195, 247, 0.2)' or 'rgba(0, 132, 255, 0.2)'};
        }}

        /* Buton container stili */
        .button-container {{
            display: flex;
            gap: 0.5rem;
            margin-top: 0.5rem;
        }}

        /* Gönder butonu stili */
        .stButton > button {{
            background: linear-gradient(135deg, #2979FF, #1565C0);
            color: white;
            border: none;
            padding: 0.75rem 1.5rem;
            border-radius: 8px;
            font-weight: 600;
            transition: transform 0.2s ease;
            flex: 1;
        }}

        .stButton > button:hover {{
            transform: translateY(-2px);
        }}

        /* Temizle butonu stili */
        .clear-button {{
            background: linear-gradient(135deg, #FF5252, #D32F2F) !important;
        }}
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
                    <div class="cloud-icon">☁️</div>
                    <div class="message-content">
                        <div class="username">Cloud</div>
                        {message["content"]}
                    </div>
                </div>
                ''', unsafe_allow_html=True)

        # Mesaj girişi
        with st.form("chat_form", clear_on_submit=True):
            user_input = st.text_input("Mesajınız:", key="user_input")
            
            # Buton container
            col1, col2 = st.columns([3, 1])
            with col1:
                submit = st.form_submit_button("Gönder", use_container_width=True)
            with col2:
                clear = st.form_submit_button("Mesajları Temizle", use_container_width=True, key="clear_button")
            
            if clear:
                self.clear_messages()
                return
                
            if submit and user_input:
                # Kullanıcı mesajını ekle
                st.session_state.messages.append({"role": "user", "content": user_input})
                
                # Düşünme animasyonu göster
                thinking = st.empty()
                thinking.markdown(f'''
                <div class="thinking-container">
                    <div class="cloud-icon">☁️</div>
                    <div class="message-content">
                        <div class="username">Cloud</div>
                        düşünüyor<span class="typing-animation"></span>
                    </div>
                </div>
                ''', unsafe_allow_html=True)
                
                try:
                    # AI yanıtını al
                    response, confidence = self.cloud_ai.sync_process_message(user_input)
                    
                    # Düşünme animasyonunu kaldır
                    thinking.empty()
                    
                    # Yanıtı yavaşça yazdır
                    response_container = st.empty()
                    for typed_response in self.type_message(response, speed=0.05):
                        response_container.markdown(f'''
                        <div class="message cloud-message">
                            <div class="cloud-icon">☁️</div>
                            <div class="message-content">
                                <div class="username">Cloud</div>
                                {typed_response}
                            </div>
                        </div>
                        ''', unsafe_allow_html=True)
                    
                    # Son yanıtı mesaj geçmişine ekle
                    st.session_state.messages.append({"role": "assistant", "content": response})
                    st.rerun()
                    
                except Exception as e:
                    st.error(f"Yanıt oluşturulurken bir hata oluştu: {str(e)}")
                    thinking.empty()