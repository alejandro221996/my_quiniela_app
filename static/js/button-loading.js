/**
 * Universal Button Loading States
 * Automatically handles loading states for all buttons with data-loading attribute
 */

class ButtonLoadingManager {
    constructor() {
        this.loadingButtons = new Map();
        this.init();
    }

    init() {
        document.addEventListener('DOMContentLoaded', () => {
            this.setupButtonHandlers();
            this.enhanceExistingButtons();
        });
    }

    setupButtonHandlers() {
        // Handle form submissions
        document.addEventListener('submit', (e) => {
            const form = e.target;
            const submitBtn = form.querySelector('button[type="submit"]');
            
            if (submitBtn && !form.classList.contains('ajax-form')) {
                // Only add loading for non-AJAX forms
                this.setButtonLoading(submitBtn, true);
            }
        });

        // Handle button clicks with data-loading attribute
        document.addEventListener('click', (e) => {
            const button = e.target.closest('button[data-loading]');
            if (button && !button.disabled) {
                const loadingText = button.dataset.loading;
                const duration = parseInt(button.dataset.loadingDuration) || 0;
                
                this.setButtonLoading(button, true, loadingText);
                
                if (duration > 0) {
                    setTimeout(() => {
                        this.setButtonLoading(button, false);
                    }, duration);
                }
            }
        });

        // Handle AJAX success/error to remove loading
        document.addEventListener('ajaxSuccess', (e) => {
            if (e.detail.button) {
                this.setButtonLoading(e.detail.button, false);
            }
        });

        document.addEventListener('ajaxError', (e) => {
            if (e.detail.button) {
                this.setButtonLoading(e.detail.button, false);
            }
        });
    }

    enhanceExistingButtons() {
        // Enhance buttons with common patterns
        this.enhanceButtonsByPattern();
        
        // Add loading capability to all submit buttons
        document.querySelectorAll('button[type="submit"]').forEach(button => {
            this.enhanceButton(button);
        });

        // Add loading to navigation buttons
        document.querySelectorAll('a[href*="crear"], a[href*="unirse"], a[href*="apostar"]').forEach(link => {
            this.enhanceNavigationLink(link);
        });
    }

    enhanceButtonsByPattern() {
        const buttonPatterns = [
            {
                selector: 'button:contains("Crear"), button:contains("crear")',
                loadingText: 'Creando...'
            },
            {
                selector: 'button:contains("Guardar"), button:contains("guardar")',
                loadingText: 'Guardando...'
            },
            {
                selector: 'button:contains("Enviar"), button:contains("enviar")',
                loadingText: 'Enviando...'
            },
            {
                selector: 'button:contains("Unirse"), button:contains("unirse")',
                loadingText: 'Uniéndote...'
            },
            {
                selector: 'button:contains("Apostar"), button:contains("apostar")',
                loadingText: 'Apostando...'
            },
            {
                selector: 'button:contains("Eliminar"), button:contains("eliminar")',
                loadingText: 'Eliminando...'
            },
            {
                selector: 'button:contains("Actualizar"), button:contains("actualizar")',
                loadingText: 'Actualizando...'
            }
        ];

        buttonPatterns.forEach(pattern => {
            document.querySelectorAll('button').forEach(button => {
                const text = button.textContent.toLowerCase();
                const keywords = pattern.selector.match(/:contains\("([^"]+)"\)/g);
                
                if (keywords && keywords.some(keyword => {
                    const word = keyword.match(/"([^"]+)"/)[1].toLowerCase();
                    return text.includes(word);
                })) {
                    button.dataset.loading = pattern.loadingText;
                    this.enhanceButton(button);
                }
            });
        });
    }

    enhanceButton(button) {
        if (button.classList.contains('enhanced-loading')) return;
        if (button.classList.contains('no-auto-loading')) return; // Skip auto-loading buttons
        
        button.classList.add('enhanced-loading');
        
        // Add default loading text if not set
        if (!button.dataset.loading) {
            button.dataset.loading = 'Cargando...';
        }

        // Add transition styles
        button.style.transition = 'all 0.2s ease-in-out';
        
        // Store original styles
        button.dataset.originalPadding = window.getComputedStyle(button).padding;
    }

    enhanceNavigationLink(link) {
        link.addEventListener('click', (e) => {
            if (link.target !== '_blank') {
                this.setLinkLoading(link, true);
            }
        });
    }

    setButtonLoading(button, isLoading, customText = null) {
        if (!button) return;

        const buttonId = this.getButtonId(button);
        
        if (isLoading) {
            // Store original state
            const originalState = {
                text: button.innerHTML,
                disabled: button.disabled,
                classes: button.className
            };
            this.loadingButtons.set(buttonId, originalState);

            // Set loading state
            button.disabled = true;
            const loadingText = customText || button.dataset.loading || 'Cargando...';
            
            button.innerHTML = `
                <div class="flex items-center justify-center">
                    <svg class="animate-spin -ml-1 mr-2 h-4 w-4" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                        <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                        <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                    </svg>
                    <span>${loadingText}</span>
                </div>
            `;
            
            button.classList.add('loading-state', 'opacity-75', 'cursor-not-allowed');
            
        } else {
            // Restore original state
            const originalState = this.loadingButtons.get(buttonId);
            if (originalState) {
                button.innerHTML = originalState.text;
                button.disabled = originalState.disabled;
                button.className = originalState.classes;
                this.loadingButtons.delete(buttonId);
            }
            
            button.classList.remove('loading-state', 'opacity-75', 'cursor-not-allowed');
        }
    }

    setLinkLoading(link, isLoading) {
        if (isLoading) {
            const originalText = link.textContent;
            link.dataset.originalText = originalText;
            
            link.innerHTML = `
                <div class="flex items-center">
                    <svg class="animate-spin -ml-1 mr-2 h-4 w-4" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                        <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                        <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                    </svg>
                    <span>Cargando...</span>
                </div>
            `;
            
            link.classList.add('loading-state', 'opacity-75', 'pointer-events-none');
        } else {
            link.textContent = link.dataset.originalText || 'Link';
            link.classList.remove('loading-state', 'opacity-75', 'pointer-events-none');
        }
    }

    getButtonId(button) {
        if (button.id) return button.id;
        
        // Generate unique ID based on button properties
        const form = button.closest('form');
        const formAction = form ? form.action : '';
        const buttonText = button.textContent.trim();
        const position = Array.from(document.querySelectorAll('button')).indexOf(button);
        
        // Safe encoding that handles UTF-8 characters
        const safeEncode = (str) => {
            try {
                // Remove non-ASCII characters and encode safely
                const ascii = str.replace(/[^\x00-\x7F]/g, "");
                return btoa(ascii).slice(0, 8);
            } catch (e) {
                // Fallback to simple hash if btoa fails
                return Math.abs(str.split('').reduce((a,b) => {
                    a = ((a << 5) - a) + b.charCodeAt(0);
                    return a & a;
                }, 0)).toString(16).slice(0, 8);
            }
        };
        
        return `btn_${safeEncode(formAction + buttonText + position)}`;
    }

    // Public methods for manual control
    startLoading(buttonSelector, text = 'Cargando...') {
        const button = typeof buttonSelector === 'string' 
            ? document.querySelector(buttonSelector)
            : buttonSelector;
            
        if (button) {
            this.setButtonLoading(button, true, text);
        }
    }

    stopLoading(buttonSelector) {
        const button = typeof buttonSelector === 'string' 
            ? document.querySelector(buttonSelector)
            : buttonSelector;
            
        if (button) {
            this.setButtonLoading(button, false);
        }
    }

    // Handle page navigation loading
    setupPageLoadingStates() {
        // Show loading on page navigation
        window.addEventListener('beforeunload', () => {
            document.querySelectorAll('a[href]:not([target="_blank"])').forEach(link => {
                if (!link.href.startsWith('javascript:') && !link.href.startsWith('#')) {
                    this.setLinkLoading(link, true);
                }
            });
        });
    }
}

// Enhanced button styles
const buttonLoadingStyles = `
<style>
.loading-state {
    position: relative;
    pointer-events: none;
}

.enhanced-loading {
    position: relative;
    overflow: hidden;
}

.enhanced-loading::before {
    content: '';
    position: absolute;
    top: 0;
    left: -100%;
    width: 100%;
    height: 100%;
    background: linear-gradient(90deg, transparent, rgba(255,255,255,0.2), transparent);
    transition: left 0.5s;
}

.enhanced-loading:hover::before {
    left: 100%;
}

/* Pulse effect for critical buttons */
.btn-critical.enhanced-loading {
    animation: criticalPulse 2s infinite;
}

@keyframes criticalPulse {
    0%, 100% { 
        box-shadow: 0 0 0 0 rgba(239, 68, 68, 0.4); 
    }
    50% { 
        box-shadow: 0 0 0 10px rgba(239, 68, 68, 0); 
    }
}

/* Success state after loading */
.btn-success-state {
    background-color: #10b981 !important;
    border-color: #10b981 !important;
    animation: successBounce 0.6s ease-out;
}

@keyframes successBounce {
    0% { transform: scale(1); }
    50% { transform: scale(1.05); }
    100% { transform: scale(1); }
}

/* Loading skeleton for button text */
.loading-skeleton {
    background: linear-gradient(90deg, #f0f0f0 25%, #e0e0e0 50%, #f0f0f0 75%);
    background-size: 200% 100%;
    animation: loading-skeleton 1.5s infinite;
}

@keyframes loading-skeleton {
    0% { background-position: 200% 0; }
    100% { background-position: -200% 0; }
}
</style>
`;

// Inject styles
document.head.insertAdjacentHTML('beforeend', buttonLoadingStyles);

// Initialize button loading manager
const buttonLoadingManager = new ButtonLoadingManager();

// Export for global use
window.buttonLoadingManager = buttonLoadingManager;
