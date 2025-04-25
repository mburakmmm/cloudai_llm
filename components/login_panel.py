import streamlit as st
from datetime import datetime
import logging
import asyncio
from supabase import create_client, Client
import os
from dotenv import load_dotenv

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
        # Dark mode kontrolü
        is_dark_mode = st.session_state.get('dark_mode', False)
        
        st.markdown(f"""
        <style>
        /* Ana container stili */
        .main-container {{
            max-width: 500px;
            margin: 0 auto;
            padding: 2rem;
        }}
        
        /* Cloud başlık stili */
        .cloud-header {{
            display: flex;
            align-items: center;
            justify-content: center;
            margin-bottom: 2rem;
            background: linear-gradient(135deg, #0084ff, #00c6ff);
            padding: 1.5rem;
            border-radius: 15px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        }}
        
        .cloud-icon {{
            font-size: 3rem;
            margin-right: 1rem;
            color: white;
        }}
        
        .cloud-title {{
            font-size: 2.5rem;
            font-weight: bold;
            color: white;
        }}
        
        /* Tab container stili */
        .stTabs {{
            background-color: {is_dark_mode and '#1E1E1E' or 'white'};
            padding: 2rem;
            border-radius: 15px;
            box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
        }}
        
        /* Form container stili */
        .form-container {{
            background-color: {is_dark_mode and '#1E1E1E' or 'white'};
            padding: 2rem;
            border-radius: 15px;
            margin-top: 1rem;
        }}
        
        /* Input field stili */
        .stTextInput > div > div > input {{
            border: 2px solid {is_dark_mode and '#3E3E3E' or '#e0e0e0'};
            border-radius: 10px;
            padding: 0.75rem;
            font-size: 1rem;
            transition: all 0.3s ease;
            background-color: {is_dark_mode and '#2E2E2E' or 'white'} !important;
            color: {is_dark_mode and '#FFFFFF' or '#333333'} !important;
        }}
        
        .stTextInput > div > div > input:focus {{
            border-color: #0084ff;
            box-shadow: 0 0 0 2px rgba(0, 132, 255, 0.2);
        }}
        
        /* Buton stili */
        .stButton > button {{
            width: 100%;
            padding: 0.75rem;
            font-size: 1.1rem;
            font-weight: 600;
            border-radius: 10px;
            background: linear-gradient(135deg, #0084ff, #00c6ff);
            color: white;
            border: none;
            transition: transform 0.2s ease;
        }}
        
        .stButton > button:hover {{
            transform: translateY(-2px);
        }}
        
        /* Form başlık stili */
        .form-title {{
            color: {is_dark_mode and '#FFFFFF' or '#333333'};
            font-size: 1.5rem;
            font-weight: 600;
            margin-bottom: 1.5rem;
            text-align: center;
        }}
        
        /* Hata mesajı stili */
        .stAlert {{
            border-radius: 10px;
            margin: 1rem 0;
        }}

        /* Tab seçici stili */
        .stTabs [data-baseweb="tab-list"] {{
            background-color: {is_dark_mode and '#2E2E2E' or '#f5f5f5'};
            border-radius: 10px;
            padding: 0.5rem;
        }}

        .stTabs [data-baseweb="tab"] {{
            color: {is_dark_mode and '#FFFFFF' or '#333333'} !important;
        }}

        .stTabs [aria-selected="true"] {{
            background-color: {is_dark_mode and '#3E3E3E' or '#FFFFFF'} !important;
            border-radius: 8px;
        }}

        /* Label stili */
        .stTextInput label {{
            color: {is_dark_mode and '#FFFFFF' or '#333333'} !important;
        }}

        /* Placeholder stili */
        .stTextInput > div > div > input::placeholder {{
            color: {is_dark_mode and '#666666' or '#999999'} !important;
        }}
        </style>
        """, unsafe_allow_html=True)

        st.markdown('<div class="main-container">', unsafe_allow_html=True)
        
        # Cloud başlığı
        st.markdown("""
        <div class="cloud-header">
            <div class="cloud-icon">☁️</div>
            <div class="cloud-title">Cloud</div>
        </div>
        """, unsafe_allow_html=True)

        # Giriş/Kayıt sekmeleri
        tab1, tab2 = st.tabs(["Giriş Yap", "Kaydol"])

        # Giriş sekmesi
        with tab1:
            with st.form("login_form", clear_on_submit=True):
                st.markdown('<p class="form-title">☁️ Cloud\'a Hoş Geldiniz</p>', unsafe_allow_html=True)
                email = st.text_input("E-posta Adresi", placeholder="ornek@email.com")
                password = st.text_input("Şifre", type="password", placeholder="••••••••")
                submit = st.form_submit_button("Giriş Yap")
                
                if submit:
                    if not email or not password:
                        st.error("Lütfen e-posta ve şifre alanlarını doldurun.")
                        return
                        
                    try:
                        auth_response = self.supabase.auth.sign_in_with_password({
                            "email": email,
                            "password": password
                        })
                        
                        if auth_response and hasattr(auth_response.user, 'id'):
                            st.session_state.token = auth_response.session.access_token
                            st.session_state.user_id = auth_response.user.id
                            st.session_state.is_authenticated = True
                            st.success("Giriş başarılı! Yönlendiriliyorsunuz...")
                            st.rerun()
                        else:
                            st.error("Giriş başarısız. Lütfen bilgilerinizi kontrol edin.")
                            
                    except Exception as e:
                        logger.error(f"Giriş hatası: {str(e)}")
                        st.error("Giriş sırasında bir hata oluştu. Lütfen tekrar deneyin.")

        # Kayıt sekmesi
        with tab2:
            with st.form("register_form", clear_on_submit=True):
                st.markdown('<p class="form-title">☁️ Yeni Hesap Oluştur</p>', unsafe_allow_html=True)
                email = st.text_input("E-posta Adresi", placeholder="ornek@email.com")
                password = st.text_input("Şifre", type="password", placeholder="••••••••")
                confirm_password = st.text_input("Şifre Tekrar", type="password", placeholder="••••••••")
                submit = st.form_submit_button("Kaydol")
                
                if submit:
                    if not email or not password or not confirm_password:
                        st.error("Lütfen tüm alanları doldurun.")
                        return
                        
                    if password != confirm_password:
                        st.error("Şifreler eşleşmiyor!")
                        return
                        
                    try:
                        auth_response = self.supabase.auth.sign_up({
                            "email": email,
                            "password": password
                        })
                        
                        if auth_response and hasattr(auth_response.user, 'id'):
                            st.success("Kayıt başarılı! Lütfen e-posta adresinizi doğrulayın.")
                            st.info("E-posta doğrulaması yapıldıktan sonra giriş yapabilirsiniz.")
                        else:
                            st.error("Kayıt başarısız. Lütfen tekrar deneyin.")
                            
                    except Exception as e:
                        logger.error(f"Kayıt hatası: {str(e)}")
                        st.error("Kayıt sırasında bir hata oluştu. Lütfen tekrar deneyin.")
            
            # Şifremi Unuttum butonu
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("Şifremi Unuttum", type="secondary"):
                st.info("Şifre sıfırlama bağlantısı e-posta adresinize gönderilecek.")
        
        st.markdown('</div>', unsafe_allow_html=True) 