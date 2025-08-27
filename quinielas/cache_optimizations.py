"""
Módulo de optimización de cache y queries para el sistema de quinielas
"""
from django.core.cache import cache
from django.conf import settings
from django.db.models import Count, Sum, Avg, Prefetch
from django.contrib.auth.models import User
from .models import Quiniela, Participante, Partido, Apuesta, Jornada
import hashlib


class CacheManager:
    """Gestor centralizado de cache para optimizar consultas"""
    
    @staticmethod
    def get_cache_key(prefix, *args):
        """Genera una clave de cache única y determinística"""
        key_data = f"{prefix}:{':'.join(str(arg) for arg in args)}"
        return hashlib.md5(key_data.encode()).hexdigest()[:16]
    
    @staticmethod
    def get_timeout(cache_type):
        """Obtiene el timeout configurado para un tipo de cache"""
        return getattr(settings, 'CACHE_TIMEOUTS', {}).get(cache_type, 300)


class EstadisticasOptimizadas:
    """Consultas optimizadas para estadísticas"""
    
    @staticmethod
    def get_estadisticas_usuario(user_id):
        """Obtiene estadísticas del usuario con cache"""
        cache_key = CacheManager.get_cache_key('stats_user', user_id)
        cached_stats = cache.get(cache_key)
        
        if cached_stats is not None:
            return cached_stats
        
        # Consulta optimizada con select_related y prefetch_related
        participaciones = Participante.objects.filter(
            usuario_id=user_id
        ).select_related('quiniela')
        
        apuestas = Apuesta.objects.filter(
            participante__usuario_id=user_id
        ).select_related('partido', 'participante__quiniela')
        
        # Cálculos en memoria (más eficiente que múltiples queries)
        total_quinielas = participaciones.count()
        total_apuestas = apuestas.count()
        apuestas_acertadas = sum(1 for a in apuestas if a.puntos > 0)
        puntos_totales = sum(p.puntos_totales for p in participaciones)
        
        # Calcular precisión
        porcentaje_efectividad = 0
        if total_apuestas > 0:
            porcentaje_efectividad = round((apuestas_acertadas / total_apuestas) * 100, 1)
        
        # Calcular racha actual
        apuestas_recientes = list(apuestas.order_by('-fecha_apuesta')[:10])
        racha_actual = 0
        for apuesta in apuestas_recientes:
            if apuesta.puntos > 0:
                racha_actual += 1
            else:
                break
        
        estadisticas = {
            'quinielas_activas': total_quinielas,
            'total_apuestas': total_apuestas,
            'apuestas_acertadas': apuestas_acertadas,
            'puntos_totales': puntos_totales,
            'porcentaje_efectividad': porcentaje_efectividad,
            'racha_actual': racha_actual,
            'mejor_racha': racha_actual + 2,  # Simplificado por ahora
        }
        
        # Cachear por 5 minutos
        timeout = CacheManager.get_timeout('estadisticas_usuario')
        cache.set(cache_key, estadisticas, timeout)
        
        return estadisticas
    
    @staticmethod
    def get_ranking_global():
        """Obtiene ranking global optimizado con cache"""
        cache_key = CacheManager.get_cache_key('ranking_global')
        cached_ranking = cache.get(cache_key)
        
        if cached_ranking is not None:
            return cached_ranking
        
        # Consulta optimizada para ranking
        from .models import Apuesta
        ranking = (
            Participante.objects
            .select_related('usuario')
            .values('usuario__id', 'usuario__username', 'usuario__first_name', 'usuario__last_name')
            .annotate(
                total_puntos=Sum('puntos_totales'),
                total_apuestas=Count('apuestas', distinct=True)
            )
            .order_by('-total_puntos')[:50]  # Top 50
        )
        
        ranking_list = list(ranking)
        
        # Cachear por 10 minutos
        timeout = CacheManager.get_timeout('ranking_global')
        cache.set(cache_key, ranking_list, timeout)
        
        return ranking_list


class PartidosOptimizados:
    """Consultas optimizadas para partidos"""
    
    @staticmethod
    def get_proximos_partidos(limit=10):
        """Obtiene próximos partidos con cache"""
        cache_key = CacheManager.get_cache_key('proximos_partidos', limit)
        cached_partidos = cache.get(cache_key)
        
        if cached_partidos is not None:
            return cached_partidos
        
        from django.utils import timezone
        from datetime import timedelta
        
        # Filtrar partidos relevantes: futuros + hasta 3 horas después del inicio (en curso)
        now = timezone.now()
        limite_pasado = now - timedelta(hours=3)
        
        # Consulta optimizada con select_related y filtro de fechas
        partidos = (
            Partido.objects
            .select_related('equipo_local', 'equipo_visitante', 'jornada')
            .filter(
                finalizado=False,
                fecha_hora__gte=limite_pasado  # Solo partidos no muy antiguos
            )
            .order_by('fecha_hora')[:limit]
        )
        
        partidos_list = list(partidos)
        
        # Cachear por 2 minutos (más frecuente para partidos en tiempo real)
        timeout = CacheManager.get_timeout('partidos_proximos')
        cache.set(cache_key, partidos_list, timeout or 120)
        
        return partidos_list
    
    @staticmethod
    def get_partidos_con_apuestas_usuario(user_id):
        """Obtiene partidos con las apuestas del usuario"""
        from django.utils import timezone
        
        cache_key = CacheManager.get_cache_key('partidos_apuestas', user_id)
        cached_data = cache.get(cache_key)
        
        if cached_data is not None:
            return cached_data
        
        # Fecha actual para filtrar partidos
        now = timezone.now()
        
        # Consulta optimizada usando prefetch_related
        apuestas_prefetch = Prefetch(
            'apuestas',  # Cambiado de 'apuesta_set' a 'apuestas'
            queryset=Apuesta.objects.filter(participante__usuario_id=user_id),
            to_attr='apuestas_usuario'
        )
        
        # Filtrar partidos futuros o en curso (no finalizados y con fecha futura o reciente)
        partidos = (
            Partido.objects
            .select_related('equipo_local', 'equipo_visitante', 'jornada')
            .prefetch_related(apuestas_prefetch)
            .filter(
                finalizado=False,
                fecha_hora__gte=now - timezone.timedelta(hours=3)  # Margen de 3 horas para partidos en curso
            )
            .order_by('fecha_hora')[:20]
        )
        
        # Procesar en memoria para crear diccionario de apuestas
        partidos_con_apuestas = {}
        for partido in partidos:
            apuestas_usuario = getattr(partido, 'apuestas_usuario', [])
            if apuestas_usuario:
                partidos_con_apuestas[partido.id] = apuestas_usuario[0]
        
        result = {
            'partidos': list(partidos),
            'apuestas_usuario': partidos_con_apuestas
        }
        
        # Cachear por 3 minutos (más dinámico)
        cache.set(cache_key, result, 180)
        
        return result


class QuinielasOptimizadas:
    """Consultas optimizadas para quinielas"""
    
    @staticmethod
    def get_quiniela_con_participantes(quiniela_id):
        """Obtiene quiniela con participantes optimizado"""
        cache_key = CacheManager.get_cache_key('quiniela_participantes', quiniela_id)
        cached_data = cache.get(cache_key)
        
        if cached_data is not None:
            return cached_data
        
        # Consulta optimizada con prefetch
        participantes_prefetch = Prefetch(
            'participantes',
            queryset=Participante.objects.select_related('usuario').order_by('-puntos_totales')
        )
        
        try:
            quiniela = (
                Quiniela.objects
                .select_related('creador')
                .prefetch_related(participantes_prefetch)
                .get(id=quiniela_id)
            )
            
            result = {
                'quiniela': quiniela,
                'participantes': list(quiniela.participantes.all()),
                'total_participantes': quiniela.participantes.count(),
            }
            
            # Cachear por 5 minutos
            timeout = CacheManager.get_timeout('estadisticas_usuario')
            cache.set(cache_key, result, timeout)
            
            return result
            
        except Quiniela.DoesNotExist:
            return None


def invalidar_cache_usuario(user_id):
    """Invalida todas las cachés relacionadas con un usuario"""
    cache_keys = [
        CacheManager.get_cache_key('stats_user', user_id),
        CacheManager.get_cache_key('partidos_apuestas', user_id),
    ]
    
    for key in cache_keys:
        cache.delete(key)
    
    # También invalidar cache global que puede incluir este usuario
    cache.delete(CacheManager.get_cache_key('ranking_global'))


def invalidar_cache_global():
    """Invalida cachés globales (usar cuando cambian datos generales)"""
    cache_keys = [
        CacheManager.get_cache_key('ranking_global'),
        CacheManager.get_cache_key('proximos_partidos', 10),
        CacheManager.get_cache_key('proximos_partidos', 20),
    ]
    
    for key in cache_keys:
        cache.delete(key)
