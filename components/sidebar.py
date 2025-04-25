import streamlit as st
import logging

logger = logging.getLogger(__name__)

class Sidebar:
    def __init__(self):
        if "selected_panel" not in st.session_state:
            st.session_state.selected_panel = "chat"
            
    def render(self):
        with st.sidebar:
            st.title("Menü")
            
            # Ana menü seçenekleri
            menu_items = [
                "Sohbet", "Hafıza", "Eğitici", "Temizle",
                "Ayarlar", "İstatistikler", "Intent Grupları",
                "Dışa Aktar"
            ]
            
            selected = st.radio("Seçiniz", menu_items)
            
            if selected != st.session_state.selected_panel:
                st.session_state.selected_panel = selected
                st.rerun()
            
            # Ayarlar
            st.divider()
            
            # TTS ve tema ayarları
            col1, col2 = st.columns(2)
            with col1:
                tts = st.toggle("TTS", value=st.session_state.get("tts_enabled", False))
                if tts != st.session_state.get("tts_enabled", False):
                    st.session_state.tts_enabled = tts
                    
            with col2:
                dark_mode = st.toggle("Karanlık Mod", value=st.session_state.get("dark_mode", False))
                if dark_mode != st.session_state.get("dark_mode", False):
                    st.session_state.dark_mode = dark_mode
                    st.rerun()
            
            # Çıkış butonu
            st.divider()
            if st.button("Çıkış Yap", type="primary"):
                st.session_state.clear()
                st.rerun() 