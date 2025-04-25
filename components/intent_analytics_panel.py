# components/intent_analytics_panel.py
import streamlit as st
import logging
from datetime import datetime
import asyncio
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

class IntentAnalyticsPanel:
    def __init__(self, app):
        self.app = app
        self.logger = logging.getLogger(__name__)
        
        # Filtreleme seçeneklerini başlat
        if 'selected_intent' not in st.session_state:
            st.session_state.selected_intent = None
        if 'start_date' not in st.session_state:
            st.session_state.start_date = None
        if 'end_date' not in st.session_state:
            st.session_state.end_date = None

    def render(self):
        """Intent analiz panelini göster"""
        # CSS stilleri
        st.markdown("""
            <style>
            .analytics-container {
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
            .stats-container {
                background-color: white;
                padding: 2rem;
                border-radius: 20px;
                box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
            }
            .chart-container {
                background-color: white;
                padding: 2rem;
                border-radius: 20px;
                box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
            }
            .stat-card {
                padding: 1rem;
                margin-bottom: 1rem;
                border-radius: 10px;
                background-color: #f5f5f5;
            }
            </style>
        """, unsafe_allow_html=True)

        # Ana container
        with st.container():
            st.markdown('<div class="analytics-container">', unsafe_allow_html=True)
            
            # Başlık
            st.title("Intent Analizi")
            
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
                    # DataFrame oluştur
                    df = pd.DataFrame(response.data)
                    
                    # İstatistikler container
                    st.markdown('<div class="stats-container">', unsafe_allow_html=True)
                    
                    # İstatistikler
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        st.markdown(f"""
                            <div class="stat-card">
                                <h3>Toplam Intent</h3>
                                <p>{len(df['intent'].unique())}</p>
                            </div>
                        """, unsafe_allow_html=True)
                    
                    with col2:
                        st.markdown(f"""
                            <div class="stat-card">
                                <h3>Toplam Örnek</h3>
                                <p>{len(df)}</p>
                            </div>
                        """, unsafe_allow_html=True)
                    
                    with col3:
                        st.markdown(f"""
                            <div class="stat-card">
                                <h3>Ortalama Güven</h3>
                                <p>{df['confidence'].mean():.2f}</p>
                            </div>
                        """, unsafe_allow_html=True)
                    
                    st.markdown('</div>', unsafe_allow_html=True)
                    
                    # Grafikler container
                    st.markdown('<div class="chart-container">', unsafe_allow_html=True)
                    
                    # Intent dağılımı
                    st.markdown("### Intent Dağılımı")
                    intent_counts = df['intent'].value_counts()
                    fig = px.bar(
                        x=intent_counts.index,
                        y=intent_counts.values,
                        labels={'x': 'Intent', 'y': 'Örnek Sayısı'}
                    )
                    st.plotly_chart(fig, use_container_width=True)
                    
                    # Güven skoru dağılımı
                    st.markdown("### Güven Skoru Dağılımı")
                    fig = px.histogram(
                        df,
                        x='confidence',
                        nbins=20,
                        labels={'x': 'Güven Skoru', 'y': 'Örnek Sayısı'}
                    )
                    st.plotly_chart(fig, use_container_width=True)
                    
                    # Günlük örnek sayısı
                    st.markdown("### Günlük Örnek Sayısı")
                    df['date'] = pd.to_datetime(df['created_at']).dt.date
                    daily_counts = df.groupby('date').size().reset_index(name='count')
                    fig = px.line(
                        daily_counts,
                        x='date',
                        y='count',
                        labels={'x': 'Tarih', 'y': 'Örnek Sayısı'}
                    )
                    st.plotly_chart(fig, use_container_width=True)
                    
                    st.markdown('</div>', unsafe_allow_html=True)
                
                else:
                    st.info("Filtre kriterlerine uygun veri bulunamadı.")
                
            except Exception as e:
                self.logger.error(f"Veri yükleme hatası: {str(e)}")
                st.error("Veriler yüklenirken bir hata oluştu.")
            
            st.markdown('</div>', unsafe_allow_html=True)
