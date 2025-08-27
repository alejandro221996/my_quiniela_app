# 📄 Scripts de Utilidad

Este directorio contiene scripts para configuración y mantenimiento del proyecto.

## 📋 Archivos

- `config_minima_cron.sh` - Configuración mínima para crontab
- `setup_cron.sh` - Configurador completo de cron jobs  
- `setup_scheduled_jobs.py` - Configurador automático
- `limpiar_scripts.sh` - Limpieza de archivos no esenciales
- `simple_wrapper.sh` - Script wrapper básico para cron

## 🚀 Uso Recomendado

Para scheduled jobs, usar el comando Django integrado:

```bash
# Instalar cron jobs
python manage.py scheduled_jobs install

# Ver estado
python manage.py scheduled_jobs status

# Probar
python manage.py scheduled_jobs test
```

Los scripts en este directorio son para configuración manual o casos especiales.
