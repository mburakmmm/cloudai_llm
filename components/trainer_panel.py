# components/trainer_panel.py
import streamlit as st
import logging
from cloud import CloudAI
from datetime import datetime

class TrainerPanel:
    def __init__(self, app):
        self.app = app
        self.cloud_ai = CloudAI()
        self.logger = logging.getLogger(__name__)
        
        # Session state başlatma
        if 'training_data' not in st.session_state:
            st.session_state.training_data = []
        if 'current_prompt' not in st.session_state:
            st.session_state.current_prompt = ""
        if 'current_response' not in st.session_state:
            st.session_state.current_response = ""
        if 'current_tag' not in st.session_state:
            st.session_state.current_tag = ""
        if 'current_intent' not in st.session_state:
            st.session_state.current_intent = ""
        
    def render(self):
        st.title("Eğitim Paneli")
        
        with st.form("training_form"):
            st.markdown("### Yeni Eğitim Verisi Ekle")
            
            prompt = st.text_area("Soru/Prompt", height=100)
            response = st.text_area("Yanıt/Response", height=150)
            intent = st.text_input("Intent (Opsiyonel)")
            
            col1, col2 = st.columns(2)
            with col1:
                priority = st.number_input("Öncelik", min_value=1, value=1)
            with col2:
                category = st.selectbox("Kategori", ["genel", "teknik", "müşteri", "diğer"])
            
            submit = st.form_submit_button("Eğitim Verisini Ekle", use_container_width=True)
            
            if submit:
                if not prompt or not response:
                    st.error("Lütfen soru ve yanıt alanlarını doldurun.")
                    return
                    
                try:
                    success = self.app.cloud_ai.sync_train(
                        prompt=prompt,
                        response=response,
                        intent=intent,
                        tags=[category]
                    )
                    
                    if success:
                        st.success("Eğitim verisi başarıyla eklendi!")
                        st.balloons()
                    else:
                        st.error("Eğitim verisi eklenirken bir hata oluştu.")
                        
                except Exception as e:
                    st.error(f"Eğitim sırasında bir hata oluştu: {str(e)}")
