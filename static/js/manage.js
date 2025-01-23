// Utility functions
const formatGrade = (value) => {
    const grade = parseFloat(value);
    return isNaN(grade) ? 0 : Math.min(Math.max(grade, 0), 10);
};

function getCSRFToken() {
    const name = 'csrftoken';
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

function showNotification(message, type = 'success') {
    const notification = document.createElement('div');
    notification.className = `fixed top-4 right-4 px-6 py-3 rounded-md ${
        type === 'success' ? 'bg-green-500' : 'bg-red-500'
    } text-white z-50`;
    notification.textContent = message;
    document.body.appendChild(notification);
    setTimeout(() => notification.remove(), 3000);
}


const calculateAverage = (row) => {
    const tasks = [
        parseFloat(row.querySelector('[data-task="1"]').value),
        parseFloat(row.querySelector('[data-task="2"]').value),
        parseFloat(row.querySelector('[data-task="3"]').value),
        parseFloat(row.querySelector('[data-task="4"]').value)
    ];
    const exam = parseFloat(row.querySelector('[data-exam]').value);
    
    const tasksAverage = tasks.reduce((a, b) => a + b, 0) / 4 * 0.8;
    const examScore = exam * 0.2;
    
    return (tasksAverage + examScore).toFixed(2);
};

// DOM Elements
const periodoSelect = document.getElementById('periodoSelect');
const materiaSelect = document.getElementById('materiaSelect');
const parcialSelect = document.getElementById('parcialSelect');
const gradesTableBody = document.getElementById('gradesTableBody');
const importExcelBtn = document.getElementById('importExcel');
const importModal = document.getElementById('importModal');
const closeModalBtn = document.getElementById('closeModal');
const processExcelBtn = document.getElementById('processExcel');
const saveGradesBtn = document.getElementById('saveGrades');

// Event Listeners
document.addEventListener('DOMContentLoaded', () => {
    loadStudents();
    setupEventListeners();
});

function setupEventListeners() {
    // Filter change events
    periodoSelect.addEventListener('change', loadStudents);
    materiaSelect.addEventListener('change', loadStudents);
    parcialSelect.addEventListener('change', loadStudents);

    // Modal events
    importExcelBtn.addEventListener('click', () => importModal.classList.remove('hidden'));
    closeModalBtn.addEventListener('click', () => importModal.classList.add('hidden'));
    
    // Save grades
    saveGradesBtn.addEventListener('click', saveGrades);

    // Grade input events
    gradesTableBody.addEventListener('input', (e) => {
        if (e.target.matches('input[type="number"]')) {
            const row = e.target.closest('tr');
            const averageCell = row.querySelector('.average-cell');
            averageCell.textContent = calculateAverage(row);
        }
    });
}

async function loadStudents() {
    const periodo = periodoSelect.value;
    const materia = materiaSelect.value;
    const parcial = parcialSelect.value;

    if (!periodo || !materia) return;

    try {
        const response = await fetch(`/subjects/request/calificaciones/?periodo=${periodo}&materia=${materia}&parcial=${parcial}`);
        const data = await response.json();
        renderGradesTable(data);
    } catch (error) {
        console.error('Error loading students:', error);
    }
}

function renderGradesTable(data) {
    gradesTableBody.innerHTML = data.map(student => `
        <tr data-student-id="${student.id}">
            <td class="px-6 py-4 whitespace-nowrap">
                <div class="text-sm font-medium text-gray-900">
                    ${student.nombre}
                </div>
            </td>
            <td class="px-6 py-4 whitespace-nowrap">
                <input type="number" data-task="1" class="w-20 rounded-md border-gray-300" 
                    value="${student.tarea1}" min="0" max="10" step="0.01">
            </td>
            <td class="px-6 py-4 whitespace-nowrap">
                <input type="number" data-task="2" class="w-20 rounded-md border-gray-300" 
                    value="${student.tarea2}" min="0" max="10" step="0.01">
            </td>
            <td class="px-6 py-4 whitespace-nowrap">
                <input type="number" data-task="3" class="w-20 rounded-md border-gray-300" 
                    value="${student.tarea3}" min="0" max="10" step="0.01">
            </td>
            <td class="px-6 py-4 whitespace-nowrap">
                <input type="number" data-task="4" class="w-20 rounded-md border-gray-300" 
                    value="${student.tarea4}" min="0" max="10" step="0.01">
            </td>
            <td class="px-6 py-4 whitespace-nowrap">
                <input type="number" data-exam class="w-20 rounded-md border-gray-300" 
                    value="${student.examen}" min="0" max="10" step="0.01">
            </td>
            <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900 average-cell">
                ${student.promedio_final}
            </td>
        </tr>
    `).join('');
}

async function saveGrades() {
    const grades = [];
    const rows = document.querySelectorAll('#gradesTableBody tr');
    
    // Mostrar indicador de carga
    const loadingOverlay = document.createElement('div');
    loadingOverlay.className = 'fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50';
    loadingOverlay.innerHTML = `
        <div class="bg-white p-4 rounded-md">
            <p class="text-gray-800">Guardando calificaciones...</p>
        </div>
    `;
    document.body.appendChild(loadingOverlay);
    
    try {
        // Recopilar datos
        rows.forEach(row => {
            grades.push({
                student_id: row.dataset.studentId,
                tarea1: parseFloat(row.querySelector('[data-task="1"]').value) || 0,
                tarea2: parseFloat(row.querySelector('[data-task="2"]').value) || 0,
                tarea3: parseFloat(row.querySelector('[data-task="3"]').value) || 0,
                tarea4: parseFloat(row.querySelector('[data-task="4"]').value) || 0,
                examen: parseFloat(row.querySelector('[data-exam]').value) || 0,
                parcial: document.getElementById('parcialSelect').value
            });
        });

        // Realizar la petición
        const response = await fetch('/subjects/request/calificaciones/bulk/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCSRFToken(),
            },
            body: JSON.stringify(grades),
            credentials: 'include'
        });

        const data = await response.json();

        if (response.ok) {
            showNotification('Calificaciones guardadas exitosamente');
            // Actualizar promedios si es necesario
            if (data.grades) {
                data.grades.forEach(grade => {
                    const row = document.querySelector(`tr[data-student-id="${grade.id}"]`);
                    if (row) {
                        const averageCell = row.querySelector('.average-cell');
                        if (averageCell) {
                            averageCell.textContent = grade.promedio_final;
                        }
                    }
                });
            }
        } else {
            throw new Error(data.error || 'Error al guardar las calificaciones');
        }
    } catch (error) {
        console.error('Error:', error);
        showNotification(error.message || 'Error al guardar las calificaciones', 'error');
    } finally {
        // Eliminar indicador de carga
        loadingOverlay.remove();
    }
}

// Asegurarse de que el botón de guardar tenga el evento correcto
document.addEventListener('DOMContentLoaded', () => {
    const saveButton = document.getElementById('saveGrades');
    if (saveButton) {
        saveButton.addEventListener('click', saveGrades);
    }
});