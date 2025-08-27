from django.urls import path
from . import views

app_name = 'api_mock'

urlpatterns = [
    # APIs básicas
    path('equipos/', views.api_equipos, name='equipos'),
    path('partidos/', views.api_partidos, name='partidos'),
    path('estadisticas/', views.api_estadisticas, name='estadisticas'),
    path('tabla-posiciones/', views.api_tabla_posiciones, name='tabla_posiciones'),
    
    # APIs específicas
    path('partido/<int:partido_id>/', views.api_partido_detalle, name='partido_detalle'),
    path('partido/<int:partido_id>/simular/', views.api_simular_resultado, name='simular_resultado'),
    path('jornada/<int:jornada_numero>/resumen/', views.api_resumen_jornada, name='resumen_jornada'),
    
    # APIs avanzadas
    path('pronosticos-ia/', views.api_pronosticos_ia, name='pronosticos_ia'),
    
    # APIs de usuario
    path('usuario/<int:user_id>/estadisticas/', views.api_estadisticas_usuario, name='estadisticas_usuario'),
    path('usuario/estadisticas/', views.api_estadisticas_usuario, name='estadisticas_usuario_actual'),
    
    # API de estado
    path('status/', views.api_status, name='status'),
    
    # ===== NUEVAS APIs AVANZADAS =====
    # Tiempo real y simulaciones
    path('partido/<int:partido_id>/tiempo-real/', views.api_partido_tiempo_real, name='partido_tiempo_real'),
    path('partido/<int:partido_id>/mercado-apuestas/', views.api_mercado_apuestas, name='mercado_apuestas'),
    path('partido/<int:partido_id>/analytics-avanzados/', views.api_analytics_avanzados, name='analytics_avanzados'),
    path('partido/<int:partido_id>/simular-completo/', views.api_simular_partido_completo, name='simular_partido_completo'),
    
    # ===== ENDPOINTS PARA TESTING DE OPTIMIZACIÓN =====
    path('test/optimization/', views.api_test_optimization, name='test_optimization'),
    path('test/rate-limiting/', views.api_test_rate_limiting, name='test_rate_limiting'),
    path('test/cache-performance/', views.api_test_cache_performance, name='test_cache_performance'),
    path('test/fallback-system/', views.api_test_fallback_system, name='test_fallback_system'),
    path('test/optimization-status/', views.api_optimization_status, name='optimization_status'),
    path('test/optimization-status-public/', views.api_optimization_status_public, name='optimization_status_public'),
    
    # ===== DEMOS PÚBLICOS =====
    path('demo/cache/', views.api_demo_cache, name='demo_cache'),
    path('demo/rate-limiting/', views.api_demo_rate_limiting, name='demo_rate_limiting'),
    path('demo/fallback/', views.api_demo_fallback, name='demo_fallback'),
    path('demo/optimization/', views.api_demo_optimization, name='demo_optimization'),
]
