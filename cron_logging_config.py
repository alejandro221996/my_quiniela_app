# 
# Configuración de Logging para Scheduled Jobs
# Agregar esta configuración al settings.py para logs detallados
#

import os

# Directorio de logs
LOGS_DIR = os.path.join(BASE_DIR, 'logs')
os.makedirs(LOGS_DIR, exist_ok=True)

# Configuración de logging para cron jobs
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '[{levelname}] {asctime} {name} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'simple': {
            'format': '[{levelname}] {asctime} {message}',
            'style': '{',
        },
        'cron': {
            'format': '{asctime} | {levelname} | {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'simple'
        },
        'file_cron': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': os.path.join(LOGS_DIR, 'cron_actualizar_resultados.log'),
            'maxBytes': 1024*1024*5,  # 5 MB
            'backupCount': 5,
            'formatter': 'cron',
        },
        'file_error': {
            'level': 'ERROR',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': os.path.join(LOGS_DIR, 'cron_errors.log'),
            'maxBytes': 1024*1024*5,  # 5 MB
            'backupCount': 3,
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'quinielas.management.commands.actualizar_resultados': {
            'handlers': ['file_cron', 'file_error'],
            'level': 'INFO',
            'propagate': False,
        },
        'django': {
            'handlers': ['console'],
            'level': 'INFO',
        },
    },
}

# Configuración específica para cron jobs
CRON_SETTINGS = {
    'API_TIMEOUT': 10,  # segundos
    'MAX_RETRIES': 3,
    'RETRY_DELAY': 5,   # segundos entre reintentos
    'DEFAULT_DAYS_BACK': 1,
    'API_ENDPOINTS': {
        'liga_mx': 'https://api-football-v1.p.rapidapi.com/v3/fixtures',
        'backup': 'http://localhost:8000/api/partidos/',  # API local de respaldo
    }
}
