#!/bin/bash
#
# CONFIGURACIÓN MÍNIMA DE CRONTAB - Solo lo esencial
#

echo "🎯 CONFIGURACIÓN MÍNIMA PARA CRONTAB"
echo "=================================="

PROJECT_DIR="/Users/alejandrojuarez/QuinielaDjango"
PYTHON_PATH="$PROJECT_DIR/.venv/bin/python"

echo "📋 OPCIÓN 1: Cron directo (sin script wrapper)"
echo "Agregar a crontab -e:"
echo ""
echo "# Verificar resultados cada 30 minutos"
echo "*/30 9-23 * * * cd $PROJECT_DIR && $PYTHON_PATH manage.py actualizar_resultados >> logs/cron.log 2>&1"
echo ""

echo "📋 OPCIÓN 2: Con script wrapper simple"
echo "Crear script básico:"

# Crear script wrapper mínimo
cat > simple_wrapper.sh << 'EOF'
#!/bin/bash
cd /Users/alejandrojuarez/QuinielaDjango
.venv/bin/python manage.py actualizar_resultados "$@"
EOF

chmod +x simple_wrapper.sh

echo "✅ Script simple creado: simple_wrapper.sh"
echo ""
echo "Agregar a crontab -e:"
echo "*/30 9-23 * * * $PROJECT_DIR/simple_wrapper.sh >> $PROJECT_DIR/logs/cron.log 2>&1"
echo ""

echo "🗑️  ARCHIVOS QUE PUEDES ELIMINAR:"
echo "   • setup_cron.sh"
echo "   • setup_scheduled_jobs.py"
echo "   • SCHEDULED_JOBS_README.md"
echo "   • demo_flujo_puntos.py"
echo "   • cron_logging_config.py"
echo ""

echo "📁 MANTENER SOLO:"
echo "   ✅ quinielas/management/commands/actualizar_resultados.py"
echo "   ✅ simple_wrapper.sh (este script básico)"
echo "   ✅ logs/ (directorio)"
