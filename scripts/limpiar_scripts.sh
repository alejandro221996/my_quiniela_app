#!/bin/bash
#
# Script para limpiar archivos no esenciales
#

echo "🧹 LIMPIEZA DE ARCHIVOS NO ESENCIALES"
echo "===================================="

echo "🗑️  Los siguientes archivos NO son necesarios para crontab:"
echo "   • setup_cron.sh"
echo "   • setup_scheduled_jobs.py"
echo "   • SCHEDULED_JOBS_README.md"
echo "   • demo_flujo_puntos.py"
echo "   • cron_logging_config.py"
echo "   • config_minima_cron.sh"
echo "   • cron_scripts/ (directorio completo)"
echo ""

read -p "¿Quieres eliminar estos archivos? (y/N): " respuesta

if [[ $respuesta =~ ^[Yy]$ ]]; then
    echo "🗑️  Eliminando archivos opcionales..."
    
    rm -f setup_cron.sh
    rm -f setup_scheduled_jobs.py
    rm -f SCHEDULED_JOBS_README.md
    rm -f demo_flujo_puntos.py
    rm -f cron_logging_config.py
    rm -f config_minima_cron.sh
    rm -rf cron_scripts/
    
    echo "✅ Archivos eliminados"
    echo ""
    echo "📁 ARCHIVOS RESTANTES (necesarios):"
    echo "   ✅ quinielas/management/commands/actualizar_resultados.py"
    echo "   ✅ simple_wrapper.sh"
    echo "   ✅ logs/ (directorio)"
    echo ""
    echo "🎯 Para configurar cron:"
    echo "   crontab -e"
    echo "   # Agregar: */30 9-23 * * * $(pwd)/simple_wrapper.sh >> $(pwd)/logs/cron.log 2>&1"
else
    echo "❌ Limpieza cancelada - archivos conservados"
fi
