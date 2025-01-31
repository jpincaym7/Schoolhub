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
    // Get all task grades
    const tasks = [
        parseFloat(row.querySelector('[data-task="1"]').value) || 0,
        parseFloat(row.querySelector('[data-task="2"]').value) || 0,
        parseFloat(row.querySelector('[data-task="3"]').value) || 0,
        parseFloat(row.querySelector('[data-task="4"]').value) || 0
    ];
    
    // Get exam grade
    const exam = parseFloat(row.querySelector('[data-exam]').value) || 0;
    
    // Calculate tasks average (70%)
    const tasksAverage = tasks.reduce((a, b) => a + b, 0) / 4 * 0.70;
    
    // Calculate exam contribution (30%)
    const examScore = exam * 0.30;
    
    // Calculate and round final average to 2 decimal places
    return (tasksAverage + examScore).toFixed(2);
};


// DOM Elements
const periodoSelect = document.getElementById('periodoSelect');
const trimestreSelect = document.getElementById('trimestreSelect');
const materiaSelect = document.getElementById('materiaSelect');
const parcialSelect = document.getElementById('parcialSelect');
const gradesTableBody = document.getElementById('gradesTableBody');
const importExcelBtn = document.getElementById('importExcel');
const importModal = document.getElementById('importModal');
const closeModalBtn = document.getElementById('closeModal');
const importForm = document.getElementById('importForm');
const saveGradesBtn = document.getElementById('saveGrades');

// Event Listeners
document.addEventListener('DOMContentLoaded', () => {
    loadStudents();
    setupEventListeners();
});

function setupEventListeners() {
    // Filter change events
    periodoSelect.addEventListener('change', loadStudents);
    trimestreSelect.addEventListener('change', loadStudents);
    materiaSelect.addEventListener('change', loadStudents);
    parcialSelect.addEventListener('change', loadStudents);

    // Modal events
    importExcelBtn.addEventListener('click', () => importModal.classList.remove('hidden'));
    closeModalBtn.addEventListener('click', () => importModal.classList.add('hidden'));
    
    // Import form submission
    importForm.addEventListener('submit', handleImportSubmit);
    
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
    const trimestre = trimestreSelect.value;
    const materia = materiaSelect.value;
    const parcial = parcialSelect.value;

    if (!periodo || !trimestre || !materia || !parcial) return;

    try {
        const response = await fetch(`/subjects/request/calificaciones/?periodo=${periodo}&trimestre=${trimestre}&materia=${materia}&parcial=${parcial}`);
        const data = await response.json();
        console.log(data)
        renderGradesTable(data);
    } catch (error) {
        console.error('Error loading students:', error);
        showNotification('Error al cargar los estudiantes', 'error');
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
                    value="${student.tarea1 || 0}" min="0" max="10" step="0.01">
            </td>
            <td class="px-6 py-4 whitespace-nowrap">
                <input type="number" data-task="2" class="w-20 rounded-md border-gray-300" 
                    value="${student.tarea2 || 0}" min="0" max="10" step="0.01">
            </td>
            <td class="px-6 py-4 whitespace-nowrap">
                <input type="number" data-task="3" class="w-20 rounded-md border-gray-300" 
                    value="${student.tarea3 || 0}" min="0" max="10" step="0.01">
            </td>
            <td class="px-6 py-4 whitespace-nowrap">
                <input type="number" data-task="4" class="w-20 rounded-md border-gray-300" 
                    value="${student.tarea4 || 0}" min="0" max="10" step="0.01">
            </td>
            <td class="px-6 py-4 whitespace-nowrap">
                <input type="number" data-exam class="w-20 rounded-md border-gray-300" 
                    value="${student.examen || 0}" min="0" max="10" step="0.01">
            </td>
            <td class="px-6 py-4 whitespace-nowrap text-sm font-medium average-cell">
                ${student.promedio_final || '0.00'}
            </td>
        </tr>
    `).join('');
}

async function handleImportSubmit(e) {
    e.preventDefault();
    
    const formData = new FormData();
    const fileInput = document.getElementById('excelFile');
    const file = fileInput.files[0];
    
    if (!file) {
        showNotification('Por favor seleccione un archivo', 'error');
        return;
    }
    
    formData.append('file', file);
    formData.append('trimestre', trimestreSelect.value);
    formData.append('parcial', parcialSelect.value);
    
    try {
        const response = await fetch('/subjects/request/calificaciones/excel/', {
            method: 'POST',
            headers: {
                'X-CSRFToken': getCSRFToken(),
            },
            body: formData
        });
        
        const data = await response.json();
        
        if (response.ok) {
            showNotification('Archivo importado exitosamente');
            importModal.classList.add('hidden');
            loadStudents(); // Reload the table
        } else {
            throw new Error(data.error || 'Error al importar el archivo');
        }
    } catch (error) {
        console.error('Error:', error);
        showNotification(error.message || 'Error al importar el archivo', 'error');
    }
}

async function saveGrades() {
    const grades = [];
    const rows = document.querySelectorAll('#gradesTableBody tr');
    
    // Create loading overlay
    const loadingOverlay = document.createElement('div');
    loadingOverlay.className = 'fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50';
    loadingOverlay.innerHTML = `
        <div class="bg-white p-4 rounded-md">
            <p class="text-gray-800">Guardando calificaciones...</p>
        </div>
    `;
    document.body.appendChild(loadingOverlay);
    
    try {
        // Collect data
        rows.forEach(row => {
            const gradeData = {
                student_id: row.dataset.studentId,
                tarea1: formatGrade(row.querySelector('[data-task="1"]').value),
                tarea2: formatGrade(row.querySelector('[data-task="2"]').value),
                tarea3: formatGrade(row.querySelector('[data-task="3"]').value),
                tarea4: formatGrade(row.querySelector('[data-task="4"]').value),
                examen: formatGrade(row.querySelector('[data-exam]').value),
                parcial: parcialSelect.value,
                trimestre: trimestreSelect.value
            };
            grades.push(gradeData);
        });

        // Send request
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
            // Update averages if provided
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
        loadingOverlay.remove();
    }
}

// Initialize tooltips if using them
document.addEventListener('DOMContentLoaded', () => {
    const saveButton = document.getElementById('saveGrades');
    if (saveButton) {
        saveButton.addEventListener('click', saveGrades);
    }
});