/**
 * Toast Notification System
 * Maneja notificaciones emergentes modernas con animaciones
 */

class ToastManager {
    constructor() {
        this.container = this.createContainer();
        this.toasts = new Map();
        this.toastCount = 0;
    }

    createContainer() {
        const container = document.createElement('div');
        container.id = 'toast-container';
        container.className = 'fixed top-4 right-4 z-50 space-y-2 max-w-sm w-full';
        document.body.appendChild(container);
        return container;
    }

    show(message, type = 'info', duration = 5000, options = {}) {
        const toast = this.createToast(message, type, options);
        this.container.appendChild(toast);
        
        // Trigger animation
        requestAnimationFrame(() => {
            toast.classList.add('toast-enter');
        });

        // Auto-remove toast
        if (duration > 0) {
            setTimeout(() => {
                this.hide(toast);
            }, duration);
        }

        return toast;
    }

    createToast(message, type, options) {
        const toastId = `toast-${++this.toastCount}`;
        const toast = document.createElement('div');
        toast.id = toastId;
        toast.className = `toast toast-${type} transform translate-x-full transition-all duration-300 ease-in-out`;
        
        const config = this.getTypeConfig(type);
        
        toast.innerHTML = `
            <div class="flex items-start p-4 bg-white dark:bg-gray-800 border-l-4 ${config.borderColor} rounded-lg shadow-lg backdrop-blur-sm">
                <div class="flex-shrink-0">
                    <div class="w-6 h-6 ${config.bgColor} rounded-full flex items-center justify-center">
                        <svg class="w-4 h-4 ${config.iconColor}" fill="currentColor" viewBox="0 0 20 20">
                            ${config.icon}
                        </svg>
                    </div>
                </div>
                <div class="ml-3 flex-1">
                    ${options.title ? `<h4 class="text-sm font-medium text-gray-900 dark:text-white">${options.title}</h4>` : ''}
                    <p class="text-sm text-gray-700 dark:text-gray-300 ${options.title ? 'mt-1' : ''}">${message}</p>
                    ${options.action ? `
                        <div class="mt-2">
                            <button onclick="${options.action.callback}" class="text-sm ${config.actionColor} hover:underline">
                                ${options.action.text}
                            </button>
                        </div>
                    ` : ''}
                </div>
                <div class="ml-4 flex-shrink-0">
                    <button onclick="toastManager.hide(document.getElementById('${toastId}'))" 
                            class="inline-flex text-gray-400 hover:text-gray-600 dark:hover:text-gray-200 transition-colors">
                        <svg class="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                            <path fill-rule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clip-rule="evenodd"></path>
                        </svg>
                    </button>
                </div>
            </div>
        `;

        this.toasts.set(toastId, toast);
        return toast;
    }

    getTypeConfig(type) {
        const configs = {
            success: {
                borderColor: 'border-green-500',
                bgColor: 'bg-green-100',
                iconColor: 'text-green-600',
                actionColor: 'text-green-600',
                icon: '<path fill-rule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clip-rule="evenodd"></path>'
            },
            error: {
                borderColor: 'border-red-500',
                bgColor: 'bg-red-100',
                iconColor: 'text-red-600',
                actionColor: 'text-red-600',
                icon: '<path fill-rule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clip-rule="evenodd"></path>'
            },
            warning: {
                borderColor: 'border-yellow-500',
                bgColor: 'bg-yellow-100',
                iconColor: 'text-yellow-600',
                actionColor: 'text-yellow-600',
                icon: '<path fill-rule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clip-rule="evenodd"></path>'
            },
            info: {
                borderColor: 'border-blue-500',
                bgColor: 'bg-blue-100',
                iconColor: 'text-blue-600',
                actionColor: 'text-blue-600',
                icon: '<path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clip-rule="evenodd"></path>'
            }
        };
        return configs[type] || configs.info;
    }

    hide(toast) {
        if (!toast) return;
        
        toast.classList.remove('toast-enter');
        toast.classList.add('toast-exit');
        
        setTimeout(() => {
            if (toast.parentNode) {
                toast.parentNode.removeChild(toast);
                this.toasts.delete(toast.id);
            }
        }, 300);
    }

    // Helper methods for common toast types
    success(message, options = {}) {
        return this.show(message, 'success', 5000, options);
    }

    error(message, options = {}) {
        return this.show(message, 'error', 7000, options);
    }

    warning(message, options = {}) {
        return this.show(message, 'warning', 6000, options);
    }

    info(message, options = {}) {
        return this.show(message, 'info', 5000, options);
    }

    // Show Django messages as toasts
    showDjangoMessages() {
        const messageElements = document.querySelectorAll('.django-message');
        messageElements.forEach(element => {
            const message = element.textContent.trim();
            const level = element.dataset.level || 'info';
            
            // Map Django message levels to toast types
            const typeMap = {
                'error': 'error',
                'warning': 'warning', 
                'success': 'success',
                'info': 'info',
                'debug': 'info'
            };
            
            this.show(message, typeMap[level] || 'info');
            element.style.display = 'none'; // Hide original Django message
        });
    }
}

// Global toast manager instance
const toastManager = new ToastManager();

// Auto-show Django messages when page loads
document.addEventListener('DOMContentLoaded', function() {
    toastManager.showDjangoMessages();
});

// CSS Styles for animations
const toastStyles = `
<style>
.toast-enter {
    transform: translateX(0) !important;
}

.toast-exit {
    transform: translateX(100%) !important;
    opacity: 0 !important;
}

.toast {
    transition: all 0.3s ease-in-out;
}

@keyframes toast-slide-in {
    from {
        transform: translateX(100%);
        opacity: 0;
    }
    to {
        transform: translateX(0);
        opacity: 1;
    }
}

@keyframes toast-slide-out {
    from {
        transform: translateX(0);
        opacity: 1;
    }
    to {
        transform: translateX(100%);
        opacity: 0;
    }
}

/* Dark mode styles */
@media (prefers-color-scheme: dark) {
    .toast {
        background-color: #1f2937;
        border-color: #374151;
        color: #f9fafb;
    }
}

/* Mobile responsive */
@media (max-width: 640px) {
    #toast-container {
        left: 1rem;
        right: 1rem;
        max-width: none;
    }
}
</style>
`;

// Inject styles
document.head.insertAdjacentHTML('beforeend', toastStyles);

// Export for use in other scripts
window.toastManager = toastManager;
