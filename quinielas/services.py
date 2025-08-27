"""
Servicio para integrar datos mock con el sistema de quinielas
"""
import requests
import json
from typing import Dict, List, Optional
from django.conf import settings
from django.utils import timezone
from datetime import datetime


class APIMockService:
    """Servicio para interactuar con APIs mock autenticadas"""
    
    def __init__(self):
        self.base_url = "http://127.0.0.1:8000/api"
        self.session = requests.Session()
    
    def set_auth_session(self, user, session_key=None):
        """Configura la sesión para hacer peticiones autenticadas"""
        if session_key:
            self.session.cookies.set('sessionid', session_key)
    
    def _make_authenticated_request(self, endpoint: str, params: Optional[Dict] = None, user=None) -> Optional[Dict]:
        """Realiza una petición HTTP autenticada a la API mock"""
        try:
            url = f"{self.base_url}/{endpoint}/"
            
            # Para desarrollo, usar respuestas simuladas que no requieren servidor
            # En producción, descomentar la siguiente línea:
            # response = self.session.get(url, params=params or {}, timeout=5)
            
            return self._get_mock_response(endpoint, params, user)
            
        except requests.RequestException as e:
            print(f"Error al consultar API mock: {e}")
            return self._get_mock_response(endpoint, params, user)
    
    def _get_mock_response(self, endpoint: str, params: Optional[Dict] = None, user=None) -> Optional[Dict]:
        """Genera respuestas mock para desarrollo"""
        import random
        from datetime import datetime, timedelta
        
        params = params or {}
        
        if endpoint == 'equipos':
            return {
                'equipos': [
                    {'id': 1, 'nombre': 'Club América', 'ciudad': 'Ciudad de México'},
                    {'id': 2, 'nombre': 'Cruz Azul', 'ciudad': 'Ciudad de México'},
                    {'id': 3, 'nombre': 'Chivas', 'ciudad': 'Guadalajara'},
                    {'id': 4, 'nombre': 'Pumas', 'ciudad': 'Ciudad de México'}
                ]
            }
        elif endpoint == 'partidos':
            equipos = ['América', 'Cruz Azul', 'Chivas', 'Pumas']
            partidos = []
            for i in range(5):
                fecha = datetime.now() + timedelta(days=i+1)
                local = random.choice(equipos)
                visitante = random.choice([e for e in equipos if e != local])
                partidos.append({
                    'id': i + 1,
                    'equipo_local': local,
                    'equipo_visitante': visitante,
                    'fecha': fecha.isoformat(),
                    'finalizado': params.get('finalizados') == 'true'
                })
            return {'partidos': partidos}
        elif endpoint.startswith('usuario/') and endpoint.endswith('/estadisticas'):
            # Estadísticas de usuario autenticado
            if user:
                seed = user.id if hasattr(user, 'id') else 1
                random.seed(seed)
                total_apuestas = random.randint(10, 100)
                acertadas = random.randint(int(total_apuestas * 0.2), int(total_apuestas * 0.7))
                return {
                    'total_apuestas': total_apuestas,
                    'apuestas_acertadas': acertadas,
                    'puntos_totales': random.randint(50, 500),
                    'porcentaje_efectividad': round((acertadas / total_apuestas) * 100, 2)
                }
        elif endpoint == 'estadisticas':
            return {'estadisticas_generales': {}}
        
        return None
    
    def obtener_equipos(self, equipo_id: Optional[int] = None, user=None) -> Optional[Dict]:
        """Obtiene información de equipos"""
        params = {'id': equipo_id} if equipo_id else {}
        return self._make_authenticated_request('equipos', params, user)
    
    def obtener_partidos_proximos(self, user=None) -> List[Dict]:
        """Obtiene partidos próximos"""
        data = self._make_authenticated_request('partidos', {'proximos': 'true'}, user)
        return data.get('partidos', []) if data else []
    
    def obtener_partidos_finalizados(self, user=None) -> List[Dict]:
        """Obtiene partidos finalizados"""
        data = self._make_authenticated_request('partidos', {'finalizados': 'true'}, user)
        return data.get('partidos', []) if data else []
    
    def obtener_tabla_posiciones(self, user=None) -> List[Dict]:
        """Obtiene tabla de posiciones actual"""
        data = self._make_authenticated_request('tabla-posiciones', user=user)
        return data.get('tabla_posiciones', []) if data else []
    
    def obtener_pronosticos_ia(self, user=None) -> List[Dict]:
        """Obtiene pronósticos de IA para partidos próximos"""
        data = self._make_authenticated_request('pronosticos-ia', user=user)
        return data.get('pronosticos_ia', []) if data else []
    
    def obtener_detalle_partido(self, partido_id: int, user=None) -> Optional[Dict]:
        """Obtiene detalles específicos de un partido"""
        return self._make_authenticated_request(f'partido/{partido_id}', user=user)
    
    def obtener_resumen_jornada(self, jornada_numero: int, user=None) -> Optional[Dict]:
        """Obtiene resumen completo de una jornada"""
        return self._make_authenticated_request(f'jornada/{jornada_numero}/resumen', user=user)
    
    def obtener_estadisticas(self, tipo: Optional[str] = None, user=None) -> Optional[Dict]:
        """Obtiene estadísticas avanzadas"""
        params = {'tipo': tipo} if tipo else {}
        return self._make_authenticated_request('estadisticas', params, user)
    
    def obtener_estadisticas_usuario(self, user_id: int, user=None) -> Optional[Dict]:
        """Obtiene estadísticas específicas del usuario autenticado"""
        if not user:
            return None
        return self._make_authenticated_request(f'usuario/{user_id}/estadisticas', user=user)
    
    def simular_resultado_partido(self, partido_id: int) -> Optional[Dict]:
        """Simula el resultado de un partido"""
        try:
            url = f"{self.base_url}/partido/{partido_id}/simular/"
            response = requests.post(url, timeout=5)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            print(f"Error al simular resultado: {e}")
            return None


class QuinielasDataEnricher:
    """Enriquece los datos del sistema con información de APIs mock autenticadas"""
    
    def __init__(self):
        self.api_service = APIMockService()
    
    def set_user_context(self, user, session_key=None):
        """Configura el contexto de usuario para las peticiones"""
        self.api_service.set_auth_session(user, session_key)
    
    def enriquecer_partido_con_datos_mock(self, partido_django, user=None) -> Dict:
        """Enriquece un partido Django con datos mock"""
        # Buscar datos mock que coincidan
        partidos_mock = self.api_service.obtener_partidos_proximos(user)
        partidos_mock.extend(self.api_service.obtener_partidos_finalizados(user))
        
        datos_enriquecidos = {
            'partido_django': partido_django,
            'clima': None,
            'pronostico_ia': None,
            'eventos': [],
            'estadisticas_equipos': {}
        }
        
        # Buscar partido correspondiente en datos mock
        partido_mock = None
        for p_mock in partidos_mock:
            # Aquí harías la lógica para emparejar partidos
            # Por simplicidad, usando nombres de equipos
            if (p_mock.get('equipo_local_id') and p_mock.get('equipo_visitante_id')):
                partido_mock = p_mock
                break
        
        if partido_mock:
            # Obtener detalles completos
            detalle = self.api_service.obtener_detalle_partido(partido_mock['id'], user)
            if detalle:
                datos_enriquecidos.update({
                    'clima': detalle.get('clima'),
                    'eventos': partido_mock.get('eventos', []),
                    'estadio_info': partido_mock.get('estadio'),
                    'arbitro': partido_mock.get('arbitro'),
                    'temperatura': partido_mock.get('temperatura')
                })
        
        # Obtener pronósticos de IA
        pronosticos = self.api_service.obtener_pronosticos_ia(user)
        for pronostico in pronosticos:
            if partido_mock and pronostico.get('partido_id') == partido_mock['id']:
                datos_enriquecidos['pronostico_ia'] = pronostico
                break
        
        return datos_enriquecidos
    
    def obtener_estadisticas_para_quiniela(self, quiniela, user=None) -> Dict:
        """Obtiene estadísticas enriquecidas para una quiniela"""
        return {
            'tabla_posiciones': self.api_service.obtener_tabla_posiciones(user),
            'jugadores_destacados': self.api_service.obtener_estadisticas('jugadores', user),
            'tendencias_apuestas': self.api_service.obtener_estadisticas('tendencias', user),
            'pronosticos_expertos': self.api_service.obtener_estadisticas('pronosticos', user),
        }
    
    def obtener_datos_dashboard(self, user=None) -> Dict:
        """Obtiene datos para el dashboard principal con información del usuario"""
        datos = {
            'partidos_proximos': self.api_service.obtener_partidos_proximos(user)[:5],
            'ultimos_resultados': self.api_service.obtener_partidos_finalizados(user)[-5:],
            'tabla_posiciones': self.api_service.obtener_tabla_posiciones(user)[:10],
            'pronosticos_destacados': self.api_service.obtener_pronosticos_ia(user)[:3],
        }
        
        # Agregar estadísticas del usuario si está autenticado
        if user and hasattr(user, 'id'):
            stats_usuario = self.api_service.obtener_estadisticas_usuario(user.id, user)
            if stats_usuario:
                datos['estadisticas_usuario'] = stats_usuario
        
        return datos


# Instancia global del servicio
api_mock_service = APIMockService()
data_enricher = QuinielasDataEnricher()
