# components/ai_intent_group_panel.py
import streamlit as st
import logging
from datetime import datetime
import asyncio
import pandas as pd

class AIIntentGroupPanel:
    def __init__(self, app):
        self.app = app
        self.supabase = app.supabase
        self.logger = logging.getLogger(__name__)
        
        # Filtreleme seçeneklerini başlat
        if 'selected_intent' not in st.session_state:
            st.session_state.selected_intent = None
        if 'start_date' not in st.session_state:
            st.session_state.start_date = None
        if 'end_date' not in st.session_state:
            st.session_state.end_date = None

    def render(self):
        """AI Intent Grupları panelini göster"""
        # CSS stilleri
        st.markdown("""
            <style>
            .groups-container {
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
            .groups-list {
                background-color: white;
                padding: 2rem;
                border-radius: 20px;
                box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
            }
            .group-item {
                padding: 1rem;
                margin-bottom: 1rem;
                border-radius: 10px;
                background-color: #f5f5f5;
            }
            .group-header {
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin-bottom: 0.5rem;
            }
            .group-content {
                margin-top: 0.5rem;
            }
            .intent-list {
                margin-top: 0.5rem;
                padding-left: 1rem;
            }
            .intent-item {
                margin-bottom: 0.5rem;
                padding: 0.5rem;
                background-color: #e8e8e8;
                border-radius: 5px;
            }
            </style>
        """, unsafe_allow_html=True)

        # Ana container
        with st.container():
            st.markdown('<div class="groups-container">', unsafe_allow_html=True)
            
            # Başlık
            st.title("Intent Grupları")
            
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
            
            # Gruplar listesi
            st.markdown('<div class="groups-list">', unsafe_allow_html=True)
            
            try:
                # Intent gruplarını al
                query = self.supabase.table('ai_intent_groups').select('*')
                
                if selected_intent != "Tümü":
                    query = query.eq('intent', selected_intent)
                
                if start_date:
                    query = query.gte('created_at', start_date.isoformat())
                
                if end_date:
                    query = query.lte('created_at', end_date.isoformat())
                
                response = query.order('created_at', desc=True).execute()
                
                if response.data:
                    for group in response.data:
                        st.markdown(f"""
                            <div class="group-item">
                                <div class="group-header">
                                    <h3>{group['group_name']}</h3>
                                    <span>{group['created_at']}</span>
                                </div>
                                <div class="group-content">
                                    <p><strong>Açıklama:</strong> {group['description']}</p>
                                    <p><strong>Oluşturan:</strong> {group['created_by']}</p>
                                    <div class="intent-list">
                                        <p><strong>İçerdiği Intentler:</strong></p>
                                        {''.join([f'<div class="intent-item">{intent}</div>' for intent in group['intents']])}
                                    </div>
                                </div>
                            </div>
                        """, unsafe_allow_html=True)
                else:
                    st.info("Filtre kriterlerine uygun grup bulunamadı.")
                
            except Exception as e:
                self.logger.error(f"Intent grupları yükleme hatası: {str(e)}")
                st.error("Intent grupları yüklenirken bir hata oluştu.")
            
            st.markdown('</div>', unsafe_allow_html=True)
            
            # Yeni grup ekleme
            with st.expander("Yeni Intent Grubu Ekle"):
                with st.form("new_intent_group"):
                    name = st.text_input("Grup Adı")
                    description = st.text_area("Açıklama")
                    intents = st.text_area("Intentler (her satıra bir tane)")
                    priority = st.number_input("Öncelik", min_value=1, value=1)
                    submit = st.form_submit_button("Ekle")
                    
                    if submit and name:
                        try:
                            # Intent listesini oluştur
                            intent_list = [i.strip() for i in intents.split('\n') if i.strip()]
                            
                            # Yeni grubu ekle
                            data = {
                                "name": name,
                                "description": description,
                                "intents": intent_list,
                                "priority": priority
                            }
                            self.supabase.table('ai_intent_groups').insert(data).execute()
                            st.success("Intent grubu başarıyla eklendi!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Grup eklenirken hata oluştu: {str(e)}")
            
            # Mevcut grupları listele
            result = self.supabase.table('ai_intent_groups').select("*").execute()
            intent_groups = result.data if result else []
            
            for group in intent_groups:
                with st.expander(f"{group['name']} (Öncelik: {group['priority']})"):
                    st.write(f"**Açıklama:** {group['description']}")
                    st.write("**Intentler:**")
                    for intent in group['intents']:
                        st.write(f"- {intent}")
                        
                    # Silme butonu
                    if st.button(f"Sil {group['name']}", key=f"delete_{group['id']}"):
                        try:
                            self.supabase.table('ai_intent_groups').delete().eq('id', group['id']).execute()
                            st.success("Grup başarıyla silindi!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Grup silinirken hata oluştu: {str(e)}")
            
            st.markdown('</div>', unsafe_allow_html=True)
            
            st.markdown('</div>', unsafe_allow_html=True)
