"""
Sistema de cache inteligente para APIs con tokens limitados
Estrategia multi-capa para minimizar requests a APIs externas
"""

from django.core.cache import cache
from django.utils import timezone
from datetime import timedelta
import logging
import json

logger = logging.getLogger(__name__)

class APIRateLimitManager:
    """Gestor inteligente de rate limiting para APIs externas"""
    
    def __init__(self):
        self.cache_strategies = {
            # Datos que cambian poco - cache largo
            'equipos': {'ttl': 86400, 'priority': 'low'},  # 24 horas
            'estadisticas_temporada': {'ttl': 43200, 'priority': 'low'},  # 12 horas
            
            # Datos que cambian ocasionalmente - cache medio
            'partidos_programados': {'ttl': 3600, 'priority': 'medium'},  # 1 hora
            'tabla_posiciones': {'ttl': 1800, 'priority': 'medium'},  # 30 min
            
            # Datos críticos en tiempo real - cache corto
            'partidos_en_vivo': {'ttl': 120, 'priority': 'high'},  # 2 minutos
            'marcadores_live': {'ttl': 30, 'priority': 'critical'},  # 30 segundos
        }
        
        self.daily_token_limit = 1000  # Límite diario de la API
        self.hourly_token_limit = 100  # Límite por hora
        
    def get_cache_key(self, endpoint, params=None):
        """Genera clave de cache única"""
        key = f"api_external:{endpoint}"
        if params:
            param_str = ":".join([f"{k}={v}" for k, v in sorted(params.items())])
            key += f":{param_str}"
        return key
    
    def can_make_request(self, priority='medium'):
        """Verifica si podemos hacer request según el rate limit"""
        now = timezone.now()
        
        # Verificar límite por hora
        hour_key = f"api_tokens_hour:{now.hour}"
        hourly_count = cache.get(hour_key, 0)
        
        # Verificar límite diario
        day_key = f"api_tokens_day:{now.date()}"
        daily_count = cache.get(day_key, 0)
        
        # Límites por prioridad
        priority_limits = {
            'critical': {'hourly': 50, 'daily': 400},
            'high': {'hourly': 30, 'daily': 300},
            'medium': {'hourly': 15, 'daily': 200},
            'low': {'hourly': 5, 'daily': 100}
        }
        
        limits = priority_limits.get(priority, priority_limits['medium'])
        
        if hourly_count >= limits['hourly'] or daily_count >= limits['daily']:
            logger.warning(f"Rate limit exceeded for priority {priority}")
            return False
            
        return True
    
    def record_request(self):
        """Registra un request consumido"""
        now = timezone.now()
        
        # Incrementar contador por hora
        hour_key = f"api_tokens_hour:{now.hour}"
        cache.set(hour_key, cache.get(hour_key, 0) + 1, 3600)
        
        # Incrementar contador diario
        day_key = f"api_tokens_day:{now.date()}"
        cache.set(day_key, cache.get(day_key, 0) + 1, 86400)
    
    def get_cached_or_fetch(self, endpoint, fetch_function, params=None, data_type='medium'):
        """Obtiene datos del cache o hace request si es necesario"""
        cache_key = self.get_cache_key(endpoint, params)
        cached_data = cache.get(cache_key)
        
        # Si hay datos en cache, devolverlos
        if cached_data is not None:
            logger.info(f"Cache HIT for {endpoint}")
            return cached_data
        
        # Verificar si podemos hacer request
        strategy = self.cache_strategies.get(data_type, self.cache_strategies['medium'])
        if not self.can_make_request(strategy['priority']):
            logger.warning(f"Cannot make request for {endpoint} - rate limit")
            # Devolver datos mock o datos obsoletos si los hay
            return self.get_fallback_data(endpoint, params)
        
        # Hacer request a la API externa
        try:
            logger.info(f"Making API request for {endpoint}")
            data = fetch_function(params) if params else fetch_function()
            
            # Guardar en cache
            cache.set(cache_key, data, strategy['ttl'])
            
            # Registrar el consumo de token
            self.record_request()
            
            return data
            
        except Exception as e:
            logger.error(f"API request failed for {endpoint}: {str(e)}")
            return self.get_fallback_data(endpoint, params)
    
    def get_fallback_data(self, endpoint, params=None):
        """Obtiene datos de fallback cuando la API falla"""
        # Intentar obtener datos obsoletos del cache
        cache_key = self.get_cache_key(endpoint, params)
        stale_key = f"{cache_key}:stale"
        stale_data = cache.get(stale_key)
        
        if stale_data:
            logger.info(f"Using stale data for {endpoint}")
            return stale_data
            
        # Si no hay datos obsoletos, usar datos mock
        logger.info(f"Using mock data for {endpoint}")
        return self.get_mock_data(endpoint, params)
    
    def get_mock_data(self, endpoint, params=None):
        """Genera datos mock como último recurso"""
        mock_data = {
            'partidos_en_vivo': {
                'partidos': [],
                'source': 'mock',
                'timestamp': timezone.now().isoformat()
            },
            'tabla_posiciones': {
                'equipos': [],
                'source': 'mock',
                'timestamp': timezone.now().isoformat()
            }
        }
        
        return mock_data.get(endpoint, {'error': 'No data available', 'source': 'mock'})


class SmartAPIClient:
    """Cliente inteligente para APIs deportivas con gestión de tokens"""
    
    def __init__(self):
        self.rate_manager = APIRateLimitManager()
        self.base_url = "https://api.football-data.org/v4/"  # Ejemplo
        self.headers = {
            'X-Auth-Token': 'YOUR_API_TOKEN',
            'Content-Type': 'application/json'
        }
    
    def get_live_matches(self):
        """Obtiene partidos en vivo con cache inteligente"""
        def fetch_live_matches():
            # Aquí iría el request real a la API
            import requests
            response = requests.get(
                f"{self.base_url}matches",
                headers=self.headers,
                params={'status': 'LIVE'}
            )
            return response.json()
        
        return self.rate_manager.get_cached_or_fetch(
            endpoint='partidos_en_vivo',
            fetch_function=fetch_live_matches,
            data_type='partidos_en_vivo'
        )
    
    def get_team_standings(self, competition_id):
        """Obtiene tabla de posiciones con cache"""
        def fetch_standings():
            import requests
            response = requests.get(
                f"{self.base_url}competitions/{competition_id}/standings",
                headers=self.headers
            )
            return response.json()
        
        return self.rate_manager.get_cached_or_fetch(
            endpoint='tabla_posiciones',
            fetch_function=fetch_standings,
            params={'competition': competition_id},
            data_type='tabla_posiciones'
        )


# Ejemplo de uso en las vistas
def ejemplo_uso_optimizado():
    """Ejemplo de cómo usar el sistema optimizado"""
    client = SmartAPIClient()
    
    # Esto consumirá token solo si es necesario
    partidos_vivos = client.get_live_matches()
    
    # Esto usará cache si está disponible
    tabla = client.get_team_standings(competition_id=2014)
    
    return {
        'partidos_vivos': partidos_vivos,
        'tabla': tabla
    }
