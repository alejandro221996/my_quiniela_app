from django import template
from django.urls import reverse
from django.utils.safestring import mark_safe

register = template.Library()


@register.inclusion_tag('components/breadcrumbs.html', takes_context=True)
def breadcrumbs(context, current_title=None):
    """
    Genera breadcrumbs basados en la URL actual
    """
    request = context['request']
    path = request.path
    breadcrumb_list = []
    
    # Breadcrumb raíz siempre presente
    breadcrumb_list.append({
        'title': '🏠 Inicio',
        'url': reverse('quinielas:home'),
        'is_current': False
    })
    
    # Analizar la ruta actual para generar breadcrumbs
    if path.startswith('/dashboard'):
        breadcrumb_list.append({
            'title': '📊 Dashboard',
            'url': reverse('quinielas:dashboard'),
            'is_current': current_title is None
        })
        
    elif path.startswith('/partidos'):
        breadcrumb_list.append({
            'title': '⚽ Partidos',
            'url': reverse('quinielas:partidos'),
            'is_current': current_title is None
        })
        
    elif path.startswith('/mis-apuestas'):
        breadcrumb_list.append({
            'title': '🎯 Mis Apuestas',
            'url': reverse('quinielas:mis_apuestas'),
            'is_current': current_title is None
        })
        
    elif path.startswith('/crear'):
        breadcrumb_list.append({
            'title': '➕ Crear Quiniela',
            'url': reverse('quinielas:crear'),
            'is_current': current_title is None
        })
        
    elif '/quiniela/' in path:
        # Obtener quiniela desde el contexto si está disponible
        quiniela = context.get('quiniela')
        if quiniela:
            breadcrumb_list.append({
                'title': f'🏆 {quiniela.nombre}',
                'url': quiniela.get_absolute_url(),
                'is_current': False
            })
            
            if '/ranking/' in path:
                breadcrumb_list.append({
                    'title': '📈 Ranking',
                    'url': reverse('quinielas:ranking_slug', kwargs={'slug': quiniela.get_slug()}),
                    'is_current': current_title is None
                })
        
    elif '/partido/' in path and '/apostar/' in path:
        # Obtener partido desde el contexto si está disponible
        partido = context.get('partido')
        if partido:
            breadcrumb_list.append({
                'title': f'⚽ {partido.equipo_local} vs {partido.equipo_visitante}',
                'url': partido.get_absolute_url(),
                'is_current': current_title is None
            })
    
    # Agregar título actual si se especifica
    if current_title:
        breadcrumb_list.append({
            'title': current_title,
            'url': None,
            'is_current': True
        })
    
    # Marcar el último elemento como actual si no hay título específico
    if breadcrumb_list and not current_title:
        breadcrumb_list[-1]['is_current'] = True
    
    return {
        'breadcrumbs': breadcrumb_list,
        'request': request
    }


@register.simple_tag
def nav_active(request, url_name, css_class="active"):
    """
    Retorna la clase CSS si la URL actual coincide con el nombre dado
    """
    from django.urls import reverse, NoReverseMatch
    try:
        url = reverse(url_name)
        if request.path == url or request.path.startswith(url.rstrip('/')):
            return css_class
    except NoReverseMatch:
        pass
    return ""


@register.filter
def friendly_url(obj):
    """
    Convierte un objeto a su URL amigable si tiene el método get_absolute_url
    """
    if hasattr(obj, 'get_absolute_url'):
        return obj.get_absolute_url()
    return "#"


@register.simple_tag(takes_context=True)
def quick_nav(context):
    """
    Genera navegación rápida contextual
    """
    request = context['request']
    user = request.user
    nav_items = []
    
    if user.is_authenticated:
        nav_items.extend([
            {
                'title': '📊 Dashboard',
                'url': reverse('quinielas:dashboard'),
                'icon': '📊',
                'description': 'Vista general de tus estadísticas'
            },
            {
                'title': '⚽ Partidos',
                'url': reverse('quinielas:partidos'),
                'icon': '⚽',
                'description': 'Partidos disponibles para apostar'
            },
            {
                'title': '🎯 Mis Apuestas',
                'url': reverse('quinielas:mis_apuestas'),
                'icon': '🎯',
                'description': 'Historial de tus predicciones'
            },
        ])
        
        # Agregar navegación específica según permisos
        if hasattr(user, 'userprofile') and user.userprofile.tipo_usuario == 'ORGANIZADOR':
            nav_items.append({
                'title': '➕ Crear Quiniela',
                'url': reverse('quinielas:crear'),
                'icon': '➕',
                'description': 'Organizar nueva quiniela'
            })
    
    return nav_items
