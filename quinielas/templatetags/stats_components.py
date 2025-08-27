from django import template
from django.utils.safestring import mark_safe
from django.template.loader import render_to_string

register = template.Library()

@register.tag('stats_grid')
def do_stats_grid(parser, token):
    """
    Parse the stats_grid template tag
    Usage: {% stats_grid columns=4 size='normal' %}...{% endstats_grid %}
    """
    tokens = token.split_contents()
    tag_name = tokens[0]
    
    # Parse arguments
    kwargs = {}
    for token_part in tokens[1:]:
        if '=' in token_part:
            key, value = token_part.split('=', 1)
            # Remove quotes if present
            if value.startswith('"') and value.endswith('"'):
                value = value[1:-1]
            elif value.startswith("'") and value.endswith("'"):
                value = value[1:-1]
            kwargs[key] = value
    
    # Parse the contents between tags
    nodelist = parser.parse(('endstats_grid',))
    parser.delete_first_token()
    
    return StatsGridNode(nodelist, kwargs)

class StatsGridNode(template.Node):
    def __init__(self, nodelist, kwargs):
        self.nodelist = nodelist
        self.kwargs = kwargs
    
    def render(self, context):
        # Get parameters with defaults
        columns = self.kwargs.get('columns', 'auto')
        size = self.kwargs.get('size', 'normal')
        
        # Render the content inside the tag
        content = self.nodelist.render(context)
        
        # Generate CSS classes
        if columns == 'auto':
            grid_class = 'stats-grid-auto'
        else:
            grid_class = f'stats-grid-{columns}'
        
        # Wrap content in grid container
        html = f'''
        <div class="stats-grid {grid_class}">
            {content}
        </div>
        
        <style>
        .stats-grid {{
            display: grid;
            gap: 1rem;
            width: 100%;
        }}
        
        .stats-grid-auto {{
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
        }}
        
        .stats-grid-1 {{
            grid-template-columns: 1fr;
        }}
        
        .stats-grid-2 {{
            grid-template-columns: repeat(2, 1fr);
        }}
        
        .stats-grid-3 {{
            grid-template-columns: repeat(3, 1fr);
        }}
        
        .stats-grid-4 {{
            grid-template-columns: repeat(4, 1fr);
        }}
        
        @media (max-width: 768px) {{
            .stats-grid {{
                grid-template-columns: 1fr;
            }}
            
            .stats-grid-2,
            .stats-grid-3,
            .stats-grid-4 {{
                grid-template-columns: repeat(2, 1fr);
            }}
        }}
        
        @media (max-width: 480px) {{
            .stats-grid,
            .stats-grid-2,
            .stats-grid-3,
            .stats-grid-4 {{
                grid-template-columns: 1fr;
            }}
        }}
        </style>
        '''
        
        return mark_safe(html)

@register.inclusion_tag('components/stat_card.html')
def stat_card(title, value, icon=None, size='normal', variant='default', 
              icon_color='primary', value_color='primary', unit=None, 
              trend=None, trend_label=None, description=None, subtitle=None,
              action_url=None, action_text=None):
    """
    Renderiza una tarjeta de estadística unificada
    
    Args:
        title: Título de la estadística
        value: Valor principal a mostrar
        icon: Icono emoji o unicode
        size: 'compact', 'normal', 'large'
        variant: 'default', 'minimal', 'highlighted', 'warning', 'danger'
        icon_color: 'primary', 'success', 'warning', 'danger', 'info'
        value_color: 'primary', 'success', 'warning', 'danger', 'neutral'
        unit: Unidad de medida (ej: '%', 'pts', 'días')
        trend: Porcentaje de cambio (+/-)
        trend_label: Etiqueta del trend (ej: 'vs mes anterior')
        description: Descripción adicional
        subtitle: Subtítulo bajo el título
        action_url: URL de acción opcional
        action_text: Texto del botón de acción
    """
    return {
        'title': title,
        'value': value,
        'icon': icon,
        'size': size,
        'variant': variant,
        'icon_color': icon_color,
        'value_color': value_color,
        'unit': unit,
        'trend': trend,
        'trend_label': trend_label,
        'description': description,
        'subtitle': subtitle,
        'action_url': action_url,
        'action_text': action_text,
    }

@register.inclusion_tag('components/ranking_item.html')
def ranking_item(position, username, points, precision=None, streak=None,
                 style='default', size='normal', show_avatar=True, 
                 show_medals=True, show_stats=False, show_precision=True,
                 show_streak=False, show_progress=False, is_current_user=False,
                 highlight=False, avatar_color='primary', user_type=None,
                 total_bets=None, member_since=None, action_url=None, action_text=None):
    """
    Renderiza un item de ranking unificado
    
    Args:
        position: Posición en el ranking
        username: Nombre del usuario
        points: Puntos totales
        precision: Porcentaje de precisión
        streak: Racha actual
        style: 'default', 'simple', 'card', 'minimal'
        size: 'compact', 'normal', 'large'
        show_avatar: Mostrar avatar del usuario
        show_medals: Mostrar medallas para top 3
        show_stats: Mostrar estadísticas adicionales
        show_precision: Mostrar precisión
        show_streak: Mostrar racha
        show_progress: Mostrar barra de progreso
        is_current_user: Es el usuario actual
        highlight: Destacar el item
        avatar_color: Color del avatar
        user_type: Tipo de usuario (ORGANIZADOR/PARTICIPANTE)
        total_bets: Total de apuestas realizadas
        member_since: Fecha de registro
        action_url: URL de acción opcional
        action_text: Texto de acción
    """
    return {
        'position': position,
        'username': username,
        'points': points,
        'precision': precision,
        'streak': streak,
        'style': style,
        'size': size,
        'show_avatar': show_avatar,
        'show_medals': show_medals,
        'show_stats': show_stats,
        'show_precision': show_precision,
        'show_streak': show_streak,
        'show_progress': show_progress,
        'is_current_user': is_current_user,
        'highlight': highlight,
        'avatar_color': avatar_color,
        'user_type': user_type,
        'total_bets': total_bets,
        'member_since': member_since,
        'action_url': action_url,
        'action_text': action_text,
    }

@register.simple_tag
def format_precision(precision, show_color=True):
    """
    Formatea la precisión con colores apropiados
    """
    precision = float(precision or 0)
    
    if show_color:
        if precision >= 70:
            color_class = 'text-green-600'
        elif precision >= 50:
            color_class = 'text-yellow-600'
        else:
            color_class = 'text-red-600'
        
        return mark_safe(f'<span class="{color_class} font-semibold">{precision:.1f}%</span>')
    else:
        return f'{precision:.1f}%'

@register.simple_tag
def format_points(points, show_suffix=True):
    """
    Formatea los puntos con sufijo opcional
    """
    points = int(points or 0)
    suffix = ' pts' if show_suffix else ''
    
    if points >= 1000:
        return f'{points/1000:.1f}k{suffix}'
    else:
        return f'{points}{suffix}'

@register.simple_tag
def format_trend(current, previous=None, show_icon=True):
    """
    Calcula y formatea el trend de una métrica
    """
    if previous is None or previous == 0:
        return ''
    
    trend = ((current - previous) / previous) * 100
    icon = '▲' if trend >= 0 else '▼'
    color = 'text-green-600' if trend >= 0 else 'text-red-600'
    
    if show_icon:
        return mark_safe(f'<span class="{color}">{icon} {abs(trend):.1f}%</span>')
    else:
        return f'{trend:+.1f}%'

@register.simple_tag
def user_rank_badge(position):
    """
    Retorna el badge apropiado para la posición del usuario
    """
    if position == 1:
        return mark_safe('<span class="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-yellow-100 text-yellow-800">🥇 Campeón</span>')
    elif position <= 3:
        return mark_safe('<span class="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-orange-100 text-orange-800">🏆 Podio</span>')
    elif position <= 10:
        return mark_safe('<span class="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-800">⭐ Top 10</span>')
    else:
        return mark_safe('<span class="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-gray-100 text-gray-800">👤 Participante</span>')

@register.filter
def stats_color(value, metric_type='default'):
    """
    Retorna la clase de color apropiada para una estadística
    """
    value = float(value or 0)
    
    if metric_type == 'precision':
        if value >= 70:
            return 'success'
        elif value >= 50:
            return 'warning'
        else:
            return 'danger'
    elif metric_type == 'points':
        if value >= 100:
            return 'success'
        elif value >= 50:
            return 'primary'
        else:
            return 'neutral'
    elif metric_type == 'streak':
        if value >= 5:
            return 'success'
        elif value >= 3:
            return 'warning'
        elif value > 0:
            return 'primary'
        else:
            return 'neutral'
    
    return 'primary'

@register.inclusion_tag('components/stats_grid.html')
def stats_grid_list(stats_list, columns='auto', size='normal'):
    """
    Renderiza una grilla de estadísticas (versión inclusion_tag para listas)
    
    Args:
        stats_list: Lista de diccionarios con estadísticas
        columns: Número de columnas o 'auto'
        size: Tamaño de las tarjetas
    """
    return {
        'stats_list': stats_list,
        'columns': columns,
        'size': size,
    }
