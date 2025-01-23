class EnrollmentManager {
    constructor() {
        this.toastContainer = document.getElementById('toastContainer');
        this.modal = document.getElementById('enrollmentModal');
        this.form = document.getElementById('enrollmentForm');
        this.submitButton = document.getElementById('submitButton');
        this.submitSpinner = document.getElementById('submitSpinner');
        this.endpoints = {
            students: '/students/query-students/',
            periods: '/students/query-periods/',
            enrollments: '/students/matriculas/',
        };
        this.isSubmitting = false;
        this.init();
    }

    // Toast Notification System
    showToast(message, type = 'success') {
        const toast = document.createElement('div');
        toast.className = `mb-2 p-4 rounded-md text-white ${
            type === 'success' ? 'bg-green-500' : 'bg-red-500'
        } transition-all duration-300 transform translate-x-full flex items-center gap-2`;
        
        const icon = this.createToastIcon(type);
        const text = document.createElement('span');
        text.textContent = message;
        
        toast.append(icon, text);
        this.toastContainer.appendChild(toast);
        
        // Animation sequence
        setTimeout(() => toast.classList.remove('translate-x-full'), 100);
        setTimeout(() => {
            toast.classList.add('translate-x-full');
            setTimeout(() => toast.remove(), 300);
        }, 3000);
    }

    createToastIcon(type) {
        const icon = document.createElement('span');
        icon.className = type === 'success' ? 'text-green-200' : 'text-red-200';
        icon.innerHTML = type === 'success' 
            ? '<svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"/></svg>'
            : '<svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/></svg>';
        return icon;
    }

    // Form Validation Methods
    setupValidation() {
        // Required fields validation
        const requiredFields = {
            'estudiante': 'Debe seleccionar un estudiante',
            'periodo': 'Debe seleccionar un periodo'
        };

        this.form.addEventListener('change', (e) => {
            if (e.target.name in requiredFields) {
                this.validateField(e.target, requiredFields[e.target.name]);
            }
        });

        // Subject selection validation
        const subjectsList = document.getElementById('subjectsList');
        subjectsList.addEventListener('change', () => {
            const checkedSubjects = subjectsList.querySelectorAll('input[type="checkbox"]:checked');
            if (checkedSubjects.length === 0) {
                subjectsList.classList.add('border-red-500');
            } else {
                subjectsList.classList.remove('border-red-500');
            }
        });
    }

    validateField(field, message) {
        const errorId = `${field.name}-error`;
        let errorElement = document.getElementById(errorId);

        if (!field.value) {
            if (!errorElement) {
                errorElement = document.createElement('p');
                errorElement.id = errorId;
                errorElement.className = 'mt-1 text-sm text-red-600';
                field.parentNode.appendChild(errorElement);
            }
            errorElement.textContent = message;
            field.classList.add('border-red-500');
            return false;
        } else {
            if (errorElement) {
                errorElement.remove();
            }
            field.classList.remove('border-red-500');
            return true;
        }
    }

    validateForm() {
        let isValid = true;

        // Validate student and period selections
        const studentSelect = this.form.querySelector('[name="estudiante"]');
        const periodSelect = this.form.querySelector('[name="periodo"]');
        
        isValid = this.validateField(studentSelect, 'Debe seleccionar un estudiante') && isValid;
        isValid = this.validateField(periodSelect, 'Debe seleccionar un periodo') && isValid;

        // Validate subject selection
        const checkedSubjects = this.form.querySelectorAll('input[name="subjects"]:checked');
        const subjectsList = document.getElementById('subjectsList');
        
        if (checkedSubjects.length === 0) {
            subjectsList.classList.add('border-red-500');
            const errorId = 'subjects-error';
            let errorElement = document.getElementById(errorId);
            
            if (!errorElement) {
                errorElement = document.createElement('p');
                errorElement.id = errorId;
                errorElement.className = 'mt-1 text-sm text-red-600';
                subjectsList.parentNode.appendChild(errorElement);
            }
            errorElement.textContent = 'Debe seleccionar al menos una materia';
            isValid = false;
        }

        return isValid;
    }

    // Modal Management
    openModal = () => {
        this.modal.classList.add('active');
        this.loadInitialData();
    }

    closeModal = () => {
        this.modal.classList.remove('active');
        this.form.reset();
        
        // Restablecer el modo del formulario
        this.form.dataset.mode = 'create';
        delete this.form.dataset.enrollmentId;
        
        // Restablecer el título
        document.querySelector('#enrollmentModal h2').textContent = 'Nueva Matrícula';
        
        // Habilitar campos
        this.form.querySelector('[name="estudiante"]').disabled = false;
        this.form.querySelector('[name="periodo"]').disabled = false;
        
        // Limpiar lista de materias
        document.getElementById('subjectsList').innerHTML = 
            '<div class="p-4 text-center text-gray-500">Seleccione un periodo para ver las materias disponibles</div>';
    }

    // Data Loading Methods
    async loadInitialData() {
        try {
            await Promise.all([
                this.loadStudents(),
                this.loadPeriods(),
                this.loadEnrollments()
            ]);
            await this.updateDashboardStats();
        } catch (error) {
            this.showToast('Error al cargar datos iniciales', 'error');
            console.error('Error loading initial data:', error);
        }
    }

    async fetchData(endpoint, options = {}) {
        try {
            const response = await fetch(this.endpoints[endpoint], options);
            if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
            const data = await response.json();
            return data.results || [];
        } catch (error) {
            this.showToast(`Error al cargar ${endpoint}`, 'error');
            throw error;
        }
    }

    async loadStudents() {
        const students = await this.fetchData('students');
        const select = document.getElementById('studentSelect');
        select.innerHTML = '<option value="">Seleccione un estudiante</option>' +
            students.map(student => 
                `<option value="${student.id}">${student.usuario}</option>`
            ).join('');
        
        document.getElementById('totalStudents').textContent = students.length;
    }

    async loadPeriods() {
        const periods = await this.fetchData('periods');
        const select = document.getElementById('periodSelect');
        
        select.innerHTML = '<option value="">Seleccione un periodo</option>' +
            periods.map(period => 
                `<option value="${period.id}" ${period.activo ? 'selected' : ''}>
                    ${period.nombre}
                </option>`
            ).join('');
        
        const activePeriod = periods.find(p => p.activo);
        if (activePeriod) {
            await this.loadSubjects(activePeriod.id);
        }
    }

    async loadSubjects() {
        try {
            const response = await fetch(`/students/query-mat/`);
            const data = await response.json();
            const subjects = data.results || [];
            document.getElementById('subjectsList').innerHTML = subjects.length 
                ? this.renderSubjectsList(subjects)
                : '<div class="p-4 text-center text-gray-500">No hay materias disponibles para este periodo</div>';
        } catch (error) {
            this.showToast('Error al cargar materias', 'error');
            throw error;
        }
    }

    renderSubjectsList(subjects) {
        return subjects.map(subject => `
            <div class="flex items-center p-3 border-b">
                <input type="checkbox" name="subjects" value="${subject.id}"
                    class="h-4 w-4 text-indigo-600 border-gray-300 rounded">
                <label class="ml-3 block text-sm font-medium text-gray-700">
                    ${subject.codigo} - ${subject.nombre}
                    <span class="text-sm text-gray-500">(${subject.horas_semanales} Horas Semanales)</span>
                </label>
            </div>
        `).join('');
    }

    async loadEnrollments(searchTerm = '') {
        const tbody = document.getElementById('enrollmentsList');
        tbody.innerHTML = '<tr class="loading-placeholder">...</tr>';

        try {
            const url = searchTerm 
                ? `${this.endpoints.enrollments}?search=${encodeURIComponent(searchTerm)}`
                : this.endpoints.enrollments;
            
            const enrollments = await this.fetchData('enrollments', { 
                headers: { 'Accept': 'application/json' }
            });

            console.log(enrollments)

            tbody.innerHTML = enrollments.length 
                ? this.renderEnrollmentsList(enrollments)
                : '<tr><td colspan="6" class="px-6 py-4 text-center text-gray-500">No se encontraron matrículas</td></tr>';

            document.getElementById('activeEnrollments').textContent = enrollments.length;
        } catch (error) {
            tbody.innerHTML = '<tr><td colspan="6" class="px-6 py-4 text-center text-red-500">Error al cargar las matrículas</td></tr>';
            throw error;
        }
    }

    async editEnrollment(enrollmentId) {
        try {
            // Mostrar estado de carga en el modal
            this.openModal();
            document.getElementById('subjectsList').innerHTML = `
                <div class="p-4 text-center text-gray-500">
                    <svg class="inline w-6 h-6 animate-spin" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                        <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                        <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                    </svg>
                    <span class="ml-2">Cargando materias...</span>
                </div>`;

            // Fetch enrollment details
            const response = await fetch(`${this.endpoints.enrollments}${enrollmentId}/`);
            if (!response.ok) throw new Error('Error al cargar la matrícula');
            const enrollment = await response.json();

            console.log('Enrollment data:', enrollment); // Para debugging

            // Actualizar título del modal
            document.querySelector('#enrollmentModal h2').textContent = 'Editar Matrícula';

            // Marcar el formulario como modo edición
            this.form.dataset.mode = 'edit';
            this.form.dataset.enrollmentId = enrollmentId;

            // Establecer estudiante y periodo
            const studentSelect = this.form.querySelector('[name="estudiante"]');
            const periodSelect = this.form.querySelector('[name="periodo"]');

            // Cargar estudiantes y periodos si es necesario
            await Promise.all([
                this.loadStudents(),
                this.loadPeriods()
            ]);

            // Establecer los valores seleccionados
            studentSelect.value = enrollment.estudiante;
            periodSelect.value = enrollment.periodo;

            // Cargar y marcar las materias
            await this.loadSubjects();
            
            // Esperar un momento para asegurarse de que las materias se han cargado
            setTimeout(() => {
                const subjectsCheckboxes = this.form.querySelectorAll('input[name="subjects"]');
                const enrolledMateriaIds = enrollment.detalles.map(d => d.materia);
                
                console.log('Materias matriculadas:', enrolledMateriaIds); // Para debugging

                subjectsCheckboxes.forEach(checkbox => {
                    checkbox.checked = enrolledMateriaIds.includes(parseInt(checkbox.value));
                });
            }, 300);

            // Deshabilitar campos que no deberían cambiar en edición
            studentSelect.disabled = true;
            periodSelect.disabled = true;

        } catch (error) {
            console.error('Error en editEnrollment:', error);
            this.showToast('Error al cargar la matrícula: ' + error.message, 'error');
            this.closeModal();
        }
    }

    async deleteEnrollment(enrollmentId) {
        if (!confirm('¿Está seguro de eliminar esta matrícula? Esta acción no se puede deshacer.')) {
            return;
        }

        try {
            const response = await fetch(`${this.endpoints.enrollments}${enrollmentId}/`, {
                method: 'DELETE',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCsrfToken()
                }
            });

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.error || 'Error al eliminar la matrícula');
            }

            this.showToast('Matrícula eliminada exitosamente', 'success');
            await this.loadEnrollments();
            await this.updateDashboardStats();
        } catch (error) {
            this.showToast(error.message, 'error');
            console.error('Error:', error);
        }
    }

    renderEnrollmentsList(enrollments) {
        return enrollments.map(enrollment => `
            <tr class="hover:bg-gray-50">
                <td class="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                    ${enrollment.numero_matricula}
                </td>
                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    ${enrollment.estudiante_get_full_name}
                </td>
                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    ${enrollment.periodo_nombre}
                </td>
                <td class="px-6 py-4 text-sm text-gray-500">
                    <div class="flex flex-wrap gap-1">
                        ${enrollment.detalles.map(detalle => `
                            <span class="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                                ${detalle.codigo_materia}
                            </span>
                        `).join('')}
                    </div>
                </td>
                <td class="px-6 py-4 whitespace-nowrap">
                    ${this.renderEnrollmentStatus(enrollment.fecha_inscripcion)}
                </td>
                <td class="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                    <div class="flex justify-end gap-2">
                        <button onclick="enrollmentManager.editEnrollment(${enrollment.id})" 
                                class="text-indigo-600 hover:text-indigo-900">
                            Editar
                        </button>
                        <button onclick="enrollmentManager.deleteEnrollment(${enrollment.id})" 
                                class="text-red-600 hover:text-red-900">
                            Eliminar
                        </button>
                    </div>
                </td>
            </tr>
        `).join('');
    }

    renderEnrollmentStatus(dateString) {
        const isRecent = new Date(dateString) > new Date(Date.now() - 24*60*60*1000);
        return `
            <span class="px-2 py-1 text-xs rounded-full ${
                isRecent ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800'
            }">
                ${isRecent ? 'Reciente' : 'Regular'}
            </span>
        `;
    }

    async handleSubmit(event) {
        event.preventDefault();
        
        // Prevent multiple submissions
        if (this.isSubmitting) return;
        this.isSubmitting = true;
    
        if (!this.validateForm()) {
            this.isSubmitting = false;
            return;
        }
    
        this.submitButton.disabled = true;
        this.submitSpinner.classList.remove('hidden');
    
        try {
            const isEditMode = this.form.dataset.mode === 'edit';
            const enrollmentId = this.form.dataset.enrollmentId;
    
            const jsonData = {
                materias_ids: Array.from(this.form.querySelectorAll('input[name="subjects"]:checked'))
                    .map(checkbox => parseInt(checkbox.value))
            };
    
            if (!isEditMode) {
                // Solo incluir estudiante y periodo en modo creación
                jsonData.estudiante = parseInt(this.form.querySelector('[name="estudiante"]').value);
                jsonData.periodo = parseInt(this.form.querySelector('[name="periodo"]').value);
            }
    
            const url = isEditMode 
                ? `${this.endpoints.enrollments}${enrollmentId}/update_subjects/`
                : this.endpoints.enrollments;
    
            const response = await fetch(url, {
                method: isEditMode ? 'PATCH' : 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Accept': 'application/json',
                    'X-CSRFToken': this.getCsrfToken()
                },
                body: JSON.stringify(jsonData)
            });
    
            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(JSON.stringify(errorData));
            }
    
            this.showToast(
                isEditMode ? 'Matrícula actualizada exitosamente' : 'Matrícula creada exitosamente',
                'success'
            );
            this.closeModal();
            await this.loadEnrollments();
            await this.updateDashboardStats();
    
        } catch (error) {
            console.error('Error:', error);
            let errorMessage = 'Error al procesar la matrícula';
            try {
                const errorData = JSON.parse(error.message);
                if (errorData.estudiante) {
                    errorMessage = `Error: ${errorData.estudiante.join(', ')}`;
                }
            } catch (e) {
                // Usar mensaje genérico si falla el parsing
            }
            this.showToast(errorMessage, 'error');
        } finally {
            this.submitButton.disabled = false;
            this.submitSpinner.classList.add('hidden');
            this.isSubmitting = false;  // Reset submission flag
        }
    }

    getCsrfToken() {
        return document.querySelector('[name=csrfmiddlewaretoken]')?.value;
    }

    handleSearch = debounce(async (event) => {
        await this.loadEnrollments(event.target.value);
    }, 300);

    // Update Methods
    async updateDashboardStats() {
        try {
            const response = await fetch('/students/dashboard-stats/');
            const stats = await response.json();
            
            Object.entries(stats).forEach(([key, value]) => {
                const element = document.getElementById(key);
                if (element) element.textContent = value;
            });
        } catch (error) {
            console.error('Error updating dashboard stats:', error);
        }
    }

    // Lifecycle Methods
    startPeriodicUpdates() {
        this.intervalId = setInterval(async () => {
            await this.loadEnrollments();
            await this.updateDashboardStats();
        }, this.updateInterval);
    }

    stopPeriodicUpdates() {
        if (this.intervalId) {
            clearInterval(this.intervalId);
            this.intervalId = null;
        }
    }

    // Initialization
    init() {
        // Event Listeners
        document.getElementById('btnNewEnrollment').addEventListener('click', this.openModal);
        document.querySelectorAll('.modal-close').forEach(btn => 
            btn.addEventListener('click', this.closeModal)
        );
        
        document.getElementById('studentSearch').addEventListener('input', this.handleSearch);
        document.getElementById('periodSelect').addEventListener('change', (e) => 
            this.loadSubjects(e.target.value)
        );
        
        this.form.addEventListener('submit', (e) => this.handleSubmit(e));
        
        // Setup form validation
        this.setupValidation();
        
        // Check for new=true in URL
        if (window.location.search.includes('new=true')) {
            this.openModal();
        }
        
        // Initial load
        this.loadInitialData();
    }
}

// Utility function for debouncing
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// Initialize the enrollment manager
const enrollmentManager = new EnrollmentManager();
document.addEventListener('DOMContentLoaded', () => enrollmentManager.init());