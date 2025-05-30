# Cloud AI LLM

Cloud AI LLM, yapay zeka destekli bir sohbet ve eğitim platformudur.

## Yerel Kurulum

1. Repoyu klonlayın:
```bash
git clone https://github.com/mburakmmm/cloudai_llm.git
cd cloudai_llm
```

2. Virtual environment oluşturun ve aktif edin:
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac için
# veya
.\venv\Scripts\activate  # Windows için
```

3. Gerekli paketleri yükleyin:
```bash
pip install -r requirements.txt
```

4. Ortam değişkenlerini ayarlayın:
   - `.env.example` dosyasını `.env` olarak kopyalayın
   - `.env` dosyasını kendi credentials'larınızla güncelleyin

```bash
cp .env.example .env
```

## Streamlit Cloud Deployment

1. [Streamlit Cloud](https://streamlit.io/cloud) hesabınıza giriş yapın

2. "New app" butonuna tıklayın

3. GitHub reponuzu seçin ve main branch'i belirleyin

4. Advanced Settings'de Python versiyonunu seçin (3.10 önerilen)

5. Secrets yönetimi:
   - Settings > Secrets menüsüne gidin
   - Aşağıdaki içeriği `.streamlit/secrets.toml` formatında ekleyin:
   ```toml
   # Supabase Credentials
   SUPABASE_URL = "your_supabase_url_here"
   SUPABASE_KEY = "your_supabase_key_here"

   # Model Settings
   MODEL_PATH = "models/"
   MODEL_NAME = "cloud_llm"
   CONFIDENCE_THRESHOLD = 0.7
   MAX_CONTEXT_LENGTH = 2000

   # Logging
   LOG_LEVEL = "INFO"

   # Backup Settings
   AUTO_BACKUP = true
   BACKUP_FREQUENCY = "Günlük"

   # Optional Settings
   TTS_ENABLED = false
   DARK_MODE = false
   ```

6. Deploy butonuna tıklayın

Not: Streamlit Cloud'da environment variables yerine `st.secrets` kullanılır. Uygulama kodunda aşağıdaki gibi erişebilirsiniz:
```python
import streamlit as st

# .env'den okuma
supabase_url = os.getenv("SUPABASE_URL")

# Streamlit secrets'dan okuma
supabase_url = st.secrets["SUPABASE_URL"]
```

## Ortam Değişkenleri

Uygulama çalışmadan önce aşağıdaki değişkenlerin ayarlanması gerekir:

### Zorunlu Değişkenler:

- `SUPABASE_URL`: Supabase proje URL'iniz
- `SUPABASE_KEY`: Supabase API anahtarınız

### Opsiyonel Değişkenler:

- `MODEL_PATH`: Model dosyalarının bulunduğu klasör (varsayılan: models/)
- `MODEL_NAME`: Kullanılacak model adı (varsayılan: cloud_llm)
- `CONFIDENCE_THRESHOLD`: Minimum güven skoru (varsayılan: 0.7)
- `MAX_CONTEXT_LENGTH`: Maksimum bağlam uzunluğu (varsayılan: 2000)
- `LOG_LEVEL`: Loglama seviyesi (varsayılan: INFO)
- `AUTO_BACKUP`: Otomatik yedekleme (varsayılan: True)
- `BACKUP_FREQUENCY`: Yedekleme sıklığı (varsayılan: Günlük)
- `TTS_ENABLED`: Ses sentezi özelliği (varsayılan: False)
- `DARK_MODE`: Karanlık tema (varsayılan: False)

## Supabase Kurulumu

1. [Supabase](https://supabase.com) üzerinde yeni bir proje oluşturun
2. Proje ayarlarından URL ve API Key bilgilerini alın
3. Bu bilgileri:
   - Yerel geliştirme için `.env` dosyanıza
   - Streamlit Cloud için Secrets yönetimine ekleyin

## Güvenlik Notları

- `.env` dosyası asla Git reposuna eklenmemelidir
- Supabase credentials'larını güvenli bir şekilde saklayın
- Production ortamında farklı credentials kullanın
- Streamlit Cloud'da secrets.toml dosyasını güvenli bir şekilde yönetin

## Yerel Geliştirme İçin Uygulama Başlatma

```bash
streamlit run streamlit_app.py
```

## Lisans

Bu proje MIT lisansı altında lisanslanmıştır.
