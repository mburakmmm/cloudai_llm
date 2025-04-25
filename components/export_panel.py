# components/export_panel.py
import streamlit as st
import json
import csv
from datetime import datetime
import logging
import asyncio
import pandas as pd
import io

class ExportPanel(ft.Container):
    def __init__(self, app):
        super().__init__()
        self.app = app
        self.logger = logging.getLogger(__name__)
        
        # Geri bildirim alanı
        self.feedback = ft.Text()
        
        # İçeriği oluştur
        self.content = ft.Column(
            [
                ft.Text("📤 Eğitim Verisi Aktarımı", size=24, weight="bold"),
                ft.Text("Hafızadaki verileri dışa aktarın.", 
                       size=13, italic=True),
                ft.Divider(),
                ft.ElevatedButton(
                    "JSON Olarak Dışa Aktar",
                    icon=ft.icons.DOWNLOAD,
                    on_click=self.export_json
                ),
                ft.ElevatedButton(
                    "CSV Olarak Dışa Aktar",
                    icon=ft.icons.DOWNLOAD,
                    on_click=self.export_csv
                ),
                self.feedback
            ],
            spacing=20,
            expand=True
        )
        
        # Filtreleme seçeneklerini başlat
        if 'selected_intent' not in st.session_state:
            st.session_state.selected_intent = None
        if 'start_date' not in st.session_state:
            st.session_state.start_date = None
        if 'end_date' not in st.session_state:
            st.session_state.end_date = None
        
    async def export_json(self, e):
        """JSON olarak dışa aktar"""
        try:
            # Hafızaları getir
            memories = await self.app.supabase_manager.export_memories(self.app.user_id)
            
            # Dosya adı oluştur
            filename = f"training_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            
            # JSON olarak kaydet
            with open(filename, "w", encoding="utf-8") as f:
                json.dump(memories, f, ensure_ascii=False, indent=2)
                
            self.feedback.value = f"✅ {filename} dosyası oluşturuldu."
            self.update()
            
        except Exception as e:
            self.app.show_error(f"Dışa aktarma hatası: {str(e)}")
            
    async def export_csv(self, e):
        """CSV olarak dışa aktar"""
        try:
            # Hafızaları getir
            memories = await self.app.supabase_manager.export_memories(self.app.user_id)
            
            # Dosya adı oluştur
            filename = f"training_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            
            # CSV olarak kaydet
            with open(filename, "w", encoding="utf-8", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=[
                    "prompt", "response", "intent", "tags", 
                    "priority", "usage_count", "category", 
                    "created_at"
                ])
                writer.writeheader()
                writer.writerows(memories)
                
            self.feedback.value = f"✅ {filename} dosyası oluşturuldu."
            self.update()
            
        except Exception as e:
            self.app.show_error(f"Dışa aktarma hatası: {str(e)}")
            
    async def did_mount(self):
        """Panel yüklendiğinde çağrılır"""
        try:
            # Supabase bağlantısını test et
            self.app.test_supabase_connection()
            
            # Dışa aktarma geçmişini yükle
            response = self.app.supabase.table("export_history").select("*").order("created_at", desc=True).execute()
            
            if response.data:
                for export in response.data:
                    self.add_export_item(
                        export["filename"],
                        export["size"],
                        export["created_at"]
                    )
                    
        except Exception as e:
            logging.error(f"Export panel başlatma hatası: {str(e)}")
            self.show_error("Bağlantı hatası. Lütfen internet bağlantınızı kontrol edin.")

    def render(self):
        """Export panelini göster"""
        # CSS stilleri
        st.markdown("""
            <style>
            .export-container {
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
            .format-container {
                background-color: white;
                padding: 2rem;
                border-radius: 20px;
                box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
            }
            </style>
        """, unsafe_allow_html=True)

        # Ana container
        with st.container():
            st.markdown('<div class="export-container">', unsafe_allow_html=True)
            
            # Başlık
            st.title("Veri Dışa Aktarma")
            
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
            
            # Format container
            st.markdown('<div class="format-container">', unsafe_allow_html=True)
            
            # Format seçimi
            export_format = st.radio(
                "Dışa Aktarma Formatı",
                ["CSV", "JSON", "Excel"],
                horizontal=True
            )
            
            # Dışa aktarma butonu
            if st.button("Dışa Aktar", use_container_width=True):
                try:
                    # Verileri al
                    query = self.app.supabase.table('training_data').select('*')
                    
                    if selected_intent != "Tümü":
                        query = query.eq('intent', selected_intent)
                    
                    if start_date:
                        query = query.gte('created_at', start_date.isoformat())
                    
                    if end_date:
                        query = query.lte('created_at', end_date.isoformat())
                    
                    response = query.execute()
                    
                    if response.data:
                        # DataFrame oluştur
                        df = pd.DataFrame(response.data)
                        
                        if export_format == "CSV":
                            # CSV olarak dışa aktar
                            csv = df.to_csv(index=False)
                            st.download_button(
                                label="CSV Dosyasını İndir",
                                data=csv,
                                file_name=f"training_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                                mime="text/csv"
                            )
                        elif export_format == "JSON":
                            json_data = df.to_json(orient="records", indent=2)
                            st.download_button(
                                label="JSON Dosyasını İndir",
                                data=json_data,
                                file_name="export.json",
                                mime="application/json"
                            )
                        elif export_format == "Excel":
                            # Excel olarak dışa aktar
                            excel = io.BytesIO()
                            with pd.ExcelWriter(excel, engine='xlsxwriter') as writer:
                                df.to_excel(writer, index=False)
                            st.download_button(
                                label="Excel Dosyasını İndir",
                                data=excel,
                                file_name=f"training_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                            )
                        else:
                            self.app.show_error("Geçersiz format seçildi.")
                except Exception as e:
                    self.app.show_error(f"Dışa aktarma hatası: {str(e)}")
            
            st.markdown('</div>', unsafe_allow_html=True)