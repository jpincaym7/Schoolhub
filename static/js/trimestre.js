// Utility functions
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

const formatGrade = (value) => {
    const grade = parseFloat(value);
    return isNaN(grade) ? 0 : Math.min(Math.max(grade, 0), 10);
};

// DOM Elements
const periodoSelect = document.getElementById('periodoSelect');
const materiaSelect = document.getElementById('materiaSelect');
const trimestreSelect = document.getElementById('trimestreSelect');
const examsTableBody = document.getElementById('examsTableBody');
const saveExamsBtn = document.getElementById('saveExams');

// Event Listeners
document.addEventListener('DOMContentLoaded', () => {
    setupEventListeners();
    loadPromedios();
});

function setupEventListeners() {
    // Filter change events
    periodoSelect.addEventListener('change', loadPromedios);
    materiaSelect.addEventListener('change', loadPromedios);
    trimestreSelect.addEventListener('change', loadPromedios);
    
    // Save exams
    saveExamsBtn.addEventListener('click', saveExamenes);

    // Grade input events
    examsTableBody.addEventListener('input', (e) => {
        if (e.target.matches('input[type="number"]')) {
            const row = e.target.closest('tr');
            calculatePreviewAverage(row);
        }
    });
}

function calculatePreviewAverage(row) {
    // Obtener los valores de los promedios parciales
    const promedio_p1 = parseFloat(row.querySelector('.promedio-p1').textContent) || 0;
    const promedio_p2 = parseFloat(row.querySelector('.promedio-p2').textContent) || 0;
    const examenTrimestral = parseFloat(row.querySelector('.examen-trimestral').value) || 0;
    const proyectoTrimestral = parseFloat(row.querySelector('.proyecto-trimestral').value) || 0;
    
    // Calcular usando los porcentajes actualizados:
    // 30% P1 + 30% P2 + 20% Examen trimestral + 20% Proyecto trimestral
    const promedioFinal = (
        (promedio_p1 * 0.30) + 
        (promedio_p2 * 0.30) + 
        (examenTrimestral * 0.20) +
        (proyectoTrimestral * 0.20)
    ).toFixed(2);
    
    // Actualizar la UI
    const finalCell = row.querySelector('.promedio-final');
    if (finalCell.textContent !== promedioFinal) {
        finalCell.textContent = promedioFinal;
        finalCell.classList.add('bg-yellow-100');
        setTimeout(() => finalCell.classList.remove('bg-yellow-100'), 1000);
    }
}

async function loadPromedios() {
    const periodo = periodoSelect.value;
    const materia = materiaSelect.value;
    const trimestre = trimestreSelect.value;

    if (!periodo || !materia || !trimestre) return;

    try {
        const response = await fetch(`/students/promedios-trimestre/?periodo=${periodo}&materia=${materia}&trimestre=${trimestre}`);
        const data = await response.json();
        renderExamsTable(data);
    } catch (error) {
        console.error('Error loading promedios:', error);
        showNotification('Error al cargar los promedios', 'error');
    }
}

function renderExamsTable(data) {
    examsTableBody.innerHTML = data.map(promedio => {
        const promedio_p1 = parseFloat(promedio.promedio_p1) || 0;
        const promedio_p2 = parseFloat(promedio.promedio_p2) || 0;

        return `
        <tr data-promedio-id="${promedio.id}">
            <td class="px-6 py-4 whitespace-nowrap">
                <div class="text-sm font-medium text-gray-900">
                    ${promedio.estudiante}
                </div>
            </td>
            <td class="px-6 py-4 whitespace-nowrap">
                <div class="grid grid-cols-2 gap-4">
                    <div>
                        <span class="text-xs text-gray-500">P1:</span>
                        <span class="text-sm font-medium ml-1 promedio-p1">${promedio_p1.toFixed(2)}</span>
                    </div>
                    <div>
                        <span class="text-xs text-gray-500">P2:</span>
                        <span class="text-sm font-medium ml-1 promedio-p2">${promedio_p2.toFixed(2)}</span>
                    </div>
                </div>
            </td>
            <td class="px-6 py-4 whitespace-nowrap text-sm">
                ${((promedio_p1 * 0.30 + promedio_p2 * 0.30) * (10/6)).toFixed(2)}
            </td>
            <td class="px-6 py-4 whitespace-nowrap">
                <input type="number" 
                       class="w-20 rounded-md border-gray-300 examen-trimestral" 
                       value="${promedio.examen_trimestral || 0}" 
                       min="0" 
                       max="10" 
                       step="0.01">
            </td>
            <td class="px-6 py-4 whitespace-nowrap">
                <input type="number" 
                       class="w-20 rounded-md border-gray-300 proyecto-trimestral" 
                       value="${promedio.proyecto_trimestral || 0}" 
                       min="0" 
                       max="10" 
                       step="0.01">
            </td>
            <td class="px-6 py-4 whitespace-nowrap text-sm font-medium promedio-final transition-all duration-300">
                ${promedio.promedio_final || '0.00'}
            </td>
        </tr>
    `}).join('');

    // Calcular promedios iniciales
    document.querySelectorAll('#examsTableBody tr').forEach(calculatePreviewAverage);
}

async function saveExamenes() {
    const examenes = [];
    const rows = document.querySelectorAll('#examsTableBody tr');
    
    // Create loading overlay
    const loadingOverlay = document.createElement('div');
    loadingOverlay.className = 'fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50';
    loadingOverlay.innerHTML = `
        <div class="bg-white p-4 rounded-md">
            <p class="text-gray-800">Guardando calificaciones trimestrales...</p>
        </div>
    `;
    document.body.appendChild(loadingOverlay);
    
    try {
        // Collect data
        rows.forEach(row => {
            examenes.push({
                promedio_id: row.dataset.promedioId,
                examen_trimestral: formatGrade(row.querySelector('.examen-trimestral').value),
                proyecto_trimestral: formatGrade(row.querySelector('.proyecto-trimestral').value)
            });
        });

        // Send request
        const response = await fetch('/students/examenes-trimestrales/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCSRFToken(),
            },
            body: JSON.stringify(examenes)
        });

        const data = await response.json();
        
        if (response.ok) {
            showNotification('Calificaciones guardadas exitosamente');
            
            // Update final averages with animation
            if (data.promedios) {
                data.promedios.forEach(promedio => {
                    const row = document.querySelector(`tr[data-promedio-id="${promedio.id}"]`);
                    if (row) {
                        const finalCell = row.querySelector('.promedio-final');
                        if (finalCell) {
                            finalCell.classList.add('bg-green-100');
                            finalCell.textContent = promedio.promedio_final.toFixed(2);
                            
                            setTimeout(() => {
                                finalCell.classList.remove('bg-green-100');
                            }, 1000);
                        }
                    }
                });
            }
            
            await loadPromedios();
            
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