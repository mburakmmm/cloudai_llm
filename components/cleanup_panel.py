# components/cleanup_panel.py
import streamlit as st
import logging
from datetime import datetime
import asyncio

class CleanupPanel:
    def __init__(self, app):
        self.app = app
        self.logger = logging.getLogger(__name__)
        
        # Session state başlatma
        if 'selected_items' not in st.session_state:
            st.session_state.selected_items = []
    
    def render(self):
        """Temizlik panelini göster"""
        # CSS stilleri
        st.markdown("""
            <style>
            .cleanup-container {
                display: flex;
                flex-direction: column;
                gap: 2rem;
            }
            .filter-container {
                background-color: white;
                padding: 2rem;
                border-radius: 20px;
                box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
            }
            .data-container {
                background-color: white;
                padding: 2rem;
                border-radius: 20px;
                box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
            }
            .item-card {
                padding: 1rem;
                margin-bottom: 1rem;
                border-radius: 10px;
                background-color: #f5f5f5;
            }
            </style>
        """, unsafe_allow_html=True)
        
        # Ana container
        with st.container():
            st.markdown('<div class="cleanup-container">', unsafe_allow_html=True)
            
            # Başlık
            st.title("Temizlik")
            
            # Filtre container
            st.markdown('<div class="filter-container">', unsafe_allow_html=True)
            
            # Filtre formu
            with st.form("filter_form"):
                col1, col2 = st.columns(2)
                
                with col1:
                    # Intent seçimi
                    try:
                        response = self.app.supabase.table('training_data').select('intent').execute()
                        intents = list(set([data['intent'] for data in response.data if data['intent']]))
                        selected_intent = st.selectbox(
                            "Intent",
                            ["Tümü"] + intents,
                            index=0
                        )
                    except Exception as e:
                        self.logger.error(f"Intent listesi yükleme hatası: {str(e)}")
                        selected_intent = "Tümü"
                
                with col2:
                    # Tarih seçimi
                    col1, col2 = st.columns(2)
                    with col1:
                        start_date = st.date_input("Başlangıç Tarihi")
                    with col2:
                        end_date = st.date_input("Bitiş Tarihi")
                
                filter_button = st.form_submit_button("Filtrele", use_container_width=True)
            
            st.markdown('</div>', unsafe_allow_html=True)
            
            # Veri container
            st.markdown('<div class="data-container">', unsafe_allow_html=True)
            
            try:
                # Verileri al
                query = self.app.supabase.table('training_data').select('*')
                
                if selected_intent != "Tümü":
                    query = query.eq('intent', selected_intent)
                
                if start_date:
                    query = query.gte('created_at', start_date.isoformat())
                
                if end_date:
                    query = query.lte('created_at', end_date.isoformat())
                
                response = query.order('created_at', desc=True).execute()
                
                if response.data:
                    # Verileri göster
                    for item in response.data:
                        with st.expander(f"ID: {item['id']} - Intent: {item['intent']}"):
                            st.markdown(f"""
                                <div class="item-card">
                                    <p><strong>Prompt:</strong> {item['prompt']}</p>
                                    <p><strong>Intent:</strong> {item['intent']}</p>
                                    <p><strong>Güven Skoru:</strong> {item['confidence_score']}</p>
                                    <p><strong>Oluşturulma Tarihi:</strong> {item['created_at']}</p>
                                </div>
                            """, unsafe_allow_html=True)
                            
                            # Silme butonu
                            if st.button("Sil", key=f"delete_{item['id']}"):
                                try:
                                    self.app.supabase.table('training_data').delete().eq('id', item['id']).execute()
                                    st.success("Veri başarıyla silindi.")
                                    st.rerun()
                                except Exception as e:
                                    self.logger.error(f"Veri silme hatası: {str(e)}")
                                    st.error("Veri silinirken bir hata oluştu.")
                else:
                    st.info("Filtre kriterlerine uygun veri bulunamadı.")
                
            except Exception as e:
                self.logger.error(f"Veri yükleme hatası: {str(e)}")
                st.error("Veriler yüklenirken bir hata oluştu.")
            
            st.markdown('</div>', unsafe_allow_html=True)
            
            st.markdown('</div>', unsafe_allow_html=True)
