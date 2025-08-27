"""
Sistema de predicción inteligente para minimizar requests a APIs
Predice cuándo es necesario actualizar datos y usa fallbacks inteligentes
"""

from django.utils import timezone
from datetime import timedelta
import numpy as np
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)

class DataFreshnessPredictor:
    """Predice cuándo los datos necesitan actualizarse"""
    
    def __init__(self):
        # Patrones de actualización por tipo de dato
        self.update_patterns = {
            'live_scores': {
                'base_interval': 30,  # segundos
                'volatility_factor': 2.0,  # multiplica intervalo durante eventos
                'peak_hours': [17, 18, 19, 20, 21],
                'weekend_multiplier': 1.5
            },
            'match_schedules': {
                'base_interval': 3600,  # 1 hora
                'volatility_factor': 0.5,
                'peak_hours': [9, 10, 11, 12],
                'weekend_multiplier': 0.8
            },
            'team_stats': {
                'base_interval': 21600,  # 6 horas
                'volatility_factor': 1.0,
                'peak_hours': [8, 12, 18],
                'weekend_multiplier': 2.0
            }
        }
    
    def predict_next_update_time(self, data_type: str, last_update: timezone, 
                                context: Dict = None) -> timezone:
        """Predice cuándo se necesita la próxima actualización"""
        pattern = self.update_patterns.get(data_type, self.update_patterns['team_stats'])
        
        # Calcular intervalo base
        interval = pattern['base_interval']
        
        # Ajustar por hora del día
        now = timezone.now()
        if now.hour in pattern['peak_hours']:
            interval *= 0.7  # Más frecuente en horas pico
        
        # Ajustar por día de la semana
        if now.weekday() >= 5:  # Fin de semana
            interval *= pattern['weekend_multiplier']
        
        # Ajustar por contexto (ej: partidos en vivo)
        if context and context.get('has_live_matches', False):
            interval *= pattern['volatility_factor']
        
        return last_update + timedelta(seconds=interval)
    
    def should_update_now(self, data_type: str, last_update: timezone, 
                         context: Dict = None) -> bool:
        """Determina si se debe actualizar ahora"""
        next_update = self.predict_next_update_time(data_type, last_update, context)
        return timezone.now() >= next_update


class IntelligentFallbackSystem:
    """Sistema de fallback que combina múltiples fuentes de datos"""
    
    def __init__(self):
        self.data_sources = {
            'primary': 'external_api',
            'secondary': 'cached_data',
            'tertiary': 'predicted_data',
            'emergency': 'mock_data'
        }
        
        self.confidence_thresholds = {
            'high': 0.9,      # Usar datos primarios
            'medium': 0.7,    # Usar datos secundarios
            'low': 0.5,       # Usar datos predichos
            'emergency': 0.0  # Usar datos mock
        }
    
    def get_best_available_data(self, endpoint: str, required_confidence: float = 0.7):
        """Obtiene los mejores datos disponibles según confianza"""
        
        # Intentar fuente primaria (API externa)
        primary_data = self.try_primary_source(endpoint)
        if primary_data and primary_data.get('confidence', 0) >= required_confidence:
            return primary_data
        
        # Intentar fuente secundaria (cache)
        secondary_data = self.try_secondary_source(endpoint)
        if secondary_data and secondary_data.get('confidence', 0) >= required_confidence:
            return secondary_data
        
        # Intentar datos predichos
        predicted_data = self.try_predicted_data(endpoint)
        if predicted_data and predicted_data.get('confidence', 0) >= required_confidence:
            return predicted_data
        
        # Fallback final: datos mock
        return self.get_emergency_data(endpoint)
    
    def try_primary_source(self, endpoint: str) -> Optional[Dict]:
        """Intenta obtener datos de la API externa"""
        from .api_rate_limit_manager import APIRateLimitManager
        
        rate_manager = APIRateLimitManager()
        
        if not rate_manager.can_make_request('high'):
            logger.info(f"Rate limit reached, skipping primary source for {endpoint}")
            return None
        
        try:
            # Aquí iría el request real a la API
            # data = make_external_api_request(endpoint)
            # return {'data': data, 'confidence': 0.95, 'source': 'primary'}
            return None  # Placeholder
        except Exception as e:
            logger.error(f"Primary source failed for {endpoint}: {str(e)}")
            return None
    
    def try_secondary_source(self, endpoint: str) -> Optional[Dict]:
        """Intenta obtener datos del cache"""
        from django.core.cache import cache
        
        cache_key = f"fallback_data:{endpoint}"
        cached_data = cache.get(cache_key)
        
        if cached_data:
            # Calcular confianza basada en edad de los datos
            age_hours = (timezone.now() - cached_data['timestamp']).total_seconds() / 3600
            confidence = max(0.3, 0.9 - (age_hours * 0.1))  # Decrece con el tiempo
            
            return {
                'data': cached_data['data'],
                'confidence': confidence,
                'source': 'secondary',
                'age_hours': age_hours
            }
        
        return None
    
    def try_predicted_data(self, endpoint: str) -> Optional[Dict]:
        """Genera datos predichos basados en patrones históricos"""
        predictor = DataPatternPredictor()
        predicted = predictor.predict_data(endpoint)
        
        if predicted:
            return {
                'data': predicted,
                'confidence': 0.6,  # Confianza media para datos predichos
                'source': 'predicted'
            }
        
        return None
    
    def get_emergency_data(self, endpoint: str) -> Dict:
        """Datos mock de emergencia"""
        emergency_data = {
            'live_matches': {'matches': [], 'count': 0},
            'standings': {'table': [], 'competition': 'unknown'},
            'team_stats': {'stats': {}, 'team': 'unknown'}
        }
        
        return {
            'data': emergency_data.get(endpoint, {}),
            'confidence': 0.1,
            'source': 'emergency'
        }


class DataPatternPredictor:
    """Predice datos basado en patrones históricos"""
    
    def __init__(self):
        self.patterns = {}
        self.load_historical_patterns()
    
    def load_historical_patterns(self):
        """Carga patrones históricos de la base de datos"""
        # En implementación real, esto cargaría datos históricos
        self.patterns = {
            'goal_scoring_rate': 0.12,  # Goles por minuto promedio
            'card_rate': 0.08,          # Tarjetas por minuto promedio
            'match_duration': 95,       # Duración promedio en minutos
        }
    
    def predict_data(self, endpoint: str) -> Optional[Dict]:
        """Predice datos basado en patrones"""
        if endpoint == 'live_matches':
            return self.predict_live_match_data()
        elif endpoint == 'standings':
            return self.predict_standings()
        
        return None
    
    def predict_live_match_data(self) -> Dict:
        """Predice datos de partidos en vivo"""
        from quinielas.models import Partido
        
        # Obtener partidos que deberían estar en vivo
        now = timezone.now()
        live_matches = Partido.objects.filter(
            fecha_hora__lte=now,
            fecha_hora__gte=now - timedelta(hours=2),
            finalizado=False
        )
        
        predicted_matches = []
        for match in live_matches:
            # Predecir estado basado en tiempo transcurrido
            elapsed_minutes = (now - match.fecha_hora).total_seconds() / 60
            
            if 0 <= elapsed_minutes <= 45:
                predicted_state = 'first_half'
                predicted_minute = int(elapsed_minutes)
            elif 45 < elapsed_minutes <= 60:
                predicted_state = 'half_time'
                predicted_minute = 45
            elif 60 < elapsed_minutes <= 105:
                predicted_state = 'second_half'
                predicted_minute = int(elapsed_minutes - 15)  # Descontando descanso
            else:
                predicted_state = 'finished'
                predicted_minute = 90
            
            # Predecir marcador basado en patrones
            expected_goals = elapsed_minutes * self.patterns['goal_scoring_rate']
            home_goals = max(0, int(np.random.poisson(expected_goals / 2)))
            away_goals = max(0, int(np.random.poisson(expected_goals / 2)))
            
            predicted_matches.append({
                'id': match.id,
                'state': predicted_state,
                'minute': predicted_minute,
                'home_score': home_goals,
                'away_score': away_goals,
                'confidence': 0.6 if predicted_state != 'finished' else 0.3
            })
        
        return {'matches': predicted_matches}


# Función helper para usar en las vistas
def get_optimized_data(endpoint: str, required_confidence: float = 0.7):
    """Función principal para obtener datos optimizados"""
    fallback_system = IntelligentFallbackSystem()
    
    result = fallback_system.get_best_available_data(endpoint, required_confidence)
    
    # Log para monitoreo
    logger.info(f"Data for {endpoint}: source={result['source']}, confidence={result['confidence']}")
    
    return result
