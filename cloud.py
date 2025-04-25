# cloud.py
from sentence_transformers import SentenceTransformer, util
from settings import settings
from match_logger import log_match
from intent_classifier import predict_intent
from prompt_variants import is_paraphrase
from memory_sqlite import SQLiteMemoryManager
import logging
from datetime import datetime
import asyncio
from typing import Dict, List, Optional, Any
from supabase import create_client, Client
import os
from dotenv import load_dotenv
import nest_asyncio
import torch
import numpy as np

# .env dosyasını yükle
load_dotenv()

# Debug loglarını aç
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Hata mesajlarını özelleştir
ERRORS = {
    "input_error": "Üzgünüm, girdiğiniz mesajı anlayamadım. Lütfen daha açık bir şekilde ifade eder misiniz?",
    "memory_error": "Hafıza işlemi sırasında bir hata oluştu. Lütfen tekrar deneyin.",
    "learning_error": "Öğrenme sırasında bir hata oluştu. Ancak bu sohbetimizi etkilemeyecek.",
    "response_error": "Yanıt oluşturulurken bir hata oluştu. Lütfen tekrar deneyin.",
    "tts_error": "Ses dönüşümü sırasında bir hata oluştu. Metin olarak devam ediyorum.",
    "stt_error": "Ses tanıma sırasında bir hata oluştu. Lütfen tekrar deneyin veya yazarak ilerlemeyi deneyin."
}

# Event loop sorununu çöz
try:
    loop = asyncio.get_event_loop()
except RuntimeError:
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
nest_asyncio.apply()

class CloudAI:
    def __init__(self):
        # Supabase bağlantısı
        supabase_url = os.getenv("SUPABASE_URL", "https://dnnuvhzfihduvyalmzru.supabase.co")
        supabase_key = os.getenv("SUPABASE_KEY", "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZS1kZW1vIiwicm9sZSI6ImFub24iLCJleHAiOjE5ODM4MTI5OTZ9.CRXP1A7WOeoJeXxjNni43kdQwgnWNReilDMblYTn_I0")
        self.supabase: Client = create_client(supabase_url, supabase_key)
        logger.info(f"Supabase bağlantısı başarılı - URL: {supabase_url}")

        # Event loop yönetimi
        try:
            self.loop = asyncio.get_event_loop()
        except RuntimeError:
            self.loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self.loop)

        # NLP modeli yükleme - PyTorch ayarları
        device = 'cpu'  # Varsayılan olarak CPU kullan
        if torch.backends.mps.is_available():
            device = 'mps'
        elif torch.cuda.is_available():
            device = 'cuda'
            
        self.model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2', device=device)
        logger.debug(f"CloudAI initialized with device: {device}")

        # SQLite bellek yöneticisi
        self.memory_manager = SQLiteMemoryManager()

        self.context_length = int(os.getenv("MAX_CONTEXT_LENGTH", 1024))
        self.confidence_threshold = float(os.getenv("CONFIDENCE_THRESHOLD", 0.7))
        self.history = []
        self.current_topic = None
        self.conversation_state = {}
        self.emotion_state = "neutral"
        
        # TTS ve STT ayarlarını kontrol et
        self.tts_enabled = settings.get("TTS_ENABLED", False)
        self.stt_enabled = settings.get("STT_ENABLED", False)
        
        if self.tts_enabled:
            try:
                from gtts import gTTS
                import pygame
                self.gTTS = gTTS
                self.pygame = pygame
                pygame.mixer.init()
            except ImportError:
                logger.warning("TTS için gerekli kütüphaneler yüklü değil")
                self.tts_enabled = False
                
        if self.stt_enabled:
            try:
                import speech_recognition as sr
                self.sr = sr
                self.recognizer = sr.Recognizer()
            except ImportError:
                logger.warning("STT için gerekli kütüphaneler yüklü değil")
                self.stt_enabled = False
        
        # Gelişmiş NLP özellikleri
        self.nlp_features = {
            "word_embeddings": {},
            "sentence_templates": [],
            "context_rules": [],
            "language_models": {},
            "semantic_networks": {},
            "grammar_patterns": {},
            "word_senses": {},
            "phrase_chunks": {},
            "dependency_trees": {},
            "coreference_chains": {}
        }
        
        # Öğrenme sistemi
        self.learning_system = {
            "word_patterns": {},
            "response_patterns": {},
            "topic_transitions": {},
            "user_habits": {
                "topics": {},
                "emotions": {},
                "interaction_count": 0,
                "time_patterns": {}
            },
            "learning_rate": 0.1,
            "adaptation_threshold": 0.7,
            "knowledge_base": {},
            "reinforcement": {
                "state_space": {},
                "action_space": {},
                "rewards": {},
                "policy": {},
                "value_function": {}
            },
            "transfer": {
                "source_domains": {},
                "target_domains": {},
                "mapping_rules": {}
            },
            "meta": {
                "learning_strategies": {},
                "adaptation_rules": {},
                "performance_metrics": {}
            }
        }
        
        # Duygu analizi sözlükleri
        self.emotion_lexicon = {
            "neutral": {
                "words": ["nasılsın", "naber", "ne haber", "iyi misin", "merhaba", "selam"],
                "emojis": ["😐", "🙂", "👋"],
                "intensity": 0.0
            },
            "mutluluk": {
                "words": ["mutlu", "sevinç", "harika", "mükemmel", "teşekkür", "sağol", "güzel", "harika", "müthiş"],
                "emojis": ["😊", "😄", "😍", "🥰", "🤗"],
                "intensity": 1.0
            },
            "üzüntü": {
                "words": ["üzgün", "kötü", "berbat", "yorgun", "bitkin", "moral", "bozuk"],
                "emojis": ["😔", "😢", "😞", "😥", "😭"],
                "intensity": -1.0
            },
            "öfke": {
                "words": ["kızgın", "sinir", "kızdım", "sinirlendim", "öfke", "kızgınım"],
                "emojis": ["😠", "😡", "🤬", "👿", "💢"],
                "intensity": -0.8
            },
            "şaşkınlık": {
                "words": ["şaşırdım", "vay", "vay canına", "inanılmaz", "harika"],
                "emojis": ["😲", "😮", "🤯", "😳", "😱"],
                "intensity": 0.5
            },
            "korku": {
                "words": ["korktum", "korkuyorum", "endişe", "kaygı", "panik"],
                "emojis": ["😨", "😰", "😱", "😖", "😫"],
                "intensity": -0.7
            },
            "sevgi": {
                "words": ["seviyorum", "aşk", "kalp", "canım", "tatlım"],
                "emojis": ["❤️", "💕", "💖", "💗", "💝"],
                "intensity": 0.9
            }
        }
        
        # Duygu durumu geçmişi
        self.emotion_history = {
            "current_emotion": "neutral",
            "emotion_timeline": [],
            "emotion_intensity": 0.0,
            "last_emotion_change": None,
            "emotion_triggers": {},
            "emotion_patterns": []
        }
        
        # Konuşma bağlamı yönetimi
        self.conversation_context = {
            "current_topic": None,
            "previous_topics": [],
            "topic_history": [],
            "last_question": None,
            "pending_questions": [],
            "context_window": [],
            "conversation_flow": [],
            "topic_switch_count": 0,
            "last_topic_switch_time": None
        }
        
        # Kullanıcı tercihleri
        self.user_preferences = {
            "response_style": "normal",
            "language_preference": "tr",
            "favorite_topics": set(),
            "disliked_topics": set(),
            "interaction_count": 0,
            "last_interaction_time": None
        }
        
        # Eş anlamlı kelimeler sözlüğü
        self.synonyms = {
            "merhaba": ["selam", "hey", "hi", "hello"],
            "güle güle": ["hoşça kal", "bay bay", "bye", "görüşürüz"],
            "nasılsın": ["iyi misin", "ne haber", "ne var ne yok"],
            "teşekkür": ["sağol", "eyvallah", "thanks", "thank you"],
            "evet": ["tabi", "olur", "tamam", "yes"],
            "hayır": ["olmaz", "yok", "no", "nope"],
        }
        
        # Cümle yapısı kalıpları
        self.sentence_patterns = {
            "soru": ["mi", "mı", "mu", "mü", "?", "ne", "nasıl", "neden", "kim", "ne zaman"],
            "emir": ["lütfen", "rica", "yap", "et", "getir", "ver"],
            "istek": ["isterim", "istiyorum", "arzu", "dilek"],
        }

    def run_async(self, coro):
        """Asenkron fonksiyonları çalıştırmak için yardımcı metod"""
        try:
            return self.loop.run_until_complete(coro)
        except Exception as e:
            logger.error(f"Asenkron işlem hatası: {str(e)}")
            return None

    def preprocess_text(self, text: str) -> str:
        """Metni temizler ve hazırlar"""
        try:
            if not isinstance(text, str):
                text = str(text)
            
            text = text.strip()
            if not text:
                raise ValueError("Boş metin vektörleştirilemez")
                
            return text
            
        except Exception as e:
            logger.error(f"Metin ön işleme hatası: {str(e)}")
            raise

    def encode_text(self, text: str) -> np.ndarray:
        """Metni vektöre dönüştürür"""
        try:
            # Metni temizle ve hazırla
            text = self.preprocess_text(text)
            
            # Vektör hesapla
            with torch.no_grad():
                embedding = self.model.encode(text)
                # PyTorch tensörünü NumPy dizisine dönüştür
                if torch.is_tensor(embedding):
                    embedding = embedding.cpu().numpy()
                return embedding
                
        except Exception as e:
            logger.error(f"Metin kodlama hatası: {str(e)}")
            return None

    def is_meaningful_input(self, text: str) -> bool:
        """Girişin anlamlı olup olmadığını kontrol et"""
        try:
            # Basit kontroller
            if not text or len(text.strip()) < 2:
                return False
                
            # Kelime sayısı kontrolü
            words = text.split()
            if len(words) < 1:
                return False
                
            return True
            
        except Exception as e:
            logger.error(f"Giriş kontrolü hatası: {str(e)}")
            return False

    async def process_message(self, message: str) -> Optional[str]:
        """Kullanıcı mesajını işle ve yanıt üret"""
        try:
            # Giriş kontrolü
            if not self.is_meaningful_input(message):
                return "Lütfen geçerli bir mesaj girin."
                
            # Mesaj vektörünü hesapla
            message_embedding = self.encode_text(message)
            
            # En benzer yanıtı bul
            response, similarity = self.memory_manager.find_best_response(message_embedding)
            
            if response and similarity > 0.7:
                return response
            else:
                return "Üzgünüm, bu konuda yardımcı olamıyorum."
                
        except Exception as e:
            logger.error(f"Mesaj işleme hatası: {str(e)}")
            return None

    async def learn(self, prompt: str, response: str, intent: str = "genel") -> bool:
        """Yeni bir prompt-yanıt çifti öğren"""
        try:
            # Giriş kontrolü
            if not self.is_meaningful_input(prompt) or not self.is_meaningful_input(response):
                return False
                
            # Vektör hesapla
            try:
                prompt_embedding = self.encode_text(prompt)
            except Exception as e:
                logger.error(f"Vektör hesaplama hatası: {str(e)}")
                return False
                
            # Hafızaya ekle
            memory_data = {
                "prompt": prompt,
                "response": response,
                "embedding": prompt_embedding,
                "intent": intent,
                "created_at": datetime.now().isoformat()
            }
            
            try:
                memory_id = self.memory_manager.add_memory(memory_data)
                logger.info(f"Yeni bellek eklendi: {memory_id}")
                return True
            except Exception as e:
                logger.error(f"Hafıza ekleme hatası: {str(e)}")
                return False
                
        except Exception as e:
            logger.error(f"Öğrenme hatası: {str(e)}")
            return False

    def get_training_data(self, intent: str = None, limit: int = 100) -> List[Dict[str, Any]]:
        """Eğitim verilerini getir"""
        try:
            return self.memory_manager.get_all_memories()
        except Exception as e:
            logger.error(f"Eğitim verisi getirme hatası: {str(e)}")
            return []

    def delete_training_data(self, memory_id: int) -> bool:
        """Eğitim verisini sil"""
        try:
            return self.memory_manager.delete_memory(memory_id)
        except Exception as e:
            logger.error(f"Eğitim verisi silme hatası: {str(e)}")
            return False

    async def test_connection(self) -> bool:
        """Bağlantı testi yap"""
        try:
            # Test verisi
            test_prompt = "test_connection"
            test_response = "connection_successful"
            
            # Test verisini ekle
            await self.learn(test_prompt, test_response)
            
            # Test verisini sil
            memories = self.get_training_data()
            for memory in memories:
                if memory["prompt"] == test_prompt:
                    self.delete_training_data(memory["id"])
                    
            return True
            
        except Exception as e:
            logger.error(f"Bağlantı testi hatası: {str(e)}")
            return False

    def sync_test_connection(self) -> bool:
        """Supabase bağlantısını test eder ve veritabanı yapısını kontrol eder."""
        try:
            logger.debug("Supabase bağlantı testi başlatılıyor...")
            
            # Gerekli sütunları kontrol et
            required_columns = [
                "prompt",
                "response",
                "intent",
                "confidence_score",
                "created_at"
            ]
            
            # Test verisi oluştur
            test_data = {
                "prompt": "test_prompt",
                "response": "test_response",
                "intent": "test_intent",
                "confidence_score": 1.0,
                "created_at": datetime.now().isoformat()
            }
            
            # Sütunları kontrol et
            try:
                result = self.supabase.table('training_data').select("*").limit(1).execute()
                if result.data:
                    existing_columns = list(result.data[0].keys())
                    missing_columns = [col for col in required_columns if col not in existing_columns]
                    if missing_columns:
                        logger.error(f"Eksik sütunlar: {missing_columns}")
                        return False
            except Exception as e:
                logger.error(f"Sütun kontrolü hatası: {str(e)}")
                return False
            
            # Test verisini ekle
            result = self.supabase.table('training_data').insert(test_data).execute()
            logger.info(f"Test verisi eklendi: {result.data}")
            
            # Eklenen veriyi sil
            if result.data and len(result.data) > 0:
                test_id = result.data[0]['id']
                self.supabase.table('training_data').delete().eq('id', test_id).execute()
                logger.info("Test verisi başarıyla silindi")
            
            logger.info("Supabase bağlantı testi başarılı!")
            return True
            
        except Exception as e:
            logger.error(f"Supabase bağlantı testi başarısız: {str(e)}")
            return False

    def sync_process_message(self, message: str) -> tuple[str, float]:
        """Mesajı işle ve yanıt döndür"""
        try:
            # Mesajı ön işle
            processed_message = self.preprocess_text(message)
            
            # Eğer mesaj anlamlı değilse hata döndür
            if not self.is_meaningful_input(processed_message):
                return ERRORS["input_error"], 0.0
                
            # Mesajı vektöre dönüştür
            message_embedding = self.encode_text(processed_message)
            
            # Hafızada benzer mesajları ara
            similar_memories = self.memory_manager.find_similar_memories(
                message_embedding,
                threshold=self.confidence_threshold
            )
            
            # Eğer benzer mesaj bulunamazsa
            if not similar_memories:
                # Temel yanıtları kontrol et
                if processed_message.lower() in ["merhaba", "selam", "hey", "hi", "hello"]:
                    return "Merhaba! Size nasıl yardımcı olabilirim?", 1.0
                elif processed_message.lower() in ["nasılsın", "iyi misin", "ne haber"]:
                    return "İyiyim, teşekkür ederim! Siz nasılsınız?", 1.0
                elif processed_message.lower() in ["teşekkür", "sağol", "eyvallah"]:
                    return "Rica ederim! Başka bir konuda yardımcı olabilir miyim?", 1.0
                elif processed_message.lower() in ["güle güle", "hoşça kal", "bay bay"]:
                    return "Güle güle! İyi günler dilerim.", 1.0
                else:
                    return ERRORS["input_error"], 0.0
            
            # En iyi eşleşmeyi bul
            best_match = max(similar_memories, key=lambda x: x["similarity"])
            
            # Yanıtı döndür
            return best_match["response"], best_match["similarity"]
            
        except Exception as e:
            logger.error(f"Mesaj işleme hatası: {str(e)}")
            return ERRORS["response_error"], 0.0

    async def learn(self, prompt: str, response: str, intent: str = None) -> bool:
        """Yeni bir prompt-yanıt çifti öğrenir."""
        try:
            logger.info(f"Yeni eğitim verisi ekleniyor - Prompt: {prompt}, Intent: {intent}")
            
            # Vektör hesapla
            try:
                prompt_embedding = self.encode_text(prompt)
            except Exception as e:
                logger.error(f"Vektör hesaplama hatası: {str(e)}")
                return False
            
            # Veritabanına kaydet
            try:
                self.memory_manager.add_memory(prompt, prompt_embedding, response, intent)
            except Exception as e:
                logger.error(f"Bellek yöneticisi hatası: {str(e)}")
                return False
            
            # Supabase'e kaydet
            try:
                training_data = {
                    "prompt": prompt,
                    "response": response,
                    "intent": intent,
                    "confidence_score": 1.0,  # Öğrenme sırasında güven skoru 1.0
                    "created_at": datetime.now().isoformat()
                }
                
                result = self.supabase.table('training_data').insert(training_data).execute()
                
                if not result.data:
                    raise Exception("Supabase'e veri eklenemedi")
                    
                logger.info(f"Eğitim verisi başarıyla eklendi - ID: {result.data[0]['id']}")
                return True
            except Exception as e:
                logger.error(f"Supabase kayıt hatası: {str(e)}")
                return False
                
        except Exception as e:
            logger.error(f"Eğitim verisi eklenirken hata: {str(e)}")
            return False

    def sync_learn(self, prompt: str, response: str, intent: str = None) -> bool:
        """Senkron olarak yeni bir prompt-yanıt çifti öğrenir."""
        try:
            if not self.loop.is_running():
                return self.loop.run_until_complete(self.learn(prompt, response, intent))
            else:
                future = asyncio.run_coroutine_threadsafe(self.learn(prompt, response, intent), self.loop)
                return future.result(timeout=10)  # 10 saniye timeout
        except Exception as e:
            logger.error(f"Senkron öğrenme hatası: {str(e)}")
            return False

    async def delete_training_data(self, id: int) -> bool:
        """Belirtilen ID'ye sahip eğitim verisini siler."""
        try:
            self.supabase.table('training_data').delete().eq('id', id).execute()
            return True
        except Exception as e:
            logger.error(f"Eğitim verisi silme hatası: {str(e)}")
            return False

    def sync_delete_training_data(self, id: int) -> bool:
        """Senkron olarak eğitim verisini siler."""
        try:
            return self.run_async(self.delete_training_data(id))
        except Exception as e:
            logger.error(f"Senkron silme hatası: {str(e)}")
            return False

    def test_training(self):
        """Test eğitim verisi ekleme ve silme işlemlerini."""
        logger.info("Eğitim testi başlatılıyor...")
        
        # Test verisi
        test_data = {
            "prompt": "Merhaba, nasılsın?",
            "response": "İyiyim, teşekkür ederim. Siz nasılsınız?",
            "intent": "selamlaşma",
            "tags": ["selam", "hal hatır"],
            "priority": 1,
            "context_message": "",
            "category": "genel"
        }
        
        # Belleğe ekle
        memory_id = self.memory_manager.add_memory(test_data)
        if memory_id:
            logger.info(f"Test verisi belleğe eklendi - ID: {memory_id}")
            
            # Supabase'e ekle
            try:
                data = {
                    "prompt": test_data["prompt"],
                    "response": test_data["response"],
                    "intent": test_data["intent"],
                    "confidence_score": 0.95
                }
                result = self.supabase.table("training_data").insert(data).execute()
                
                if result.data:
                    logger.info("Test verisi Supabase'e başarıyla eklendi")
                    return True
                else:
                    logger.error("Test verisi Supabase'e eklenemedi")
                    return False
                    
            except Exception as e:
                logger.error(f"Eğitim testi başarısız: {e}")
                return False
        else:
            logger.error("Test verisi belleğe eklenemedi")
            return False

    def sync_train(self, prompt: str, response: str, intent: str = None, tags: list = None) -> bool:
        """Senkron eğitim metodu"""
        try:
            # Giriş kontrolü
            if not self.is_meaningful_input(prompt) or not self.is_meaningful_input(response):
                logger.warning("Anlamsız giriş tespit edildi")
                return False
                
            # Vektör hesapla
            try:
                prompt_embedding = self.encode_text(prompt)
                # PyTorch tensörünü NumPy dizisine dönüştür
                if torch.is_tensor(prompt_embedding):
                    prompt_embedding = prompt_embedding.cpu().numpy()
            except Exception as e:
                logger.error(f"Vektör hesaplama hatası: {str(e)}")
                return False
                
            # Belleğe ekle
            try:
                memory_data = {
                    "prompt": prompt,
                    "response": response,
                    "embedding": prompt_embedding,
                    "intent": intent or "genel",
                    "created_at": datetime.now().isoformat()
                }
                
                memory_id = self.memory_manager.add_memory(memory_data)
                logger.info(f"Yeni bellek eklendi: {memory_id}")
                
                # Supabase'e kaydet
                training_data = {
                    "prompt": prompt,
                    "response": response,
                    "intent": intent or "genel",
                    "confidence_score": 1.0,
                    "created_at": datetime.now().isoformat()
                }
                
                result = self.supabase.table('training_data').insert(training_data).execute()
                
                if not result.data:
                    raise Exception("Supabase'e veri eklenemedi")
                    
                logger.info(f"Eğitim verisi başarıyla eklendi - ID: {result.data[0]['id']}")
                return True
                
            except Exception as e:
                logger.error(f"Bellek/Supabase kayıt hatası: {str(e)}")
                return False
                
        except Exception as e:
            logger.error(f"Eğitim verisi eklenirken hata: {str(e)}")
            return False

