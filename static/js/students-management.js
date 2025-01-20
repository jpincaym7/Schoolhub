const API_ENDPOINTS = {
    STUDENTS: '/students/api-students/',
    PARENTS: '/users/api/?user_type=parent'
};

// Form Options Constants
const ACADEMIC_YEARS = [
    { value: '2023-2024', label: '2023-2024' },
    { value: '2024-2025', label: '2024-2025' },
    { value: '2025-2026', label: '2025-2026' }
];

const GRADES = [
    { value: '6TO INFORMATICA', label: 'Sexto Informatica' },
];

const PARALLELS = [
    { value: 'A', label: 'A' },
    { value: 'B', label: 'B' },
    { value: 'C', label: 'C' },
    { value: 'D', label: 'D' }
];

let currentStudentId = null;
let currentStudent = null;

const elements = {
    studentsGrid: document.getElementById('studentsGrid'),
    studentForm: document.getElementById('studentForm'),
    studentModal: document.getElementById('studentModal'),
    modalTitle: document.getElementById('modalTitle'),
    addStudentBtn: document.getElementById('addStudentBtn'),
    loadingIndicator: document.getElementById('loadingIndicator'),
    filters: {
        academicYear: document.getElementById('academicYearFilter'),
        grade: document.getElementById('gradeFilter'),
        status: document.getElementById('statusFilter'),
        applyBtn: document.getElementById('applyFilters')
    }
};

// Event Listeners
document.addEventListener('DOMContentLoaded', () => {
    loadStudents();
    loadParents();
    setupEventListeners();
    setupFormValidation();
    populateFormSelects();
});

function populateFormSelects() {
    // Populate Academic Year Select
    const academicYearSelect = elements.studentForm.elements['academic_year'];
    academicYearSelect.innerHTML = '<option value="">Seleccione el año lectivo</option>' +
        ACADEMIC_YEARS.map(year => `
            <option value="${year.value}">${year.label}</option>
        `).join('');

    // Populate Grade Select
    const gradeSelect = elements.studentForm.elements['grade'];
    gradeSelect.innerHTML = '<option value="">Seleccione el grado</option>' +
        GRADES.map(grade => `
            <option value="${grade.value}">${grade.label}</option>
        `).join('');

    // Populate Parallel Select
    const parallelSelect = elements.studentForm.elements['parallel'];
    parallelSelect.innerHTML = '<option value="">Seleccione el paralelo</option>' +
        PARALLELS.map(parallel => `
            <option value="${parallel.value}">${parallel.label}</option>
        `).join('');

    // Also populate filter selects if they exist
    if (elements.filters.academicYear) {
        elements.filters.academicYear.innerHTML = '<option value="">Todos los años</option>' +
            ACADEMIC_YEARS.map(year => `
                <option value="${year.value}">${year.label}</option>
            `).join('');
    }

    if (elements.filters.grade) {
        elements.filters.grade.innerHTML = '<option value="">Todos los grados</option>' +
            GRADES.map(grade => `
                <option value="${grade.value}">${grade.label}</option>
            `).join('');
    }
}

function setupEventListeners() {
    if (elements.addStudentBtn) {
        elements.addStudentBtn.addEventListener('click', () => openStudentModal());
    }
    elements.studentForm.addEventListener('submit', handleStudentSubmit);
    elements.filters.applyBtn.addEventListener('click', loadStudents);
}

function setupFormValidation() {
    const inputs = elements.studentForm.querySelectorAll('input, select');
    inputs.forEach(input => {
        input.addEventListener('invalid', (e) => {
            e.preventDefault();
            highlightInvalidField(input);
        });
        input.addEventListener('input', () => removeInvalidHighlight(input));
    });
}

function highlightInvalidField(field) {
    field.classList.add('border-red-500', 'focus:border-red-500', 'focus:ring-red-500');
    const errorMessage = field.validationMessage;
    showFieldError(field, errorMessage);
}

function removeInvalidHighlight(field) {
    field.classList.remove('border-red-500', 'focus:border-red-500', 'focus:ring-red-500');
    const errorDiv = field.parentElement.querySelector('.error-message');
    if (errorDiv) {
        errorDiv.remove();
    }
}

function showFieldError(field, message) {
    // Remove any existing error message
    const existingError = field.parentElement.querySelector('.error-message');
    if (existingError) {
        existingError.remove();
    }

    // Create and add new error message
    const errorDiv = document.createElement('div');
    errorDiv.className = 'error-message text-red-500 text-sm mt-1';
    errorDiv.textContent = message;
    field.parentElement.appendChild(errorDiv);
}

// API Functions
async function loadStudents() {
    showLoading(true);
    try {
        const filters = getActiveFilters();
        const queryString = new URLSearchParams(filters).toString();
        const response = await fetch(`${API_ENDPOINTS.STUDENTS}?${queryString}`);
        const data = await response.json();
        
        // La API de Django REST Framework devuelve los resultados en data.results
        const students = data.results || data; // Fallback por si no está paginado
        
        if (Array.isArray(students)) {
            renderStudents(students);
        } else {
            throw new Error('Formato de datos inesperado');
        }
    } catch (error) {
        showError('Error al cargar estudiantes: ' + error.message);
        console.error('Error:', error);
        // En caso de error, mostrar grid vacío
        elements.studentsGrid.innerHTML = `
            <div class="col-span-full text-center py-8">
                <p class="text-gray-500">
                    <i class="fas fa-exclamation-circle mr-2"></i>
                    Error al cargar los estudiantes. Por favor, intente nuevamente.
                </p>
            </div>
        `;
    } finally {
        showLoading(false);
    }
}

async function loadParents() {
    try {
        const response = await fetch(API_ENDPOINTS.PARENTS);
        const data = await response.json();
        
        // Asegurarnos de que tenemos un array de padres
        const parents = data.results || data;
        
        if (Array.isArray(parents)) {
            populateParentSelect(parents);
        } else {
            throw new Error('Formato de datos de padres inesperado');
        }
    } catch (error) {
        showError('Error al cargar representantes: ' + error.message);
        console.error('Error:', error);
    }
}

async function createStudent(formData) {
    try {
        const response = await fetch(API_ENDPOINTS.STUDENTS, {
            method: 'POST',
            headers: {
                'X-CSRFToken': getCSRFToken()
            },
            body: formData
        });
        const data = await response.json();
        
        if (response.ok) {
            showSuccess('Estudiante creado exitosamente');
            await loadStudents();
            return true;
        } else {
            throw new Error(data.message || 'Error al crear estudiante');
        }
    } catch (error) {
        showError(error.message);
        return false;
    }
}

async function updateStudent(id, formData) {
    try {
        const response = await fetch(`${API_ENDPOINTS.STUDENTS}${id}/`, {
            method: 'PATCH',
            headers: {
                'X-CSRFToken': getCSRFToken()
            },
            body: formData
        });
        const data = await response.json();
        
        if (response.ok) {
            showSuccess('Estudiante actualizado exitosamente');
            await loadStudents();
            return true;
        } else {
            throw new Error(data.message || 'Error al actualizar estudiante');
        }
    } catch (error) {
        showError(error.message);
        return false;
    }
}

async function deleteStudent(id) {
    try {
        const result = await Swal.fire({
            title: '¿Estás seguro?',
            text: "Esta acción desactivará al estudiante",
            icon: 'warning',
            showCancelButton: true,
            confirmButtonColor: '#d33',
            cancelButtonColor: '#3085d6',
            confirmButtonText: 'Sí, desactivar',
            cancelButtonText: 'Cancelar'
        });

        if (result.isConfirmed) {
            const response = await fetch(`${API_ENDPOINTS.STUDENTS}${id}/`, {
                method: 'DELETE',
                headers: {
                    'X-CSRFToken': getCSRFToken()
                }
            });

            if (response.ok) {
                showSuccess('Estudiante desactivado exitosamente');
                await loadStudents();
            } else {
                throw new Error('Error al desactivar estudiante');
            }
        }
    } catch (error) {
        showError(error.message);
    }
}

async function restoreStudent(id) {
    try {
        const response = await fetch(`${API_ENDPOINTS.STUDENTS}${id}/restore/`, {
            method: 'POST',
            headers: {
                'X-CSRFToken': getCSRFToken()
            }
        });

        if (response.ok) {
            showSuccess('Estudiante restaurado exitosamente');
            await loadStudents();
        } else {
            throw new Error('Error al restaurar estudiante');
        }
    } catch (error) {
        showError(error.message);
    }
}

function formatDateForInput(dateString) {
    try {
        const date = new Date(dateString);
        return date.toISOString().split('T')[0];
    } catch (error) {
        console.error('Error formatting date:', error);
        return '';
    }
}

function renderStudents(students) {
    console.log(students)
    if (!students || students.length === 0) {
        elements.studentsGrid.innerHTML = `
            <div class="col-span-full text-center py-8">
                <p class="text-gray-500">
                    <i class="fas fa-search mr-2"></i>
                    No se encontraron estudiantes
                </p>
            </div>
        `;
        return;
    }

    elements.studentsGrid.innerHTML = students.map(student => `
        <div class="student-card bg-white rounded-lg shadow-md overflow-hidden hover:shadow-lg transition-all duration-300">
            <div class="p-4">
                <div class="flex items-start space-x-4">
                    <img src="${student.photo || '/static/img/9334176.jpg'}" 
                         alt="Foto de ${student.first_name}"
                         class="student-photo">
                    <div class="flex-1">
                        <div class="flex justify-between items-start">
                            <div>
                                <h3 class="text-lg font-semibold text-gray-900">${student.full_name || `${student.first_name} ${student.last_name}`}</h3>
                                <p class="text-sm text-gray-600">ID: ${student.student_id || 'N/A'}</p>
                            </div>
                            <span class="px-2 py-1 text-xs font-semibold rounded ${
                                student.is_active 
                                    ? 'bg-green-100 text-green-800' 
                                    : 'bg-red-100 text-red-800'
                            }">
                                ${student.is_active ? 'Activo' : 'Inactivo'}
                            </span>
                        </div>
                    </div>
                </div>
                <div class="mt-4">
                    <p class="text-sm text-gray-600">
                        <i class="fas fa-graduation-cap mr-2"></i>
                        Grado ${student.grade} "${student.parallel}"
                    </p>
                </div>
                <div class="mt-4 flex justify-end space-x-2">
                    ${student.is_active ? `
                        <button onclick="openStudentModal(${JSON.stringify(student).replace(/"/g, '&quot;')})" 
                                class="px-3 py-1 text-sm text-blue-600 hover:bg-blue-50 rounded-md transition-colors">
                            <i class="fas fa-edit"></i>
                        </button>
                        <button onclick="deleteStudent(${student.id})"
                                class="px-3 py-1 text-sm text-red-600 hover:bg-red-50 rounded-md transition-colors">
                            <i class="fas fa-trash"></i>
                        </button>
                    ` : `
                        <button onclick="restoreStudent(${student.id})"
                                class="px-3 py-1 text-sm text-green-600 hover:bg-green-50 rounded-md transition-colors">
                            <i class="fas fa-undo"></i> Restaurar
                        </button>
                    `}
                </div>
            </div>
        </div>
    `).join('');
}

function openStudentModal(student = null) {
    try {
        currentStudentId = student ? student.id : null;
        currentStudent = student;
        elements.modalTitle.textContent = student ? 'Editar Estudiante' : 'Nuevo Estudiante';
        
        // Reset form and remove any previous error states
        elements.studentForm.reset();
        elements.studentForm.querySelectorAll('.error-message').forEach(el => el.remove());
        elements.studentForm.querySelectorAll('input, select').forEach(input => {
            input.classList.remove('border-red-500', 'focus:border-red-500', 'focus:ring-red-500');
        });

        // Update photo preview
        const photoPreview = document.getElementById('photoPreview');
        photoPreview.src = student && student.photo_url ? student.photo_url : '/api/placeholder/120/120';

        if (student) {
            // Populate form fields
            const formFields = {
                first_name: student.first_name,
                last_name: student.last_name,
                birth_date: formatDateForInput(student.birth_date),
                grade: student.grade,
                parallel: student.parallel,
                academic_year: student.academic_year,
                parent: student.parent
            };

            // Set values for each field
            Object.entries(formFields).forEach(([key, value]) => {
                const input = elements.studentForm.elements[key];
                if (input) {
                    input.value = value;
                    input.dispatchEvent(new Event('change', { bubbles: true }));
                }
            });

            // Keep academic year editable but show warning if changing
            const academicYearSelect = elements.studentForm.elements['academic_year'];
            academicYearSelect.addEventListener('change', () => {
                if (academicYearSelect.value !== student.academic_year) {
                    Swal.fire({
                        title: '¡Atención!',
                        text: 'Cambiar el año lectivo podría afectar el historial académico del estudiante.',
                        icon: 'warning',
                        showCancelButton: true,
                        confirmButtonText: 'Continuar',
                        cancelButtonText: 'Cancelar'
                    }).then((result) => {
                        if (!result.isConfirmed) {
                            academicYearSelect.value = student.academic_year;
                        }
                    });
                }
            });
        }
        
        elements.studentModal.classList.remove('hidden');
    } catch (error) {
        console.error('Error opening student modal:', error);
        showError('Error al abrir el formulario de estudiante');
    }
}

function closeStudentModal() {
    elements.studentModal.classList.add('hidden');
    elements.studentForm.reset();
    currentStudentId = null;
    currentStudent = null;
    
    // Remove any error states
    elements.studentForm.querySelectorAll('.error-message').forEach(el => el.remove());
    elements.studentForm.querySelectorAll('input, select').forEach(input => {
        input.classList.remove('border-red-500', 'focus:border-red-500', 'focus:ring-red-500');
        input.disabled = false;
    });
}

async function handleStudentSubmit(event) {
    event.preventDefault();
    
    const formData = new FormData(elements.studentForm);
    
    let success;
    if (currentStudentId) {
        success = await updateStudent(currentStudentId, formData);
    } else {
        success = await createStudent(formData);
    }
    
    if (success) {
        closeStudentModal();
    }
}

function populateParentSelect(parents) {
    const parentSelect = elements.studentForm.elements['parent'];
    parentSelect.innerHTML = '<option value="">Seleccione un representante</option>' +
        parents.map(parent => `
            <option value="${parent.id}">${parent.first_name} ${parent.last_name}</option>
        `).join('');
}

function getActiveFilters() {
    const filters = {};
    if (elements.filters.academicYear.value) {
        filters.academic_year = elements.filters.academicYear.value;
    }
    if (elements.filters.grade.value) {
        filters.grade = elements.filters.grade.value;
    }
    if (elements.filters.status.value) {
        filters.is_active = elements.filters.status.value;
    }
    return filters;
}

// Utility Functions
function showLoading(show) {
    elements.loadingIndicator.classList.toggle('hidden', !show);
    elements.studentsGrid.classList.toggle('loading', show);
}

function showSuccess(message) {
    Swal.fire({
        icon: 'success',
        title: 'Éxito',
        text: message,
        toast: true,
        position: 'top-end',
        showConfirmButton: false,
        timer: 3000,
        timerProgressBar: true
    });
}

function showError(message) {
    Swal.fire({
        icon: 'error',
        title: 'Error',
        text: message,
        toast: true,
        position: 'top-end',
        showConfirmButton: false,
        timer: 3000,
        timerProgressBar: true
    });
}

function getCSRFToken() {
    const csrfInput = document.querySelector('[name=csrfmiddlewaretoken]');
    return csrfInput ? csrfInput.value : '';
}

// Initialize tooltips and other UI enhancements
function initializeUI() {
    // Add any additional UI initialization here
    document.querySelectorAll('[data-tooltip]').forEach(element => {
        // Initialize tooltips if needed
    });
}