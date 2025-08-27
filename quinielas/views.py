from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth import authenticate, login
from django.contrib import messages
from django.views.generic import ListView, DetailView, CreateView, UpdateView
from django.urls import reverse_lazy, reverse
from django.db.models import Q, Count, Avg
from django.utils import timezone
from django.http import JsonResponse
from django.views.decorators.cache import cache_page
from django.utils.decorators import method_decorator
from django.core.cache import cache
from .models import Quiniela, Participante, Partido, Apuesta, Jornada
from .forms import QuinielaForm, ApuestaForm, UnirseQuinielaForm
from .forms_extended import RegistroConCodigoForm
from .services import data_enricher
from .optimized_data_enricher import data_enricher as optimized_enricher, API_OPTIMIZATION_AVAILABLE
from .cache_optimizations import (
    EstadisticasOptimizadas, 
    PartidosOptimizados, 
    QuinielasOptimizadas,
    invalidar_cache_usuario,
    invalidar_cache_global
)
import random
from datetime import datetime, timedelta


@login_required
def dashboard_optimizado(request):
    """
    Dashboard con sistema de optimización de APIs
    TRANSPARENTE: funciona igual con APIs mock y reales
    """
    start_time = timezone.now()
    
    # Configurar optimized enricher
    optimized_enricher.set_user_context(request.user, request.session.session_key)
    
    try:
        # Obtener todos los datos del dashboard con optimización
        datos_dashboard = optimized_enricher.obtener_datos_dashboard(request.user)
        
        # Obtener datos de estadísticas locales
        estadisticas_locales = EstadisticasOptimizadas.get_ranking_global()
        
        # Obtener partidos en vivo si están disponibles
        partidos_vivo = optimized_enricher.obtener_partidos_en_vivo()
        
        # Calcular tiempo de procesamiento
        tiempo_procesamiento = (timezone.now() - start_time).total_seconds() * 1000
        
        context = {
            # Datos principales
            'equipos_populares': datos_dashboard.get('equipos_populares', [])[:6],
            'partidos_proximos': datos_dashboard.get('partidos_proximos', [])[:8],
            'tabla_posiciones': datos_dashboard.get('tabla_posiciones', [])[:10],
            'partidos_en_vivo': partidos_vivo.get('data', [])[:5] if partidos_vivo else [],
            
            # Estadísticas locales
            'ranking_usuarios': estadisticas_locales[:10],
            'quinielas_activas': QuinielasOptimizadas.get_quinielas_activas()[:5],
            
            # Metadata de optimización
            'optimizacion_info': {
                'metadata': datos_dashboard.get('metadata', {}),
                'tiempo_procesamiento_ms': round(tiempo_procesamiento, 1),
                'cache_hits': datos_dashboard.get('metadata', {}).get('cached_count', 0),
                'api_mode': datos_dashboard.get('metadata', {}).get('api_mode', 'unknown'),
                'sources': datos_dashboard.get('metadata', {}).get('sources', {}),
                'partidos_vivo_source': partidos_vivo.get('source', 'none') if partidos_vivo else 'none'
            }
        }
        
        return render(request, 'quinielas/dashboard_optimizado.html', context)
        
    except Exception as e:
        messages.error(request, f'Error obteniendo datos del dashboard: {e}')
        # Fallback a dashboard básico
        return render(request, 'quinielas/dashboard_optimizado.html', {
            'equipos_populares': [],
            'partidos_proximos': [],
            'tabla_posiciones': [],
            'optimizacion_info': {
                'error': str(e),
                'fallback_activo': True
            }
        })


@login_required
def api_optimization_status_view(request):
    """Vista para mostrar estado de optimización de APIs"""
    
    context = {
        'mock_mode': optimized_enricher.api_config['mock_mode'],
        'api_config': optimized_enricher.api_config,
        'optimization_available': API_OPTIMIZATION_AVAILABLE,
    }
    
    # Obtener estadísticas de cache
    try:
        cache_stats = cache.get('api_cache_stats', {
            'hits': 0,
            'misses': 0,
            'total_requests': 0
        })
        context['cache_stats'] = cache_stats
    except:
        context['cache_stats'] = {'error': 'Cache stats not available'}
    
    return render(request, 'quinielas/api_optimization_status.html', context)


class HomeView(ListView):
    """Vista principal que redirige al dashboard avanzado"""
    
    def get(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect('quinielas:dashboard')
        else:
            # Para usuarios no autenticados, mostrar página de bienvenida
            return render(request, 'quinielas/landing.html')
        return Quiniela.objects.none()
    """Vista principal que redirige al dashboard avanzado"""
    
    def get(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect('quinielas:dashboard')
        else:
            # Para usuarios no autenticados, mostrar página de bienvenida
            return render(request, 'quinielas/landing.html')
        return Quiniela.objects.none()
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.user.is_authenticated:
            # USAR SISTEMA OPTIMIZADO DE APIS
            # Funciona con mock APIs ahora y reales después sin cambios
            optimized_enricher.set_user_context(self.request.user, self.request.session.session_key)
            
            # Obtener datos del dashboard con optimización automática
            datos_dashboard = optimized_enricher.obtener_datos_dashboard(self.request.user)
            
            # Agregar datos enriquecidos al contexto
            context['equipos_populares'] = datos_dashboard.get('equipos_populares', [])[:4]
            context['partidos_proximos'] = datos_dashboard.get('partidos_proximos', [])
            context['tabla_posiciones'] = datos_dashboard.get('tabla_posiciones', [])[:5]
            
            # Metadata de optimización (opcional, para debugging)
            context['api_metadata'] = datos_dashboard.get('metadata', {})
            
            # También obtener datos locales del cache optimizado
            try:
                context['estadisticas_rapidas'] = EstadisticasOptimizadas.get_ranking_global()[:5]
                context['ultimas_quinielas'] = QuinielasOptimizadas.get_quinielas_recientes()[:3]
            except Exception as e:
                # Fallback local
                context['estadisticas_rapidas'] = []
                context['ultimas_quinielas'] = []
            context['estadisticas'] = datos_dashboard.get('estadisticas_usuario', {})
            context['ultimos_resultados'] = datos_dashboard.get('ultimos_resultados', [])
            context['pronosticos_ia'] = datos_dashboard.get('pronosticos_destacados', [])
            
            # Agregar datos locales
            context['jornada_actual'] = Jornada.objects.filter(activa=True).first()
            
            # Estadísticas locales del usuario
            quinielas_count = self.get_queryset().count()
            apuestas_count = Apuesta.objects.filter(
                participante__usuario=self.request.user
            ).count()
            puntos_totales = sum(
                p.puntos_totales for p in Participante.objects.filter(usuario=self.request.user)
            )
            
            # Combinar estadísticas de API y locales
            stats = context['estadisticas']
            stats.update({
                'quinielas_activas': quinielas_count,
                'apuestas_locales': apuestas_count,
                'puntos_locales': puntos_totales
            })
            
            # Información del perfil de usuario
            profile = None
            try:
                profile = self.request.user.profile
            except:
                # Crear perfil si no existe (usuarios antiguos)
                from accounts.models import UserProfile
                profile, created = UserProfile.objects.get_or_create(user=self.request.user)
            
            if profile:
                context['user_profile'] = profile
                context['puede_crear_quinielas'] = profile.puede_crear_quinielas
                context['puede_solicitar_promocion'] = profile.puede_solicitar_promocion
                context['tipo_usuario_display'] = profile.get_tipo_usuario_display()
            else:
                # Fallback si no se puede crear el perfil
                context['user_profile'] = None
                context['puede_crear_quinielas'] = False
                context['puede_solicitar_promocion'] = True
                context['tipo_usuario_display'] = 'Participante'
            
        return context


class CrearQuinielaView(LoginRequiredMixin, CreateView):
    """Vista para crear una nueva quiniela - Solo organizadores"""
    model = Quiniela
    form_class = QuinielaForm
    template_name = 'quinielas/crear_quiniela.html'
    success_url = reverse_lazy('quinielas:home')
    
    def dispatch(self, request, *args, **kwargs):
        """Verificar que el usuario puede crear quinielas"""
        puede_crear = False
        try:
            if hasattr(request.user, 'profile') and request.user.profile:
                puede_crear = request.user.profile.puede_crear_quinielas
        except:
            puede_crear = False
            
        if not puede_crear:
            messages.error(
                request, 
                'Solo los Organizadores pueden crear quinielas. '
                'Los Participantes pueden solicitar promoción desde su perfil.'
            )
            return redirect('quinielas:home')
        return super().dispatch(request, *args, **kwargs)
    
    def form_valid(self, form):
        form.instance.creador = self.request.user
        response = super().form_valid(form)
        
        messages.success(
            self.request, 
            f'Quiniela "{self.object.nombre}" creada exitosamente. '
            f'Código de acceso: {self.object.codigo_acceso}. '
            f'Comparte este código con otros usuarios para que se unan.'
        )
        return response


class DetalleQuinielaView(LoginRequiredMixin, DetailView):
    """Vista de detalle de una quiniela"""
    model = Quiniela
    template_name = 'quinielas/detalle_quiniela.html'
    context_object_name = 'quiniela'
    
    def get_object(self):
        quiniela = get_object_or_404(Quiniela, pk=self.kwargs['pk'])
        
        # Verificar que el usuario tenga acceso
        if not (quiniela.creador == self.request.user or 
                quiniela.participantes.filter(usuario=self.request.user).exists()):
            messages.error(self.request, "No tienes acceso a esta quiniela.")
            # No podemos hacer redirect aquí, solo retornar el objeto
            # El redirect se manejará en el template o con middleware
        
        return quiniela
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        quiniela = self.object
        
        # Ranking de participantes
        context['ranking'] = quiniela.participantes.all()
        
        # Verificar si el usuario es participante
        context['es_participante'] = quiniela.participantes.filter(
            usuario=self.request.user
        ).exists()
        
        # Próximos partidos disponibles para apostar
        partidos_disponibles = Partido.objects.filter(
            fecha_hora__gt=timezone.now(),
            finalizado=False
        ).order_by('fecha_hora')[:5]
        
        context['partidos_disponibles'] = partidos_disponibles
        
        return context


@login_required
def unirse_quiniela(request):
    """Vista para unirse a una quiniela usando código de acceso"""
    if request.method == 'POST':
        form = UnirseQuinielaForm(request.POST)
        if form.is_valid():
            codigo = form.cleaned_data['codigo_acceso'].upper()
            
            try:
                quiniela = Quiniela.objects.get(codigo_acceso=codigo, activa=True)
                
                # Verificar si es el creador de la quiniela
                if quiniela.creador == request.user:
                    messages.error(
                        request, 
                        "No puedes unirte a una quiniela que tú creaste. "
                        "Como creador, ya tienes acceso completo para administrarla."
                    )
                    return render(request, 'quinielas/unirse_quiniela.html', {'form': form})
                
                # Verificar si ya es participante
                if quiniela.participantes.filter(usuario=request.user).exists():
                    messages.warning(request, "Ya eres participante de esta quiniela.")
                    return redirect('quinielas:detalle', pk=quiniela.pk)
                
                # Verificar si la quiniela aún permite nuevos participantes
                if not quiniela.puede_apostar:
                    messages.error(request, "Esta quiniela ya no acepta nuevos participantes (fecha límite vencida).")
                    return render(request, 'quinielas/unirse_quiniela.html', {'form': form})
                
                # Crear participante
                Participante.objects.create(
                    usuario=request.user,
                    quiniela=quiniela
                )
                messages.success(
                    request, 
                    f'¡Bienvenido! Te has unido exitosamente a la quiniela "{quiniela.nombre}".'
                    )
                
                return redirect('quinielas:detalle', pk=quiniela.pk)
                
            except Quiniela.DoesNotExist:
                messages.error(request, "Código de acceso inválido o quiniela no activa.")
    
    else:
        form = UnirseQuinielaForm()
    
    return render(request, 'quinielas/unirse_quiniela.html', {'form': form})


@method_decorator(cache_page(60 * 2), name='dispatch')  # Cache por 2 minutos
class PartidosView(LoginRequiredMixin, ListView):
    """Vista que muestra todos los partidos disponibles (optimizada)"""
    model = Partido
    template_name = 'quinielas/partidos.html'
    context_object_name = 'partidos'
    paginate_by = 10
    
    def get_queryset(self):
        # Usar la optimización de cache para obtener partidos
        return PartidosOptimizados.get_proximos_partidos(20)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # 🚀 OPTIMIZACIÓN CON API: Obtener datos enriquecidos de partidos
        try:
            datos_partidos = optimized_enricher.obtener_datos_dashboard(self.request.user)
            partidos_api = datos_partidos.get('partidos_proximos', [])
            equipos_api = datos_partidos.get('equipos_populares', [])
            
            # Enriquecer partidos con datos de API
            partidos_enriquecidos = []
            for partido in context['partidos']:
                partido_dict = {
                    'partido_bd': partido,
                    'equipo_local': partido.equipo_local,
                    'equipo_visitante': partido.equipo_visitante,
                    'fecha_hora': partido.fecha_hora,
                    'puede_apostar': partido.puede_apostar,
                    'estado': partido.estado_actual,
                    'api_data': {}  # Placeholder para datos de API adicionales
                }
                
                # Buscar datos adicionales de API si coincide el nombre
                for partido_api in partidos_api:
                    if (partido_api.get('equipo_local', '').lower() == partido.equipo_local.nombre.lower() or
                        partido_api.get('equipo_visitante', '').lower() == partido.equipo_visitante.nombre.lower()):
                        partido_dict['api_data'] = {
                            'probabilidades': partido_api.get('probabilidades', {}),
                            'forma_equipos': partido_api.get('forma_reciente', {}),
                            'estadisticas_head2head': partido_api.get('historial', {})
                        }
                        break
                
                partidos_enriquecidos.append(partido_dict)
            
            context['partidos_enriquecidos'] = partidos_enriquecidos
            context['equipos_destacados'] = equipos_api[:5]
            context['api_conectada'] = True
            context['api_metadata'] = datos_partidos.get('metadata', {})
            
        except Exception as e:
            # Error enriqueciendo datos de partidos - continuar sin datos de API
            context['api_conectada'] = False
        
        # Cache para jornadas activas
        cache_key = f"jornadas_activas"
        jornadas = cache.get(cache_key)
        if jornadas is None:
            jornadas = list(Jornada.objects.filter(activa=True))
            cache.set(cache_key, jornadas, 300)  # 5 minutos
        
        context['jornadas'] = jornadas
        context['now'] = timezone.now()
        
        # Usar optimización de cache para apuestas del usuario
        if hasattr(self, 'object_list') and self.object_list:
            partidos_data = PartidosOptimizados.get_partidos_con_apuestas_usuario(self.request.user.id)
            apuestas_usuario_dict = partidos_data['apuestas_usuario']
            
            # Convertir a formato esperado por el template
            apuestas_usuario = {}
            for partido_id, apuesta in apuestas_usuario_dict.items():
                apuestas_usuario[partido_id] = {
                    'goles_local': apuesta.goles_local_apostados,
                    'goles_visitante': apuesta.goles_visitante_apostados,
                    'quiniela': apuesta.participante.quiniela.nombre,
                    'puntos': apuesta.puntos,
                    'fecha_apuesta': apuesta.fecha_modificacion
                }
        else:
            apuestas_usuario = {}
        
        context['apuestas_usuario'] = apuestas_usuario
        context['partidos_apostados'] = list(apuestas_usuario.keys())
        
        return context


@login_required
def apostar_partido(request, partido_id):
    """Vista para apostar en un partido específico"""
    partido = get_object_or_404(Partido, pk=partido_id)
    
    # Para peticiones HEAD, solo verificar si puede apostar
    if request.method == 'HEAD':
        if not partido.puede_apostar:
            return JsonResponse({'success': False}, status=400)
        
        # Verificar quinielas - SOLO como participante, NO como creador
        quinielas_usuario = Quiniela.objects.filter(
            participantes__usuario=request.user,
            activa=True,
            fecha_limite__gt=timezone.now()
        ).distinct()
        
        if not quinielas_usuario.exists():
            # Para HEAD request, simplemente devolver false sin mensaje detallado
            return JsonResponse({'success': False}, status=400)
            
        return JsonResponse({'success': True})
    
    # Verificar que el partido permita apuestas usando la nueva lógica de negocio
    if not partido.puede_apostar:
        message = f"Ya no puedes apostar en este partido. Estado: {partido.estado_actual}"
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': False,
                'message': message
            })
        # Solo usar toast, no Django messages
        return JsonResponse({
            'success': False,
            'message': message,
            'redirect': True,
            'redirect_url': reverse('quinielas:partidos')
        })
    
    # Obtener SOLO las quinielas en las que participa el usuario (NO como creador)
    # Los creadores/admins no pueden apostar en sus propias quinielas
    quinielas_usuario = Quiniela.objects.filter(
        participantes__usuario=request.user,
        activa=True,
        fecha_limite__gt=timezone.now()
    ).distinct()
    
    # Verificar casos específicos para dar retroalimentación clara
    if not quinielas_usuario.exists():
        # Verificar si es creador de alguna quiniela
        es_creador = Quiniela.objects.filter(
            creador=request.user,
            activa=True,
            fecha_limite__gt=timezone.now()
        ).exists()
        
        # Verificar si está en quinielas como participante pero no activas o vencidas
        tiene_quinielas_inactivas = Quiniela.objects.filter(
            participantes__usuario=request.user
        ).exists()
        
        # Determinar mensaje específico
        if es_creador and not tiene_quinielas_inactivas:
            message = "No puedes apostar porque eres el creador/administrador de las quinielas. Los creadores no pueden participar en sus propias quinielas."
        elif es_creador and tiene_quinielas_inactivas:
            message = "No puedes apostar: eres creador de algunas quinielas y tus quinielas como participante no están activas o han vencido."
        elif tiene_quinielas_inactivas:
            message = "No puedes apostar: tus quinielas han vencido o no están activas. Únete a una quiniela activa para poder apostar."
        else:
            message = "No puedes apostar: no participas en ninguna quiniela activa. Únete a una quiniela para comenzar a apostar."
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': False,
                'message': message
            })
        # Solo usar toast, no Django messages
        return JsonResponse({
            'success': False,
            'message': message,
            'redirect': True,
            'redirect_url': reverse('quinielas:partidos')
        })
    
    if request.method == 'POST':
        form = ApuestaForm(request.POST)
        quiniela_id = request.POST.get('quiniela')
        
        if form.is_valid() and quiniela_id:
            try:
                quiniela = quinielas_usuario.get(pk=quiniela_id)
                participante = quiniela.participantes.get(usuario=request.user)
                
                # Verificar o crear apuesta
                apuesta, created = Apuesta.objects.get_or_create(
                    participante=participante,
                    partido=partido,
                    defaults={
                        'goles_local_apostados': form.cleaned_data['goles_local'],
                        'goles_visitante_apostados': form.cleaned_data['goles_visitante']
                    }
                )
                
                if not created:
                    # Actualizar apuesta existente
                    apuesta.goles_local_apostados = form.cleaned_data['goles_local']
                    apuesta.goles_visitante_apostados = form.cleaned_data['goles_visitante']
                    apuesta.save()
                    success_message = "Apuesta actualizada exitosamente."
                else:
                    success_message = "Apuesta registrada exitosamente."
                    # Nueva apuesta - actualizar contador en el perfil
                    try:
                        if hasattr(request.user, 'profile') and request.user.profile:
                            request.user.profile.apuestas_realizadas += 1
                            request.user.profile.save()
                    except:
                        pass  # No es crítico si no se puede actualizar el contador
                
                # ===== OPTIMIZACIÓN: Invalidar cache del usuario =====
                invalidar_cache_usuario(request.user.id)
                
                # Respuesta AJAX
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    # Obtener total de apuestas del usuario
                    total_apuestas = Apuesta.objects.filter(
                        participante__usuario=request.user
                    ).count()
                    
                    # Obtener puntos totales del participante en esta quiniela
                    puntos_totales = participante.puntos_totales
                    
                    return JsonResponse({
                        'success': True,
                        'message': success_message,
                        'resultado_apostado': f"{apuesta.goles_local_apostados}-{apuesta.goles_visitante_apostados}",
                        'total_apuestas': total_apuestas,
                        'puntos_totales': puntos_totales,
                        'created': created,
                        'redirect_url': reverse('quinielas:partidos')  # Redirigir a partidos para seguir apostando
                    })
                
                messages.success(request, success_message)
                return redirect('quinielas:detalle', pk=quiniela.pk)
                
            except (Quiniela.DoesNotExist, Participante.DoesNotExist):
                error_message = "Error al procesar la apuesta."
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({
                        'success': False,
                        'message': error_message
                    })
                messages.error(request, error_message)
        else:
            # Form validation errors
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': False,
                    'message': 'Por favor corrige los errores en el formulario.',
                    'errors': form.errors
                })
    
    else:
        form = ApuestaForm()
    
    # Obtener apuesta existente del usuario para este partido (si hay alguna)
    apuesta_existente = Apuesta.objects.filter(
        partido=partido,
        participante__usuario=request.user
    ).select_related('participante__quiniela').first()
    
    context = {
        'partido': partido,
        'form': form,
        'quinielas': quinielas_usuario,
        'apuesta_existente': apuesta_existente,
    }
    
    return render(request, 'quinielas/apostar_partido_clean.html', context)


class MisApuestasView(LoginRequiredMixin, ListView):
    """Vista que muestra las apuestas del usuario"""
    model = Apuesta
    template_name = 'quinielas/mis_apuestas.html'
    context_object_name = 'apuestas'
    paginate_by = 20
    
    def get_queryset(self):
        return Apuesta.objects.filter(
            participante__usuario=self.request.user
        ).select_related(
            'partido__equipo_local', 
            'partido__equipo_visitante',
            'partido__jornada',
            'participante__quiniela',
            'participante__usuario'
        ).order_by('-fecha_modificacion')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # 🚀 OPTIMIZACIÓN CON API: Obtener datos enriquecidos para análisis de apuestas
        try:
            datos_dashboard = optimized_enricher.obtener_datos_dashboard(self.request.user)
            equipos_api = datos_dashboard.get('equipos_populares', [])
            tabla_posiciones = datos_dashboard.get('tabla_posiciones', [])
            
            # Enriquecer apuestas con datos de API para mejor análisis
            apuestas_enriquecidas = []
            for apuesta in context['apuestas']:
                apuesta_dict = {
                    'apuesta': apuesta,
                    'partido': apuesta.partido,
                    'equipo_local': apuesta.partido.equipo_local,
                    'equipo_visitante': apuesta.partido.equipo_visitante,
                    'api_data': {}
                }
                
                # Buscar datos adicionales de equipos
                for equipo_api in equipos_api:
                    if (equipo_api.get('nombre', '').lower() == apuesta.partido.equipo_local.nombre.lower() or
                        equipo_api.get('nombre', '').lower() == apuesta.partido.equipo_visitante.nombre.lower()):
                        apuesta_dict['api_data'] = {
                            'estadisticas_equipo': equipo_api.get('estadisticas', {}),
                            'forma_reciente': equipo_api.get('forma_reciente', [])
                        }
                        break
                
                apuestas_enriquecidas.append(apuesta_dict)
            
            context['apuestas_enriquecidas'] = apuestas_enriquecidas
            context['equipos_destacados'] = equipos_api[:10]
            context['tabla_posiciones_api'] = tabla_posiciones[:10]
            context['api_conectada'] = True
            context['api_metadata'] = datos_dashboard.get('metadata', {})
            
        except Exception as e:
            # Error enriqueciendo datos - continuar con funcionalidad básica
            context['api_conectada'] = False
        
        # 🚀 OPTIMIZACIÓN: Usar cache para estadísticas del usuario
        estadisticas_usuario = EstadisticasOptimizadas.get_estadisticas_usuario(self.request.user.id)
        
        # Obtener todas las apuestas del usuario para estadísticas detalladas
        apuestas_usuario = Apuesta.objects.filter(
            participante__usuario=self.request.user
        )
        
        # Calcular estadísticas
        total_apuestas = apuestas_usuario.count()
        aciertos_exactos = apuestas_usuario.filter(puntos=3).count()
        aciertos_ganador = apuestas_usuario.filter(puntos=1).count()
        puntos_totales = sum(apuesta.puntos for apuesta in apuestas_usuario)
        
        # Calcular porcentaje de efectividad
        apuestas_finalizadas = apuestas_usuario.filter(partido__finalizado=True)
        if apuestas_finalizadas.count() > 0:
            aciertos_totales = apuestas_finalizadas.filter(puntos__gt=0).count()
            porcentaje_efectividad = round((aciertos_totales / apuestas_finalizadas.count()) * 100, 1)
        else:
            porcentaje_efectividad = 0
        
        # Obtener quinielas del usuario para el filtro
        user_quinielas = Quiniela.objects.filter(
            Q(creador=self.request.user) | 
            Q(participantes__usuario=self.request.user)
        ).distinct()
        
        context.update({
            'total_apuestas': total_apuestas,
            'aciertos_exactos': aciertos_exactos,
            'aciertos_ganador': aciertos_ganador,
            'puntos_totales': puntos_totales,
            'porcentaje_efectividad': porcentaje_efectividad,
            'user_quinielas': user_quinielas,
            'estadisticas_optimizadas': estadisticas_usuario,
        })
        
        return context


@login_required
def ranking_quiniela(request, pk):
    """Vista del ranking detallado de una quiniela"""
    quiniela = get_object_or_404(Quiniela, pk=pk)
    
    # Verificar acceso
    if not (quiniela.creador == request.user or 
            quiniela.participantes.filter(usuario=request.user).exists()):
        messages.error(request, "No tienes acceso a esta quiniela.")
        return redirect('quinielas:home')
    
    participantes = quiniela.participantes.all()
    
    context = {
        'quiniela': quiniela,
        'participantes': participantes,
    }
    
    return render(request, 'quinielas/ranking.html', context)


@login_required
@login_required
def dashboard_unified(request):
    """
    Vista del dashboard unificado optimizada con APIs inteligentes
    FUNCIONA CON MOCK Y APIS REALES TRANSPARENTEMENTE
    """
    start_time = timezone.now()
    
    # 🚀 USAR SISTEMA OPTIMIZADO DE APIS
    optimized_enricher.set_user_context(request.user, request.session.session_key)
    
    try:
        # Obtener datos del dashboard con optimización automática
        datos_dashboard = optimized_enricher.obtener_datos_dashboard(request.user)
        
        # ===== OPTIMIZACIÓN: Usar cache para estadísticas del usuario =====
        estadisticas_usuario = EstadisticasOptimizadas.get_estadisticas_usuario(request.user.id)
        
        # ===== OPTIMIZACIÓN: Usar cache para ranking global =====
        ranking_global = EstadisticasOptimizadas.get_ranking_global()
        
        # Encontrar posición del usuario actual en el ranking
        ranking_posicion = 1
        for i, usuario_data in enumerate(ranking_global, 1):
            if usuario_data['usuario__id'] == request.user.id:
                ranking_posicion = i
                break
        
        # Convertir ranking a formato esperado por el template
        top_usuarios = []
        for data in ranking_global[:10]:
            nombre_completo = f"{data['usuario__first_name']} {data['usuario__last_name']}".strip()
            if not nombre_completo:
                nombre_completo = data['usuario__username']
            
            top_usuarios.append({
                'usuario': {
                    'username': data['usuario__username'],
                    'first_name': data['usuario__first_name'],
                    'last_name': data['usuario__last_name'],
                    'get_full_name': lambda: nombre_completo
                },
                'puntos': data['total_puntos'] or 0,
                'total_apuestas': data['total_apuestas'],
                'apuestas_acertadas': 0,  # Simplificado por rendimiento
                'precision': 0  # Simplificado por rendimiento
            })
        
        # ===== OPTIMIZACIÓN: Usar cache para próximos partidos =====
        partidos_data = PartidosOptimizados.get_partidos_con_apuestas_usuario(request.user.id)
        partidos_bd = partidos_data['partidos']
        apuestas_usuario_dict = partidos_data['apuestas_usuario']
        
        # 🚀 DATOS DE API OPTIMIZADOS (mock o reales transparentemente)
        proximos_partidos_api = datos_dashboard.get('partidos_proximos', [])
        equipos_api = datos_dashboard.get('equipos_populares', [])
        tabla_posiciones_api = datos_dashboard.get('tabla_posiciones', [])
        
        # Enriquecer partidos con info de apuestas
        proximos_partidos = []
        for i, partido_bd in enumerate(partidos_bd[:6]):
            mi_apuesta = apuestas_usuario_dict.get(partido_bd.id)
            mi_apuesta_dict = None
            if mi_apuesta:
                mi_apuesta_dict = {
                    'goles_local_apostados': mi_apuesta.goles_local_apostados,
                    'goles_visitante_apostados': mi_apuesta.goles_visitante_apostados,
                    'puntos': mi_apuesta.puntos,
                    'fecha_modificacion': mi_apuesta.fecha_modificacion
                }
            
            partido_enriquecido = {
                'id': partido_bd.id,
                'equipo_local': {'nombre': partido_bd.equipo_local.nombre},
                'equipo_visitante': {'nombre': partido_bd.equipo_visitante.nombre},
                'fecha_hora': partido_bd.fecha_hora,
                'jornada': partido_bd.jornada.numero if partido_bd.jornada else i+1,
                'estado': partido_bd.estado_actual,  # Usar la nueva propiedad
                'puede_apostar': partido_bd.puede_apostar,  # Nueva propiedad
                'minutos_para_inicio': partido_bd.minutos_para_inicio,  # Nueva propiedad
                'tiene_apuesta': mi_apuesta is not None,
                'mi_apuesta': mi_apuesta_dict,
                'estadisticas': {
                    'goles_local': getattr(partido_bd, 'goles_local', None),
                    'goles_visitante': getattr(partido_bd, 'goles_visitante', None),
                }
            }
            proximos_partidos.append(partido_enriquecido)
        
        # Si no hay suficientes partidos de BD, rellenar con datos de API
        while len(proximos_partidos) < 4 and len(proximos_partidos) < len(proximos_partidos_api):
            i = len(proximos_partidos)
            partido_api = proximos_partidos_api[i]
            partido_enriquecido = {
                'id': f"api_{i}",
                'equipo_local': {'nombre': partido_api.get('equipo_local', f'Equipo A{i+1}')},
                'equipo_visitante': {'nombre': partido_api.get('equipo_visitante', f'Equipo B{i+1}')},
                'fecha_hora': timezone.now() + timedelta(days=i+1),
                'jornada': i+1,
                'estado': 'PROGRAMADO',
                'tiene_apuesta': False,
                'mi_apuesta': None,
            }
            proximos_partidos.append(partido_enriquecido)
        
        # Calcular tiempo de procesamiento
        tiempo_procesamiento = (timezone.now() - start_time).total_seconds() * 1000
        
        # Estadísticas globales simplificadas para mejor rendimiento
        context = {
            'estadisticas_usuario': estadisticas_usuario,
            'top_usuarios': top_usuarios,
            'ranking_posicion': ranking_posicion,
            'proximos_partidos': proximos_partidos,
            'total_usuarios': len(ranking_global),
            'total_partidos': Partido.objects.count(),  # Cached separately if needed
            'promedio_puntos': sum(u['total_puntos'] or 0 for u in ranking_global[:20]) / min(len(ranking_global), 20) if ranking_global else 0,
            'now': timezone.now(),
            'user': request.user,
            'static_path': '/static/',
            
            # 🚀 DATOS ENRIQUECIDOS DE API (transparente mock/real)
            'equipos_populares': equipos_api[:5],
            'tabla_posiciones': tabla_posiciones_api[:10], 
            'api_metadata': datos_dashboard.get('metadata', {}),
            'tiempo_procesamiento_ms': round(tiempo_procesamiento, 1)
        }
        
        return render(request, 'quinielas/dashboard_unified.html', context)
        
    except Exception as e:
        # Fallback en caso de error
        messages.error(request, f'Error obteniendo datos del dashboard: {e}')
        
        # Datos mínimos de fallback
        estadisticas_usuario = EstadisticasOptimizadas.get_estadisticas_usuario(request.user.id)
        ranking_global = EstadisticasOptimizadas.get_ranking_global()[:10]
        
        context = {
            'estadisticas_usuario': estadisticas_usuario,
            'top_usuarios': [],
            'ranking_posicion': 1,
            'proximos_partidos': [],
            'total_usuarios': 0,
            'total_partidos': 0,
            'promedio_puntos': 0,
            'now': timezone.now(),
            'user': request.user,
            'static_path': '/static/',
            'error_fallback': True
        }
        
        return render(request, 'quinielas/dashboard_unified.html', context)


def registro_con_codigo(request):
    """Vista para registrarse directamente con código de quiniela"""
    if request.user.is_authenticated:
        # Si ya está autenticado, redirigir a unirse normalmente
        return redirect('quinielas:unirse')
    
    if request.method == 'POST':
        form = RegistroConCodigoForm(request.POST)
        if form.is_valid():
            codigo = form.cleaned_data['codigo_acceso'].upper()
            
            try:
                # Verificar que el código existe y la quiniela está activa
                quiniela = Quiniela.objects.get(codigo_acceso=codigo, activa=True)
                
                # Verificar que la quiniela acepta nuevos participantes
                if not quiniela.puede_apostar:
                    messages.error(request, "Esta quiniela ya no acepta nuevos participantes (fecha límite vencida).")
                    return render(request, 'quinielas/registro_con_codigo.html', {'form': form, 'quiniela': None})
                
                # Crear el usuario
                user = form.save()
                
                # Configurar perfil como PARTICIPANTE y guardar código usado
                try:
                    if hasattr(user, 'profile') and user.profile:
                        user.profile.tipo_usuario = 'PARTICIPANTE'
                        user.profile.codigo_invitacion_usado = codigo
                        user.profile.save()
                    else:
                        from accounts.models import UserProfile
                        profile, created = UserProfile.objects.get_or_create(
                            user=user,
                            defaults={
                                'tipo_usuario': 'PARTICIPANTE',
                                'codigo_invitacion_usado': codigo
                            }
                        )
                except Exception as e:
                    # Si falla la configuración del perfil, no es crítico
                    pass
                    UserProfile.objects.create(
                        user=user, 
                        tipo_usuario='PARTICIPANTE',
                        codigo_invitacion_usado=codigo
                    )
                
                # Crear participante automáticamente
                Participante.objects.create(
                    usuario=user,
                    quiniela=quiniela
                )
                
                # Iniciar sesión automáticamente
                login(request, user)
                
                messages.success(
                    request, 
                    f'¡Bienvenido {user.username}! Te has registrado y unido exitosamente a "{quiniela.nombre}".'
                )
                
                return redirect('quinielas:detalle', pk=quiniela.pk)
                
            except Quiniela.DoesNotExist:
                form.add_error('codigo_acceso', 'Código de acceso inválido o quiniela no activa.')
    
    else:
        # Pre-llenar el código si viene en la URL
        codigo_inicial = request.GET.get('codigo', '')
        form = RegistroConCodigoForm(initial={'codigo_acceso': codigo_inicial})
    
    return render(request, 'quinielas/registro_con_codigo.html', {'form': form})


# Fin del archivo de views - dashboard único implementado

@login_required
def solicitar_promocion(request):
    """Vista para que los participantes soliciten promoción a organizador"""
    if not hasattr(request.user, 'profile'):
        from accounts.models import UserProfile
        UserProfile.objects.create(user=request.user)
    
    profile = request.user.profile
    
    if profile.tipo_usuario == 'ORGANIZADOR':
        messages.info(request, 'Ya eres un Organizador.')
        return redirect('quinielas:home')
    
    if not profile.puede_solicitar_promocion:
        if profile.promocion_solicitada:
            messages.info(request, 'Tu solicitud de promoción ya está en proceso.')
        else:
            messages.warning(
                request, 
                f'Necesitas al menos 5 apuestas para solicitar promoción. '
                f'Tienes {profile.apuestas_realizadas} apuestas.'
            )
        return redirect('quinielas:home')
    
    if request.method == 'POST':
        profile.solicitar_promocion()
        messages.success(
            request, 
            'Tu solicitud de promoción a Organizador ha sido enviada. '
            'Te notificaremos cuando sea aprobada.'
        )
        return redirect('quinielas:home')
    
    return render(request, 'quinielas/solicitar_promocion.html', {
        'profile': profile,
        'apuestas_realizadas': profile.apuestas_realizadas
    })

@login_required  
def aprobar_promocion(request, user_id):
    """Vista para que administradores aprueben promociones (temporal)"""
    if not request.user.is_staff:
        messages.error(request, 'No tienes permisos para esta acción.')
        return redirect('quinielas:home')
    
    try:
        from django.contrib.auth.models import User
        user = User.objects.get(id=user_id)
        if hasattr(user, 'profile'):
            user.profile.promover_a_organizador()
            messages.success(
                request, 
                f'{user.username} ha sido promovido a Organizador.'
            )
        else:
            messages.error(request, 'Usuario sin perfil.')
    except User.DoesNotExist:
        messages.error(request, 'Usuario no encontrado.')
    
    return redirect('quinielas:home')


# ============================================================================
# VISTAS CON URLs AMIGABLES (SLUG-BASED)
# ============================================================================

class DetalleQuinielaSlugView(LoginRequiredMixin, DetailView):
    """Vista de detalle de quiniela usando slug amigable"""
    model = Quiniela
    template_name = 'quinielas/detalle_quiniela.html'
    context_object_name = 'quiniela'
    
    def get_object(self, queryset=None):
        """Obtiene la quiniela usando el slug"""
        slug = self.kwargs.get('slug')
        
        # Extraer código de acceso del slug (últimos 6 caracteres después del último guión)
        if '-' in slug:
            codigo_acceso = slug.split('-')[-1].upper()
            return get_object_or_404(Quiniela, codigo_acceso=codigo_acceso)
        
        # Fallback: buscar por slug completo (no debería pasar)
        return get_object_or_404(Quiniela, codigo_acceso=slug.upper())
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        quiniela = self.get_object()
        
        # Usar la misma lógica de la vista original
        participantes = Participante.objects.filter(quiniela=quiniela).select_related('usuario')
        context['participantes'] = participantes
        context['es_participante'] = participantes.filter(usuario=self.request.user).exists()
        context['puede_apostar'] = quiniela.puede_apostar
        
        return context


@login_required
def ranking_quiniela_slug(request, slug):
    """Vista de ranking usando slug amigable"""
    # Extraer código de acceso del slug
    if '-' in slug:
        codigo_acceso = slug.split('-')[-1].upper()
        quiniela = get_object_or_404(Quiniela, codigo_acceso=codigo_acceso)
    else:
        quiniela = get_object_or_404(Quiniela, codigo_acceso=slug.upper())
    
    # Usar la misma lógica de la vista original
    return ranking_quiniela(request, quiniela.pk)


@login_required
def apostar_partido_slug(request, slug):
    """Vista de apuesta usando slug amigable"""
    # Extraer ID del partido del slug (últimos números después del último guión)
    if '-' in slug:
        partido_id = slug.split('-')[-1]
        try:
            partido_id = int(partido_id)
        except ValueError:
            # Si no es un número, buscar por equipos
            partido = get_object_or_404(Partido, pk=1)  # Fallback temporal
    else:
        partido_id = 1  # Fallback temporal
    
    # Usar la misma lógica de la vista original
    return apostar_partido(request, partido_id)


# Importar las vistas de gestión de participantes
from .views_gestion import (
    gestionar_participantes,
    marcar_pago_participante,
    cambiar_estado_participante,
    eliminar_participante,
    exportar_participantes,
    dashboard_creador
)
