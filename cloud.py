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
from typing import Dict, List, Optional, Any, Tuple
from supabase import create_client, Client
import os
from dotenv import load_dotenv
import nest_asyncio
import torch
import numpy as np
import streamlit as st

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

# Supabase bağlantısı için güvenli yapılandırma
supabase_url = os.getenv("SUPABASE_URL")
supabase_key = os.getenv("SUPABASE_KEY")

if not supabase_url or not supabase_key:
    raise ValueError("Supabase bağlantı bilgileri eksik. Lütfen .env dosyasını kontrol edin.")

class CloudAI:
    def __init__(self):
        # Supabase bağlantısı
        self.supabase = create_client(
            os.getenv("SUPABASE_URL"),
            os.getenv("SUPABASE_KEY")
        )
        logger.info("Supabase bağlantısı başarılı")

        # NLP modeli yükleme - PyTorch ayarları
        device = self._get_device()
        self.model = self._load_model(device)
        
        # SQLite bellek yöneticisi
        self.memory_manager = SQLiteMemoryManager()
        
        # Yapılandırma
        self._load_config()
        
        # Sistemleri başlat
        self._initialize_systems()

    def _get_device(self) -> str:
        """Kullanılacak cihazı belirle"""
        if torch.backends.mps.is_available():
            return 'mps'
        elif torch.cuda.is_available():
            return 'cuda'
        return 'cpu'

    def _load_model(self, device: str) -> SentenceTransformer:
        """NLP modelini yükle"""
        try:
            model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2', device=device)
            logger.debug(f"Model başarıyla yüklendi - Device: {device}")
            return model
        except Exception as e:
            logger.error(f"Model yükleme hatası: {str(e)}")
            raise

    def _load_config(self):
        """Yapılandırma ayarlarını yükle"""
        try:
            self.context_length = int(os.getenv("MAX_CONTEXT_LENGTH", 1024))
            self.confidence_threshold = float(os.getenv("CONFIDENCE_THRESHOLD", 0.7))
            self.tts_enabled = settings.get("TTS_ENABLED", False)
            self.stt_enabled = settings.get("STT_ENABLED", False)
            
            # TTS ve STT için gerekli kütüphaneleri kontrol et
            if self.tts_enabled:
                self._setup_tts()
            if self.stt_enabled:
                self._setup_stt()
                
        except Exception as e:
            logger.error(f"Yapılandırma yükleme hatası: {str(e)}")
            raise

    def _setup_tts(self):
        """TTS sistemini kur"""
        try:
            from gtts import gTTS
            import pygame
            self.gTTS = gTTS
            self.pygame = pygame
            pygame.mixer.init()
        except ImportError:
            logger.warning("TTS için gerekli kütüphaneler yüklü değil")
            self.tts_enabled = False

    def _setup_stt(self):
        """STT sistemini kur"""
        try:
            import speech_recognition as sr
            self.sr = sr
            self.recognizer = sr.Recognizer()
        except ImportError:
            logger.warning("STT için gerekli kütüphaneler yüklü değil")
            self.stt_enabled = False

    def _initialize_systems(self):
        """Alt sistemleri başlat"""
        try:
            # Geçmiş
            self.history = []
            self.current_topic = None
            
            # Durum yönetimi
            self.conversation_state = {}
            self.emotion_state = "neutral"
            
            # NLP özellikleri
            self._init_nlp_features()
            
            # Öğrenme sistemi
            self._init_learning_system()
            
            # Duygu analizi
            self._init_emotion_system()
            
            # Konuşma bağlamı
            self._init_conversation_context()
            
            # Kullanıcı tercihleri
            self._init_user_preferences()
            
        except Exception as e:
            logger.error(f"Sistem başlatma hatası: {str(e)}")
            raise

    def _init_nlp_features(self):
        """NLP özelliklerini başlat"""
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

    def _init_learning_system(self):
        """Öğrenme sistemini başlat"""
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

    def _init_emotion_system(self):
        """Duygu analizi sistemini başlat"""
        self.emotion_lexicon = {
            "neutral": {
                "words": ["nasılsın", "naber", "ne haber", "iyi misin", "merhaba", "selam"],
                "emojis": ["😐", "🙂", "👋"],
                "intensity": 0.0
            },
            "mutluluk": {
                "words": ["mutlu", "sevinç", "harika", "mükemmel", "teşekkür", "sağol"],
                "emojis": ["😊", "😄", "😍"],
                "intensity": 1.0
            },
            "üzüntü": {
                "words": ["üzgün", "kötü", "berbat", "yorgun", "bitkin"],
                "emojis": ["😔", "😢", "😞"],
                "intensity": -1.0
            }
        }
        
        self.emotion_history = {
            "current_emotion": "neutral",
            "emotion_timeline": [],
            "emotion_intensity": 0.0,
            "last_emotion_change": None,
            "emotion_triggers": {},
            "emotion_patterns": []
        }

    def _init_conversation_context(self):
        """Konuşma bağlamını başlat"""
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

    def _init_user_preferences(self):
        """Kullanıcı tercihlerini başlat"""
        self.user_preferences = {
            "response_style": "normal",
            "language_preference": "tr",
            "favorite_topics": set(),
            "disliked_topics": set(),
            "interaction_count": 0,
            "last_interaction_time": None
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

    def analyze_emotion(self, text: str) -> dict:
        """Metindeki duygu durumunu analiz et"""
        try:
            # Varsayılan değerler
            max_intensity = 0.0
            current_emotion = "neutral"
            
            # Giriş kontrolü
            if not isinstance(text, str) or not text.strip():
                logger.warning("Geçersiz metin girişi")
                return {
                    "emotion": current_emotion,
                    "intensity": max_intensity,
                    "emoji": "😐"
                }
            
            # Kelimeleri kontrol et
            text_lower = text.lower()
            for emotion, data in self.emotion_lexicon.items():
                for word in data["words"]:
                    if word in text_lower:
                        intensity = float(data["intensity"])  # Sayısal değere dönüştür
                        if abs(intensity) > abs(max_intensity):
                            max_intensity = intensity
                            current_emotion = emotion
            
            # Duygu geçmişini güncelle
            try:
                self.emotion_history["current_emotion"] = current_emotion
                self.emotion_history["emotion_intensity"] = max_intensity
                self.emotion_history["emotion_timeline"].append({
                    "emotion": current_emotion,
                    "intensity": max_intensity,
                    "timestamp": datetime.now().isoformat()
                })
            except Exception as e:
                logger.error(f"Duygu geçmişi güncelleme hatası: {str(e)}")
            
            # Sonuç sözlüğünü oluştur
            result = {
                "emotion": current_emotion,
                "intensity": float(max_intensity),  # Sayısal değer olduğundan emin ol
                "emoji": self.emotion_lexicon[current_emotion]["emojis"][0]
            }
            
            logger.debug(f"Duygu analizi sonucu: {result}")
            return result
            
        except Exception as e:
            logger.error(f"Duygu analizi hatası: {str(e)}")
            # Hata durumunda varsayılan değerleri döndür
            return {
                "emotion": "neutral",
                "intensity": 0.0,
                "emoji": "😐"
            }

    def update_context(self, message: str, intent: str = None):
        """Konuşma bağlamını akıllı bir şekilde güncelle"""
        try:
            current_time = datetime.now()
            
            # Konu değişikliği tespiti
            topic_changed = False
            if intent and self.conversation_context["current_topic"] != intent:
                topic_changed = True
                self.conversation_context["topic_switch_count"] += 1
                self.conversation_context["last_topic_switch_time"] = current_time.isoformat()
                
                # Önceki konuyu kaydet
                if self.conversation_context["current_topic"]:
                    self.conversation_context["previous_topics"].append({
                        "topic": self.conversation_context["current_topic"],
                        "duration": (current_time - datetime.fromisoformat(self.conversation_context["last_topic_switch_time"])).seconds,
                        "messages_count": len([m for m in self.conversation_context["context_window"] 
                                            if m["topic"] == self.conversation_context["current_topic"]]),
                        "timestamp": current_time.isoformat()
                    })
            
            # Yeni konuyu belirle
            self.conversation_context["current_topic"] = intent or "genel"
            
            # Konu geçmişini güncelle
            self.conversation_context["topic_history"].append({
                "topic": self.conversation_context["current_topic"],
                "message": message,
                "timestamp": current_time.isoformat(),
                "topic_changed": topic_changed
            })
            
            # Bağlam penceresini güncelle
            new_context = {
                "message": message,
                "topic": self.conversation_context["current_topic"],
                "timestamp": current_time.isoformat(),
                "topic_changed": topic_changed
            }
            
            # Soru kontrolü
            if any(q in message.lower() for q in ["?", "mi", "mı", "mu", "mü", "ne", "nasıl", "neden", "kim"]):
                self.conversation_context["last_question"] = new_context
                self.conversation_context["pending_questions"].append(new_context)
            
            # Bağlam penceresini güncelle ve sınırla
            self.conversation_context["context_window"].append(new_context)
            if len(self.conversation_context["context_window"]) > 5:
                self.conversation_context["context_window"].pop(0)
                
            # Konuşma akışını analiz et
            self.conversation_context["conversation_flow"].append({
                "timestamp": current_time.isoformat(),
                "topic": self.conversation_context["current_topic"],
                "topic_changed": topic_changed,
                "message_type": "question" if "?" in message else "statement",
                "context_size": len(self.conversation_context["context_window"])
            })
            
            # Kullanıcı tercihlerini güncelle
            if topic_changed:
                self.user_preferences["favorite_topics"].add(self.conversation_context["current_topic"])
                self.user_preferences["interaction_count"] += 1
                self.user_preferences["last_interaction_time"] = current_time.isoformat()
                
        except Exception as e:
            logger.error(f"Bağlam güncelleme hatası: {str(e)}")

    def generate_response(self, message: str, intent: str = None) -> str:
        """Mesaja uygun akıllı yanıt oluştur"""
        try:
            # Duygu analizi
            emotion_data = self.analyze_emotion(message)
            current_emotion = emotion_data["emotion"]
            emotion_intensity = emotion_data["intensity"]
            
            # Bağlam analizi
            self.update_context(message, intent)
            context_window = self.conversation_context["context_window"]
            current_topic = self.conversation_context["current_topic"]
            
            # Kullanıcı tercihleri analizi
            user_style = self.user_preferences["response_style"]
            favorite_topics = self.user_preferences["favorite_topics"]
            
            # Yanıt önceliği belirleme
            response_priority = {
                "context_match": 0.4,
                "emotion_match": 0.3,
                "intent_match": 0.2,
                "user_preference": 0.1
            }
            
            best_response = None
            max_score = 0
            
            # Öğrenme sisteminden yanıtları değerlendir
            for pattern, response in self.learning_system["response_patterns"].items():
                score = 0
                
                # Bağlam uyumu
                if any(c["topic"] == current_topic for c in context_window):
                    score += response_priority["context_match"]
                    
                # Duygu uyumu
                response_emotion = self.analyze_emotion(response)
                if response_emotion["emotion"] == current_emotion:
                    score += response_priority["emotion_match"]
                    
                # Intent uyumu
                if intent and intent in pattern:
                    score += response_priority["intent_match"]
                    
                # Kullanıcı tercihleri
                if current_topic in favorite_topics:
                    score += response_priority["user_preference"]
                    
                if score > max_score:
                    max_score = score
                    best_response = response
            
            # En iyi yanıtı seç veya yeni yanıt oluştur
            if best_response and max_score > 0.5:
                base_response = best_response
            else:
                # Temel yanıtları oluştur
                if intent == "selamlaşma":
                    base_response = self._generate_greeting(emotion_data)
                elif intent == "hal_hatır":
                    base_response = self._generate_wellbeing_response(emotion_data)
                elif intent == "teşekkür":
                    base_response = self._generate_gratitude_response(emotion_data)
                else:
                    base_response = "Üzgünüm, bu konuda yardımcı olamıyorum."
            
            # Yanıtı kişiselleştir
            final_response = self._personalize_response(base_response, user_style, emotion_data)
            
            # Yanıtı öğrenme sistemine ekle
            self.learning_system["response_patterns"][message.lower()] = final_response
            
            return final_response
            
        except Exception as e:
            logger.error(f"Yanıt oluşturma hatası: {str(e)}")
            return ERRORS["response_error"]
        
    def _generate_greeting(self, emotion_data: dict) -> str:
        """Selamlaşma yanıtı oluştur"""
        if emotion_data["emotion"] == "mutluluk":
            return f"Merhaba! {emotion_data['emoji']} Harika bir gün, değil mi? Size nasıl yardımcı olabilirim?"
        elif emotion_data["emotion"] == "üzüntü":
            return f"Merhaba... {emotion_data['emoji']} Üzgün görünüyorsunuz, bir şey mi oldu?"
        else:
            return "Merhaba! Size nasıl yardımcı olabilirim?"

    def _generate_wellbeing_response(self, emotion_data: dict) -> str:
        """Hal hatır yanıtı oluştur"""
        if emotion_data["emotion"] == "mutluluk":
            return f"Ben de çok iyiyim! {emotion_data['emoji']} Mutluluğunuz bana da yansıdı!"
        elif emotion_data["emotion"] == "üzüntü":
            return f"İyiyim, teşekkürler. Ama sizi üzgün görmek beni de üzdü {emotion_data['emoji']} Paylaşmak ister misiniz?"
        else:
            return "İyiyim, teşekkür ederim. Siz nasılsınız?"

    def _generate_gratitude_response(self, emotion_data: dict) -> str:
        """Teşekkür yanıtı oluştur"""
        if emotion_data["emotion"] == "mutluluk":
            return f"Rica ederim! {emotion_data['emoji']} Size yardımcı olabildiğime çok sevindim!"
        else:
            return "Rica ederim! Her zaman yardımcı olmaktan mutluluk duyarım."

    def _personalize_response(self, response: str, style: str, emotion_data: dict) -> str:
        """Yanıtı kişiselleştir"""
        try:
            if style == "formal":
                response = response.replace("!", ".")
                response = response.replace("merhaba", "iyi günler")
            elif style == "casual":
                response = response.replace("iyi günler", "selam")
                response = response.replace(".", "!")
            
            # Emoji ekle
            if emotion_data["intensity"] > 0.5:
                response += f" {emotion_data['emoji']}"
            
            return response
            
        except Exception as e:
            logger.error(f"Yanıt kişiselleştirme hatası: {str(e)}")
            return response

    def sync_process_message(self, message: str) -> tuple[str, float]:
        """Mesajı işle ve yanıt döndür"""
        try:
            # Mesajı ön işle
            processed_message = self.preprocess_text(message)
            logger.debug(f"İşlenmiş mesaj: {processed_message}")
            
            # Embedding hesapla
            message_embedding = self.encode_text(processed_message)
            logger.debug("Embedding hesaplandı")
            
            # Intent belirle
            intent = predict_intent(processed_message)
            logger.debug(f"Intent: {intent}")
            
            # Duygu analizi
            try:
                emotion_data = self.analyze_emotion(processed_message)
                logger.debug(f"Duygu analizi sonucu: {emotion_data}")
                
                if not isinstance(emotion_data, dict):
                    logger.error(f"Duygu analizi geçersiz veri döndürdü: {type(emotion_data)}")
                    emotion_data = {"emotion": "neutral", "intensity": 0.0, "emoji": "😐"}
            except Exception as e:
                logger.error(f"Duygu analizi hatası: {str(e)}")
                emotion_data = {"emotion": "neutral", "intensity": 0.0, "emoji": "😐"}
            
            # Bağlamı güncelle
            self.update_context(processed_message, intent)
            
            # Yanıt oluştur
            response = self.generate_response(processed_message, intent)
            logger.debug(f"Oluşturulan yanıt: {response}")
            
            # Öğrenme sistemini güncelle
            self.update_learning_system(processed_message, response)
            
            # Yanıtı hafızaya ekle
            try:
                memory_data = {
                    "prompt": processed_message,
                    "response": response,
                    "embedding": message_embedding,
                    "intent": intent,
                    "emotion": emotion_data["emotion"],
                    "created_at": datetime.now().isoformat()
                }
                
                self.memory_manager.add_memory(memory_data)
                logger.debug("Hafızaya eklendi")
            except Exception as e:
                logger.error(f"Hafıza ekleme hatası: {str(e)}")
            
            # Güven skorunu hesapla
            try:
                intensity = emotion_data.get("intensity", 0.0)
                logger.debug(f"Duygu yoğunluğu: {intensity}, Tipi: {type(intensity)}")
                
                if intensity is None:
                    confidence = 0.0
                else:
                    confidence = float(abs(intensity))
                
                logger.debug(f"Hesaplanan güven skoru: {confidence}")
            except Exception as e:
                logger.error(f"Güven skoru hesaplama hatası: {str(e)}")
                confidence = 0.0
            
            return response, confidence
            
        except Exception as e:
            logger.error(f"Mesaj işleme hatası: {str(e)}")
            return ERRORS["response_error"], 0.0

    def update_learning_system(self, message: str, response: str, feedback: float = None):
        """Öğrenme sistemini güncelle"""
        try:
            current_time = datetime.now()
            
            # Kelime kalıplarını güncelle
            words = message.lower().split()
            for word in words:
                if word not in self.learning_system["word_patterns"]:
                    self.learning_system["word_patterns"][word] = {
                        "count": 0,
                        "contexts": set(),
                        "responses": set()
                    }
                self.learning_system["word_patterns"][word]["count"] += 1
                self.learning_system["word_patterns"][word]["contexts"].add(self.conversation_context["current_topic"])
                self.learning_system["word_patterns"][word]["responses"].add(response)
            
            # Yanıt kalıplarını güncelle
            if message.lower() not in self.learning_system["response_patterns"]:
                self.learning_system["response_patterns"][message.lower()] = response
            
            # Konu geçişlerini güncelle
            if len(self.conversation_context["topic_history"]) > 1:
                prev_topic = self.conversation_context["topic_history"][-2]["topic"]
                curr_topic = self.conversation_context["topic_history"][-1]["topic"]
                
                if prev_topic != curr_topic:
                    transition_key = f"{prev_topic}->{curr_topic}"
                    if transition_key not in self.learning_system["topic_transitions"]:
                        self.learning_system["topic_transitions"][transition_key] = {
                            "count": 0,
                            "success_rate": 0.0,
                            "last_used": None
                        }
                    self.learning_system["topic_transitions"][transition_key]["count"] += 1
                    self.learning_system["topic_transitions"][transition_key]["last_used"] = current_time.isoformat()
            
            # Kullanıcı alışkanlıklarını güncelle
            topic = self.conversation_context["current_topic"]
            if topic not in self.learning_system["user_habits"]["topics"]:
                self.learning_system["user_habits"]["topics"][topic] = {
                    "count": 0,
                    "avg_duration": 0,
                    "success_rate": 0.0,
                    "last_used": None
                }
            
            self.learning_system["user_habits"]["topics"][topic]["count"] += 1
            self.learning_system["user_habits"]["topics"][topic]["last_used"] = current_time.isoformat()
            
            # Duygu durumunu güncelle
            emotion = self.emotion_history["current_emotion"]
            if emotion not in self.learning_system["user_habits"]["emotions"]:
                self.learning_system["user_habits"]["emotions"][emotion] = {
                    "count": 0,
                    "triggers": set(),
                    "responses": set()
                }
            
            self.learning_system["user_habits"]["emotions"][emotion]["count"] += 1
            self.learning_system["user_habits"]["emotions"][emotion]["triggers"].add(message.lower())
            self.learning_system["user_habits"]["emotions"][emotion]["responses"].add(response)
            
            # Zaman kalıplarını güncelle
            hour = current_time.hour
            if hour not in self.learning_system["user_habits"]["time_patterns"]:
                self.learning_system["user_habits"]["time_patterns"][hour] = {
                    "count": 0,
                    "topics": set(),
                    "emotions": set()
                }
            
            self.learning_system["user_habits"]["time_patterns"][hour]["count"] += 1
            self.learning_system["user_habits"]["time_patterns"][hour]["topics"].add(topic)
            self.learning_system["user_habits"]["time_patterns"][hour]["emotions"].add(emotion)
            
            # Etkileşim sayısını güncelle
            self.learning_system["user_habits"]["interaction_count"] += 1
            
            # Geri bildirim varsa başarı oranlarını güncelle
            if feedback is not None:
                # Konu geçiş başarısını güncelle
                if len(self.conversation_context["topic_history"]) > 1:
                    transition_key = f"{prev_topic}->{curr_topic}"
                    current_success = self.learning_system["topic_transitions"][transition_key]["success_rate"]
                    new_success = (current_success * (self.learning_system["topic_transitions"][transition_key]["count"] - 1) + feedback) / self.learning_system["topic_transitions"][transition_key]["count"]
                    self.learning_system["topic_transitions"][transition_key]["success_rate"] = new_success
                
                # Konu başarısını güncelle
                current_success = self.learning_system["user_habits"]["topics"][topic]["success_rate"]
                topic_count = self.learning_system["user_habits"]["topics"][topic]["count"]
                new_success = (current_success * (topic_count - 1) + feedback) / topic_count
                self.learning_system["user_habits"]["topics"][topic]["success_rate"] = new_success
            
            # Öğrenme stratejilerini güncelle
            self._update_learning_strategies()
            
        except Exception as e:
            logger.error(f"Öğrenme sistemi güncelleme hatası: {str(e)}")

    def _update_learning_strategies(self):
        """Öğrenme stratejilerini güncelle"""
        try:
            # Başarılı yanıt kalıplarını belirle
            successful_patterns = {}
            for topic, data in self.learning_system["user_habits"]["topics"].items():
                if data["success_rate"] > self.learning_system["adaptation_threshold"]:
                    successful_patterns[topic] = {
                        "success_rate": data["success_rate"],
                        "count": data["count"]
                    }
            
            # Başarılı kalıpları öğrenme stratejilerine ekle
            self.learning_system["meta"]["learning_strategies"] = successful_patterns
            
            # Adaptasyon kurallarını güncelle
            self.learning_system["meta"]["adaptation_rules"] = {
                "min_success_rate": self.learning_system["adaptation_threshold"],
                "min_interaction_count": 5,
                "learning_rate": self.learning_system["learning_rate"]
            }
            
            # Performans metriklerini güncelle
            total_success = sum(data["success_rate"] * data["count"] for data in self.learning_system["user_habits"]["topics"].values())
            total_count = sum(data["count"] for data in self.learning_system["user_habits"]["topics"].values())
            
            if total_count > 0:
                avg_success = total_success / total_count
            else:
                avg_success = 0.0
                
            self.learning_system["meta"]["performance_metrics"] = {
                "average_success_rate": avg_success,
                "total_interactions": total_count,
                "successful_patterns_count": len(successful_patterns)
            }
            
        except Exception as e:
            logger.error(f"Öğrenme stratejileri güncelleme hatası: {str(e)}")

    def get_learning_stats(self) -> dict:
        """Öğrenme sistemi istatistiklerini getir"""
        try:
            return {
                "total_interactions": self.learning_system["user_habits"]["interaction_count"],
                "known_patterns": len(self.learning_system["word_patterns"]),
                "topic_transitions": len(self.learning_system["topic_transitions"]),
                "average_success": self.learning_system["meta"]["performance_metrics"]["average_success_rate"],
                "successful_patterns": self.learning_system["meta"]["performance_metrics"]["successful_patterns_count"]
            }
        except Exception as e:
            logger.error(f"Öğrenme istatistikleri getirme hatası: {str(e)}")
            return {}

    def close(self):
        """Sistemleri güvenli bir şekilde kapat"""
        try:
            # Veritabanı bağlantılarını kapat
            if hasattr(self, 'memory_manager'):
                del self.memory_manager
                
            # PyTorch modelini temizle
            if hasattr(self, 'model'):
                del self.model
                
            # Supabase bağlantısını kapat
            if hasattr(self, 'supabase'):
                del self.supabase
                
            logger.info("Sistem başarıyla kapatıldı")
            
        except Exception as e:
            logger.error(f"Sistem kapatma hatası: {str(e)}")

    def __del__(self):
        """Yıkıcı metod"""
        self.close()

    def sync_login(self, email: str, password: str) -> bool:
        """Senkron giriş işlemi"""
        try:
            # Supabase auth işlemi
            auth_response = self.supabase.auth.sign_in_with_password({
                "email": email,
                "password": password
            })
            
            if auth_response and hasattr(auth_response.user, 'id'):
                return True
            return False
            
        except Exception as e:
            logger.error(f"Giriş hatası: {str(e)}")
            return False

    def sync_register(self, email: str, password: str) -> bool:
        """Senkron kayıt işlemi"""
        try:
            # Supabase auth işlemi
            auth_response = self.supabase.auth.sign_up({
                "email": email,
                "password": password
            })
            
            if auth_response and hasattr(auth_response.user, 'id'):
                return True
            return False
            
        except Exception as e:
            logger.error(f"Kayıt hatası: {str(e)}")
            return False

