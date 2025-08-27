"""
Data Enricher con Sistema de Optimización de APIs
Funciona con APIs mock ahora y reales después SIN CAMBIOS en las vistas
"""

from django.core.cache import cache
from django.utils import timezone
from django.conf import settings
import logging
import requests
import json
from datetime import datetime, timedelta

# Importar sistema de optimización
try:
    from .api_rate_limit_manager import APIRateLimitManager
    from .api_optimization_config import CACHE_STRATEGIES, API_CONFIGURATIONS
    API_OPTIMIZATION_AVAILABLE = True
except ImportError:
    API_OPTIMIZATION_AVAILABLE = False

logger = logging.getLogger(__name__)

class OptimizedDataEnricher:
    """
    Data enricher que usa optimización de APIs automáticamente
    - Mock APIs para desarrollo
    - APIs reales para producción
    - Sin cambios en código de vistas
    """
    
    def __init__(self):
        self.user_context = None
        self.session_key = None
        
        # Configuración automática de APIs
        self.api_config = {
            'mock_mode': getattr(settings, 'USE_MOCK_APIS', True),
            'mock_base_url': 'http://127.0.0.1:8000/api/mock',
            'real_apis': getattr(settings, 'EXTERNAL_APIS', {}),
            'fallback_enabled': True
        }
        
        # Rate manager para APIs reales
        if API_OPTIMIZATION_AVAILABLE and not self.api_config['mock_mode']:
            self.rate_manager = APIRateLimitManager()
        else:
            self.rate_manager = None
    
    def set_user_context(self, user, session_key):
        """Configurar contexto de usuario"""
        self.user_context = user
        self.session_key = session_key
    
    def _make_optimized_api_call(self, endpoint, cache_key=None, cache_ttl=900, priority='medium'):
        """
        Llamada a API optimizada que funciona con mock y real
        Esta función NO cambia cuando switches de mock a real
        """
        if cache_key is None:
            cache_key = f"api_data_{endpoint}_{hash(str(self.user_context.id if self.user_context else 'anon'))}"
        
        # 1. Verificar cache primero
        cached_data = cache.get(cache_key)
        if cached_data and not self._is_cache_expired(cached_data, cache_ttl):
            logger.info(f"Cache HIT para {endpoint}")
            return {
                'data': cached_data['data'],
                'source': 'cache',
                'cached': True,
                'timestamp': cached_data['timestamp']
            }
        
        # 2. Decidir qué API usar automáticamente
        try:
            if self.api_config['mock_mode']:
                # Usar API mock (desarrollo)
                result = self._call_mock_api(endpoint)
            else:
                # Usar API real con optimización (producción)
                result = self._call_real_api_optimized(endpoint, priority)
            
            # 3. Guardar en cache
            cache_data = {
                'data': result['data'],
                'timestamp': timezone.now(),
                'source': result['source']
            }
            cache.set(cache_key, cache_data, timeout=cache_ttl)
            
            logger.info(f"API call realizada para {endpoint} desde {result['source']}")
            return result
            
        except Exception as e:
            logger.error(f"Error en API call {endpoint}: {e}")
            return self._get_fallback_data(endpoint, cached_data)
    
    def _call_mock_api(self, endpoint):
        """Llamada a API mock local"""
        url_mapping = {
            'equipos': f"{self.api_config['mock_base_url']}/equipos/",
            'partidos': f"{self.api_config['mock_base_url']}/partidos/?proximos=true",
            'resultados': f"{self.api_config['mock_base_url']}/partidos/?finalizados=true",
            'tabla_posiciones': f"{self.api_config['mock_base_url']}/tabla-posiciones/",
            'estadisticas': f"{self.api_config['mock_base_url']}/estadisticas/",
            'pronosticos': f"{self.api_config['mock_base_url']}/pronosticos-ia/"
        }
        
        url = url_mapping.get(endpoint, f"{self.api_config['mock_base_url']}/status/")
        
        try:
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                return {
                    'data': response.json(),
                    'source': 'mock_api',
                    'cached': False
                }
            else:
                raise Exception(f"Mock API error: {response.status_code}")
                
        except Exception as e:
            raise Exception(f"Mock API unavailable: {e}")
    
    def _call_real_api_optimized(self, endpoint, priority):
        """Llamada a API real con optimización completa"""
        if not self.rate_manager:
            raise Exception("Rate manager not available")
        
        # Verificar rate limiting
        if not self.rate_manager.puede_hacer_request(endpoint, priority):
            logger.warning(f"Rate limit alcanzado para {endpoint}")
            raise Exception("Rate limit exceeded")
        
        # Mapeo de endpoints a APIs reales
        api_mapping = {
            'equipos': ('football_data', '/teams'),
            'partidos': ('football_data', '/matches'),
            'tabla_posiciones': ('football_data', '/standings'),
            'estadisticas': ('sports_api', '/statistics')
        }
        
        api_name, api_endpoint = api_mapping.get(endpoint, ('football_data', '/status'))
        api_config = self.api_config['real_apis'].get(api_name, {})
        
        if not api_config:
            raise Exception(f"API config not found for {api_name}")
        
        # Hacer request real
        headers = {
            'X-Auth-Token': api_config.get('api_key', ''),
            'Content-Type': 'application/json'
        }
        
        url = f"{api_config.get('base_url', '')}{api_endpoint}"
        
        try:
            response = requests.get(url, headers=headers, timeout=15)
            if response.status_code == 200:
                # Registrar uso de rate limit
                self.rate_manager.registrar_request(endpoint, priority)
                
                return {
                    'data': response.json(),
                    'source': 'external_api',
                    'cached': False,
                    'api_name': api_name
                }
            else:
                raise Exception(f"API error: {response.status_code}")
                
        except Exception as e:
            raise Exception(f"Real API call failed: {e}")
    
    def _is_cache_expired(self, cached_data, ttl):
        """Verificar si cache está expirado"""
        if not cached_data or 'timestamp' not in cached_data:
            return True
        
        age = (timezone.now() - cached_data['timestamp']).total_seconds()
        return age > ttl
    
    def _get_fallback_data(self, endpoint, stale_cache=None):
        """Obtener datos de fallback cuando APIs fallan"""
        logger.warning(f"Usando fallback para {endpoint}")
        
        # 1. Usar cache expirado si está disponible
        if stale_cache:
            return {
                'data': stale_cache['data'],
                'source': 'stale_cache',
                'cached': True,
                'warning': 'Using stale cache data due to API failure'
            }
        
        # 2. Datos de fallback estáticos
        fallback_data = {
            'equipos': {
                'equipos': [
                    {'id': 1, 'nombre': 'Real Madrid', 'logo': '/static/img/teams/real_madrid.png'},
                    {'id': 2, 'nombre': 'Barcelona', 'logo': '/static/img/teams/barcelona.png'},
                    {'id': 3, 'nombre': 'Atletico Madrid', 'logo': '/static/img/teams/atletico.png'}
                ]
            },
            'partidos': {
                'partidos': [
                    {
                        'id': 1,
                        'equipo_local': 'Real Madrid',
                        'equipo_visitante': 'Barcelona',
                        'fecha_hora': (timezone.now() + timedelta(days=1)).isoformat(),
                        'finalizado': False
                    }
                ]
            },
            'tabla_posiciones': {
                'tabla_posiciones': [
                    {'posicion': 1, 'equipo': {'nombre': 'Real Madrid'}, 'puntos': 85},
                    {'posicion': 2, 'equipo': {'nombre': 'Barcelona'}, 'puntos': 82},
                    {'posicion': 3, 'equipo': {'nombre': 'Atletico Madrid'}, 'puntos': 78}
                ]
            }
        }
        
        return {
            'data': fallback_data.get(endpoint, {'error': 'No fallback data available'}),
            'source': 'fallback_static',
            'cached': False,
            'confidence': 0.3,
            'warning': 'Using static fallback data'
        }
    
    # ===== MÉTODOS PÚBLICOS PARA LAS VISTAS =====
    # Estos métodos NO cambian cuando switches de mock a real
    
    def obtener_datos_dashboard(self, user):
        """
        Obtener datos completos del dashboard
        FUNCIONA IGUAL con APIs mock y reales
        """
        self.set_user_context(user, None)
        
        dashboard_data = {}
        
        try:
            # Obtener datos en paralelo (conceptualmente)
            equipos_result = self._make_optimized_api_call(
                'equipos', 
                cache_key=f"dashboard_equipos_{user.id}",
                cache_ttl=3600,  # 1 hora
                priority='low'
            )
            
            partidos_result = self._make_optimized_api_call(
                'partidos',
                cache_key=f"dashboard_partidos_{user.id}",
                cache_ttl=900,   # 15 minutos
                priority='high'
            )
            
            tabla_result = self._make_optimized_api_call(
                'tabla_posiciones',
                cache_key=f"dashboard_tabla_{user.id}",
                cache_ttl=1800,  # 30 minutos
                priority='medium'
            )
            
            # Procesar resultados
            dashboard_data = {
                'equipos_populares': self._extract_equipos(equipos_result['data']),
                'partidos_proximos': self._extract_partidos(partidos_result['data']),
                'tabla_posiciones': self._extract_tabla(tabla_result['data']),
                'metadata': {
                    'sources': {
                        'equipos': equipos_result['source'],
                        'partidos': partidos_result['source'],
                        'tabla': tabla_result['source']
                    },
                    'cached_count': sum([
                        1 for r in [equipos_result, partidos_result, tabla_result] 
                        if r.get('cached', False)
                    ]),
                    'api_mode': 'mock' if self.api_config['mock_mode'] else 'real'
                }
            }
            
        except Exception as e:
            logger.error(f"Error obteniendo datos dashboard: {e}")
            # Fallback completo
            dashboard_data = self._get_dashboard_fallback()
        
        return dashboard_data
    
    def obtener_partidos_en_vivo(self):
        """Obtener partidos en vivo con optimización"""
        return self._make_optimized_api_call(
            'partidos_vivo',
            cache_key="partidos_en_vivo",
            cache_ttl=30,  # 30 segundos para datos en vivo
            priority='critical'
        )
    
    def obtener_pronosticos_ia(self):
        """Obtener pronósticos de IA"""
        return self._make_optimized_api_call(
            'pronosticos',
            cache_key="pronosticos_ia",
            cache_ttl=1800,  # 30 minutos
            priority='medium'
        )
    
    # ===== MÉTODOS DE EXTRACCIÓN DE DATOS =====
    
    def _extract_equipos(self, data):
        """Extraer y normalizar datos de equipos"""
        if 'equipos' in data:
            return data['equipos'][:10]  # Top 10 equipos
        return []
    
    def _extract_partidos(self, data):
        """Extraer y normalizar datos de partidos"""
        if 'partidos' in data:
            return data['partidos'][:5]  # Próximos 5 partidos
        elif 'jornadas' in data:
            # Formato de mock API
            proximos = []
            for jornada in data['jornadas']:
                for partido in jornada.get('partidos', []):
                    if not partido.get('finalizado', False):
                        proximos.append(partido)
            return proximos[:5]
        return []
    
    def _extract_tabla(self, data):
        """Extraer y normalizar tabla de posiciones"""
        if 'tabla_posiciones' in data:
            return data['tabla_posiciones'][:10]  # Top 10
        return []
    
    def _get_dashboard_fallback(self):
        """Fallback completo para dashboard"""
        return {
            'equipos_populares': [],
            'partidos_proximos': [],
            'tabla_posiciones': [],
            'metadata': {
                'sources': {'all': 'fallback'},
                'cached_count': 0,
                'api_mode': 'fallback',
                'warning': 'Todos los datos desde fallback'
            }
        }


# Instancia global que se usa en las vistas
# Se configura automáticamente según settings
data_enricher = OptimizedDataEnricher()
