#!/bin/bash
# 
# Script para configurar cron jobs para actualización automática de resultados
# 

# Configuración
PROJECT_DIR="/Users/alejandrojuarez/QuinielaDjango"
PYTHON_PATH="$PROJECT_DIR/.venv/bin/python"
MANAGE_PY="$PROJECT_DIR/manage.py"
LOG_DIR="$PROJECT_DIR/logs"

# Crear directorio de logs si no existe
mkdir -p "$LOG_DIR"

echo "🔧 CONFIGURADOR DE CRON JOBS PARA QUINIELAS"
echo "=========================================="

# Función para mostrar ayuda
show_help() {
    echo "Uso: $0 [OPCIÓN]"
    echo ""
    echo "Opciones:"
    echo "  install     Instala los cron jobs"
    echo "  uninstall   Desinstala los cron jobs"
    echo "  status      Muestra el estado actual"
    echo "  test        Ejecuta una prueba del comando"
    echo "  help        Muestra esta ayuda"
    echo ""
    echo "Cron jobs que se instalarán:"
    echo "  • Cada 30 minutos: Verificar resultados recientes"
    echo "  • Cada 2 horas: Verificar resultados del día"
    echo "  • Diario a las 23:00: Verificar resultados completos"
}

# Función para instalar cron jobs
install_crons() {
    echo "📥 Instalando cron jobs..."
    
    # Crear archivo temporal con nuevos cron jobs
    TEMP_CRON="/tmp/quinielas_cron"
    
    # Obtener cron jobs existentes (excluyendo los nuestros)
    crontab -l 2>/dev/null | grep -v "# QUINIELAS AUTO-UPDATE" > "$TEMP_CRON"
    
    # Agregar nuestros cron jobs
    cat >> "$TEMP_CRON" << EOF

# QUINIELAS AUTO-UPDATE - Inicio
# Verificar resultados cada 30 minutos durante horarios de juego
*/30 9-23 * * * cd $PROJECT_DIR && $PYTHON_PATH $MANAGE_PY actualizar_resultados --days-back=1 >> $LOG_DIR/cron_resultados.log 2>&1

# Verificar resultados cada 2 horas (más comprehensivo)
0 */2 * * * cd $PROJECT_DIR && $PYTHON_PATH $MANAGE_PY actualizar_resultados --days-back=2 --verbose >> $LOG_DIR/cron_resultados_detalle.log 2>&1

# Verificación diaria completa a las 23:00
0 23 * * * cd $PROJECT_DIR && $PYTHON_PATH $MANAGE_PY actualizar_resultados --days-back=7 --verbose >> $LOG_DIR/cron_resultados_diario.log 2>&1

# Limpiar logs antiguos cada domingo a las 02:00
0 2 * * 0 find $LOG_DIR -name "cron_*.log" -mtime +7 -delete

# QUINIELAS AUTO-UPDATE - Fin
EOF
    
    # Instalar el nuevo crontab
    crontab "$TEMP_CRON"
    rm "$TEMP_CRON"
    
    echo "✅ Cron jobs instalados exitosamente!"
    echo ""
    echo "📋 Horarios configurados:"
    echo "   🕐 Cada 30 min (9:00-23:00): Verificación rápida"
    echo "   🕑 Cada 2 horas: Verificación detallada"
    echo "   🌙 23:00 diario: Verificación completa"
    echo "   🧹 Domingo 2:00: Limpieza de logs"
    echo ""
    echo "📁 Logs en: $LOG_DIR/"
}

# Función para desinstalar cron jobs
uninstall_crons() {
    echo "🗑️  Desinstalando cron jobs..."
    
    # Crear archivo temporal sin nuestros cron jobs
    TEMP_CRON="/tmp/quinielas_cron_clean"
    
    # Filtrar cron jobs existentes excluyendo los nuestros
    crontab -l 2>/dev/null | sed '/# QUINIELAS AUTO-UPDATE - Inicio/,/# QUINIELAS AUTO-UPDATE - Fin/d' > "$TEMP_CRON"
    
    # Instalar el crontab limpio
    crontab "$TEMP_CRON"
    rm "$TEMP_CRON"
    
    echo "✅ Cron jobs desinstalados exitosamente!"
}

# Función para mostrar estado
show_status() {
    echo "📊 Estado actual de cron jobs:"
    echo ""
    
    if crontab -l 2>/dev/null | grep -q "QUINIELAS AUTO-UPDATE"; then
        echo "✅ Cron jobs instalados"
        echo ""
        echo "📋 Cron jobs activos:"
        crontab -l 2>/dev/null | sed -n '/# QUINIELAS AUTO-UPDATE - Inicio/,/# QUINIELAS AUTO-UPDATE - Fin/p'
        echo ""
        
        # Mostrar logs recientes si existen
        if [ -f "$LOG_DIR/cron_resultados.log" ]; then
            echo "📄 Últimas ejecuciones (últimas 5 líneas):"
            tail -5 "$LOG_DIR/cron_resultados.log" 2>/dev/null || echo "   No hay logs disponibles"
        fi
    else
        echo "❌ Cron jobs no instalados"
        echo "💡 Ejecuta: $0 install"
    fi
}

# Función para probar el comando
test_command() {
    echo "🧪 Probando comando de actualización..."
    echo ""
    
    if [ ! -f "$PYTHON_PATH" ]; then
        echo "❌ No se encontró Python en: $PYTHON_PATH"
        echo "💡 Verifica que el entorno virtual esté activado"
        exit 1
    fi
    
    if [ ! -f "$MANAGE_PY" ]; then
        echo "❌ No se encontró manage.py en: $MANAGE_PY"
        echo "💡 Verifica la ruta del proyecto"
        exit 1
    fi
    
    echo "🔄 Ejecutando prueba (dry-run)..."
    cd "$PROJECT_DIR"
    "$PYTHON_PATH" "$MANAGE_PY" actualizar_resultados --dry-run --verbose
    
    echo ""
    echo "✅ Prueba completada!"
}

# Función principal
main() {
    case "${1:-help}" in
        "install")
            install_crons
            ;;
        "uninstall")
            uninstall_crons
            ;;
        "status")
            show_status
            ;;
        "test")
            test_command
            ;;
        "help"|*)
            show_help
            ;;
    esac
}

# Ejecutar función principal
main "$@"
