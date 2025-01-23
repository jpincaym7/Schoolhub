const API_URL = '/subjects/horarios-atencion/';
const DateTime = luxon.DateTime;

// State
let currentHorarios = [];

// DOM Elements
const horarioModal = document.getElementById('horario-modal');
const horarioForm = document.getElementById('horario-form');
const notification = document.getElementById('notification');
const diaFilter = document.getElementById('dia-filter');

// Initialize
document.addEventListener('DOMContentLoaded', async () => {
    await loadHorarios();
    setupEventListeners();
});

// Event Listeners
function setupEventListeners() {
    horarioForm.addEventListener('submit', handleHorarioSubmit);
    diaFilter.addEventListener('change', loadHorarios);
}


async function loadHorarios() {
    const dia = diaFilter.value;
    
    let url = API_URL;
    const params = new URLSearchParams();
    if (dia) params.append('dia', dia);
    
    try {
        const response = await fetch(`${url}?${params}`);
        const data = await response.json();
        console.log(data)
        currentHorarios = data.results || [];
        renderHorariosTable();
    } catch (error) {
        showNotification('Error al cargar horarios', 'error');
    }
}

async function saveHorario(horarioData) {
    const isEdit = !!horarioData.id;
    const url = isEdit ? `${API_URL}${horarioData.id}/` : API_URL;
    const method = isEdit ? 'PUT' : 'POST';

    try {
        const response = await fetch(url, {
            method,
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken')
            },
            body: JSON.stringify(horarioData)
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Error al guardar el horario');
        }

        await loadHorarios();
        closeModal();
        showNotification(
            isEdit ? 'Horario actualizado exitosamente' : 'Horario creado exitosamente',
            'success'
        );
    } catch (error) {
        showNotification(error.message, 'error');
    }
}

async function deleteHorario(id) {
    if (!confirm('¿Está seguro de eliminar este horario?')) return;

    try {
        const response = await fetch(`${API_URL}${id}/`, {
            method: 'DELETE',
            headers: {
                'X-CSRFToken': getCookie('csrftoken')
            }
        });

        if (!response.ok) {
            throw new Error('Error al eliminar el horario');
        }

        await loadHorarios();
        showNotification('Horario eliminado exitosamente', 'success');
    } catch (error) {
        showNotification(error.message, 'error');
    }
}

// UI Functions
function populateProfesorSelects() {
    const profesorSelect = document.getElementById('profesor-select');
    const filterSelect = document.getElementById('profesor-filter');
    
    const options = profesores.map(profesor => 
        `<option value="${profesor.id}">${profesor.nombre}</option>`
    );
    
    profesorSelect.innerHTML = options.join('');
    filterSelect.innerHTML = '<option value="">Todos los profesores</option>' + options.join('');
}

function renderHorariosTable() {
    const tbody = document.getElementById('horarios-table-body');
    tbody.innerHTML = currentHorarios.map(horario => `
        <tr>
            <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">${horario.dia_display}</td>
            <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                ${DateTime.fromISO(horario.hora_inicio).toFormat('HH:mm')}
            </td>
            <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                ${DateTime.fromISO(horario.hora_fin).toFormat('HH:mm')}
            </td>
            <td class="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                <button onclick="editHorario(${horario.id})" 
                        class="text-indigo-600 hover:text-indigo-900 mr-2">
                    Editar
                </button>
                <button onclick="deleteHorario(${horario.id})" 
                        class="text-red-600 hover:text-red-900">
                    Eliminar
                </button>
            </td>
        </tr>
    `).join('');
}


function openNewHorarioModal() {
    document.getElementById('modal-title').textContent = 'Nuevo Horario de Atención';
    document.getElementById('horario-id').value = '';
    horarioForm.reset();
    horarioModal.classList.remove('hidden');
}


function editHorario(id) {
    const horario = currentHorarios.find(h => h.id === id);
    if (!horario) return;

    document.getElementById('modal-title').textContent = 'Editar Horario de Atención';
    document.getElementById('horario-id').value = horario.id;
    document.getElementById('dia-select').value = horario.dia;
    document.getElementById('hora-inicio').value = DateTime.fromISO(horario.hora_inicio).toFormat('HH:mm');
    document.getElementById('hora-fin').value = DateTime.fromISO(horario.hora_fin).toFormat('HH:mm');
    
    horarioModal.classList.remove('hidden');
}

function closeModal() {
    horarioModal.classList.add('hidden');
    horarioForm.reset();
}

async function handleHorarioSubmit(event) {
    event.preventDefault();
    
    if (!validateForm()) {
        return;
    }
    
    const horarioData = {
        id: document.getElementById('horario-id').value,
        dia: document.getElementById('dia-select').value,
        hora_inicio: document.getElementById('hora-inicio').value,
        hora_fin: document.getElementById('hora-fin').value
    };

    await saveHorario(horarioData);
}

function showNotification(message, type = 'success') {
    const notification = document.querySelector('.notification');
    const notificationMessage = document.getElementById('notification-message');
    const notificationIcon = document.getElementById('notification-icon');
    
    // Reset classes
    notification.classList.remove('success', 'error');
    notificationIcon.classList.remove('fa-check-circle', 'fa-exclamation-circle', 'text-green-500', 'text-red-500');
    
    // Set type-specific styles
    if (type === 'error') {
        notification.classList.add('error');
        notificationIcon.classList.add('fa-exclamation-circle', 'text-red-500');
    } else {
        notification.classList.add('success');
        notificationIcon.classList.add('fa-check-circle', 'text-green-500');
    }
    
    // Set message and show notification
    notificationMessage.textContent = message;
    notification.classList.add('show');
    
    // Auto-hide after 3 seconds
    setTimeout(closeNotification, 3000);
}

function closeNotification() {
    const notification = document.querySelector('.notification');
    notification.classList.remove('show');
}

function validateForm() {
    const form = document.getElementById('horario-form');
    const controls = form.querySelectorAll('.form-control');
    let isValid = true;
    
    controls.forEach(control => {
        if (control.hasAttribute('required') && !control.value) {
            markInvalid(control);
            isValid = false;
        } else {
            markValid(control);
        }
    });
    
    // Validate time range
    const horaInicio = document.getElementById('hora-inicio');
    const horaFin = document.getElementById('hora-fin');
    
    if (horaInicio.value && horaFin.value) {
        if (horaInicio.value >= horaFin.value) {
            markInvalid(horaFin, 'La hora de fin debe ser posterior a la hora de inicio');
            isValid = false;
        }
    }
    
    return isValid;
}

function markInvalid(element, message) {
    element.classList.add('is-invalid');
    const feedback = element.nextElementSibling.classList.contains('invalid-feedback') 
        ? element.nextElementSibling 
        : element.parentElement.querySelector('.invalid-feedback');
    if (feedback && message) {
        feedback.textContent = message;
    }
}

function markValid(element) {
    element.classList.remove('is-invalid');
}

// Utility Functions
function getCookie(name) {
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

document.querySelectorAll('input[type="time"]').forEach(input => {
    input.addEventListener('change', function() {
        const time = this.value;
        const [hours, minutes] = time.split(':').map(Number);
        const totalMinutes = hours * 60 + minutes;
        
        if (totalMinutes < 13 * 60 + 30 || totalMinutes > 18 * 60) {
            markInvalid(this, 'El horario debe estar entre 1:30 PM y 6:00 PM');
            this.value = '';
        } else {
            markValid(this);
        }
    });
});

// Real-time validation
document.querySelectorAll('.form-control').forEach(control => {
    control.addEventListener('input', function() {
        if (this.value) {
            markValid(this);
        }
    });
});