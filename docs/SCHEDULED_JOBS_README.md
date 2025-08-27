# 🕐 Scheduled Jobs para Actualización Automática de Resultados

## 📋 Resumen

Sistema completo de **scheduled jobs** con **cron** para automatizar la verificación y actualización de resultados de partidos en el sistema de quinielas.

## 🚀 Características

- ✅ **Verificación automática** cada 30 minutos durante horarios de juego
- ✅ **Múltiples niveles** de verificación (rápida, detallada, completa)
- ✅ **Logging robusto** con rotación automática de archivos
- ✅ **Manejo de errores** y reintentos
- ✅ **Modo dry-run** para pruebas
- ✅ **Scripts wrapper** seguros para cron
- ✅ **Limpieza automática** de logs antiguos

## 📁 Estructura de Archivos

```
QuinielaDjango/
├── 🔧 setup_scheduled_jobs.py          # Configurador principal
├── 🔧 setup_cron.sh                    # Gestor de cron jobs
├── ⚙️  quinielas/management/commands/
│   └── actualizar_resultados.py        # Comando Django
├── 📂 cron_scripts/
│   ├── actualizar_resultados.sh        # Script wrapper
│   └── crontab_example.txt             # Configuración ejemplo
└── 📂 logs/
    ├── cron_resultados.log             # Log verificaciones frecuentes
    ├── cron_resultados_detalle.log     # Log verificaciones detalladas
    ├── cron_resultados_diario.log      # Log verificaciones diarias
    └── cron_wrapper.log                # Log del script wrapper
```

## ⚙️ Configuración de Horarios

| Frecuencia | Horario | Propósito | Comando |
|------------|---------|-----------|---------|
| **Cada 30 min** | 9:00-23:00 | Verificación rápida durante juegos | `--days-back=1` |
| **Cada 2 horas** | 24/7 | Verificación detallada | `--days-back=2 --verbose` |
| **Diario** | 23:00 | Verificación completa semanal | `--days-back=7 --verbose` |
| **Semanal** | Dom 2:00 | Limpieza de logs antiguos | `find ... -mtime +7 -delete` |

## 🛠️ Instalación y Configuración

### 1. Configuración Inicial
```bash
# Configurar todo automáticamente
python3 setup_scheduled_jobs.py
```

### 2. Gestión de Cron Jobs
```bash
# Mostrar ayuda
./setup_cron.sh help

# Probar comando
./setup_cron.sh test

# Instalar cron jobs
./setup_cron.sh install

# Ver estado
./setup_cron.sh status

# Desinstalar
./setup_cron.sh uninstall
```

### 3. Ejecución Manual
```bash
# Modo prueba (sin cambios)
python3 manage.py actualizar_resultados --dry-run --verbose

# Aplicar cambios reales
python3 manage.py actualizar_resultados --verbose

# Verificar últimos 3 días
python3 manage.py actualizar_resultados --days-back=3

# Usar script wrapper
./cron_scripts/actualizar_resultados.sh --dry-run
```

## 📊 Monitoreo y Logs

### Ubicación de Logs
```bash
# Logs principales
tail -f logs/cron_resultados.log              # Verificaciones frecuentes
tail -f logs/cron_resultados_detalle.log      # Verificaciones detalladas
tail -f logs/cron_resultados_diario.log       # Verificaciones diarias
tail -f logs/cron_wrapper.log                 # Script wrapper
```

### Comandos de Monitoreo
```bash
# Ver últimas ejecuciones
tail -20 logs/cron_resultados.log

# Buscar errores
grep -i error logs/*.log

# Ver estadísticas del día
grep "$(date +%Y-%m-%d)" logs/cron_resultados.log | grep "RESUMEN"

# Verificar cron jobs activos
crontab -l | grep QUINIELAS
```

## 🔧 Personalización

### Modificar Horarios
Edita `setup_cron.sh` o modifica directamente con `crontab -e`:

```bash
# Ejemplo: Verificar cada 15 minutos en lugar de 30
*/15 9-23 * * * /ruta/al/script --days-back=1

# Ejemplo: Solo durante días laborales
*/30 9-23 * * 1-5 /ruta/al/script --days-back=1
```

### Configurar API Real
Modifica `actualizar_resultados.py`:

```python
def obtener_resultado_api_real(self, partido):
    # Agregar tu API key y endpoint
    api_key = "TU_API_KEY_AQUI"
    # ... implementar conexión real
```

### Logging Personalizado
Modifica configuración en `quinielas_project/settings.py`:

```python
LOGGING = {
    # ... configuración personalizada
}
```

## 🚨 Solución de Problemas

### Problemas Comunes

1. **Cron no ejecuta**
```bash
# Verificar servicio cron
sudo systemctl status cron  # Linux
sudo launchctl list | grep cron  # macOS

# Verificar permisos
ls -la cron_scripts/actualizar_resultados.sh
```

2. **Errores de Python/Django**
```bash
# Verificar entorno virtual
which python3
source .venv/bin/activate

# Probar comando manualmente
python3 manage.py actualizar_resultados --dry-run
```

3. **Problemas de logs**
```bash
# Verificar permisos de escritura
ls -la logs/
mkdir -p logs/
chmod 755 logs/
```

### Debug Mode
```bash
# Activar modo verbose para debugging
python3 manage.py actualizar_resultados --verbose --days-back=1

# Ver todos los logs en tiempo real
tail -f logs/*.log
```

## 🎯 Flujo de Funcionamiento

1. **Cron ejecuta** script wrapper cada 30 minutos
2. **Script wrapper** configura entorno y ejecuta comando Django
3. **Comando Django** verifica partidos pendientes
4. **API mock/real** proporciona resultados actualizados
5. **Sistema calcula** puntos automáticamente para todas las apuestas
6. **Rankings se actualizan** en tiempo real
7. **Logs registran** toda la actividad

## 📈 Beneficios

- 🔄 **Automatización completa** sin intervención manual
- ⚡ **Actualizaciones en tiempo real** durante juegos
- 📊 **Logging detallado** para auditoría y debugging
- 🛡️ **Manejo robusto de errores** y recuperación
- 🎯 **Precisión** en cálculo de puntos automático
- 📱 **Escalabilidad** para múltiples ligas y competencias

## 🔮 Próximas Mejoras

- [ ] Integración con APIs deportivas reales (ESPN, API-Football)
- [ ] Notificaciones push cuando se actualizan resultados
- [ ] Dashboard de monitoreo de cron jobs
- [ ] Webhook endpoints para recibir resultados en tiempo real
- [ ] Machine Learning para predecir mejores horarios de verificación
