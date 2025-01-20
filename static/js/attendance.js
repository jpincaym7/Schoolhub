// Namespace para evitar conflictos globales
const AttendanceApp = {
    // Configuración de Flatpickr
    initFlatpickr() {
        flatpickr("#dateRange", {
            mode: "range",
            dateFormat: "Y-m-d",
            locale: "es",
            defaultDate: [
                new Date().setDate(new Date().getDate() - 30),
                new Date()
            ],
        });
    },

    // Variables globales
    API_ENDPOINTS: {
        ATTENDANCE: '/students/attendances/',
        STUDENTS: '/students/api-students/',
    },

    CSRF_TOKEN: document.querySelector('[name=csrfmiddlewaretoken]').value,

    // Clase para manejar notificaciones
    NotificationManager: {
        show(message, type = 'success') {
            const container = document.getElementById('notificationContainer');
            const notification = document.createElement('div');
            
            notification.className = `notification-toast glass-effect p-4 mb-4 rounded-lg shadow-lg flex items-center ${
                type === 'success' ? 'bg-green-50 text-green-800' : 'bg-red-50 text-red-800'
            }`;
            
            notification.innerHTML = `
                <i class="fas fa-${type === 'success' ? 'check-circle' : 'exclamation-circle'} mr-2"></i>
                <span>${message}</span>
                <button class="ml-auto" onclick="this.parentElement.remove()">
                    <i class="fas fa-times"></i>
                </button>
            `;
            
            container.appendChild(notification);
            notification.classList.add('show');
            
            setTimeout(() => {
                notification.classList.remove('show');
                setTimeout(() => notification.remove(), 300);
            }, 5000);
        }
    },

    // Servicio API
    ApiService: {
        async fetch(endpoint, options = {}) {
            const defaultOptions = {
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': AttendanceApp.CSRF_TOKEN
                }
            };
            
            try {
                const response = await fetch(endpoint, { ...defaultOptions, ...options });
                if (!response.ok) {
                    const errorData = await response.json();
                    throw new Error(errorData.detail || 'Error en la petición');
                }
                return await response.json();
            } catch (error) {
                console.error('Error API:', error);
                throw error;
            }
        }
    },

    // Actualizador del Dashboard
    DashboardUpdater: {
        async updateStatistics(filters = {}) {
            try {
                const queryParams = new URLSearchParams(filters).toString();
                const data = await AttendanceApp.ApiService.fetch(
                    `${AttendanceApp.API_ENDPOINTS.ATTENDANCE}statistics/?${queryParams}`
                );
                
                document.getElementById('totalRecords').textContent = data.total_records;
                this.updateStatusDistribution(data.status_distribution);
            } catch (error) {
                AttendanceApp.NotificationManager.show('Error al actualizar estadísticas', 'error');
            }
        },

        updateStatusDistribution(distribution) {
            distribution.forEach(status => {
                const statusCard = document.querySelector(`[data-status="${status.status}"]`);
                if (statusCard) {
                    statusCard.querySelector('.percentage').textContent = `${status.percentage.toFixed(1)}%`;
                    statusCard.querySelector('.count').textContent = `(${status.count} registros)`;
                }
            });
        },

        async updateLatestRecords() {
            try {
                const data = await AttendanceApp.ApiService.fetch(AttendanceApp.API_ENDPOINTS.ATTENDANCE);
                const tableBody = document.querySelector('#latestRecordsTable tbody');
                tableBody.innerHTML = data.results.slice(0, 10).map(record => `
                    <tr class="hover:bg-gray-50">
                        <td class="px-4 py-2">${record.student_name}</td>
                        <td class="px-4 py-2">${record.date}</td>
                        <td class="px-4 py-2">
                            <span class="status-badge status-${record.status}">
                                ${record.status_display}
                            </span>
                        </td>
                    </tr>
                `).join('');
            } catch (error) {
                AttendanceApp.NotificationManager.show('Error al actualizar registros recientes', 'error');
            }
        }
    },

    // Formulario de Asistencia
    AttendanceForm: {
        init() {
            this.form = document.getElementById('newAttendanceForm');
            this.setupEventListeners();
            this.loadStudents();
        },

        async loadStudents() {
            try {
                const students = await AttendanceApp.ApiService.fetch(AttendanceApp.API_ENDPOINTS.STUDENTS);
                const select = document.getElementById('studentSelect');
                
                students.results.forEach(student => {
                    const option = document.createElement('option');
                    option.value = student.id;
                    option.textContent = `${student.first_name} ${student.last_name}`;
                    select.appendChild(option);
                });
            } catch (error) {
                AttendanceApp.NotificationManager.show('Error al cargar lista de estudiantes', 'error');
            }
        },

        setupEventListeners() {
            this.form.addEventListener('submit', async (e) => {
                e.preventDefault();
                
                const formData = {
                    student: document.getElementById('studentSelect').value,
                    date: document.getElementById('attendanceDate').value,
                    status: document.getElementById('attendanceStatus').value
                };
                
                try {
                    await AttendanceApp.ApiService.fetch(AttendanceApp.API_ENDPOINTS.ATTENDANCE, {
                        method: 'POST',
                        body: JSON.stringify(formData)
                    });
                    
                    AttendanceApp.NotificationManager.show('Asistencia registrada exitosamente');
                    this.form.reset();
                    
                    await AttendanceApp.DashboardUpdater.updateStatistics();
                    await AttendanceApp.DashboardUpdater.updateLatestRecords();
                } catch (error) {
                    AttendanceApp.NotificationManager.show('Error al registrar asistencia', 'error');
                }
            });
        }
    },

    // Modal Manager para registro masivo
    ModalManager: {
        init() {
            this.modal = document.getElementById('bulkAttendanceModal');
            this.form = document.getElementById('bulkAttendanceForm');
            
            // Verificar que los elementos existan antes de configurar
            if (this.modal && this.form) {
                this.setupEventListeners();
            } else {
                console.warn('Elementos del modal no encontrados en el DOM');
            }
        },
    
        setupEventListeners() {
            if (!this.form) return;
            
            this.form.addEventListener('submit', async (e) => {
                e.preventDefault();
                
                const selectedStudents = Array.from(
                    document.querySelectorAll('#studentsList input[type="checkbox"]:checked')
                ).map(cb => parseInt(cb.value));
    
                if (selectedStudents.length === 0) {
                    AttendanceApp.NotificationManager.show('Seleccione al menos un estudiante', 'error');
                    return;
                }
    
                const formData = {
                    student_ids: selectedStudents,
                    date: document.getElementById('bulkAttendanceDate').value,
                    status: document.getElementById('bulkAttendanceStatus').value
                };
    
                try {
                    await AttendanceApp.ApiService.fetch(
                        `${AttendanceApp.API_ENDPOINTS.ATTENDANCE}bulk_create/`,
                        {
                            method: 'POST',
                            body: JSON.stringify(formData)
                        }
                    );
    
                    AttendanceApp.NotificationManager.show('Asistencias registradas exitosamente');
                    this.form.reset();
                    toggleBulkModal(false);
                    
                    // Actualizar dashboard
                    await AttendanceApp.DashboardUpdater.updateStatistics();
                    await AttendanceApp.DashboardUpdater.updateLatestRecords();
                } catch (error) {
                    AttendanceApp.NotificationManager.show('Error al registrar asistencias', 'error');
                }
            });
        },

        async loadStudentsList() {
            try {
                const students = await AttendanceApp.ApiService.fetch(AttendanceApp.API_ENDPOINTS.STUDENTS);
                const container = document.getElementById('studentsList');
                
                container.innerHTML = students.results.map(student => `
                    <div class="p-3 hover:bg-gray-50 flex items-center">
                        <input type="checkbox" 
                               id="student_${student.id}" 
                               value="${student.id}"
                               class="mr-3 h-4 w-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500">
                        <label for="student_${student.id}" class="flex-grow cursor-pointer">
                            ${student.first_name} ${student.last_name}
                        </label>
                    </div>
                `).join('');
            } catch (error) {
                AttendanceApp.NotificationManager.show('Error al cargar lista de estudiantes', 'error');
            }
        }
    },

    // Gestor de Filtros
    FilterManager: {
        init() {
            this.filterButton = document.getElementById('applyFilters');
            this.setupEventListeners();
        },

        getFilterValues() {
            const dateRange = document.getElementById('dateRange').value;
            const [startDate, endDate] = dateRange.split(' to ');
            
            return {
                start_date: startDate,
                end_date: endDate || startDate,
                status: document.getElementById('statusFilter').value
            };
        },

        setupEventListeners() {
            this.filterButton.addEventListener('click', async () => {
                const filters = this.getFilterValues();
                
                try {
                    await AttendanceApp.DashboardUpdater.updateStatistics(filters);
                    await AttendanceApp.DashboardUpdater.updateLatestRecords();
                    AttendanceApp.NotificationManager.show('Filtros aplicados correctamente');
                } catch (error) {
                    AttendanceApp.NotificationManager.show('Error al aplicar filtros', 'error');
                }
            });
        }
    },

    // Actualizador en tiempo real
    RealTimeUpdater: {
        init() {
            setInterval(async () => {
                await AttendanceApp.DashboardUpdater.updateStatistics();
                await AttendanceApp.DashboardUpdater.updateLatestRecords();
            }, 5 * 60 * 1000); // Cada 5 minutos
        }
    },

    // Inicialización de la aplicación
    init() {
        this.initFlatpickr();
        this.AttendanceForm.init();
        this.FilterManager.init();
        this.RealTimeUpdater.init();
        this.ModalManager.init();
        
        // Primera carga de datos
        this.DashboardUpdater.updateStatistics();
        this.DashboardUpdater.updateLatestRecords();
    }
};

// Funciones globales para el modal
function toggleBulkModal(show) {
    const modal = document.getElementById('bulkAttendanceModal');
    if (show) {
        modal.classList.remove('hidden');
        modal.classList.add('flex');
        // Set today's date as default
        document.getElementById('bulkAttendanceDate').value = new Date().toISOString().split('T')[0];
        // Load students list
        AttendanceApp.ModalManager.loadStudentsList();
    } else {
        modal.classList.add('hidden');
        modal.classList.remove('flex');
    }
}

function selectAllStudents(select) {
    document.querySelectorAll('#studentsList input[type="checkbox"]')
        .forEach(checkbox => checkbox.checked = select);
}

// Inicializar cuando el DOM esté listo
document.addEventListener('DOMContentLoaded', () => {
    AttendanceApp.init();
});