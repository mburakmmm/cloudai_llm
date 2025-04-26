import streamlit as st
from datetime import datetime
import logging
import asyncio
from supabase import create_client, Client
import os
from dotenv import load_dotenv
import json
import jwt
from passlib.context import CryptContext
from typing import Optional, Dict, Any

# .env dosyasını yükle
load_dotenv()

logger = logging.getLogger(__name__)

class LoginPanel:
    def __init__(self, app):
        self.app = app
        self.supabase = create_client(
            os.getenv("SUPABASE_URL"),
            os.getenv("SUPABASE_KEY")
        )
        self.logger = logging.getLogger(__name__)
        
        # Session state başlatma
        if 'show_register' not in st.session_state:
            st.session_state.show_register = False
    
    def render(self):
        st.title("Cloud AI Giriş")
        
        # CSS stilleri
        st.markdown("""
        <style>
        /* Ana container */
        .main-container {
            max-width: 400px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f8f9fa;
            border-radius: 12px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        }
        
        /* Form alanları */
        .stTextInput > div > div > input {
            background-color: #ffffff !important;
            color: #2c3e50 !important;
            border: 1px solid #e0e0e0;
            border-radius: 8px;
            padding: 12px;
            font-size: 16px;
            transition: all 0.2s ease;
        }
        
        .stTextInput > div > div > input:focus {
            border-color: #3498db;
            box-shadow: 0 0 0 2px rgba(52, 152, 219, 0.1);
        }
        
        /* Butonlar */
        .stButton > button {
            background: linear-gradient(135deg, #3498db, #2980b9);
            color: white;
            border: none;
            padding: 12px 24px;
            border-radius: 8px;
            font-weight: 500;
            transition: all 0.2s ease;
            width: 100%;
        }
        
        .stButton > button:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 8px rgba(0,0,0,0.1);
        }
        
        /* Başlık */
        h1 {
            color: #2c3e50;
            font-weight: 600;
            margin-bottom: 24px;
        }
        
        /* Etiketler */
        label {
            color: #34495e;
            font-weight: 500;
            margin-bottom: 8px;
        }
        
        /* Hata mesajları */
        .stAlert {
            background-color: #fef2f2;
            border: 1px solid #fee2e2;
            border-radius: 8px;
            padding: 12px;
            margin: 12px 0;
        }
        
        /* Başarı mesajları */
        .stSuccess {
            background-color: #f0fdf4;
            border: 1px solid #dcfce7;
            border-radius: 8px;
            padding: 12px;
            margin: 12px 0;
        }
        
        /* Mobil uyumluluk */
        @media (max-width: 768px) {
            .main-container {
                padding: 16px;
            }
            
            .stTextInput > div > div > input {
                padding: 10px;
                font-size: 14px;
            }
            
            .stButton > button {
                padding: 10px 20px;
                font-size: 14px;
            }
        }
        </style>
        """, unsafe_allow_html=True)
        
        with st.form("login_form"):
            st.markdown("<div class='main-container'>", unsafe_allow_html=True)
            
            # Giriş formu
            email = st.text_input("E-posta", key="login_email")
            password = st.text_input("Şifre", type="password", key="login_password")
            
            col1, col2 = st.columns(2)
            with col1:
                login = st.form_submit_button("Giriş Yap", use_container_width=True)
            with col2:
                register = st.form_submit_button("Kayıt Ol", use_container_width=True)
            
            st.markdown("</div>", unsafe_allow_html=True)
            
            if login:
                if not email or not password:
                    st.error("Lütfen e-posta ve şifre girin.")
                    return
                    
                try:
                    success = self.app.cloud_ai.sync_login(email, password)
                    if success:
                        st.success("Giriş başarılı!")
                        st.session_state.logged_in = True
                        st.session_state.email = email
                        st.rerun()
                    else:
                        st.error("Geçersiz e-posta veya şifre.")
                except Exception as e:
                    st.error(f"Giriş sırasında bir hata oluştu: {str(e)}")
                    
            if register:
                if not email or not password:
                    st.error("Lütfen e-posta ve şifre girin.")
                    return
                    
                try:
                    success = self.app.cloud_ai.sync_register(email, password)
                    if success:
                        st.success("Kayıt başarılı! Giriş yapabilirsiniz.")
                    else:
                        st.error("Kayıt sırasında bir hata oluştu.")
                except Exception as e:
                    st.error(f"Kayıt sırasında bir hata oluştu: {str(e)}") 