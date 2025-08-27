/**
 * AJAX Form Handler for Betting System
 * Handles form submissions without page reload with loading states
 */

class AjaxFormHandler {
    constructor() {
        this.init();
    }

    init() {
        document.addEventListener('DOMContentLoaded', () => {
            this.setupFormHandlers();
            this.setupCSRFToken();
        });
    }

    setupCSRFToken() {
        // Get CSRF token from cookies or meta tag
        this.csrfToken = this.getCookie('csrftoken') || 
                        document.querySelector('[name=csrfmiddlewaretoken]')?.value ||
                        document.querySelector('meta[name="csrf-token"]')?.getAttribute('content');
    }

    getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }

    setupFormHandlers() {
        // Handle betting forms
        this.handleForms('.ajax-bet-form', this.handleBetForm.bind(this));
        
        // Handle join quiniela forms  
        this.handleForms('.ajax-join-form', this.handleJoinForm.bind(this));
        
        // Handle create quiniela forms
        this.handleForms('.ajax-create-form', this.handleCreateForm.bind(this));
    }

    handleForms(selector, handler) {
        document.addEventListener('submit', (e) => {
            if (e.target.matches(selector)) {
                e.preventDefault();
                handler(e.target);
            }
        });
    }

    async handleBetForm(form) {
        const formData = new FormData(form);
        const submitBtn = form.querySelector('button[type="submit"]');
        const partidoId = form.dataset.partidoId;
        
        // Add loading state
        this.setLoadingState(submitBtn, true, 'Guardando...');
        
        try {
            const response = await fetch(form.action, {
                method: 'POST',
                body: formData,
                headers: {
                    'X-CSRFToken': this.csrfToken,
                    'X-Requested-With': 'XMLHttpRequest'
                }
            });

            const data = await response.json();

            if (data.success) {
                toastManager.success(data.message || 'Apuesta guardada exitosamente', {
                    title: 'Éxito',
                    duration: 2500 // Duración un poco más larga para que el usuario vea el mensaje
                });
                
                // Update UI elements
                this.updateBetUI(form, data);
                
                // Update points if provided
                if (data.puntos_totales !== undefined) {
                    this.updateUserPoints(data.puntos_totales);
                }
                
                // Redirigir después de mostrar el toast
                setTimeout(() => {
                    const redirectUrl = data.redirect_url || '/partidos/';
                    window.location.href = redirectUrl;
                }, 2000); // Dar tiempo para que el usuario vea el toast
                
            } else {
                toastManager.error(data.message || 'Error al guardar la apuesta', {
                    title: 'Error'
                });
                
                // Show field errors
                if (data.errors) {
                    this.showFieldErrors(form, data.errors);
                }
            }

        } catch (error) {
            console.error('Error submitting bet:', error);
            toastManager.error('Error de conexión. Intenta de nuevo.', {
                title: 'Error de Red'
            });
        } finally {
            this.setLoadingState(submitBtn, false);
        }
    }

    async handleJoinForm(form) {
        const formData = new FormData(form);
        const submitBtn = form.querySelector('button[type="submit"]');
        
        this.setLoadingState(submitBtn, true, 'Uniéndote...');
        
        try {
            const response = await fetch(form.action, {
                method: 'POST',
                body: formData,
                headers: {
                    'X-CSRFToken': this.csrfToken,
                    'X-Requested-With': 'XMLHttpRequest'
                }
            });

            const data = await response.json();

            if (data.success) {
                toastManager.success(data.message, {
                    title: 'Te has unido exitosamente',
                    action: {
                        text: 'Ver quiniela',
                        callback: `window.location.href = '${data.redirect_url}'`
                    }
                });
                
                // Redirect after delay
                setTimeout(() => {
                    window.location.href = data.redirect_url;
                }, 2000);
                
            } else {
                toastManager.error(data.message || 'Error al unirse a la quiniela');
                
                if (data.errors) {
                    this.showFieldErrors(form, data.errors);
                }
            }

        } catch (error) {
            console.error('Error joining quiniela:', error);
            toastManager.error('Error de conexión. Intenta de nuevo.');
        } finally {
            this.setLoadingState(submitBtn, false);
        }
    }

    async handleCreateForm(form) {
        const formData = new FormData(form);
        const submitBtn = form.querySelector('button[type="submit"]');
        
        this.setLoadingState(submitBtn, true, 'Creando...');
        
        try {
            const response = await fetch(form.action, {
                method: 'POST',
                body: formData,
                headers: {
                    'X-CSRFToken': this.csrfToken,
                    'X-Requested-With': 'XMLHttpRequest'
                }
            });

            const data = await response.json();

            if (data.success) {
                toastManager.success(data.message, {
                    title: 'Quiniela creada',
                    action: {
                        text: 'Ver quiniela',
                        callback: `window.location.href = '${data.redirect_url}'`
                    }
                });
                
                // Clear form
                form.reset();
                
                // Redirect after delay
                setTimeout(() => {
                    window.location.href = data.redirect_url;
                }, 2000);
                
            } else {
                toastManager.error(data.message || 'Error al crear la quiniela');
                
                if (data.errors) {
                    this.showFieldErrors(form, data.errors);
                }
            }

        } catch (error) {
            console.error('Error creating quiniela:', error);
            toastManager.error('Error de conexión. Intenta de nuevo.');
        } finally {
            this.setLoadingState(submitBtn, false);
        }
    }

    setLoadingState(button, isLoading, loadingText = 'Cargando...') {
        if (!button) return;
        
        if (isLoading) {
            button.disabled = true;
            button.dataset.originalText = button.textContent;
            button.innerHTML = `
                <svg class="animate-spin -ml-1 mr-3 h-4 w-4 text-white inline-block" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                    <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                    <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                ${loadingText}
            `;
            button.classList.add('opacity-75', 'cursor-not-allowed');
        } else {
            button.disabled = false;
            button.textContent = button.dataset.originalText || 'Enviar';
            button.classList.remove('opacity-75', 'cursor-not-allowed');
        }
    }

    updateBetUI(form, data) {
        // Update the bet display if it exists
        const betDisplay = form.closest('.partido-card')?.querySelector('.bet-display');
        if (betDisplay && data.resultado_apostado) {
            betDisplay.textContent = `Tu apuesta: ${data.resultado_apostado}`;
            betDisplay.classList.remove('hidden');
        }
        
        // Update bet count
        if (data.total_apuestas !== undefined) {
            const betCount = document.querySelector('.bet-count');
            if (betCount) {
                betCount.textContent = data.total_apuestas;
            }
        }
        
        // Add visual feedback
        form.classList.add('bet-success');
        setTimeout(() => {
            form.classList.remove('bet-success');
        }, 3000);
    }

    updateUserPoints(points) {
        const pointsDisplay = document.querySelector('.user-points');
        if (pointsDisplay) {
            const oldPoints = parseInt(pointsDisplay.textContent) || 0;
            this.animateNumber(pointsDisplay, oldPoints, points);
        }
    }

    animateNumber(element, from, to) {
        const duration = 1000; // 1 second
        const start = Date.now();
        const timer = setInterval(() => {
            const now = Date.now();
            const progress = Math.min((now - start) / duration, 1);
            const value = Math.floor(from + (to - from) * progress);
            element.textContent = value;
            
            if (progress === 1) {
                clearInterval(timer);
            }
        }, 16); // ~60fps
    }

    showFieldErrors(form, errors) {
        // Clear previous errors
        form.querySelectorAll('.field-error').forEach(error => error.remove());
        
        // Show new errors
        Object.keys(errors).forEach(fieldName => {
            const field = form.querySelector(`[name="${fieldName}"]`);
            if (field) {
                const errorDiv = document.createElement('div');
                errorDiv.className = 'field-error text-red-600 text-sm mt-1';
                errorDiv.textContent = errors[fieldName][0]; // Show first error
                field.parentNode.appendChild(errorDiv);
                
                // Add error styling to field
                field.classList.add('border-red-500');
                
                // Remove error styling on input
                field.addEventListener('input', () => {
                    field.classList.remove('border-red-500');
                    errorDiv.remove();
                }, { once: true });
            }
        });
    }
}

// Additional CSS for loading and success states
const ajaxStyles = `
<style>
.bet-success {
    animation: successPulse 3s ease-in-out;
    border-color: #10b981 !important;
}

@keyframes successPulse {
    0%, 100% { 
        border-color: #d1d5db; 
        background-color: transparent; 
    }
    50% { 
        border-color: #10b981; 
        background-color: #ecfdf5; 
    }
}

.loading-overlay {
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: rgba(255, 255, 255, 0.8);
    display: flex;
    align-items: center;
    justify-content: center;
    border-radius: inherit;
}

.field-error {
    animation: errorSlideIn 0.3s ease-out;
}

@keyframes errorSlideIn {
    from {
        opacity: 0;
        transform: translateY(-10px);
    }
    to {
        opacity: 1;
        transform: translateY(0);
    }
}

/* Improved button loading state */
button:disabled {
    pointer-events: none;
}

/* Success state for forms */
.form-success {
    background: linear-gradient(135deg, #ecfdf5, #f0fdf4);
    border: 2px solid #10b981;
}
</style>
`;

// Inject styles
document.head.insertAdjacentHTML('beforeend', ajaxStyles);

// Initialize AJAX handler
const ajaxFormHandler = new AjaxFormHandler();

// Export for global use
window.ajaxFormHandler = ajaxFormHandler;
