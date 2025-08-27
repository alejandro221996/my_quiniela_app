from django import template
from quinielas.models import Quiniela

register = template.Library()

@register.simple_tag
def get_user_created_quinielas(user):
    """
    Template tag para obtener las quinielas creadas por el usuario
    Uso: {% get_user_created_quinielas user as created_quinielas %}
    """
    if user.is_authenticated:
        return Quiniela.objects.filter(creador=user, activa=True).order_by('-fecha_creacion')[:5]
    return []

@register.filter
def get_item(dictionary, key):
    """
    Filtro personalizado para obtener un item de un diccionario en templates
    Uso: {{ diccionario|get_item:clave }}
    """
    if dictionary and key in dictionary:
        return dictionary[key]
    return None

@register.filter
def get_bet_info(apuestas_dict, partido_id):
    """
    Filtro para obtener información específica de una apuesta
    Uso: {{ apuestas_usuario|get_bet_info:partido.id }}
    """
    if apuestas_dict and partido_id in apuestas_dict:
        return apuestas_dict[partido_id]
    return {}

@register.filter
def tiempo_amigable(minutos):
    """
    Convierte minutos en un formato más amigable para el usuario
    Uso: {{ partido.minutos_para_inicio|tiempo_amigable }}
    
    Ejemplos:
    - 30 minutos -> "30 min"
    - 90 minutos -> "1h 30min"
    - 1440 minutos -> "1 día"
    - 2880 minutos -> "2 días"
    """
    if not minutos or minutos <= 0:
        return "¡Ya empezó!"
    
    # Menos de 1 hora
    if minutos < 60:
        return f"{minutos} min"
    
    # Menos de 1 día (24 horas)
    elif minutos < 1440:
        horas = minutos // 60
        mins_restantes = minutos % 60
        if mins_restantes == 0:
            return f"{horas}h"
        else:
            return f"{horas}h {mins_restantes}min"
    
    # 1 día o más
    else:
        dias = minutos // 1440
        horas_restantes = (minutos % 1440) // 60
        
        if dias == 1:
            if horas_restantes == 0:
                return "1 día"
            else:
                return f"1 día {horas_restantes}h"
        else:
            if horas_restantes == 0:
                return f"{dias} días"
            else:
                return f"{dias} días {horas_restantes}h"
