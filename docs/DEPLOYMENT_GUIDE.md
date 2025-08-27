# Configuración para Producción - Django Quinielas

## 🚀 Guía de Deployment a Producción

### 1. **Configuración de Variables de Entorno**

Crear archivo `.env` en la raíz del proyecto:

```bash
# Seguridad
SECRET_KEY=your-super-secret-key-here-generate-new-one
DEBUG=False
ALLOWED_HOSTS=your-domain.com,www.your-domain.com,localhost

# Base de Datos PostgreSQL
DATABASE_URL=postgres://username:password@localhost:5432/quinielas_prod
# O configuración específica:
DB_NAME=quinielas_prod
DB_USER=postgres_user
DB_PASSWORD=secure_password_here
DB_HOST=localhost
DB_PORT=5432

# Cache Redis
REDIS_URL=redis://localhost:6379/0

# Email (opcional)
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
EMAIL_USE_TLS=True

# Archivos Estáticos (para AWS S3 o similar)
# AWS_ACCESS_KEY_ID=your-access-key
# AWS_SECRET_ACCESS_KEY=your-secret-key
# AWS_STORAGE_BUCKET_NAME=your-bucket-name
# AWS_S3_REGION_NAME=us-east-1
```

### 2. **Configuración de Settings para Producción**

Crear `quinielas_project/settings_prod.py`:

```python
from .settings import *
import os
import dj_database_url

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False

# Hosts permitidos
ALLOWED_HOSTS = os.environ.get('ALLOWED_HOSTS', '').split(',')

# Base de datos PostgreSQL
DATABASES = {
    'default': dj_database_url.parse(os.environ.get('DATABASE_URL', 'sqlite:///db.sqlite3'))
}

# Cache Redis para producción
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': os.environ.get('REDIS_URL', 'redis://127.0.0.1:6379/1'),
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
            'PARSER_CLASS': 'redis.connection.HiredisParser',
            'CONNECTION_POOL_KWARGS': {
                'max_connections': 50,
                'retry_on_timeout': True,
            },
        },
        'KEY_PREFIX': 'quinielas',
        'TIMEOUT': 300,
    }
}

# Archivos estáticos
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'mediafiles')

# Configuración de seguridad
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'
SECURE_HSTS_SECONDS = 31536000  # 1 año
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

# HTTPS Settings (si usas HTTPS)
# SECURE_SSL_REDIRECT = True
# SESSION_COOKIE_SECURE = True
# CSRF_COOKIE_SECURE = True

# Logging para producción
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': 'logs/django.log',
            'formatter': 'verbose',
        },
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },
    },
    'root': {
        'handlers': ['console', 'file'],
        'level': 'INFO',
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': False,
        },
        'performance': {
            'handlers': ['file'],
            'level': 'WARNING',
            'propagate': False,
        },
    },
}

# Email configuration
if os.environ.get('EMAIL_HOST'):
    EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
    EMAIL_HOST = os.environ.get('EMAIL_HOST')
    EMAIL_PORT = int(os.environ.get('EMAIL_PORT', 587))
    EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER')
    EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD')
    EMAIL_USE_TLS = os.environ.get('EMAIL_USE_TLS', 'True').lower() == 'true'
    DEFAULT_FROM_EMAIL = EMAIL_HOST_USER
```

### 3. **Opciones de Deployment**

#### **A. Heroku (Recomendado para inicio)**

**Archivo `Procfile`:**
```
web: gunicorn quinielas_project.wsgi:application --bind 0.0.0.0:$PORT
worker: python manage.py qcluster
```

**Archivo `runtime.txt`:**
```
python-3.11.5
```

**Comandos de deployment:**
```bash
# Instalar Heroku CLI
# Crear app
heroku create quinielas-app-name

# Configurar addons
heroku addons:create heroku-postgresql:hobby-dev
heroku addons:create heroku-redis:hobby-dev

# Configurar variables de entorno
heroku config:set DJANGO_SETTINGS_MODULE=quinielas_project.settings_prod
heroku config:set SECRET_KEY=$(python -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())')
heroku config:set DEBUG=False

# Deploy
git add .
git commit -m "Ready for production deployment"
git push heroku main

# Ejecutar migraciones
heroku run python manage.py migrate
heroku run python manage.py createsuperuser
heroku run python manage.py collectstatic --noinput
```

#### **B. DigitalOcean/VPS (Producción robusta)**

**1. Configurar servidor:**
```bash
# Actualizar sistema
sudo apt update && sudo apt upgrade -y

# Instalar dependencias
sudo apt install python3.11 python3.11-venv python3-pip nginx postgresql postgresql-contrib redis-server

# Configurar PostgreSQL
sudo -u postgres createuser --interactive quinielas_user
sudo -u postgres createdb quinielas_prod --owner quinielas_user
```

**2. Configurar aplicación:**
```bash
# Clonar repositorio
git clone <your-repo-url> /var/www/quinielas
cd /var/www/quinielas

# Configurar entorno virtual
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Configurar variables de entorno
cp .env.example .env
nano .env  # Editar con valores reales

# Ejecutar migraciones y recopilar estáticos
python manage.py migrate --settings=quinielas_project.settings_prod
python manage.py createsuperuser --settings=quinielas_project.settings_prod
python manage.py collectstatic --noinput --settings=quinielas_project.settings_prod
```

**3. Configurar Gunicorn:**

Archivo `/etc/systemd/system/quinielas.service`:
```ini
[Unit]
Description=Quinielas Django App
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/var/www/quinielas
Environment="PATH=/var/www/quinielas/.venv/bin"
ExecStart=/var/www/quinielas/.venv/bin/gunicorn --workers 3 --bind unix:/var/www/quinielas/quinielas.sock quinielas_project.wsgi:application
Environment=DJANGO_SETTINGS_MODULE=quinielas_project.settings_prod

[Install]
WantedBy=multi-user.target
```

**4. Configurar Nginx:**

Archivo `/etc/nginx/sites-available/quinielas`:
```nginx
server {
    listen 80;
    server_name your-domain.com www.your-domain.com;
    
    location = /favicon.ico { access_log off; log_not_found off; }
    
    location /static/ {
        root /var/www/quinielas;
    }
    
    location /media/ {
        root /var/www/quinielas;
    }
    
    location / {
        include proxy_params;
        proxy_pass http://unix:/var/www/quinielas/quinielas.sock;
    }
}
```

**5. Activar servicios:**
```bash
# Activar y iniciar servicios
sudo systemctl daemon-reload
sudo systemctl start quinielas
sudo systemctl enable quinielas

# Configurar Nginx
sudo ln -s /etc/nginx/sites-available/quinielas /etc/nginx/sites-enabled
sudo nginx -t
sudo systemctl restart nginx

# Configurar SSL con Let's Encrypt (opcional)
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d your-domain.com -d www.your-domain.com
```

#### **C. Railway/Render (Alternativa simple)**

**Railway:**
```bash
# Instalar Railway CLI
npm install -g @railway/cli

# Deploy
railway login
railway init
railway up
```

**Render:**
1. Conectar repositorio GitHub
2. Configurar como Web Service
3. Configurar variables de entorno en dashboard
4. Auto-deploy activado

### 4. **Checklist Pre-Deploy**

- [ ] **Seguridad**
  - [ ] SECRET_KEY único generado
  - [ ] DEBUG=False
  - [ ] ALLOWED_HOSTS configurado
  - [ ] Variables sensibles en .env

- [ ] **Base de Datos**
  - [ ] PostgreSQL configurado
  - [ ] Migraciones aplicadas
  - [ ] Datos de prueba cargados (opcional)

- [ ] **Cache**
  - [ ] Redis configurado
  - [ ] Cache keys optimizadas

- [ ] **Archivos Estáticos**
  - [ ] STATIC_ROOT configurado
  - [ ] collectstatic ejecutado
  - [ ] Media files manejados

- [ ] **Monitoreo**
  - [ ] Logging configurado
  - [ ] Error tracking (Sentry opcional)

- [ ] **Performance**
  - [ ] Sistema de cache activo
  - [ ] Queries optimizadas
  - [ ] Middleware de monitoreo (opcional)

### 5. **Comandos Post-Deploy**

```bash
# Verificar funcionamiento
python manage.py check --deploy --settings=quinielas_project.settings_prod

# Limpiar cache si es necesario
python manage.py clear_cache --type all

# Backup de base de datos
pg_dump quinielas_prod > backup_$(date +%Y%m%d).sql

# Monitorear logs
tail -f logs/django.log
```

### 6. **Mantenimiento Continuo**

**Actualizaciones:**
```bash
# Pull cambios
git pull origin main

# Actualizar dependencias
pip install -r requirements.txt

# Aplicar migraciones
python manage.py migrate --settings=quinielas_project.settings_prod

# Recopilar estáticos
python manage.py collectstatic --noinput --settings=quinielas_project.settings_prod

# Reiniciar servicio
sudo systemctl restart quinielas
```

**Backups automáticos (crontab):**
```bash
# Backup diario a las 2 AM
0 2 * * * pg_dump quinielas_prod > /var/backups/quiniela_$(date +\%Y\%m\%d).sql
```

---

## 🎯 Checklist Final

- [ ] README.md actualizado
- [ ] requirements.txt completo
- [ ] settings_prod.py configurado
- [ ] .env.example creado
- [ ] Archivos de deployment listos
- [ ] Tests pasando
- [ ] Cache funcionando
- [ ] Sistema listo para producción ✅

**¡Tu aplicación está lista para ser desplegada en producción!** 🚀
