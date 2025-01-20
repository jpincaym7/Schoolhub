class ActivityManager {
    constructor() {
        this.subjectId = document.querySelector('meta[name="subject-id"]').content;
        this.academicPeriodId = document.querySelector('meta[name="academic-period-id"]').content;
        this.currentParcial = this.getInitialParcial();
        this.students = [];
        this.academicPeriods = [];
        this.setupEventListeners();
        this.initializeView();
        this.setupNotificationSystem();
    }

    getInitialParcial() {
        // Obtener el parcial de la URL o default a 1
        const urlParams = new URLSearchParams(window.location.search);
        console.log(urlParams)
        return urlParams.get('parcial') || '1';
    }

    setupNotificationSystem() {
        if (!document.getElementById('notificationContainer')) {
            const container = document.createElement('div');
            container.id = 'notificationContainer';
            container.className = 'fixed top-4 right-4 z-50 space-y-2 w-96'; // Aumentado el ancho
            document.body.appendChild(container);
        }
    }

    showNotification(message, type = 'success', duration = 4000) {
        const container = document.getElementById('notificationContainer');
        const notification = document.createElement('div');
        
        const baseClasses = 'w-full shadow-lg rounded-lg pointer-events-auto overflow-hidden';
        const typeClasses = type === 'success' ? 'bg-green-50' : 'bg-red-50';
        
        notification.className = `${baseClasses} ${typeClasses} transform transition-all duration-300 ease-out opacity-0 translate-x-full`;
        
        notification.innerHTML = `
            <div class="p-6"> <!-- Aumentado el padding -->
                <div class="flex items-start">
                    <div class="flex-shrink-0 text-xl"> <!-- Aumentado el tamaño del ícono -->
                        <i class="fas ${type === 'success' ? 'fa-check-circle text-green-600' : 'fa-exclamation-circle text-red-600'}"></i>
                    </div>
                    <div class="ml-4 w-0 flex-1"> <!-- Aumentado el margen -->
                        <p class="text-base font-medium ${type === 'success' ? 'text-green-800' : 'text-red-800'}"> <!-- Aumentado el tamaño del texto -->
                            ${message}
                        </p>
                    </div>
                    <div class="ml-4 flex-shrink-0 flex">
                        <button class="inline-flex text-gray-400 hover:text-gray-500 text-xl"> <!-- Aumentado el tamaño del botón de cerrar -->
                            <i class="fas fa-times"></i>
                        </button>
                    </div>
                </div>
            </div>
        `;

        container.appendChild(notification);
        
        requestAnimationFrame(() => {
            notification.classList.remove('opacity-0', 'translate-x-full');
        });

        notification.querySelector('button').addEventListener('click', () => {
            this.removeNotification(notification);
        });

        setTimeout(() => {
            this.removeNotification(notification);
        }, duration);
    }

    setupEventListeners() {
        // Existing event listeners
        document.getElementById('createActivityBtn').addEventListener('click', () => this.showModal());
        document.getElementById('cancelActivityBtn').addEventListener('click', () => this.hideModal());
        document.getElementById('closeModal').addEventListener('click', () => this.hideModal());
        document.getElementById('activityForm').addEventListener('submit', (e) => this.handleFormSubmit(e));
        
        // Mejorado el manejo de clicks en las pestañas de parciales
        document.querySelectorAll('.parcial-tab').forEach(tab => {
            tab.addEventListener('click', (e) => {
                e.preventDefault();
                e.stopPropagation();
                const parcial = tab.dataset.parcial;
                this.handleParcialChange(parcial);
            });
        });

        // Actualizar la UI para reflejar el parcial inicial
        this.updateParcialUI(this.currentParcial);

        // Select all students functionality
        document.getElementById('selectAllStudents').addEventListener('change', (e) => {
            const checkboxes = document.querySelectorAll('#studentsList input[type="checkbox"]');
            checkboxes.forEach(checkbox => checkbox.checked = e.target.checked);
        });
    }

    handleParcialChange(parcial) {
        this.currentParcial = parcial;
        this.updateParcialUI(parcial);
        this.loadActivities(parcial);
        
        // Actualizar la URL sin recargar la página
        const newUrl = new URL(window.location);
        newUrl.searchParams.set('parcial', parcial);
        window.history.pushState({}, '', newUrl);
    }

    updateParcialUI(parcial) {
        document.querySelectorAll('.parcial-tab').forEach(tab => {
            const isActive = tab.dataset.parcial === parcial;
            tab.classList.toggle('text-blue-600', isActive);
            tab.classList.toggle('border-b-2', isActive);
            tab.classList.toggle('border-blue-600', isActive);
            tab.classList.toggle('bg-white', isActive);
            tab.classList.toggle('text-gray-500', !isActive);
        });
    }


removeNotification(notification) {
    notification.classList.add('opacity-0', 'translate-x-full');
    setTimeout(() => notification.remove(), 300);
}

setupRealtimeUpdates() {
    // Poll for updates every 30 seconds
    this.updateInterval = setInterval(() => {
        this.checkForUpdates();
    }, 30000);
}

async checkForUpdates() {
    try {
        const response = await fetch(
            `/subjects/activities/?subject=${this.subjectId}&partial=${this.currentParcial}&academic_period=${this.academicPeriodId}&timestamp=${Date.now()}`
        );
        
        if (!response.ok) throw new Error('Error checking for updates');
        
        const data = await response.json();
        const currentActivities = document.querySelectorAll('#activitiesList > div').length;
        
        if (data.results.length !== currentActivities) {
            this.renderActivities(data.results);
            this.showNotification('Las actividades han sido actualizadas', 'success');
        }
    } catch (error) {
        console.error('Error checking for updates:', error);
    }
}

async initializeView() {
    await Promise.all([
        this.loadAcademicPeriods(),
        this.loadStudents()
    ]);
    this.loadActivities(1);
}

async loadAcademicPeriods() {
    try {
        const response = await fetch('/subjects/academic-periods/current/');
        if (!response.ok) throw new Error('Error al cargar período académico');
        const data = await response.json();
        console.log(data)
        this.academicPeriods = data;
        this.currentAcademicPeriod = data.current_period;
        
        // Actualizar el academic_period_id en el meta tag
        const metaTag = document.querySelector('meta[name="academic-period-id"]');
        if (metaTag) {
            metaTag.content = this.currentAcademicPeriod.id;
            this.academicPeriodId = this.currentAcademicPeriod.id;
        }
        
        this.renderAcademicPeriodInfo();
    } catch (error) {
        this.showToast(error.message, 'error');
    }
}

async loadStudents() {
    try {
        const response = await fetch(`/students/api-students/`);
        if (!response.ok) throw new Error('Error al cargar estudiantes');
        const data = await response.json();
        this.students = data.results || [];
        this.renderStudentsList();
    } catch (error) {
        this.showToast(error.message, 'error');
    }
}

renderAcademicPeriodInfo() {
    // Agregar información del período académico actual en el header
    const headerInfo = document.createElement('div');
    headerInfo.className = 'mt-2 text-sm text-gray-600';
    headerInfo.innerHTML = `
        <span class="font-medium">Período Actual:</span> 
        Quimestre ${this.currentAcademicPeriod.number} - ${this.currentAcademicPeriod.school_year}
    `;
    
    // Insertar después del párrafo existente en el header
    const headerSection = document.querySelector('.mb-8 div p');
    if (headerSection) {
        headerSection.parentNode.insertBefore(headerInfo, headerSection.nextSibling);
    }
}

renderStudentsList() {
    const studentsList = document.getElementById('studentsList');
    studentsList.innerHTML = this.students.map(student => `
        <div class="flex items-center p-2 hover:bg-gray-100 rounded">
            <input type="checkbox" name="student_ids" value="${student.id}"
                   class="rounded border-gray-300 text-blue-600 focus:ring-blue-500">
            <label class="ml-3 text-sm text-gray-700">
                ${this.escapeHtml(student.full_name)}
            </label>
        </div>
    `).join('');
}

showModal() {
    document.getElementById('activityModal').classList.remove('hidden');
    document.getElementById('mainContent').classList.add('blur-sm');
    document.body.classList.add('overflow-hidden');
}

hideModal() {
    document.getElementById('activityModal').classList.add('hidden');
    document.getElementById('mainContent').classList.remove('blur-sm');
    document.body.classList.remove('overflow-hidden');
    document.getElementById('activityForm').reset();
}

async loadActivities(parcial) {
    try {
        const response = await fetch(
            `/subjects/activities/?subject=${this.subjectId}&partial=${parcial}&academic_period=${this.currentAcademicPeriod.id}`
        );
        if (!response.ok) throw new Error('Error al cargar actividades');
        const data = await response.json();
        this.renderActivities(data.results || []);
    } catch (error) {
        this.showToast(error.message, 'error');
    }
}

renderActivities(activities) {
    const activitiesList = document.getElementById('activitiesList');
    if (!activities.length) {
        activitiesList.innerHTML = `
            <div class="text-center py-12">
                <div class="mx-auto h-12 w-12 text-gray-400">
                    <i class="fas fa-tasks text-4xl"></i>
                </div>
                <h3 class="mt-2 text-sm font-medium text-gray-900">No hay actividades</h3>
                <p class="mt-1 text-sm text-gray-500">Comienza creando una nueva actividad para este parcial.</p>
            </div>
        `;
        return;
    }

    // Agrupar actividades por tipo y secuencia
    const groupedActivities = activities.reduce((acc, activity) => {
        const key = `${activity.activity_type}-${activity.sequence_number}`;
        if (!acc[key]) {
            acc[key] = {
                template: activity.template,
                name: activity.name,
                description: activity.description,
                activity_type: activity.activity_type,
                sequence_number: activity.sequence_number,
                activities: []
            };
        }
        acc[key].activities.push(activity);
        return acc;
    }, {});

    activitiesList.innerHTML = Object.values(groupedActivities).map(group => `
        <div class="bg-white rounded-lg border border-gray-200 shadow-sm hover:shadow-md transition-shadow">
            <div class="p-6">
                <div class="flex justify-between items-start mb-4">
                    <div class="flex-1">
                        <div class="flex items-center space-x-3">
                            <h3 class="text-lg font-semibold text-gray-900">
                                ${this.escapeHtml(group.name)}
                            </h3>
                            <span class="px-3 py-1 rounded-full text-xs font-medium
                                ${group.activity_type === 'individual' ? 
                                'bg-blue-100 text-blue-800' : 
                                'bg-purple-100 text-purple-800'}">
                                ${group.activity_type === 'individual' ? 'Individual' : 'Grupal'}
                            </span>
                            <span class="text-sm text-gray-500">
                                Secuencia #${group.sequence_number}
                            </span>
                        </div>
                        <p class="mt-1 text-sm text-gray-600">
                            ${this.escapeHtml(group.description || 'Sin descripción')}
                        </p>
                    </div>
                    <a href="/subjects/action-edit/${group.template}/notas" 
                       class="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-lg 
                              text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 
                              focus:ring-offset-2 focus:ring-blue-500">
                        <i class="fas fa-edit mr-2"></i>
                        Calificar
                    </a>
                </div>
                <div class="mt-4 flex items-center space-x-4 text-sm text-gray-500">
                    <div class="flex items-center">
                        <i class="fas fa-users mr-2"></i>
                        <span>${group.activities.length} estudiantes</span>
                    </div>
                    <div class="flex items-center">
                        <i class="fas fa-clock mr-2"></i>
                        <span>${new Date(group.activities[0].created_at).toLocaleDateString('es-ES', {
                            year: 'numeric',
                            month: 'long',
                            day: 'numeric'
                        })}</span>
                    </div>
                </div>
            </div>
        </div>
    `).join('');
}

showToast(message, type = 'success') {
    const toast = document.createElement('div');
    bgColor = type === 'success' ? 'bg-green-600' : 
                   type === 'error' ? 'bg-red-600' : 'bg-yellow-600';
    
    toast.className = `fixed bottom-4 right-4 px-6 py-3 rounded-lg shadow-lg ${bgColor} text-white z-50 
                      transform transition-all duration-300 ease-in-out`;
    toast.textContent = message;
    
    document.body.appendChild(toast);
    
    // Animación de entrada
    requestAnimationFrame(() => {
        toast.style.transform = 'translateY(-20px)';
        toast.style.opacity = '1';
    });

    setTimeout(() => {
        toast.style.transform = 'translateY(0)';
        toast.style.opacity = '0';
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}

async handleFormSubmit(e) {
    e.preventDefault();
    const form = e.target;
    const selectedStudents = Array.from(form.querySelectorAll('input[name="student_ids"]:checked'))
        .map(checkbox => parseInt(checkbox.value));

    if (!this.validateForm(form, selectedStudents)) return;

    try {
        const formData = {
            name: form.name.value,
            description: form.description.value,
            activity_type: form.activity_type.value,
            partial_number: this.currentParcial,
            subject: parseInt(this.subjectId),
            academic_period: this.academicPeriodId,
            student_ids: selectedStudents
        };

        const response = await fetch('/subjects/activity-templates/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
            },
            body: JSON.stringify(formData)
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Error al crear la actividad');
        }

        this.showNotification('Actividad creada exitosamente', 'success');
        await this.loadActivities(this.currentParcial);
        this.hideModal(); // Ahora correctamente removerá el blur
    } catch (error) {
        this.showNotification(error.message, 'error');
    }
}

validateForm(form, selectedStudents) {
    const name = form.name.value.trim();
    const errors = [];

    if (!name) {
        errors.push('El nombre de la actividad es requerido');
    }

    if (name.length > 100) {
        errors.push('El nombre de la actividad es demasiado largo');
    }

    if (!selectedStudents.length) {
        errors.push('Debe seleccionar al menos un estudiante');
    }

    if (errors.length > 0) {
        errors.forEach(error => this.showNotification(error, 'error'));
        return false;
    }

    return true;
}

cleanup() {
    // Clear interval when component is destroyed
    if (this.updateInterval) {
        clearInterval(this.updateInterval);
    }
}

escapeHtml(unsafe) {
    return unsafe
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
new ActivityManager();
});