import streamlit as st
import logging
from datetime import datetime
import asyncio
import os
from dotenv import load_dotenv

class SettingsPanel:
    def __init__(self, app):
        self.app = app
        self.logger = logging.getLogger(__name__)
        
        # Ayarları başlat
        if 'model_path' not in st.session_state:
            st.session_state.model_path = os.getenv('MODEL_PATH', 'models/')
        if 'model_name' not in st.session_state:
            st.session_state.model_name = os.getenv('MODEL_NAME', 'cloud_llm')
        if 'confidence_threshold' not in st.session_state:
            st.session_state.confidence_threshold = float(os.getenv('CONFIDENCE_THRESHOLD', '0.7'))
        if 'max_context_length' not in st.session_state:
            st.session_state.max_context_length = int(os.getenv('MAX_CONTEXT_LENGTH', '2000'))

    def render(self):
        """Ayarlar panelini göster"""
        # Dark mode kontrolü
        is_dark_mode = st.session_state.get('dark_mode', False)
        
        # CSS stilleri
        st.markdown(f"""
            <style>
            .settings-container {{
                display: flex;
                flex-direction: column;
                gap: 2rem;
            }}
            
            .settings-section {{
                background-color: {is_dark_mode and '#2A2A2A' or 'white'};
                padding: 2rem;
                border-radius: 20px;
                box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
            }}
            
            .setting-item {{
                margin-bottom: 1.5rem;
            }}
            
            /* Input alanı stili */
            .stTextInput > div > div > input {{
                background-color: {is_dark_mode and '#363636' or 'white'} !important;
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
            
            /* Select box stili */
            .stSelectbox > div > div {{
                background-color: {is_dark_mode and '#363636' or 'white'} !important;
                color: {is_dark_mode and '#E0E0E0' or '#212529'} !important;
                border: 1px solid {is_dark_mode and '#4A4A4A' or '#ced4da'};
            }}
            
            /* Slider stili */
            .stSlider > div > div > div {{
                background-color: {is_dark_mode and '#4FC3F7' or '#0084ff'};
            }}
            
            /* Checkbox stili */
            .stCheckbox > div > div > div {{
                border-color: {is_dark_mode and '#4A4A4A' or '#ced4da'};
            }}
            
            .stCheckbox > div > div > div:hover {{
                border-color: {is_dark_mode and '#4FC3F7' or '#0084ff'};
            }}
            
            /* Form submit button stili */
            .stButton > button {{
                background: linear-gradient(135deg, #2979FF, #1565C0);
                color: white;
                border: none;
                padding: 0.75rem 1.5rem;
                border-radius: 8px;
                font-weight: 600;
                width: 100%;
                transition: transform 0.2s ease;
            }}
            
            .stButton > button:hover {{
                transform: translateY(-2px);
            }}
            
            /* Başlık stili */
            h1, h2, h3, h4, h5, h6 {{
                color: {is_dark_mode and '#E0E0E0' or '#212529'};
            }}
            
            /* Label stili */
            .stTextInput label, .stSelectbox label, .stSlider label, .stCheckbox label {{
                color: {is_dark_mode and '#E0E0E0' or '#212529'} !important;
            }}
            </style>
        """, unsafe_allow_html=True)

        # Ana container
        with st.container():
            st.markdown('<div class="settings-container">', unsafe_allow_html=True)
            
            # Başlık
            st.title("Ayarlar")
            
            # Model Ayarları
            st.markdown('<div class="settings-section">', unsafe_allow_html=True)
            st.header("Model Ayarları")
            
            with st.form(key="model_settings_form"):
                # Model yolu
                model_path = st.text_input(
                    "Model Yolu",
                    value=st.session_state.model_path,
                    help="Model dosyalarının bulunduğu klasör yolu"
                )
                
                # Model adı
                model_name = st.text_input(
                    "Model Adı",
                    value=st.session_state.model_name,
                    help="Kullanılacak model dosyasının adı"
                )
                
                # Güven eşiği
                confidence_threshold = st.slider(
                    "Güven Eşiği",
                    min_value=0.0,
                    max_value=1.0,
                    value=st.session_state.confidence_threshold,
                    step=0.1,
                    help="Yanıtların minimum güven skoru"
                )
                
                # Maksimum bağlam uzunluğu
                max_context_length = st.number_input(
                    "Maksimum Bağlam Uzunluğu",
                    min_value=100,
                    max_value=4000,
                    value=st.session_state.max_context_length,
                    step=100,
                    help="Maksimum token sayısı"
                )
                
                # Kaydet butonu
                submitted = st.form_submit_button("Kaydet")
                if submitted:
                    try:
                        # Ayarları güncelle
                        st.session_state.model_path = model_path
                        st.session_state.model_name = model_name
                        st.session_state.confidence_threshold = confidence_threshold
                        st.session_state.max_context_length = max_context_length
                        
                        # .env dosyasını güncelle
                        with open('.env', 'w') as f:
                            f.write(f"MODEL_PATH={model_path}\n")
                            f.write(f"MODEL_NAME={model_name}\n")
                            f.write(f"CONFIDENCE_THRESHOLD={confidence_threshold}\n")
                            f.write(f"MAX_CONTEXT_LENGTH={max_context_length}\n")
                        
                        st.success("Model ayarları başarıyla kaydedildi.")
                        
                    except Exception as e:
                        self.logger.error(f"Model ayarları kaydetme hatası: {str(e)}")
                        st.error("Model ayarları kaydedilirken bir hata oluştu.")
            
            st.markdown('</div>', unsafe_allow_html=True)
            
            # Sistem Ayarları
            st.markdown('<div class="settings-section">', unsafe_allow_html=True)
            st.header("Sistem Ayarları")
            
            with st.form(key="system_settings_form"):
                # Log seviyesi
                log_level = st.selectbox(
                    "Log Seviyesi",
                    ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
                    index=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"].index(
                        os.getenv('LOG_LEVEL', 'INFO')
                    ),
                    help="Loglama detay seviyesi"
                )
                
                # Otomatik yedekleme
                auto_backup = st.checkbox(
                    "Otomatik Yedekleme",
                    value=os.getenv('AUTO_BACKUP', 'True').lower() == 'true',
                    help="Verilerin otomatik yedeklenmesi"
                )
                
                # Yedekleme sıklığı
                backup_frequency = st.selectbox(
                    "Yedekleme Sıklığı",
                    ["Günlük", "Haftalık", "Aylık"],
                    index=["Günlük", "Haftalık", "Aylık"].index(
                        os.getenv('BACKUP_FREQUENCY', 'Günlük')
                    ),
                    help="Yedekleme periyodu"
                )
                
                # Kaydet butonu
                submitted = st.form_submit_button("Kaydet")
                if submitted:
                    try:
                        # .env dosyasını güncelle
                        with open('.env', 'a') as f:
                            f.write(f"LOG_LEVEL={log_level}\n")
                            f.write(f"AUTO_BACKUP={auto_backup}\n")
                            f.write(f"BACKUP_FREQUENCY={backup_frequency}\n")
                        
                        st.success("Sistem ayarları başarıyla kaydedildi.")
                        
                    except Exception as e:
                        self.logger.error(f"Sistem ayarları kaydetme hatası: {str(e)}")
                        st.error("Sistem ayarları kaydedilirken bir hata oluştu.")
            
            st.markdown('</div>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True) 