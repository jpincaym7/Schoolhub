// notifications.js
class NotificationService {
    static DURATION = 5000; // Duración predeterminada para notificaciones (5 segundos)
    static queue = []; // Cola de notificaciones
    static isProcessing = false;

    static init() {
        // Crear el contenedor de notificaciones si no existe
        if (!document.getElementById('notification-container')) {
            const container = document.createElement('div');
            container.id = 'notification-container';
            container.className = 'fixed bottom-4 right-4 z-50 space-y-2';
            document.body.appendChild(container);
        }
    }

    static show(message, type = 'info') {
        // Añadir a la cola y procesar
        this.queue.push({ message, type });
        if (!this.isProcessing) {
            this.processQueue();
        }
    }

    static async processQueue() {
        if (this.queue.length === 0) {
            this.isProcessing = false;
            return;
        }

        this.isProcessing = true;
        const { message, type } = this.queue.shift();
        
        // Crear el elemento de notificación
        const notification = document.createElement('div');
        notification.className = `notification-toast max-w-sm w-full glass-effect rounded-lg shadow-lg p-4 mb-4 transform translate-x-full transition-transform duration-300`;
        
        // Aplicar estilos según el tipo
        const styles = this.getNotificationStyles(type);
        
        notification.innerHTML = `
            <div class="flex items-center">
                <div class="flex-shrink-0">
                    <i class="fas ${styles.icon} ${styles.iconColor}"></i>
                </div>
                <div class="ml-3 flex-grow">
                    <p class="text-sm font-medium ${styles.textColor}">${message}</p>
                </div>
                <div class="ml-4 flex-shrink-0 flex">
                    <button class="inline-flex text-gray-400 hover:text-gray-500 focus:outline-none">
                        <i class="fas fa-times"></i>
                    </button>
                </div>
            </div>
            <div class="progress-bar h-1 bg-gray-200 rounded-full mt-2">
                <div class="h-full ${styles.progressColor} rounded-full transition-all duration-300" style="width: 100%"></div>
            </div>
        `;

        // Añadir al contenedor
        const container = document.getElementById('notification-container');
        container.appendChild(notification);

        // Mostrar con animación
        setTimeout(() => {
            notification.classList.remove('translate-x-full');
            notification.classList.add('translate-x-0');
        }, 100);

        // Configurar el botón de cerrar
        const closeButton = notification.querySelector('button');
        closeButton.addEventListener('click', () => this.hideNotification(notification));

        // Auto ocultar después de DURATION
        const progressBar = notification.querySelector('.progress-bar > div');
        progressBar.style.transition = `width ${this.DURATION}ms linear`;
        progressBar.style.width = '0%';

        await this.wait(this.DURATION);
        if (notification.parentElement) {
            this.hideNotification(notification);
        }

        // Procesar siguiente notificación
        this.processQueue();
    }

    static hideNotification(notification) {
        notification.classList.remove('translate-x-0');
        notification.classList.add('translate-x-full');
        
        setTimeout(() => {
            if (notification.parentElement) {
                notification.parentElement.removeChild(notification);
            }
        }, 300);
    }

    static getNotificationStyles(type) {
        const styles = {
            success: {
                icon: 'fa-check-circle',
                iconColor: 'text-green-500',
                textColor: 'text-green-800',
                progressColor: 'bg-green-500'
            },
            error: {
                icon: 'fa-exclamation-circle',
                iconColor: 'text-red-500',
                textColor: 'text-red-800',
                progressColor: 'bg-red-500'
            },
            warning: {
                icon: 'fa-exclamation-triangle',
                iconColor: 'text-yellow-500',
                textColor: 'text-yellow-800',
                progressColor: 'bg-yellow-500'
            },
            info: {
                icon: 'fa-info-circle',
                iconColor: 'text-blue-500',
                textColor: 'text-blue-800',
                progressColor: 'bg-blue-500'
            }
        };
        
        return styles[type] || styles.info;
    }

    static wait(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }
}

// Inicializar el servicio de notificaciones cuando el DOM esté listo
document.addEventListener('DOMContentLoaded', () => {
    NotificationService.init();
});

// Para poder usarlo en otros módulos
export default NotificationService;