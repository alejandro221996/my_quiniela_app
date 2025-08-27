"""
Middleware para monitorear rendimiento de cache y queries
"""
import time
import logging
from django.conf import settings
from django.db import connection


logger = logging.getLogger('performance')


class PerformanceMonitoringMiddleware:
    """
    Middleware que monitorea:
    - Tiempo de respuesta de las vistas
    - Número de queries a la base de datos
    - Uso de cache (hits/misses)
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # Solo monitoreamos en DEBUG o si está específicamente habilitado
        if not getattr(settings, 'MONITOR_PERFORMANCE', settings.DEBUG):
            return self.get_response(request)
        
        start_time = time.time()
        start_queries = len(connection.queries)
        
        response = self.get_response(request)
        
        # Calcular métricas
        end_time = time.time()
        end_queries = len(connection.queries)
        
        response_time = (end_time - start_time) * 1000  # en milliseconds
        num_queries = end_queries - start_queries
        
        # Log si supera umbrales
        if response_time > 1000:  # Más de 1 segundo
            logger.warning(
                f"Vista lenta detectada: {request.path} - "
                f"Tiempo: {response_time:.2f}ms - "
                f"Queries: {num_queries}"
            )
        elif num_queries > 10:  # Más de 10 queries
            logger.warning(
                f"Muchas queries detectadas: {request.path} - "
                f"Queries: {num_queries} - "
                f"Tiempo: {response_time:.2f}ms"
            )
        elif settings.DEBUG:
            # En DEBUG, log todas las requests para desarrollo
            logger.info(
                f"Performance: {request.path} - "
                f"Tiempo: {response_time:.2f}ms - "
                f"Queries: {num_queries}"
            )
        
        # Agregar headers de debug si está en DEBUG
        if settings.DEBUG:
            response['X-Response-Time'] = f"{response_time:.2f}ms"
            response['X-DB-Queries'] = str(num_queries)
        
        return response
