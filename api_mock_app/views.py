import json
import os
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from django.core.cache import cache
from django.utils import timezone
from datetime import datetime, timedelta
import random
import time
import logging
from .decorators import api_login_required, api_rate_limit

# Importar nuestro sistema de optimización
try:
    from quinielas.api_rate_limit_manager import APIRateLimitManager, SmartAPIClient
    from quinielas.api_optimization_config import CACHE_STRATEGIES, API_CONFIGURATIONS
    API_OPTIMIZATION_AVAILABLE = True
except ImportError:
    API_OPTIMIZATION_AVAILABLE = False

logger = logging.getLogger(__name__)


def load_json_data(filename):
    """Carga datos desde archivos JSON"""
    file_path = os.path.join(settings.BASE_DIR, 'api_mock', filename)
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            return json.load(file)
    except FileNotFoundError:
        return {"error": f"Archivo {filename} no encontrado"}
    except json.JSONDecodeError:
        return {"error": f"Error al decodificar JSON en {filename}"}


def simulate_external_api_call(endpoint, data=None, use_optimization=True):
    """
    Simula llamada a API externa con optimización de rate limiting
    Esto permite probar el sistema sin APIs reales
    """
    if not API_OPTIMIZATION_AVAILABLE or not use_optimization:
        # Simular respuesta directa sin optimización
        time.sleep(random.uniform(0.1, 0.5))  # Simular latencia de red
        return {"data": data or {}, "source": "direct_api", "cached": False}
    
    # Usar el sistema de optimización con datos mock
    api_name = 'mock_football_api'
    rate_manager = APIRateLimitManager(
        api_name=api_name,
        daily_limit=10,  # Simular API con pocos tokens
        per_minute_limit=6
    )
    
    cache_key = f"api_mock_{endpoint}_{hash(str(data))}"
    
    # Verificar cache primero
    cached_result = cache.get(cache_key)
    if cached_result:
        logger.info(f"Cache HIT para {endpoint}")
        return {
            "data": cached_result['data'],
            "source": "cache",
            "cached": True,
            "age_seconds": (timezone.now() - cached_result['timestamp']).total_seconds()
        }
    
    # Verificar rate limiting
    usage = rate_manager.get_current_usage()
    if usage['daily_used'] >= usage['daily_limit']:
        logger.warning(f"Rate limit excedido para {api_name}")
        # Usar fallback con datos predichos
        return {
            "data": generate_fallback_data(endpoint, data),
            "source": "fallback_predicted",
            "cached": False,
            "warning": "Rate limit excedido, usando datos predichos"
        }
    
    # Simular llamada a API real
    if rate_manager.can_make_request('high'):
        rate_manager.record_request('high')
        
        # Simular latencia real
        time.sleep(random.uniform(0.2, 1.0))
        
        # Simular probabilidad de error (5%)
        if random.random() < 0.05:
            raise Exception("API externa temporal no disponible")
        
        # Generar datos mock realistas
        mock_data = generate_mock_api_data(endpoint, data)
        
        # Guardar en cache
        cache_ttl = CACHE_STRATEGIES.get('live_scores', {}).get('ttl', 30)
        cache.set(cache_key, {
            'data': mock_data,
            'timestamp': timezone.now()
        }, timeout=cache_ttl)
        
        logger.info(f"API call realizada para {endpoint}")
        return {
            "data": mock_data,
            "source": "external_api",
            "cached": False,
            "rate_limit_remaining": usage['daily_limit'] - usage['daily_used'] - 1
        }
    else:
        # Rate limit alcanzado, usar fallback
        return {
            "data": generate_fallback_data(endpoint, data),
            "source": "fallback_rate_limited",
            "cached": False,
            "warning": "Rate limit temporalmente alcanzado"
        }


def generate_mock_api_data(endpoint, params=None):
    """Genera datos mock realistas por endpoint"""
    if endpoint == 'live_matches':
        return [
            {
                'id': random.randint(1000, 9999),
                'home_team': 'Real Madrid',
                'away_team': 'Barcelona',
                'status': 'live',
                'minute': random.randint(1, 90),
                'home_score': random.randint(0, 3),
                'away_score': random.randint(0, 3)
            }
        ]
    elif endpoint == 'upcoming_matches':
        return [
            {
                'id': random.randint(1000, 9999),
                'home_team': 'Chelsea',
                'away_team': 'Arsenal',
                'kickoff': (timezone.now() + timedelta(hours=random.randint(1, 24))).isoformat()
            }
        ]
    elif endpoint == 'standings':
        return [
            {
                'position': i,
                'team': f'Team {i}',
                'points': random.randint(20, 90),
                'played': random.randint(15, 38)
            } for i in range(1, 21)
        ]
    
    return {"message": f"Mock data for {endpoint}"}


def generate_fallback_data(endpoint, params=None):
    """Genera datos de fallback cuando API no está disponible"""
    return {
        "fallback": True,
        "endpoint": endpoint,
        "estimated_data": generate_mock_api_data(endpoint, params),
        "confidence": 0.6,
        "message": "Datos estimados - API externa no disponible"
    }
    """Carga datos desde archivos JSON"""
    file_path = os.path.join(settings.BASE_DIR, 'api_mock', filename)
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            return json.load(file)
    except FileNotFoundError:
        return {"error": f"Archivo {filename} no encontrado"}
    except json.JSONDecodeError:
        return {"error": f"Error al decodificar JSON en {filename}"}


def calculate_realistic_match_state(partido_id):
    """Calcula el estado realista de un partido basado en su fecha"""
    from quinielas.models import Partido
    from django.utils import timezone
    
    try:
        partido = Partido.objects.get(id=partido_id)
        now = timezone.now()
        
        # Determinar estado basado en fecha y hora
        if partido.fecha_hora > now:
            # Partido futuro
            time_diff = partido.fecha_hora - now
            
            if time_diff.total_seconds() > 86400:  # Más de 1 día
                return {
                    'estado': 'programado',
                    'minuto_actual': None,
                    'goles_local': None,
                    'goles_visitante': None,
                    'periodo': 'programado',
                    'descripcion': f'Inicia en {time_diff.days} días'
                }
            elif time_diff.total_seconds() > 3600:  # Entre 1 hora y 1 día
                hours = int(time_diff.total_seconds() // 3600)
                return {
                    'estado': 'proximo',
                    'minuto_actual': None,
                    'goles_local': None,
                    'goles_visitante': None,
                    'periodo': 'programado',
                    'descripcion': f'Inicia en {hours}h'
                }
            else:  # Menos de 1 hora
                minutes = int(time_diff.total_seconds() // 60)
                return {
                    'estado': 'por_iniciar',
                    'minuto_actual': None,
                    'goles_local': None,
                    'goles_visitante': None,
                    'periodo': 'calentamiento',
                    'descripcion': f'Inicia en {minutes} min'
                }
        
        elif partido.fecha_hora <= now:
            # Partido presente o pasado
            time_diff = now - partido.fecha_hora
            
            # Si ya finalizó según nuestros datos
            if partido.finalizado:
                return {
                    'estado': 'finalizado',
                    'minuto_actual': 90,
                    'goles_local': partido.goles_local or 0,
                    'goles_visitante': partido.goles_visitante or 0,
                    'periodo': 'finalizado'
                }
            
            # Si está dentro del tiempo de partido (hasta 2.5 horas después del inicio)
            elif time_diff.total_seconds() <= 9000:  # 2.5 horas = 9000 segundos
                # Simular estado en vivo
                minutos_transcurridos = int(time_diff.total_seconds() / 60)
                
                if minutos_transcurridos <= 45:
                    # Primer tiempo
                    return {
                        'estado': 'en_vivo',
                        'minuto_actual': min(minutos_transcurridos, 45),
                        'goles_local': random.randint(0, 2),
                        'goles_visitante': random.randint(0, 2),
                        'periodo': 'primer_tiempo',
                        'estadisticas_live': {
                            'posesion_local': random.randint(40, 60),
                            'posesion_visitante': random.randint(40, 60),
                            'tiros_local': random.randint(0, 8),
                            'tiros_visitante': random.randint(0, 8),
                            'tiros_puerta_local': random.randint(0, 3),
                            'tiros_puerta_visitante': random.randint(0, 3)
                        }
                    }
                elif minutos_transcurridos <= 60:
                    # Medio tiempo
                    return {
                        'estado': 'medio_tiempo',
                        'minuto_actual': 45,
                        'goles_local': random.randint(0, 2),
                        'goles_visitante': random.randint(0, 2),
                        'periodo': 'descanso'
                    }
                else:
                    # Segundo tiempo
                    minuto_segundo = min(minutos_transcurridos - 60, 45) + 45
                    return {
                        'estado': 'en_vivo',
                        'minuto_actual': minuto_segundo,
                        'goles_local': random.randint(0, 3),
                        'goles_visitante': random.randint(0, 3),
                        'periodo': 'segundo_tiempo',
                        'estadisticas_live': {
                            'posesion_local': random.randint(35, 65),
                            'posesion_visitante': random.randint(35, 65),
                            'tiros_local': random.randint(3, 15),
                            'tiros_visitante': random.randint(3, 15),
                            'tiros_puerta_local': random.randint(1, 6),
                            'tiros_puerta_visitante': random.randint(1, 6)
                        }
                    }
            else:
                # Partido que debería haber terminado
                return {
                    'estado': 'finalizado',
                    'minuto_actual': 90,
                    'goles_local': random.randint(0, 4),
                    'goles_visitante': random.randint(0, 4),
                    'periodo': 'finalizado'
                }
                
    except Partido.DoesNotExist:
        # Si no existe el partido en la BD, usar datos mock básicos
        return {
            'estado': 'programado',
            'minuto_actual': None,
            'goles_local': None,
            'goles_visitante': None,
            'periodo': 'programado'
        }


def simulate_api_errors(error_probability=0.05):
    """Simula errores de API basado en probabilidad"""
    if random.random() < error_probability:
        escenarios = load_json_data('escenarios_testing.json')
        if 'escenarios_testing' in escenarios and 'errores_api' in escenarios['escenarios_testing']:
            error_scenarios = escenarios['escenarios_testing']['errores_api']
            error = random.choice(error_scenarios)
            
            if error['scenario'] == 'timeout':
                return JsonResponse(error['response'], status=408)
            elif error['scenario'] == 'rate_limit':
                return JsonResponse(error['response'], status=429)
            elif error['scenario'] == 'partial_data':
                return JsonResponse(error['response'], status=206)
    
    return None
    """Simula errores de API basado en probabilidad"""
    if random.random() < error_probability:
        escenarios = load_json_data('escenarios_testing.json')
        if 'escenarios_testing' in escenarios and 'errores_api' in escenarios['escenarios_testing']:
            error_scenarios = escenarios['escenarios_testing']['errores_api']
            error = random.choice(error_scenarios)
            
            if error['scenario'] == 'timeout':
                return JsonResponse(error['response'], status=408)
            elif error['scenario'] == 'rate_limit':
                return JsonResponse(error['response'], status=429)
            elif error['scenario'] == 'partial_data':
                return JsonResponse(error['response'], status=206)
    
    return None


@api_login_required
@api_rate_limit(max_requests=200, period=3600)
@require_http_methods(["GET"])
def api_equipos(request):
    """API para obtener información de equipos"""
    data = load_json_data('equipos.json')
    
    # Filtros opcionales
    equipo_id = request.GET.get('id')
    if equipo_id:
        try:
            equipos = [equipo for equipo in data.get('equipos', []) if equipo['id'] == int(equipo_id)]
            if equipos:
                return JsonResponse({'equipo': equipos[0]})
            else:
                return JsonResponse({'error': 'Equipo no encontrado'}, status=404)
        except (ValueError, TypeError):
            return JsonResponse({'error': 'ID de equipo inválido'}, status=400)
    
    return JsonResponse(data)


@api_login_required
@api_rate_limit(max_requests=200, period=3600)
@require_http_methods(["GET"])
def api_partidos(request):
    """API para obtener partidos y jornadas"""
    # Simular errores ocasionales
    error_response = simulate_api_errors()
    if error_response:
        return error_response
    
    data = load_json_data('partidos.json')
    
    # Filtros opcionales
    jornada = request.GET.get('jornada')
    solo_proximos = request.GET.get('proximos', 'false').lower() == 'true'
    solo_finalizados = request.GET.get('finalizados', 'false').lower() == 'true'
    
    if jornada:
        try:
            jornadas_filtradas = [j for j in data.get('jornadas', []) if j['numero'] == int(jornada)]
            return JsonResponse({'jornadas': jornadas_filtradas})
        except (ValueError, TypeError):
            return JsonResponse({'error': 'Número de jornada inválido'}, status=400)
    
    if solo_proximos:
        partidos_proximos = []
        for jornada in data.get('jornadas', []):
            for partido in jornada.get('partidos', []):
                if not partido.get('finalizado', False):
                    partidos_proximos.append({
                        **partido,
                        'jornada_numero': jornada['numero'],
                        'jornada_nombre': jornada['nombre']
                    })
        return JsonResponse({'partidos': partidos_proximos})
    
    if solo_finalizados:
        partidos_finalizados = []
        for jornada in data.get('jornadas', []):
            for partido in jornada.get('partidos', []):
                if partido.get('finalizado', False):
                    partidos_finalizados.append({
                        **partido,
                        'jornada_numero': jornada['numero'],
                        'jornada_nombre': jornada['nombre']
                    })
        return JsonResponse({'partidos': partidos_finalizados})
    
    return JsonResponse(data)


@api_login_required
@api_rate_limit(max_requests=100, period=3600)
@require_http_methods(["GET"])
def api_estadisticas(request):
    """API para obtener estadísticas avanzadas"""
    data = load_json_data('estadisticas.json')
    
    tipo = request.GET.get('tipo')
    if tipo == 'jugadores':
        return JsonResponse({'jugadores': data.get('jugadores_destacados', [])})
    elif tipo == 'pronosticos':
        return JsonResponse({'pronosticos': data.get('pronosticos_expertos', [])})
    elif tipo == 'tendencias':
        return JsonResponse({'tendencias': data.get('tendencias_apuestas', {})})
    elif tipo == 'clima':
        return JsonResponse({'clima': data.get('clima_partidos', [])})
    elif tipo == 'historiales':
        return JsonResponse({'historiales': data.get('historiales_enfrentamientos', {})})
    
    return JsonResponse(data)


@api_login_required
@api_rate_limit(max_requests=100, period=3600)
@require_http_methods(["GET"])
def api_tabla_posiciones(request):
    """API para obtener tabla de posiciones actual"""
    partidos_data = load_json_data('partidos.json')
    equipos_data = load_json_data('equipos.json')
    
    # Crear tabla de posiciones a partir de estadísticas
    estadisticas = partidos_data.get('estadisticas_equipos', {})
    equipos = equipos_data.get('equipos', [])
    
    tabla = []
    for equipo in equipos:
        equipo_id = str(equipo['id'])
        stats = estadisticas.get(equipo_id, {})
        
        tabla.append({
            'posicion': stats.get('posicion_tabla', 18),
            'equipo': equipo,
            'partidos_jugados': stats.get('partidos_jugados', 0),
            'victorias': stats.get('victorias', 0),
            'empates': stats.get('empates', 0),
            'derrotas': stats.get('derrotas', 0),
            'goles_favor': stats.get('goles_favor', 0),
            'goles_contra': stats.get('goles_contra', 0),
            'diferencia_goles': stats.get('diferencia_goles', 0),
            'puntos': stats.get('puntos', 0)
        })
    
    # Ordenar por posición
    tabla.sort(key=lambda x: x['posicion'])
    
    return JsonResponse({'tabla_posiciones': tabla})


@api_login_required
@api_rate_limit(max_requests=50, period=3600)
@require_http_methods(["GET"])
def api_partido_detalle(request, partido_id):
    """API para obtener detalles específicos de un partido"""
    try:
        partido_id = int(partido_id)
    except (ValueError, TypeError):
        return JsonResponse({'error': 'ID de partido inválido'}, status=400)
    
    data = load_json_data('partidos.json')
    equipos_data = load_json_data('equipos.json')
    stats_data = load_json_data('estadisticas.json')
    
    # Buscar el partido
    partido_encontrado = None
    jornada_info = None
    
    for jornada in data.get('jornadas', []):
        for partido in jornada.get('partidos', []):
            if partido['id'] == partido_id:
                partido_encontrado = partido
                jornada_info = {
                    'numero': jornada['numero'],
                    'nombre': jornada['nombre']
                }
                break
        if partido_encontrado:
            break
    
    if not partido_encontrado:
        return JsonResponse({'error': 'Partido no encontrado'}, status=404)
    
    # Enriquecer con datos de equipos
    equipos = equipos_data.get('equipos', [])
    equipo_local = next((e for e in equipos if e['id'] == partido_encontrado['equipo_local_id']), None)
    equipo_visitante = next((e for e in equipos if e['id'] == partido_encontrado['equipo_visitante_id']), None)
    
    # Agregar estadísticas si están disponibles
    clima_info = next((c for c in stats_data.get('clima_partidos', []) if c['partido_id'] == partido_id), None)
    
    resultado = {
        'partido': partido_encontrado,
        'jornada': jornada_info,
        'equipo_local': equipo_local,
        'equipo_visitante': equipo_visitante,
        'clima': clima_info,
        'usuario_actual': request.user.username
    }
    
    return JsonResponse(resultado)


@api_login_required
@api_rate_limit(max_requests=10, period=3600)
@require_http_methods(["POST"])
@csrf_exempt
def api_simular_resultado(request, partido_id):
    """API para simular un resultado aleatorio de partido"""
    try:
        partido_id = int(partido_id)
    except (ValueError, TypeError):
        return JsonResponse({'error': 'ID de partido inválido'}, status=400)
    
    try:
        # Generar resultado aleatorio realista
        goles_local = random.choice([0, 0, 1, 1, 2, 2, 3])
        goles_visitante = random.choice([0, 0, 1, 1, 2, 2, 3])
        
        # Simular eventos del partido
        eventos = []
        total_goles = goles_local + goles_visitante
        
        if total_goles > 0:
            for i in range(total_goles):
                minuto = random.randint(1, 90)
                equipo = 'local' if i < goles_local else 'visitante'
                eventos.append({
                    'minuto': minuto,
                    'tipo': 'gol',
                    'equipo': equipo,
                    'jugador': f'Jugador {i+1}',
                    'descripcion': 'Gol simulado'
                })
        
        # Agregar algunas tarjetas aleatorias
        for _ in range(random.randint(0, 4)):
            eventos.append({
                'minuto': random.randint(1, 90),
                'tipo': 'tarjeta_amarilla',
                'equipo': random.choice(['local', 'visitante']),
                'jugador': f'Jugador {random.randint(1, 11)}',
                'descripcion': 'Tarjeta amarilla simulada'
            })
        
        # Ordenar eventos por minuto
        eventos.sort(key=lambda x: x['minuto'])
        
        resultado = {
            'partido_id': partido_id,
            'goles_local': goles_local,
            'goles_visitante': goles_visitante,
            'finalizado': True,
            'eventos': eventos,
            'timestamp': datetime.now().isoformat(),
            'simulado_por': request.user.username
        }
        
        return JsonResponse(resultado)
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@api_login_required
@api_rate_limit(max_requests=50, period=3600)
@require_http_methods(["GET"])
def api_pronosticos_ia(request):
    """API que simula pronósticos de IA para partidos próximos"""
    partidos_data = load_json_data('partidos.json')
    
    pronosticos = []
    
    for jornada in partidos_data.get('jornadas', []):
        for partido in jornada.get('partidos', []):
            if not partido.get('finalizado', False):
                # Generar pronóstico aleatorio pero realista
                prob_local = random.randint(20, 60)
                prob_empate = random.randint(15, 35)
                prob_visitante = 100 - prob_local - prob_empate
                
                resultado_mas_probable = max(
                    [('local', prob_local), ('empate', prob_empate), ('visitante', prob_visitante)],
                    key=lambda x: x[1]
                )
                
                pronosticos.append({
                    'partido_id': partido['id'],
                    'probabilidades': {
                        'local': prob_local,
                        'empate': prob_empate,
                        'visitante': prob_visitante
                    },
                    'resultado_predicho': resultado_mas_probable[0],
                    'confianza': resultado_mas_probable[1],
                    'marcador_sugerido': f"{random.randint(0, 3)}-{random.randint(0, 3)}",
                    'algoritmo': 'QuinielasAI v2.1',
                    'factores': [
                        'Rendimiento reciente',
                        'Estadísticas head-to-head',
                        'Condiciones climáticas',
                        'Lesiones de jugadores clave'
                    ],
                    'usuario_solicitante': request.user.username
                })
    
    return JsonResponse({'pronosticos_ia': pronosticos})


@api_login_required
@api_rate_limit(max_requests=100, period=3600)
@require_http_methods(["GET"])
def api_resumen_jornada(request, jornada_numero):
    """API para obtener resumen completo de una jornada"""
    try:
        jornada_numero = int(jornada_numero)
    except (ValueError, TypeError):
        return JsonResponse({'error': 'Número de jornada inválido'}, status=400)
    
    partidos_data = load_json_data('partidos.json')
    equipos_data = load_json_data('equipos.json')
    
    jornada_encontrada = None
    for jornada in partidos_data.get('jornadas', []):
        if jornada['numero'] == jornada_numero:
            jornada_encontrada = jornada
            break
    
    if not jornada_encontrada:
        return JsonResponse({'error': 'Jornada no encontrada'}, status=404)
    
    # Enriquecer partidos con datos de equipos
    equipos = equipos_data.get('equipos', [])
    partidos_enriquecidos = []
    
    for partido in jornada_encontrada.get('partidos', []):
        equipo_local = next((e for e in equipos if e['id'] == partido['equipo_local_id']), None)
        equipo_visitante = next((e for e in equipos if e['id'] == partido['equipo_visitante_id']), None)
        
        partidos_enriquecidos.append({
            **partido,
            'equipo_local_info': equipo_local,
            'equipo_visitante_info': equipo_visitante
        })
    
    # Estadísticas de la jornada
    partidos_finalizados = sum(1 for p in jornada_encontrada['partidos'] if p.get('finalizado', False))
    total_goles = sum(
        (p.get('goles_local', 0) or 0) + (p.get('goles_visitante', 0) or 0) 
        for p in jornada_encontrada['partidos'] 
        if p.get('finalizado', False)
    )
    
    resumen = {
        'jornada': {
            **jornada_encontrada,
            'partidos': partidos_enriquecidos
        },
        'estadisticas': {
            'partidos_totales': len(jornada_encontrada['partidos']),
            'partidos_finalizados': partidos_finalizados,
            'partidos_pendientes': len(jornada_encontrada['partidos']) - partidos_finalizados,
            'total_goles': total_goles,
            'promedio_goles_por_partido': round(total_goles / max(partidos_finalizados, 1), 2)
        },
        'usuario_consultante': request.user.username
    }
    
    return JsonResponse(resumen)


@api_login_required
@api_rate_limit(max_requests=50, period=3600)
@require_http_methods(["GET"])
def api_estadisticas_usuario(request, user_id=None):
    """API para obtener estadísticas específicas de usuario"""
    if user_id is None:
        user_id = request.user.id
    else:
        try:
            user_id = int(user_id)
            # Solo permitir ver estadísticas propias o ser admin
            if user_id != request.user.id and not request.user.is_staff:
                return JsonResponse({
                    'error': 'Sin permisos',
                    'detail': 'Solo puedes ver tus propias estadísticas'
                }, status=403)
        except (ValueError, TypeError):
            return JsonResponse({'error': 'ID de usuario inválido'}, status=400)
    
    # Simular estadísticas de usuario
    stats = {
        'usuario_id': user_id,
        'username': request.user.username,
        'total_apuestas': random.randint(10, 100),
        'apuestas_acertadas': random.randint(5, 50),
        'puntos_totales': random.randint(50, 500),
        'quinielas_participadas': random.randint(1, 10),
        'quinielas_ganadas': random.randint(0, 3),
        'racha_actual': random.randint(0, 10),
        'mejor_racha': random.randint(5, 20),
        'equipo_favorito': random.choice(['América', 'Cruz Azul', 'Chivas', 'Pumas']),
        'ultima_actividad': datetime.now().isoformat()
    }
    
    # Calcular porcentaje de efectividad
    if stats['total_apuestas'] > 0:
        stats['porcentaje_efectividad'] = round(
            (stats['apuestas_acertadas'] / stats['total_apuestas']) * 100, 2
        )
    else:
        stats['porcentaje_efectividad'] = 0.0
    
    return JsonResponse({'estadisticas_usuario': stats})


# ===== ENDPOINTS PÚBLICOS PARA DEMO =====

@require_http_methods(["GET"])
def api_demo_cache(request):
    """Demo público del sistema de cache"""
    cache_key = "demo_cache_test"
    
    # Verificar si existe en cache
    cached_data = cache.get(cache_key)
    if cached_data:
        return JsonResponse({
            'cache_hit': True,
            'data': cached_data,
            'message': 'Datos obtenidos del cache',
            'performance': 'Muy rápido (~1ms)'
        })
    
    # Simular generación de datos (API lenta)
    time.sleep(0.5)  # Simular 500ms de latencia
    new_data = {
        'generated_at': timezone.now().isoformat(),
        'random_stats': {
            'goals_today': random.randint(10, 50),
            'matches_live': random.randint(3, 15),
            'predictions': random.randint(100, 500)
        }
    }
    
    # Guardar en cache por 30 segundos
    cache.set(cache_key, new_data, timeout=30)
    
    return JsonResponse({
        'cache_hit': False,
        'data': new_data,
        'message': 'Datos generados y guardados en cache',
        'performance': 'Lento primera vez (~500ms)',
        'cache_duration': '30 segundos'
    })


@require_http_methods(["GET"])
def api_demo_rate_limiting(request):
    """Demo público de rate limiting simulado"""
    
    # Simular contador en cache
    counter_key = f"rate_limit_demo_{request.META.get('REMOTE_ADDR', 'unknown')}"
    current_count = cache.get(counter_key, 0)
    
    # Limite: 5 requests por minuto
    limit = 5
    window = 60  # segundos
    
    if current_count >= limit:
        return JsonResponse({
            'rate_limited': True,
            'current_count': current_count,
            'limit': limit,
            'window_seconds': window,
            'message': 'Rate limit alcanzado - intenta en 1 minuto',
            'retry_after': window
        }, status=429)
    
    # Incrementar contador
    cache.set(counter_key, current_count + 1, timeout=window)
    
    return JsonResponse({
        'rate_limited': False,
        'current_count': current_count + 1,
        'limit': limit,
        'remaining': limit - current_count - 1,
        'window_seconds': window,
        'message': f'Request {current_count + 1} de {limit} permitido'
    })


@require_http_methods(["POST"])
@csrf_exempt
def api_demo_fallback(request):
    """Demo público del sistema de fallbacks"""
    
    failure_chance = 0.3  # 30% de probabilidad de fallo
    
    if random.random() < failure_chance:
        # Simular fallo y activar fallback
        fallback_data = {
            'source': 'fallback_cache',
            'confidence': 0.75,
            'data': {
                'live_matches': 3,
                'upcoming_matches': 12,
                'last_updated': '2 minutes ago'
            },
            'fallback_reason': 'API principal no disponible'
        }
        
        return JsonResponse({
            'success': False,
            'fallback_activated': True,
            'fallback_data': fallback_data,
            'message': 'API falló - usando datos de fallback'
        })
    else:
        # Funcionamiento normal
        return JsonResponse({
            'success': True,
            'fallback_activated': False,
            'data': {
                'live_matches': random.randint(5, 15),
                'upcoming_matches': random.randint(20, 40),
                'last_updated': 'now'
            },
            'message': 'API funcionando normalmente'
        })


@require_http_methods(["GET"])
def api_demo_optimization(request):
    """Demo completo del sistema de optimización"""
    
    start_time = time.time()
    
    # Simular diferentes escenarios
    scenario = request.GET.get('scenario', 'normal')
    
    if scenario == 'cached':
        # Respuesta super rápida desde cache
        response_data = {
            'scenario': 'cached',
            'data_source': 'redis_cache',
            'response_time_ms': 2,
            'api_calls_saved': 1,
            'cost_saved': '$0.001'
        }
        
    elif scenario == 'rate_limited':
        # Usar fallback por rate limit
        response_data = {
            'scenario': 'rate_limited',
            'data_source': 'intelligent_fallback',
            'response_time_ms': 50,
            'confidence': 0.8,
            'api_calls_saved': 1,
            'fallback_reason': 'Daily API limit reached'
        }
        
    elif scenario == 'api_slow':
        # Simular API lenta
        time.sleep(1)
        response_data = {
            'scenario': 'api_slow',
            'data_source': 'external_api',
            'response_time_ms': 1000,
            'api_calls_used': 1
        }
        
    else:
        # Funcionamiento normal optimizado
        response_data = {
            'scenario': 'optimized',
            'data_source': 'smart_cache',
            'response_time_ms': 10,
            'cache_hit_ratio': 0.85,
            'optimization_active': True
        }
    
    processing_time = round((time.time() - start_time) * 1000, 1)
    
    return JsonResponse({
        'optimization_demo': response_data,
        'actual_processing_time_ms': processing_time,
        'system_status': 'optimized',
        'benefits': [
            '🚀 85% más rápido que APIs directas',
            '💰 90% menos consumo de tokens',
            '🛡️ Fallbacks automáticos',
            '📈 Escalabilidad mejorada'
        ]
    })


# ===== ENDPOINTS PARA TESTING DE OPTIMIZACIÓN =====

@api_login_required
@require_http_methods(["GET"])
def api_test_optimization(request):
    """Endpoint para probar el sistema de optimización con datos simulados"""
    endpoint_type = request.GET.get('type', 'live_matches')
    use_cache = request.GET.get('cache', 'true').lower() == 'true'
    force_api = request.GET.get('force_api', 'false').lower() == 'true'
    
    start_time = time.time()
    
    try:
        # Probar el sistema de optimización
        result = simulate_external_api_call(
            endpoint=endpoint_type,
            data={'force': force_api},
            use_optimization=use_cache
        )
        
        processing_time = round((time.time() - start_time) * 1000, 2)
        
        return JsonResponse({
            'optimization_test': {
                'endpoint_tested': endpoint_type,
                'result': result,
                'processing_time_ms': processing_time,
                'cache_enabled': use_cache,
                'optimization_available': API_OPTIMIZATION_AVAILABLE
            },
            'sistema_info': {
                'cache_backend': str(cache.__class__.__name__),
                'rate_limiting': 'Enabled' if API_OPTIMIZATION_AVAILABLE else 'Mock Only',
                'fallback_system': 'Active'
            }
        })
        
    except Exception as e:
        return JsonResponse({
            'error': str(e),
            'fallback_activated': True,
            'processing_time_ms': round((time.time() - start_time) * 1000, 2)
        })


@api_login_required
@require_http_methods(["GET"])
def api_test_rate_limiting(request):
    """Endpoint para probar rate limiting simulado"""
    
    if not API_OPTIMIZATION_AVAILABLE:
        return JsonResponse({
            'message': 'Sistema de optimización no disponible - usando simulación básica',
            'requests_simulated': 5,
            'rate_limit_behavior': 'Mock only'
        })
    
    results = []
    api_name = 'test_api'
    
    # Simular múltiples requests rápidos
    rate_manager = APIRateLimitManager(
        api_name=api_name,
        daily_limit=3,  # Límite muy bajo para testing
        per_minute_limit=2
    )
    
    for i in range(5):
        try:
            usage = rate_manager.get_current_usage()
            can_request = rate_manager.can_make_request('high')
            
            if can_request:
                rate_manager.record_request('high')
                response_data = f"Request {i+1} successful"
                status = "success"
            else:
                response_data = f"Request {i+1} rate limited"
                status = "rate_limited"
            
            results.append({
                'request_number': i + 1,
                'status': status,
                'data': response_data,
                'daily_usage': f"{usage['daily_used']}/{usage['daily_limit']}",
                'minute_usage': f"{usage['minute_used']}/{usage['minute_limit']}"
            })
            
            time.sleep(0.1)  # Pequeña pausa entre requests
            
        except Exception as e:
            results.append({
                'request_number': i + 1,
                'status': 'error',
                'error': str(e)
            })
    
    return JsonResponse({
        'rate_limiting_test': results,
        'summary': {
            'total_requests': len(results),
            'successful': len([r for r in results if r['status'] == 'success']),
            'rate_limited': len([r for r in results if r['status'] == 'rate_limited']),
            'errors': len([r for r in results if r['status'] == 'error'])
        }
    })


@api_login_required
@require_http_methods(["GET"])
def api_test_cache_performance(request):
    """Endpoint para probar performance del cache"""
    
    cache_keys = [
        'test_live_matches',
        'test_upcoming_games', 
        'test_standings',
        'test_team_stats'
    ]
    
    results = {}
    
    for key in cache_keys:
        # Test cache miss (primera vez)
        start_time = time.time()
        cached_value = cache.get(key)
        miss_time = (time.time() - start_time) * 1000
        
        if cached_value is None:
            # Simular generación de datos y guardar en cache
            mock_data = {
                'generated_at': timezone.now().isoformat(),
                'data': f'Mock data for {key}',
                'size': random.randint(100, 1000)
            }
            cache.set(key, mock_data, timeout=60)
            generation_time = random.uniform(10, 50)  # Simular tiempo de API
        else:
            generation_time = 0
        
        # Test cache hit (segunda vez)
        start_time = time.time()
        cached_value = cache.get(key)
        hit_time = (time.time() - start_time) * 1000
        
        results[key] = {
            'cache_miss_time_ms': round(miss_time, 2),
            'cache_hit_time_ms': round(hit_time, 2),
            'data_generation_time_ms': round(generation_time, 2),
            'performance_improvement': f"{round((generation_time - hit_time) / generation_time * 100, 1)}%" if generation_time > 0 else "N/A",
            'cached_data_available': cached_value is not None
        }
    
    return JsonResponse({
        'cache_performance_test': results,
        'summary': {
            'average_cache_hit_time': round(
                sum(r['cache_hit_time_ms'] for r in results.values()) / len(results), 2
            ),
            'cache_system': 'Active',
            'total_keys_tested': len(cache_keys)
        }
    })


@api_login_required
@require_http_methods(["POST"])
@csrf_exempt
def api_test_fallback_system(request):
    """Endpoint para probar sistema de fallbacks"""
    
    try:
        # Simular diferentes tipos de fallos
        failure_type = request.POST.get('failure_type', 'api_timeout')
        
        if failure_type == 'api_timeout':
            time.sleep(2)  # Simular timeout
            raise Exception("API timeout simulado")
        
        elif failure_type == 'api_unavailable':
            raise Exception("API externa no disponible")
        
        elif failure_type == 'rate_limit_exceeded':
            return JsonResponse({
                'fallback_activated': True,
                'reason': 'Rate limit exceeded',
                'fallback_data': generate_fallback_data('live_matches'),
                'confidence_score': 0.65,
                'recommendation': 'Usar datos cacheados si están disponibles'
            })
        
        elif failure_type == 'partial_data':
            return JsonResponse({
                'partial_success': True,
                'data_received': generate_mock_api_data('live_matches')[:2],  # Solo parte de los datos
                'missing_data_count': 3,
                'fallback_used_for_missing': True
            })
        
        else:
            # Caso normal sin fallos
            return JsonResponse({
                'status': 'success',
                'data': generate_mock_api_data('live_matches'),
                'fallback_needed': False
            })
    
    except Exception as e:
        # Sistema de fallback activado
        fallback_data = generate_fallback_data('live_matches')
        
        return JsonResponse({
            'fallback_system_activated': True,
            'original_error': str(e),
            'fallback_data': fallback_data,
            'data_source': 'intelligent_fallback',
            'confidence_score': 0.7,
            'recommendation': 'Reintentar en 5 minutos'
        })


@require_http_methods(["GET"])
def api_optimization_status_public(request):
    """Endpoint público para verificar estado del sistema de optimización"""
    
    if not API_OPTIMIZATION_AVAILABLE:
        return JsonResponse({
            'optimization_system': 'Not Available',
            'reason': 'Módulos de optimización no importados',
            'mode': 'Basic Mock Only',
            'features_available': ['basic_caching', 'mock_data'],
            'features_missing': ['rate_limiting', 'intelligent_fallback', 'api_batching']
        })
    
    # Probar diferentes componentes
    status = {
        'optimization_system': 'Available',
        'components': {},
        'cache_system': {},
        'rate_limiting': {},
        'demo_mode': True,
        'recommendations': []
    }
    
    # Test cache
    try:
        test_key = f"health_check_{int(time.time())}"
        cache.set(test_key, "test_value", timeout=10)
        cache_value = cache.get(test_key)
        cache.delete(test_key)
        
        status['components']['cache'] = 'Working'
        status['cache_system'] = {
            'backend': str(cache.__class__.__name__),
            'test_result': 'Pass' if cache_value == "test_value" else 'Fail'
        }
    except Exception as e:
        status['components']['cache'] = f'Error: {str(e)}'
    
    # Test rate limiting
    try:
        rate_manager = APIRateLimitManager('health_check', daily_limit=100, per_minute_limit=10)
        current_usage = rate_manager.get_current_usage()
        
        status['components']['rate_limiting'] = 'Working'
        status['rate_limiting'] = {
            'manager_initialized': True,
            'current_usage': current_usage
        }
    except Exception as e:
        status['components']['rate_limiting'] = f'Error: {str(e)}'
    
    # Generar recomendaciones
    if all('Working' in str(comp) for comp in status['components'].values()):
        status['recommendations'] = [
            'Sistema completamente funcional',
            'Usar optimize_api_usage command para sincronización',
            'Configurar monitoreo de rate limits en producción'
        ]
    else:
        status['recommendations'] = [
            'Revisar configuración de cache en settings.py',
            'Verificar importación de módulos de optimización',
            'Usar modo mock para desarrollo'
        ]
    
    return JsonResponse(status)


@api_login_required
@require_http_methods(["GET"])
def api_optimization_status(request):
    """Endpoint para verificar estado del sistema de optimización"""
    
    if not API_OPTIMIZATION_AVAILABLE:
        return JsonResponse({
            'optimization_system': 'Not Available',
            'reason': 'Módulos de optimización no importados',
            'mode': 'Basic Mock Only',
            'features_available': ['basic_caching', 'mock_data'],
            'features_missing': ['rate_limiting', 'intelligent_fallback', 'api_batching']
        })
    
    # Probar diferentes componentes
    status = {
        'optimization_system': 'Available',
        'components': {},
        'cache_system': {},
        'rate_limiting': {},
        'recommendations': []
    }
    
    # Test cache
    try:
        test_key = f"health_check_{int(time.time())}"
        cache.set(test_key, "test_value", timeout=10)
        cache_value = cache.get(test_key)
        cache.delete(test_key)
        
        status['components']['cache'] = 'Working'
        status['cache_system'] = {
            'backend': str(cache.__class__.__name__),
            'test_result': 'Pass' if cache_value == "test_value" else 'Fail'
        }
    except Exception as e:
        status['components']['cache'] = f'Error: {str(e)}'
    
    # Test rate limiting
    try:
        rate_manager = APIRateLimitManager('health_check', daily_limit=100, per_minute_limit=10)
        current_usage = rate_manager.get_current_usage()
        
        status['components']['rate_limiting'] = 'Working'
        status['rate_limiting'] = {
            'manager_initialized': True,
            'current_usage': current_usage
        }
    except Exception as e:
        status['components']['rate_limiting'] = f'Error: {str(e)}'
    
    # Generar recomendaciones
    if all('Working' in str(comp) for comp in status['components'].values()):
        status['recommendations'] = [
            'Sistema completamente funcional',
            'Usar optimize_api_usage command para sincronización',
            'Configurar monitoreo de rate limits en producción'
        ]
    else:
        status['recommendations'] = [
            'Revisar configuración de cache en settings.py',
            'Verificar importación de módulos de optimización',
            'Usar modo mock para desarrollo'
        ]
    
    return JsonResponse(status)


# ===== ENDPOINTS ORIGINALES (MANTENIDOS) =====

@api_login_required
@require_http_methods(["GET"])
def api_status(request):
    """API de estado del sistema"""
    return JsonResponse({
        'status': 'ok',
        'version': '1.0.0',
        'timestamp': datetime.now().isoformat(),
        'usuario': request.user.username,
        'endpoints_disponibles': [
            '/api/equipos/',
            '/api/partidos/',
            '/api/estadisticas/',
            '/api/tabla-posiciones/',
            '/api/partido/<id>/',
            '/api/simular-resultado/<id>/',
            '/api/pronosticos-ia/',
            '/api/jornada/<numero>/',
            '/api/usuario/<id>/estadisticas/',
            '/api/status/',
            '/api/partido/<id>/tiempo-real/',
            '/api/mercado-apuestas/<id>/',
            '/api/analytics-avanzados/<id>/',
            '/api/simular-partido-completo/<id>/',
            '/api/test/optimization/',
            '/api/test/rate-limiting/',
            '/api/test/cache-performance/',
            '/api/test/fallback-system/',
            '/api/test/optimization-status/'
        ]
    })


# ===== NUEVOS ENDPOINTS AVANZADOS =====
    """API de estado del sistema"""
    return JsonResponse({
        'status': 'ok',
        'version': '1.0.0',
        'timestamp': datetime.now().isoformat(),
        'usuario': request.user.username,
        'endpoints_disponibles': [
            '/api/equipos/',
            '/api/partidos/',
            '/api/estadisticas/',
            '/api/tabla-posiciones/',
            '/api/partido/<id>/',
            '/api/simular-resultado/<id>/',
            '/api/pronosticos-ia/',
            '/api/jornada/<numero>/',
            '/api/usuario/<id>/estadisticas/',
            '/api/status/',
            '/api/partido/<id>/tiempo-real/',
            '/api/mercado-apuestas/<id>/',
            '/api/analytics-avanzados/<id>/',
            '/api/simular-partido-completo/<id>/'
        ]
    })


# ===== NUEVOS ENDPOINTS AVANZADOS =====

@api_login_required
@api_rate_limit(max_requests=100, period=3600)
@require_http_methods(["GET"])
def api_partido_tiempo_real(request, partido_id):
    """API para obtener estado de partido en tiempo real"""
    error_response = simulate_api_errors(0.03)
    if error_response:
        return error_response
    
    estados_data = load_json_data('estados_partido.json')
    
    # Buscar estado específico del partido
    for estado in estados_data.get('estados_tiempo_real', []):
        if estado['partido_id'] == int(partido_id):
            return JsonResponse({
                'partido_id': partido_id,
                'estado_tiempo_real': estado,
                'timestamp': datetime.now().isoformat()
            })
    
    # Si no existe, generar estado dinámico REALISTA basado en fecha
    estado_realista = calculate_realistic_match_state(partido_id)
    
    return JsonResponse({
        'partido_id': partido_id,
        'estado_tiempo_real': estado_realista,
        'timestamp': datetime.now().isoformat()
    })


@api_login_required
@api_rate_limit(max_requests=50, period=3600)
@require_http_methods(["GET"])
def api_mercado_apuestas(request, partido_id):
    """API para obtener datos de mercado de apuestas"""
    mercado_data = load_json_data('mercado_analytics.json')
    
    mercado_info = mercado_data.get('mercado_apuestas', {})
    partido_key = f"partido_{partido_id}"
    
    if partido_key in mercado_info.get('cuotas_casas', {}):
        return JsonResponse({
            'partido_id': partido_id,
            'cuotas': mercado_info['cuotas_casas'][partido_key],
            'volumen': mercado_info.get('volumen_apuestas', {}).get(partido_key, {}),
            'movimiento_cuotas': mercado_info.get('movimiento_cuotas', {}).get(partido_key, []),
            'timestamp': datetime.now().isoformat()
        })
    
    # Generar datos simulados si no existen
    return JsonResponse({
        'partido_id': partido_id,
        'cuotas': {
            'bet365': {
                'local': round(random.uniform(1.5, 4.0), 2),
                'empate': round(random.uniform(2.8, 3.5), 2),
                'visitante': round(random.uniform(1.5, 4.0), 2)
            }
        },
        'volumen': {
            'total_apostadores': random.randint(1000, 50000),
            'monto_total': random.randint(100000, 5000000)
        },
        'timestamp': datetime.now().isoformat()
    })


@api_login_required
@api_rate_limit(max_requests=30, period=3600)
@require_http_methods(["GET"])
def api_analytics_avanzados(request, partido_id):
    """API para analytics avanzados con IA"""
    analytics_data = load_json_data('mercado_analytics.json')
    
    analytics_info = analytics_data.get('analytics_avanzados', {})
    partido_key = f"partido_{partido_id}"
    
    if partido_key in analytics_info.get('predicciones_ia', {}):
        prediccion = analytics_info['predicciones_ia'][partido_key]
        return JsonResponse({
            'partido_id': partido_id,
            'prediccion_ia': prediccion,
            'patrones_temporada': analytics_info.get('patrones_temporada', {}),
            'timestamp': datetime.now().isoformat()
        })
    
    # Generar predicción simulada
    return JsonResponse({
        'partido_id': partido_id,
        'prediccion_ia': {
            'modelo_ml': 'RandomForest_v2.1',
            'confianza': round(random.uniform(0.6, 0.9), 2),
            'prediccion': {
                'resultado_mas_probable': random.choice(['local', 'empate', 'visitante']),
                'probabilidad': round(random.uniform(0.3, 0.7), 2),
                'goles_esperados_local': round(random.uniform(0.5, 3.0), 1),
                'goles_esperados_visitante': round(random.uniform(0.5, 3.0), 1)
            }
        },
        'timestamp': datetime.now().isoformat()
    })


@api_login_required
@api_rate_limit(max_requests=10, period=3600)
@require_http_methods(["POST"])
def api_simular_partido_completo(request, partido_id):
    """API para simular un partido completo en tiempo acelerado"""
    try:
        # Simulación básica sin dependencias externas
        simulacion = {
            'partido_id': int(partido_id),
            'goles_local': random.randint(0, 4),
            'goles_visitante': random.randint(0, 4),
            'eventos_destacados': random.randint(2, 8),
            'minutos_simulados': 90,
            'eventos': [
                {
                    'minuto': random.randint(1, 90),
                    'tipo': 'gol',
                    'equipo': random.choice(['local', 'visitante']),
                    'descripcion': 'Gol simulado'
                } for _ in range(random.randint(1, 5))
            ]
        }
        
        return JsonResponse({
            'partido_id': partido_id,
            'simulacion': simulacion,
            'timestamp': datetime.now().isoformat(),
            'simulador': 'BasicSimulator v1.0'
        })
    
    except Exception as e:
        return JsonResponse({
            'error': str(e),
            'partido_id': partido_id,
            'simulacion_basica': {
                'goles_local': random.randint(0, 4),
                'goles_visitante': random.randint(0, 4),
                'eventos_destacados': random.randint(2, 8)
            }
        })
