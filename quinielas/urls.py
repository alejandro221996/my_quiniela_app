from django.urls import path
from . import views

app_name = 'quinielas'

urlpatterns = [
    # URLs principales
    path('', views.HomeView.as_view(), name='home'),
    path('dashboard/', views.dashboard_unified, name='dashboard'),
    path('dashboard-optimizado/', views.dashboard_optimizado, name='dashboard_optimizado'),
    path('api-optimization-status/', views.api_optimization_status_view, name='api_optimization_status'),
    path('crear/', views.CrearQuinielaView.as_view(), name='crear'),
    path('unirse/', views.unirse_quiniela, name='unirse'),
    path('registro-rapido/', views.registro_con_codigo, name='registro_rapido'),
    
    # URLs de quinielas (ID primero para compatibilidad, luego slug)
    path('quiniela/<int:pk>/', views.DetalleQuinielaView.as_view(), name='detalle'),
    path('quiniela/<int:pk>/ranking/', views.ranking_quiniela, name='ranking'),
    path('quiniela/<slug:slug>/', views.DetalleQuinielaSlugView.as_view(), name='detalle_slug'),
    path('quiniela/<slug:slug>/ranking/', views.ranking_quiniela_slug, name='ranking_slug'),
    
    # URLs de partidos y apuestas (versiones amigables + compatibilidad)
    path('partidos/', views.PartidosView.as_view(), name='partidos'),
    path('partido/<slug:slug>/apostar/', views.apostar_partido_slug, name='apostar_slug'),
    path('apostar/<int:partido_id>/', views.apostar_partido, name='apostar'),  # Mantener compatibilidad
    path('mis-apuestas/', views.MisApuestasView.as_view(), name='mis_apuestas'),
    
    # URLs de promoción de usuarios
    path('solicitar-promocion/', views.solicitar_promocion, name='solicitar_promocion'),
    path('aprobar-promocion/<int:user_id>/', views.aprobar_promocion, name='aprobar_promocion'),
    
    # URLs de gestión de participantes (solo para creadores)
    path('quiniela/<int:quiniela_id>/gestionar-participantes/', views.gestionar_participantes, name='gestionar_participantes'),
    path('quiniela/<int:quiniela_id>/marcar-pago/', views.marcar_pago_participante, name='marcar_pago_participante'),
    path('quiniela/<int:quiniela_id>/cambiar-estado/', views.cambiar_estado_participante, name='cambiar_estado_participante'),
    path('quiniela/<int:quiniela_id>/eliminar-participante/', views.eliminar_participante, name='eliminar_participante'),
    path('quiniela/<int:quiniela_id>/exportar-participantes/', views.exportar_participantes, name='exportar_participantes'),
    path('quiniela/<int:quiniela_id>/dashboard-creador/', views.dashboard_creador, name='dashboard_creador'),
]
