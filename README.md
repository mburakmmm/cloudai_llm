# Cloud AI LLM

Cloud AI LLM, yapay zeka destekli bir sohbet ve eğitim platformudur.

## Kurulum

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

## Ortam Değişkenleri (.env)

Uygulama çalışmadan önce aşağıdaki ortam değişkenlerinin ayarlanması gerekir:

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
3. Bu bilgileri `.env` dosyanıza ekleyin:
```env
SUPABASE_URL=your_project_url
SUPABASE_KEY=your_api_key
```

## Güvenlik Notları

- `.env` dosyası asla Git reposuna eklenmemelidir
- Supabase credentials'larını güvenli bir şekilde saklayın
- Production ortamında farklı bir `.env` dosyası kullanın

## Uygulama Başlatma

```bash
streamlit run streamlit_app.py
```

## Lisans

Bu proje MIT lisansı altında lisanslanmıştır.
