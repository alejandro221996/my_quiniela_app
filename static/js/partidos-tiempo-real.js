/**
 * Sistema de estados en tiempo real para partidos
 * Actualiza automáticamente el estado de los partidos cada 30 segundos
 */

class PartidosTimeReal {
    constructor() {
        this.updateInterval = 30000; // 30 segundos
        this.intervalId = null;
        this.partidosActivos = new Set();
        this.init();
    }

    init() {
        console.log('🔴 Iniciando sistema de tiempo real...');
        this.findPartidosActivos();
        this.startUpdates();
        this.setupVisibilityChange();
    }

    findPartidosActivos() {
        // Buscar tarjetas de partidos en el DOM
        const partidoCards = document.querySelectorAll('[data-partido-id]');
        partidoCards.forEach(card => {
            const partidoId = card.getAttribute('data-partido-id');
            if (partidoId) {
                this.partidosActivos.add(partidoId);
            }
        });
        
        console.log(`🎯 Encontrados ${this.partidosActivos.size} partidos para monitorear`);
    }

    async updatePartidoEstado(partidoId) {
        try {
            const response = await fetch(`/api/mock/partido/${partidoId}/tiempo-real/`);
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }

            const data = await response.json();
            this.renderEstadoPartido(partidoId, data.estado_tiempo_real);
            
        } catch (error) {
            console.warn(`⚠️ Error actualizando partido ${partidoId}:`, error);
            // En caso de error, mostrar estado offline
            this.renderEstadoOffline(partidoId);
        }
    }

    renderEstadoPartido(partidoId, estado) {
        const card = document.querySelector(`[data-partido-id="${partidoId}"]`);
        if (!card) return;

        // Crear o actualizar el container de estado
        let estadoContainer = card.querySelector('.estado-tiempo-real');
        if (!estadoContainer) {
            estadoContainer = document.createElement('div');
            estadoContainer.className = 'estado-tiempo-real';
            
            // Insertar después del header de la tarjeta
            const header = card.querySelector('.partido-header, .bg-white');
            if (header) {
                header.insertAdjacentElement('afterend', estadoContainer);
            }
        }

        // Generar HTML del estado
        const estadoHTML = this.generarEstadoHTML(estado);
        estadoContainer.innerHTML = estadoHTML;

        // Agregar animación de actualización
        estadoContainer.classList.add('updated');
        setTimeout(() => estadoContainer.classList.remove('updated'), 1000);
    }

    generarEstadoHTML(estado) {
        const { estado: tipoEstado, minuto_actual, goles_local, goles_visitante, periodo } = estado;
        
        let badgeClass = 'bg-gray-500';
        let badgeText = 'PROGRAMADO';
        let minutoText = '';
        let marcadorText = '';

        // Configurar badge según el estado
        switch (tipoEstado) {
            case 'en_vivo':
                badgeClass = 'bg-red-500 animate-pulse';
                badgeText = '🔴 EN VIVO';
                minutoText = `Min ${minuto_actual}'`;
                break;
            case 'medio_tiempo':
                badgeClass = 'bg-orange-500';
                badgeText = '⏸️ DESCANSO';
                minutoText = 'HT';
                break;
            case 'finalizado':
                badgeClass = 'bg-green-500';
                badgeText = '✅ FINAL';
                minutoText = 'FT';
                break;
            case 'suspendido':
                badgeClass = 'bg-yellow-500';
                badgeText = '⚠️ SUSPENDIDO';
                minutoText = `Min ${estado.minuto_suspension}'`;
                break;
            case 'programado':
                badgeClass = 'bg-blue-500';
                badgeText = '📅 PROGRAMADO';
                minutoText = estado.descripcion || '';
                break;
            case 'proximo':
                badgeClass = 'bg-purple-500';
                badgeText = '⏰ PRÓXIMO';
                minutoText = estado.descripcion || '';
                break;
            case 'por_iniciar':
                badgeClass = 'bg-indigo-500 animate-pulse';
                badgeText = '🚀 INICIANDO';
                minutoText = estado.descripcion || '';
                break;
            default:
                badgeClass = 'bg-gray-500';
                badgeText = 'ESTADO DESCONOCIDO';
                break;
        }

        // Mostrar marcador si hay goles
        if (goles_local !== null && goles_visitante !== null) {
            marcadorText = `
                <div class="marcador-tiempo-real text-lg font-bold text-gray-800">
                    ${goles_local} - ${goles_visitante}
                </div>
            `;
        }

        // Estadísticas adicionales para partidos en vivo
        let estadisticasHTML = '';
        if (tipoEstado === 'en_vivo' && estado.estadisticas_live) {
            const stats = estado.estadisticas_live;
            estadisticasHTML = `
                <div class="estadisticas-live text-xs text-gray-600 mt-1">
                    <div class="flex justify-between">
                        <span>Posesión: ${stats.posesion_local}% - ${stats.posesion_visitante}%</span>
                        <span>Tiros: ${stats.tiros_local} - ${stats.tiros_visitante}</span>
                    </div>
                </div>
            `;
        }

        return `
            <div class="p-3 bg-gradient-to-r from-blue-50 to-green-50 border-l-4 border-blue-400">
                <div class="flex items-center justify-between">
                    <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium text-white ${badgeClass}">
                        ${badgeText}
                    </span>
                    <span class="text-sm font-medium text-gray-700">${minutoText}</span>
                </div>
                ${marcadorText}
                ${estadisticasHTML}
                <div class="text-xs text-gray-500 mt-1">
                    🕐 Actualizado: ${new Date().toLocaleTimeString()}
                </div>
            </div>
        `;
    }

    renderEstadoOffline(partidoId) {
        const card = document.querySelector(`[data-partido-id="${partidoId}"]`);
        if (!card) return;

        let estadoContainer = card.querySelector('.estado-tiempo-real');
        if (!estadoContainer) return;

        estadoContainer.innerHTML = `
            <div class="p-2 bg-gray-100 border-l-4 border-gray-400">
                <span class="inline-flex items-center px-2 py-1 rounded text-xs font-medium text-gray-600 bg-gray-200">
                    📡 Sin conexión
                </span>
            </div>
        `;
    }

    async updateAllPartidos() {
        console.log('🔄 Actualizando estados de partidos...');
        
        const updatePromises = Array.from(this.partidosActivos).map(partidoId => 
            this.updatePartidoEstado(partidoId)
        );

        try {
            await Promise.allSettled(updatePromises);
            console.log('✅ Actualización completada');
        } catch (error) {
            console.error('❌ Error en actualización masiva:', error);
        }
    }

    startUpdates() {
        // Actualización inicial
        this.updateAllPartidos();
        
        // Configurar intervalo
        this.intervalId = setInterval(() => {
            this.updateAllPartidos();
        }, this.updateInterval);
        
        console.log(`⏰ Actualizaciones cada ${this.updateInterval/1000} segundos`);
    }

    stopUpdates() {
        if (this.intervalId) {
            clearInterval(this.intervalId);
            this.intervalId = null;
            console.log('⏹️ Actualizaciones detenidas');
        }
    }

    setupVisibilityChange() {
        // Pausar actualizaciones cuando la pestaña no está activa
        document.addEventListener('visibilitychange', () => {
            if (document.hidden) {
                this.stopUpdates();
                console.log('⏸️ Pestaña oculta - pausando actualizaciones');
            } else {
                this.startUpdates();
                console.log('▶️ Pestaña activa - reanudando actualizaciones');
            }
        });
    }

    // Método para agregar nuevos partidos dinámicamente
    addPartido(partidoId) {
        this.partidosActivos.add(partidoId);
        this.updatePartidoEstado(partidoId);
    }

    // Método para remover partidos
    removePartido(partidoId) {
        this.partidosActivos.delete(partidoId);
    }
}

// CSS para las animaciones
const timeRealStyles = `
    <style>
        .estado-tiempo-real.updated {
            animation: updateFlash 1s ease-in-out;
        }
        
        @keyframes updateFlash {
            0% { background-color: #dbeafe; }
            50% { background-color: #bfdbfe; }
            100% { background-color: transparent; }
        }
        
        .marcador-tiempo-real {
            text-shadow: 1px 1px 2px rgba(0,0,0,0.1);
        }
        
        .estadisticas-live {
            background: rgba(255,255,255,0.5);
            border-radius: 4px;
            padding: 4px 8px;
        }
    </style>
`;

// Insertar estilos en el head
if (!document.querySelector('#tiempo-real-styles')) {
    const styleElement = document.createElement('div');
    styleElement.id = 'tiempo-real-styles';
    styleElement.innerHTML = timeRealStyles;
    document.head.appendChild(styleElement);
}

// Inicializar cuando el DOM esté listo
document.addEventListener('DOMContentLoaded', function() {
    // Esperar un poco para que otras librerías se carguen
    setTimeout(() => {
        window.partidosTimeReal = new PartidosTimeReal();
    }, 1000);
});

// Exportar para uso global
window.PartidosTimeReal = PartidosTimeReal;
