#!/usr/bin/env python3
"""
Script de instalación y configuración para Scheduled Jobs
Configura todo lo necesario para automatizar la actualización de resultados
"""

import os
import sys
import django
from pathlib import Path

# Configurar Django
PROJECT_DIR = Path(__file__).resolve().parent
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'quinielas_project.settings')
sys.path.append(str(PROJECT_DIR))
django.setup()

def configurar_scheduled_jobs():
    """
    Configura todo el sistema de scheduled jobs
    """
    print("🚀 CONFIGURADOR DE SCHEDULED JOBS PARA QUINIELAS")
    print("=" * 55)
    
    # 1. Verificar dependencias
    print("1️⃣  Verificando dependencias...")
    
    try:
        import requests
        print("   ✅ requests disponible")
    except ImportError:
        print("   ❌ requests no encontrado")
        print("   💡 Instala con: pip install requests")
        return False
    
    # 2. Crear directorios necesarios
    print("\n2️⃣  Creando directorios...")
    
    logs_dir = PROJECT_DIR / 'logs'
    logs_dir.mkdir(exist_ok=True)
    print(f"   ✅ Directorio de logs: {logs_dir}")
    
    cron_dir = PROJECT_DIR / 'cron_scripts'
    cron_dir.mkdir(exist_ok=True)
    print(f"   ✅ Directorio de scripts: {cron_dir}")
    
    # 3. Crear script wrapper para cron
    print("\n3️⃣  Creando script wrapper...")
    
    wrapper_script = cron_dir / 'actualizar_resultados.sh'
    
    wrapper_content = f"""#!/bin/bash
#
# Script wrapper para cron job de actualización de resultados
# Asegura que el entorno esté configurado correctamente
#

# Configuración de rutas
PROJECT_DIR="{PROJECT_DIR}"
PYTHON_PATH="{PROJECT_DIR}/.venv/bin/python"
MANAGE_PY="{PROJECT_DIR}/manage.py"
LOG_DIR="{PROJECT_DIR}/logs"

# Función de logging
log_message() {{
    echo "$(date '+%Y-%m-%d %H:%M:%S') | $1" >> "$LOG_DIR/cron_wrapper.log"
}}

# Verificar que existan los archivos necesarios
if [ ! -f "$PYTHON_PATH" ]; then
    log_message "ERROR: Python no encontrado en $PYTHON_PATH"
    exit 1
fi

if [ ! -f "$MANAGE_PY" ]; then
    log_message "ERROR: manage.py no encontrado en $MANAGE_PY"
    exit 1
fi

# Cambiar al directorio del proyecto
cd "$PROJECT_DIR" || {{
    log_message "ERROR: No se puede cambiar al directorio $PROJECT_DIR"
    exit 1
}}

# Ejecutar comando con parámetros
log_message "INFO: Iniciando actualización de resultados con parámetros: $*"

"$PYTHON_PATH" "$MANAGE_PY" actualizar_resultados "$@" 2>&1

# Capturar código de salida
EXIT_CODE=$?

if [ $EXIT_CODE -eq 0 ]; then
    log_message "INFO: Actualización completada exitosamente"
else
    log_message "ERROR: Actualización falló con código $EXIT_CODE"
fi

exit $EXIT_CODE
"""
    
    with open(wrapper_script, 'w') as f:
        f.write(wrapper_content)
    
    # Hacer ejecutable
    os.chmod(wrapper_script, 0o755)
    print(f"   ✅ Script wrapper creado: {wrapper_script}")
    
    # 4. Crear configuración de ejemplo para crontab
    print("\n4️⃣  Creando configuración de crontab...")
    
    crontab_config = cron_dir / 'crontab_example.txt'
    
    crontab_content = f"""# QUINIELAS AUTO-UPDATE - Configuración de ejemplo
# Copia estas líneas a tu crontab usando: crontab -e

# Verificar resultados cada 30 minutos durante horarios de juego (9 AM - 11 PM)
*/30 9-23 * * * {wrapper_script} --days-back=1 >> {logs_dir}/cron_resultados.log 2>&1

# Verificación cada 2 horas (más comprehensiva)
0 */2 * * * {wrapper_script} --days-back=2 --verbose >> {logs_dir}/cron_resultados_detalle.log 2>&1

# Verificación diaria completa a las 23:00
0 23 * * * {wrapper_script} --days-back=7 --verbose >> {logs_dir}/cron_resultados_diario.log 2>&1

# Limpiar logs antiguos cada domingo a las 02:00
0 2 * * 0 find {logs_dir} -name "cron_*.log" -mtime +7 -delete

# QUINIELAS AUTO-UPDATE - Fin
"""
    
    with open(crontab_config, 'w') as f:
        f.write(crontab_content)
    
    print(f"   ✅ Configuración de ejemplo: {crontab_config}")
    
    # 5. Probar comando
    print("\n5️⃣  Probando comando...")
    
    try:
        from django.core.management import call_command
        from io import StringIO
        
        # Capturar salida
        output = StringIO()
        call_command('actualizar_resultados', '--dry-run', stdout=output)
        
        print("   ✅ Comando ejecutado exitosamente")
        
        # Mostrar primeras líneas de la salida
        output_lines = output.getvalue().split('\n')[:3]
        for line in output_lines:
            if line.strip():
                print(f"      {line}")
                
    except Exception as e:
        print(f"   ❌ Error probando comando: {str(e)}")
        return False
    
    # 6. Instrucciones finales
    print("\n" + "=" * 55)
    print("🎉 CONFIGURACIÓN COMPLETADA!")
    print("\n📋 PRÓXIMOS PASOS:")
    print(f"1. Revisa la configuración en: {crontab_config}")
    print("2. Para instalar cron jobs automáticamente:")
    print(f"   ./setup_cron.sh install")
    print("3. Para verificar estado:")
    print(f"   ./setup_cron.sh status")
    print("4. Para probar manualmente:")
    print(f"   {wrapper_script} --dry-run --verbose")
    
    print("\n⚙️  CONFIGURACIONES AUTOMÁTICAS:")
    print("   🕐 Cada 30 min (9:00-23:00): Verificación rápida")
    print("   🕑 Cada 2 horas: Verificación detallada")  
    print("   🌙 23:00 diario: Verificación completa semanal")
    print("   🧹 Domingo 2:00: Limpieza de logs antiguos")
    
    print(f"\n📁 ARCHIVOS CREADOS:")
    print(f"   📝 {wrapper_script}")
    print(f"   📄 {crontab_config}")
    print(f"   📂 {logs_dir}/")
    
    print("\n💡 CONSEJOS:")
    print("   • Los logs se rotan automáticamente")
    print("   • Usa --dry-run para probar sin cambios")
    print("   • Revisa logs en caso de problemas")
    print("   • Personaliza horarios según tus necesidades")
    
    return True

if __name__ == '__main__':
    success = configurar_scheduled_jobs()
    sys.exit(0 if success else 1)
