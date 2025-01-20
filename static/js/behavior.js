// Configuración inicial y variables globales
let currentBehaviorId = null;
const apiEndpoints = {
    behavior: '/students/api-behavior/',
    summary: '/students/api-summary/',
    students: '/students/api-students/',
    periods: '/students/academic-periods/'
};
const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;

// Event Listeners principales
document.addEventListener('DOMContentLoaded', () => {
    initializeFilters();
    loadBehaviors();
    setupEventListeners();
});

// Inicialización
function initializeFilters() {
    fetchStudents();
    fetchAcademicPeriods();
}

function setupEventListeners() {
    // Eventos del modal
    const addButton = document.getElementById('addBehaviorBtn');
    const closeButton = document.getElementById('closeModal');
    const behaviorForm = document.getElementById('behaviorForm');

    if (addButton) addButton.addEventListener('click', () => openModal());
    if (closeButton) closeButton.addEventListener('click', closeModal);
    if (behaviorForm) behaviorForm.addEventListener('submit', handleBehaviorSubmit);

    // Eventos de filtros
    ['studentFilter', 'periodFilter', 'typeFilter'].forEach(id => {
        const element = document.getElementById(id);
        if (element) element.addEventListener('change', loadBehaviors);
    });
}

// Funciones CRUD principales
async function loadBehaviors() {
    try {
        const studentId = document.getElementById('studentFilter')?.value;
        const periodId = document.getElementById('periodFilter')?.value;
        const type = document.getElementById('typeFilter')?.value;

        let url = new URL(window.location.origin + apiEndpoints.behavior);
        if (studentId) url.searchParams.append('student', studentId);
        if (periodId) url.searchParams.append('academic_period', periodId);
        if (type) url.searchParams.append('type', type);

        const response = await fetch(url);
        const data = await response.json();

        // Asegurarse de que data es un array
        const behaviors = Array.isArray(data) ? data : data.results || [];

        updateBehaviorTable(behaviors);
        updateStatistics(behaviors);
    } catch (error) {
        console.error('Error loading behaviors:', error);
        showNotification('Error al cargar los comportamientos', 'error');
    }
}

function updateBehaviorTable(behaviors) {
    const tbody = document.getElementById('behaviorTableBody');
    if (!tbody) return;

    tbody.innerHTML = '';

    if (!Array.isArray(behaviors)) {
        console.error('behaviors no es un array:', behaviors);
        return;
    }

    behaviors.forEach(behavior => {
        const row = document.createElement('tr');
        row.innerHTML = `
            <td class="px-6 py-4 whitespace-nowrap">${formatDate(behavior.date)}</td>
            <td class="px-6 py-4">${behavior.student_name || 'N/A'}</td>
            <td class="px-6 py-4">
                <span class="px-2 py-1 rounded-full text-sm ${getBehaviorTypeClass(behavior.type)}">
                    ${behavior.type_display || behavior.type}
                </span>
            </td>
            <td class="px-6 py-4">${behavior.description || ''}</td>
            <td class="px-6 py-4">
                <div class="flex space-x-2">
                    <button onclick="openModal(${behavior.id})" class="text-blue-600 hover:text-blue-800">
                        <i class="fas fa-edit"></i>
                    </button>
                    <button onclick="deleteBehavior(${behavior.id})" class="text-red-600 hover:text-red-800">
                        <i class="fas fa-trash"></i>
                    </button>
                </div>
            </td>
        `;
        tbody.appendChild(row);
    });
}

function updateStatistics(behaviors) {
    if (!Array.isArray(behaviors)) return;

    const stats = behaviors.reduce((acc, behavior) => {
        if (behavior.type) {
            acc[behavior.type] = (acc[behavior.type] || 0) + 1;
        }
        return acc;
    }, { positive: 0, negative: 0, neutral: 0 });

    Object.entries({
        positiveCount: stats.positive,
        negativeCount: stats.negative,
        neutralCount: stats.neutral
    }).forEach(([id, value]) => {
        const element = document.getElementById(id);
        if (element) element.textContent = value;
    });
}

// Funciones de carga de datos
async function fetchStudents() {
    try {
        const response = await fetch(apiEndpoints.students);
        const data = await response.json();
        
        // Asegurarse de que data es un array
        const students = Array.isArray(data) ? data : data.results || [];

        const selects = ['studentFilter', 'modalStudent']
            .map(id => document.getElementById(id))
            .filter(Boolean);

        selects.forEach(select => {
            select.innerHTML = '<option value="">Seleccionar estudiante...</option>';
            students.forEach(student => {
                const option = document.createElement('option');
                option.value = student.id;
                option.textContent = `${student.first_name} ${student.last_name}`;
                select.appendChild(option);
            });
        });
    } catch (error) {
        console.error('Error fetching students:', error);
        showNotification('Error al cargar estudiantes', 'error');
    }
}

async function fetchAcademicPeriods() {
    try {
        const response = await fetch(apiEndpoints.periods);
        const data = await response.json();
        console.log(data)
        // Asegurarse de que data es un array
        const periods = Array.isArray(data) ? data : data.results || [];

        const periodSelect = document.getElementById('periodFilter');
        if (!periodSelect) return;

        periodSelect.innerHTML = '<option value="">Seleccionar período...</option>';
        
        periods.forEach(period => {
            const option = document.createElement('option');
            option.value = period.id;
            option.textContent = period.school_year;
            periodSelect.appendChild(option);
        });

        // Seleccionar período activo si existe
        const activePeriod = periods.find(p => p.is_active);
        if (activePeriod) {
            periodSelect.value = activePeriod.id;
            loadBehaviors();
        }
    } catch (error) {
        console.error('Error fetching periods:', error);
        showNotification('Error al cargar períodos académicos', 'error');
    }
}

// Funciones del modal
async function openModal(behaviorId = null) {
    currentBehaviorId = behaviorId;
    const modal = document.getElementById('behaviorModal');
    const title = document.getElementById('modalTitle');
    if (!modal || !title) return;

    title.textContent = behaviorId ? 'Editar Comportamiento' : 'Nuevo Comportamiento';
    modal.classList.remove('hidden');
    modal.classList.add('flex');

    if (behaviorId) {
        const behavior = await fetchBehaviorDetails(behaviorId);
        if (behavior) fillModalForm(behavior);
    } else {
        document.getElementById('behaviorForm')?.reset();
    }
}

function closeModal() {
    const modal = document.getElementById('behaviorModal');
    if (!modal) return;
    
    modal.classList.add('hidden');
    modal.classList.remove('flex');
    currentBehaviorId = null;
}

// Funciones utilitarias
async function fetchBehaviorDetails(behaviorId) {
    try {
        const response = await fetch(`${apiEndpoints.behavior}${behaviorId}/`);
        if (!response.ok) throw new Error('Error al obtener detalles del comportamiento');
        return await response.json();
    } catch (error) {
        console.error('Error:', error);
        showNotification('Error al cargar detalles del comportamiento', 'error');
        return null;
    }
}

function fillModalForm(behavior) {
    const form = document.getElementById('behaviorForm');
    if (!form || !behavior) return;

    Object.entries({
        'student': behavior.student,
        'date': behavior.date,
        'type': behavior.type,
        'partial_number': behavior.partial_number,
        'description': behavior.description
    }).forEach(([key, value]) => {
        if (form.elements[key]) form.elements[key].value = value;
    });
}

function getBehaviorTypeClass(type) {
    const classes = {
        positive: 'bg-green-100 text-green-800',
        negative: 'bg-red-100 text-red-800',
        neutral: 'bg-gray-100 text-gray-800'
    };
    return classes[type] || classes.neutral;
}

function formatDate(dateString) {
    return new Date(dateString).toLocaleDateString('es-ES');
}

// Funciones de manejo de formularios
async function handleBehaviorSubmit(event) {
    event.preventDefault();
    
    const formData = new FormData(event.target);
    const behaviorData = Object.fromEntries(formData);

    try {
        const url = apiEndpoints.behavior + (currentBehaviorId ? `${currentBehaviorId}/` : '');
        const method = currentBehaviorId ? 'PUT' : 'POST';

        const response = await fetch(url, {
            method,
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrfToken
            },
            body: JSON.stringify(behaviorData)
        });

        if (response.ok) {
            closeModal();
            loadBehaviors();
            showNotification('Comportamiento guardado exitosamente', 'success');
        } else {
            const errorData = await response.json();
            throw new Error(errorData.message || 'Error al guardar el comportamiento');
        }
    } catch (error) {
        console.error('Error:', error);
        showNotification(error.message, 'error');
    }
}

// Sistema de notificaciones
function showNotification(message, type = 'success') {
    const notificationContainer = document.createElement('div');
    notificationContainer.className = `fixed top-4 right-4 z-50 max-w-md glass-effect p-4 rounded-lg shadow-lg transform transition-transform duration-300 ${
        type === 'success' ? 'bg-green-50' : 'bg-red-50'
    }`;

    notificationContainer.innerHTML = `
        <div class="flex items-center">
            <div class="flex-shrink-0">
                <i class="fas ${type === 'success' ? 'fa-check-circle text-green-400' : 'fa-exclamation-circle text-red-400'}"></i>
            </div>
            <div class="ml-3">
                <p class="text-sm font-medium ${
                    type === 'success' ? 'text-green-800' : 'text-red-800'
                }">${message}</p>
            </div>
            <div class="ml-auto pl-3">
                <button class="inline-flex text-gray-400 hover:text-gray-500 focus:outline-none">
                    <i class="fas fa-times"></i>
                </button>
            </div>
        </div>
    `;

    document.body.appendChild(notificationContainer);

    // Efecto de entrada
    requestAnimationFrame(() => {
        notificationContainer.style.transform = 'translateX(0)';
    });

    // Cierre automático
    setTimeout(() => {
        notificationContainer.style.transform = 'translateX(100%)';
        setTimeout(() => {
            document.body.removeChild(notificationContainer);
        }, 300);
    }, 3000);

    // Cierre manual
    const closeButton = notificationContainer.querySelector('button');
    closeButton.addEventListener('click', () => {
        notificationContainer.style.transform = 'translateX(100%)';
        setTimeout(() => {
            document.body.removeChild(notificationContainer);
        }, 300);
    });
}

// Función de eliminación
async function deleteBehavior(behaviorId) {
    if (!confirm('¿Está seguro de eliminar este registro de comportamiento?')) {
        return;
    }

    try {
        const response = await fetch(`${apiEndpoints.behavior}${behaviorId}/`, {
            method: 'DELETE',
            headers: {
                'X-CSRFToken': csrfToken
            }
        });

        if (response.ok) {
            loadBehaviors();
            showNotification('Comportamiento eliminado exitosamente', 'success');
        } else {
            throw new Error('Error al eliminar el comportamiento');
        }
    } catch (error) {
        console.error('Error:', error);
        showNotification('Error al eliminar el comportamiento', 'error');
    }
}

// Exportar funciones necesarias para uso global
window.openModal = openModal;
window.deleteBehavior = deleteBehavior;