import json
import os
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from datetime import datetime, timedelta
import random
from .decorators import api_login_required, api_rate_limit


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
            '/api/status/'
        ]
    })
