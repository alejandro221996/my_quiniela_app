# Configuración para optimización de APIs externas con tokens limitados

# Settings para diferentes APIs deportivas
API_CONFIGURATIONS = {
    'football_data_org': {
        'daily_limit': 10,          # Plan gratuito
        'per_minute_limit': 6,      # 10 requests por minuto
        'base_url': 'https://api.football-data.org/v4/',
        'priority_endpoints': {
            'matches': 'high',       # Partidos en vivo
            'standings': 'medium',   # Tablas de posiciones
            'teams': 'low',         # Información de equipos
            'competitions': 'low'    # Información de competencias
        }
    },
    
    'sportradar': {
        'daily_limit': 1000,
        'per_minute_limit': 5,
        'base_url': 'https://api.sportradar.us/soccer/',
        'priority_endpoints': {
            'live_matches': 'critical',
            'match_timeline': 'high',
            'match_summary': 'medium',
            'season_standings': 'low'
        }
    },
    
    'api_sports': {
        'daily_limit': 100,         # Plan gratuito
        'per_minute_limit': 10,
        'base_url': 'https://v3.football.api-sports.io/',
        'priority_endpoints': {
            'fixtures': 'high',
            'live': 'critical',
            'standings': 'medium',
            'teams': 'low'
        }
    }
}

# Estrategias de cache por tipo de dato
CACHE_STRATEGIES = {
    # Datos críticos - actualizaciones frecuentes
    'live_scores': {
        'ttl': 30,              # 30 segundos
        'fallback_ttl': 300,    # 5 minutos si API falla
        'priority': 'critical',
        'update_conditions': ['match_in_progress']
    },
    
    # Datos importantes - actualizaciones moderadas
    'upcoming_matches': {
        'ttl': 900,             # 15 minutos
        'fallback_ttl': 3600,   # 1 hora si API falla
        'priority': 'high',
        'update_conditions': ['within_2_hours', 'lineup_changes']
    },
    
    # Datos regulares - actualizaciones ocasionales
    'match_results': {
        'ttl': 3600,            # 1 hora
        'fallback_ttl': 86400,  # 24 horas si API falla
        'priority': 'medium',
        'update_conditions': ['match_finished']
    },
    
    # Datos estáticos - actualizaciones raras
    'team_info': {
        'ttl': 86400,           # 24 horas
        'fallback_ttl': 604800, # 1 semana si API falla
        'priority': 'low',
        'update_conditions': ['transfer_window', 'season_start']
    }
}

# Horarios inteligentes para minimizar consumo
SMART_SCHEDULING = {
    'peak_hours': [17, 18, 19, 20, 21],    # 5PM-9PM (más partidos)
    'off_peak_hours': [2, 3, 4, 5, 6],    # 2AM-6AM (menos actividad)
    
    'weekend_multiplier': 1.5,             # Más requests en fin de semana
    'weekday_multiplier': 0.8,             # Menos requests entre semana
    
    # Distribución de requests por hora
    'hourly_distribution': {
        'critical': {0: 5, 6: 10, 12: 15, 18: 50, 22: 20},  # % del límite diario
        'high': {0: 2, 6: 5, 12: 20, 18: 60, 22: 13},
        'medium': {0: 1, 6: 2, 12: 30, 18: 50, 22: 17},
        'low': {0: 10, 6: 20, 12: 30, 18: 20, 22: 20}
    }
}

# Configuración de fallbacks
FALLBACK_CONFIG = {
    'enable_prediction': True,       # Usar datos predichos
    'enable_interpolation': True,    # Interpolar datos faltantes
    'enable_mock_fallback': True,    # Usar mock como último recurso
    
    'confidence_thresholds': {
        'primary': 0.95,     # API externa fresca
        'cached': 0.85,      # Datos cacheados recientes
        'predicted': 0.65,   # Datos predichos
        'interpolated': 0.50, # Datos interpolados
        'mock': 0.10         # Datos mock
    },
    
    'max_data_age': {
        'critical': 300,     # 5 minutos max para datos críticos
        'high': 1800,        # 30 minutos max para datos importantes
        'medium': 7200,      # 2 horas max para datos regulares
        'low': 86400         # 24 horas max para datos estáticos
    }
}

# Monitoreo y alertas
MONITORING_CONFIG = {
    'alert_thresholds': {
        'daily_limit_used': 0.80,      # Alerta al 80% del límite diario
        'hourly_limit_used': 0.70,     # Alerta al 70% del límite por hora
        'api_error_rate': 0.20,        # Alerta si >20% de requests fallan
        'fallback_usage': 0.50         # Alerta si >50% usa fallbacks
    },
    
    'metrics_to_track': [
        'requests_per_hour',
        'requests_per_day', 
        'api_response_time',
        'cache_hit_ratio',
        'fallback_usage_ratio',
        'data_freshness_score'
    ]
}

# Ejemplo de configuración específica para Django settings
"""
# En settings.py
EXTERNAL_APIS = {
    'FOOTBALL_DATA': {
        'API_KEY': env('FOOTBALL_DATA_API_KEY'),
        'DAILY_LIMIT': 10,
        'ENABLE_CACHE': True,
        'CACHE_TTL': {
            'live': 30,
            'fixtures': 900,
            'standings': 3600,
            'teams': 86400
        }
    }
}

CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': 'redis://127.0.0.1:6379/1',
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        }
    },
    'api_cache': {
        'BACKEND': 'django_redis.cache.RedisCache', 
        'LOCATION': 'redis://127.0.0.1:6379/2',
        'TIMEOUT': 3600,  # 1 hora por defecto
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        }
    }
}
"""
