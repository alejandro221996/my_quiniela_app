/**
 * Debug Script para Dashboard
 * Detecta y reporta problemas con botones y funcionalidades
 */

document.addEventListener('DOMContentLoaded', function() {
    console.log('🔍 Iniciando debug del dashboard...');
    
    // 1. Verificar que los scripts se cargaron
    const requiredScripts = ['toastManager', 'ajaxFormHandler', 'buttonLoader'];
    requiredScripts.forEach(script => {
        if (window[script]) {
            console.log(`✅ ${script} cargado correctamente`);
        } else {
            console.warn(`⚠️ ${script} no está disponible`);
        }
    });
    
    // 2. Verificar botones de apostar
    const botonesApostar = document.querySelectorAll('.btn-action[data-partido-id]');
    console.log(`🎯 Botones de apostar encontrados: ${botonesApostar.length}`);
    
    botonesApostar.forEach((btn, index) => {
        const partidoId = btn.getAttribute('data-partido-id');
        const href = btn.getAttribute('href');
        
        console.log(`  Botón ${index + 1}:`);
        console.log(`    - Partido ID: ${partidoId}`);
        console.log(`    - Href: ${href}`);
        console.log(`    - Clases: ${btn.className}`);
        
        // Agregar click listener de debug
        btn.addEventListener('click', function(e) {
            console.log(`🎯 Click en botón apostar partido ${partidoId}`);
            console.log(`   URL: ${href}`);
            
            // Verificar si es un enlace válido
            if (!href || href === '#' || href === '') {
                e.preventDefault();
                console.error('❌ URL inválida para el botón de apostar');
                
                // Mostrar toast de error si está disponible
                if (window.toastManager) {
                    toastManager.error('Error: No se puede acceder a la página de apuestas');
                } else {
                    alert('Error: No se puede acceder a la página de apuestas');
                }
                return false;
            }
            
            // Si todo está bien, permitir navegación
            console.log('✅ Navegando a página de apuestas...');
        });
    });
    
    // 3. Verificar partidos en el dashboard
    const partidosCards = document.querySelectorAll('.partido-card');
    console.log(`⚽ Partidos mostrados: ${partidosCards.length}`);
    
    // 4. Verificar estilos CSS
    const testElement = document.createElement('div');
    testElement.className = 'btn btn-action';
    testElement.style.display = 'none';
    document.body.appendChild(testElement);
    
    const computedStyle = window.getComputedStyle(testElement);
    const backgroundColor = computedStyle.backgroundColor;
    
    console.log(`🎨 Color de fondo de btn-action: ${backgroundColor}`);
    
    if (backgroundColor === 'rgba(0, 0, 0, 0)' || backgroundColor === 'transparent') {
        console.warn('⚠️ Los estilos CSS no se están aplicando correctamente');
    } else {
        console.log('✅ Estilos CSS cargados correctamente');
    }
    
    document.body.removeChild(testElement);
    
    // 5. Verificar estado del usuario
    const userInfo = {
        authenticated: document.body.getAttribute('data-user-authenticated') || 'unknown',
        username: document.body.getAttribute('data-username') || 'unknown'
    };
    
    console.log('👤 Estado del usuario:', userInfo);
    
    // 6. Report final
    console.log('🔍 Debug completado. Revisa los logs anteriores para identificar problemas.');
});

// Función helper para debug manual
window.debugDashboard = function() {
    console.clear();
    console.log('🔄 Ejecutando debug manual...');
    
    const botonesApostar = document.querySelectorAll('.btn-action');
    console.log('Botones encontrados:', botonesApostar);
    
    botonesApostar.forEach((btn, i) => {
        console.log(`Botón ${i}:`, {
            text: btn.textContent.trim(),
            href: btn.href,
            classes: btn.className,
            partidoId: btn.getAttribute('data-partido-id')
        });
    });
};

// Mostrar instrucciones en consola
console.log('💡 Para debug manual, ejecuta: debugDashboard()');
