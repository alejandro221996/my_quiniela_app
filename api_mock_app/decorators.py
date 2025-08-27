from functools import wraps
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.conf import settings


def api_login_required(view_func):
    """
    Decorador personalizado para APIs que requieren autenticación.
    Retorna JSON en lugar de redireccionar al login.
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse({
                'error': 'Autenticación requerida',
                'detail': 'Debes estar autenticado para acceder a esta API',
                'login_url': settings.LOGIN_URL
            }, status=401)
        
        return view_func(request, *args, **kwargs)
    
    return wrapper


def api_permission_required(permission):
    """
    Decorador para APIs que requieren permisos específicos.
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return JsonResponse({
                    'error': 'Autenticación requerida',
                    'detail': 'Debes estar autenticado para acceder a esta API'
                }, status=401)
            
            if not request.user.has_perm(permission):
                return JsonResponse({
                    'error': 'Permisos insuficientes',
                    'detail': f'Necesitas el permiso "{permission}" para acceder a esta API'
                }, status=403)
            
            return view_func(request, *args, **kwargs)
        
        return wrapper
    return decorator


def api_rate_limit(max_requests=100, period=3600):
    """
    Decorador básico de rate limiting para APIs.
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            # Implementación básica usando cache (opcional)
            # Por ahora solo pasamos la request
            return view_func(request, *args, **kwargs)
        
        return wrapper
    return decorator
