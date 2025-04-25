# intent_classifier.py
from sentence_transformers import SentenceTransformer, util

model = SentenceTransformer('all-MiniLM-L6-v2')

INTENT_LIBRARY = {
    "selamlama": ["merhaba", "selam", "günaydın", "iyi akşamlar", "ne haber"],
    "veda": ["hoşçakal", "görüşürüz", "kendine iyi bak"],
    "soru": ["neden böyle oldu", "bu nasıl çalışıyor", "ne yapmalıyım"],
    "yardım talebi": ["yardım eder misin", "bana destek olabilir misin", "bir sorum var"],
    "onay": ["evet", "katılıyorum", "doğru"],
    "ret": ["hayır", "katılmıyorum", "yanlış"],
    "duygusal olumlu": ["mutluyum", "heyecanlıyım", "harika hissediyorum"],
    "duygusal olumsuz": ["üzgünüm", "mutsuzum", "sıkıldım", "sinirliyim"],
    "teşekkür": ["teşekkür ederim", "sağ ol", "minnettarım"],
    "özür": ["özür dilerim", "pardon", "kusura bakma"],
    "teknik destek": ["uygulama açılmıyor", "şifre sıfırlama", "giriş yapamıyorum"],
    "kodlama": ["python nedir", "if else örneği", "flutter ile sayfa geçişi"],
    "tıbbi": ["ateşim var", "başım ağrıyor", "ilaç önerir misin"],
    "kullanıcı bilgisi": ["ben doktorum", "öğrenciyim", "benim yaşım 23"],
    "bilgi talebi": ["bana bilgi ver", "detaylı açıkla", "bunu anlat"],
    "öneri isteme": ["hangi kitapları önerirsin", "ne izlemeliyim", "ne yapayım sence"],
    "sohbet": ["canım sıkılıyor", "biraz konuşalım", "sadece sohbet edelim"],
    "espiri": ["bana şaka yap", "komik bir şey anlat", "fıkra biliyor musun"],
    "motivasyon": ["motive edici bir şey söyle", "bana güç ver", "pozitif bir cümle"],
    "sistemsel": ["ayarları sıfırla", "verilerimi sil", "hesabımı kapat"]
}

def predict_intent(text):
    text_emb = model.encode(text, convert_to_tensor=True)
    best_intent = "genel"
    best_score = 0.5

    for intent, examples in INTENT_LIBRARY.items():
        for ex in examples:
            ex_emb = model.encode(ex, convert_to_tensor=True)
            score = float(util.pytorch_cos_sim(text_emb, ex_emb))
            if score > best_score:
                best_score = score
                best_intent = intent

    return best_intent, best_score
