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
            
            # Zorunlu alanlar
            prompt = st.text_area("Prompt (Zorunlu)", height=100, value=st.session_state.current_prompt)
            response = st.text_area("Response (Zorunlu)", height=150, value=st.session_state.current_response)
            intent = st.text_input("Intent (Zorunlu)", value=st.session_state.current_intent)
            tags = st.text_input("Tags (Zorunlu)", value=st.session_state.current_tag, help="Virgülle ayırarak birden fazla tag ekleyebilirsiniz")
            
            # Opsiyonel alanlar
            col1, col2 = st.columns(2)
            with col1:
                priority = st.number_input("Priority (Opsiyonel)", min_value=1, value=1)
            with col2:
                category = st.selectbox("Category (Opsiyonel)", ["genel", "teknik", "müşteri", "diğer"])
            
            submit = st.form_submit_button("Eğitim Verisini Ekle", use_container_width=True)
            
            if submit:
                if not prompt or not response or not intent or not tags:
                    st.error("Lütfen zorunlu alanları doldurun.")
                    return
                    
                try:
                    # Tags'ı listeye çevir
                    tags_list = [tag.strip() for tag in tags.split(",")]
                    
                    success = self.app.cloud_ai.sync_train(
                        prompt=prompt,
                        response=response,
                        intent=intent,
                        tags=tags_list,
                        priority=priority,
                        category=category
                    )
                    
                    if success:
                        st.success("Eğitim verisi başarıyla eklendi!")
                        st.balloons()
                        # Form alanlarını temizle
                        st.session_state.current_prompt = ""
                        st.session_state.current_response = ""
                        st.session_state.current_intent = ""
                        st.session_state.current_tag = ""
                        # Form alanlarını temizle
                        st.experimental_rerun()
                    else:
                        st.error("Eğitim verisi eklenirken bir hata oluştu.")
                        
                except Exception as e:
                    st.error(f"Eğitim sırasında bir hata oluştu: {str(e)}")
