# analytics.py
import pandas as pd
import numpy as np
from typing import Dict, List, Any
from datetime import datetime, timedelta
import logging
from memory_sqlite import SQLiteMemoryManager
from intent_optimizer import IntentOptimizer

logger = logging.getLogger(__name__)

class Analytics:
    def __init__(self):
        self.memory_manager = SQLiteMemoryManager()
        self.intent_optimizer = IntentOptimizer()
        
    def get_usage_stats(self, days: int = 30) -> Dict[str, Any]:
        """Kullanım istatistiklerini getir"""
        try:
            memories = self.memory_manager.load_memory()
            df = pd.DataFrame(memories)
            
            if df.empty:
                return {
                    "total_interactions": 0,
                    "active_users": 0,
                    "avg_response_time": 0,
                    "success_rate": 0
                }
            
            # Tarih filtreleme
            df['created_at'] = pd.to_datetime(df['created_at'])
            start_date = datetime.now() - timedelta(days=days)
            df = df[df['created_at'] >= start_date]
            
            # İstatistikleri hesapla
            stats = {
                "total_interactions": len(df),
                "active_users": df['user_id'].nunique() if 'user_id' in df.columns else 0,
                "avg_response_time": df['response_time'].mean() if 'response_time' in df.columns else 0,
                "success_rate": (df['avg_match_score'] >= 0.7).mean() if 'avg_match_score' in df.columns else 0
            }
            
            return stats
            
        except Exception as e:
            logger.error(f"Kullanım istatistikleri hatası: {str(e)}")
            return {}
            
    def get_intent_analytics(self) -> Dict[str, Any]:
        """İstek analitiği getir"""
        try:
            # İstek istatistiklerini al
            intent_stats = self.intent_optimizer.get_intent_stats()
            
            # İstek geçişlerini al
            transition_matrix = self.intent_optimizer.get_transition_matrix()
            
            # En başarılı istekleri bul
            success_rates = {
                intent: stats["avg_success_rate"]
                for intent, stats in intent_stats.items()
            }
            top_intents = sorted(
                success_rates.items(),
                key=lambda x: x[1],
                reverse=True
            )[:5]
            
            return {
                "intent_stats": intent_stats,
                "transition_matrix": transition_matrix,
                "top_intents": top_intents
            }
            
        except Exception as e:
            logger.error(f"İstek analitiği hatası: {str(e)}")
            return {}
            
    def get_emotion_analytics(self) -> Dict[str, Any]:
        """Duygu analitiği getir"""
        try:
            memories = self.memory_manager.load_memory()
            df = pd.DataFrame(memories)
            
            if df.empty or 'emotion' not in df.columns:
                return {
                    "emotion_distribution": {},
                    "emotion_trends": {},
                    "emotion_triggers": {}
                }
            
            # Duygu dağılımı
            emotion_dist = df['emotion'].value_counts().to_dict()
            
            # Duygu trendleri
            df['created_at'] = pd.to_datetime(df['created_at'])
            emotion_trends = df.groupby([
                df['created_at'].dt.date,
                'emotion'
            ]).size().unstack(fill_value=0).to_dict()
            
            # Duygu tetikleyicileri
            emotion_triggers = df.groupby('emotion')['prompt'].agg(list).to_dict()
            
            return {
                "emotion_distribution": emotion_dist,
                "emotion_trends": emotion_trends,
                "emotion_triggers": emotion_triggers
            }
            
        except Exception as e:
            logger.error(f"Duygu analitiği hatası: {str(e)}")
            return {}
            
    def get_performance_metrics(self) -> Dict[str, float]:
        """Performans metriklerini getir"""
        try:
            memories = self.memory_manager.load_memory()
            df = pd.DataFrame(memories)
            
            if df.empty:
                return {
                    "avg_response_time": 0,
                    "avg_match_score": 0,
                    "success_rate": 0,
                    "memory_utilization": 0
                }
            
            metrics = {
                "avg_response_time": df['response_time'].mean() if 'response_time' in df.columns else 0,
                "avg_match_score": df['avg_match_score'].mean() if 'avg_match_score' in df.columns else 0,
                "success_rate": (df['avg_match_score'] >= 0.7).mean() if 'avg_match_score' in df.columns else 0,
                "memory_utilization": len(df) / 10000  # Maksimum bellek kapasitesine göre
            }
            
            return metrics
            
        except Exception as e:
            logger.error(f"Performans metrikleri hatası: {str(e)}")
            return {}
