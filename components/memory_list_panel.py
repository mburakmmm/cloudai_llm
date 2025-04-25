# components/memory_list_panel.py
import streamlit as st
import logging
from datetime import datetime
import asyncio

class MemoryListPanel:
    def __init__(self, app):
        self.app = app
        self.logger = logging.getLogger(__name__)

    def render(self):
        """Hafıza listesi panelini göster"""
        # CSS stilleri
        st.markdown("""
            <style>
            .memory-container {
                max-width: 800px;
                margin: 0 auto;
                padding: 2rem;
            }
            .memory-item {
                background-color: white;
                padding: 1rem;
                border-radius: 20px;
                box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
                margin-bottom: 1rem;
            }
            </style>
        """, unsafe_allow_html=True)
        
        # Ana container
        with st.container():
            st.markdown('<div class="memory-container">', unsafe_allow_html=True)
            
            # Başlık
            st.title("Hafıza Listesi")
            
            # Filtreleme seçenekleri
            col1, col2 = st.columns(2)
            with col1:
                search_term = st.text_input("Arama", placeholder="Hafızada ara...")
            with col2:
                date_filter = st.date_input("Tarih Filtresi")
            
            # Hafıza listesi
            memories = self.app.supabase.table('training_data').select('*').execute()
            
            if memories.data:
                for memory in memories.data:
                    with st.container():
                        st.markdown('<div class="memory-item">', unsafe_allow_html=True)
                        st.write(f"**Prompt:** {memory['prompt']}")
                        st.write(f"**Intent:** {memory['intent']}")
                        st.write(f"**Güven Skoru:** {memory['confidence_score']}")
                        st.write(f"**Tarih:** {memory['created_at']}")
                        st.markdown('</div>', unsafe_allow_html=True)
            else:
                st.info("Henüz hafızada kayıtlı veri bulunmuyor.")
            
            st.markdown('</div>', unsafe_allow_html=True)
