// Toast Utility Class
class ToastManager {
    static show(message, type = 'success') {
        const toast = document.createElement('div');
        toast.className = `fixed bottom-4 right-4 px-6 py-3 rounded-lg shadow-lg ${
            type === 'success' ? 'bg-green-600' : 'bg-red-600'
        } text-white z-50`;
        toast.textContent = message;
        document.body.appendChild(toast);
        setTimeout(() => toast.remove(), 3000);
    }
}

// Activities Manager Class
class ActivitiesManager {
    constructor(subjectId) {
        this.subjectId = subjectId;
        this.activitiesList = document.getElementById('activitiesList');
        this.init();
    }

    init() {
        this.setupParcialTabs();
        this.loadActivities(1);
    }

    setupParcialTabs() {
        const tabContainer = document.querySelector('.parcial-tabs');
        if (!tabContainer) return;

        tabContainer.addEventListener('click', (e) => {
            const tab = e.target.closest('.parcial-tab');
            if (!tab) return;

            document.querySelectorAll('.parcial-tab').forEach(t => {
                t.classList.remove('text-blue-600', 'border-b-2', 'border-blue-600');
            });
            tab.classList.add('text-blue-600', 'border-b-2', 'border-blue-600');
            this.loadActivities(tab.dataset.parcial);
        });
    }

    async loadActivities(parcial) {
        try {
            const response = await fetch(`/subjects/activities/?subject=${this.subjectId}&partial=${parcial}`);
            if (!response.ok) throw new Error('Network response was not ok');
            
            const data = await response.json();
            console.log(data)
            this.renderActivities(data);
        } catch (error) {
            ToastManager.show('Error al cargar actividades', 'error');
        }
    }

    renderActivities(activities) {
        if (!this.activitiesList) return;

        this.activitiesList.innerHTML = activities.map(activity => this.getActivityTemplate(activity)).join('');
    }

    getActivityTemplate(activity) {
        return `
            <div class="bg-white p-4 rounded-lg shadow-sm hover:shadow-md transition border border-gray-200">
                <div class="flex justify-between items-center">
                    <div>
                        <h3 class="text-lg font-medium text-gray-900">${activity.name}</h3>
                        <p class="text-sm text-gray-500">${activity.description}</p>
                    </div>
                    <a href="/subjects/activities/${activity.id}/grades" 
                       class="bg-blue-100 text-blue-700 px-4 py-2 rounded-lg hover:bg-blue-200 transition">
                        <i class="fas fa-edit mr-2"></i>Calificar
                    </a>
                </div>
            </div>
        `;
    }
}

// Grades Manager Class
class GradesManager {
    constructor(activityId) {
        this.activityId = activityId;
        this.tbody = document.getElementById('gradesTableBody');
        this.init();
    }

    init() {
        this.setupEventListeners();
        this.loadGrades();
    }

    setupEventListeners() {
        // Event delegation for grade inputs and save buttons
        if (this.tbody) {
            this.tbody.addEventListener('click', (e) => {
                const saveBtn = e.target.closest('.save-grade');
                if (saveBtn) {
                    const studentId = saveBtn.dataset.studentId;
                    const input = document.querySelector(`input[data-student-id="${studentId}"]`);
                    this.saveGrade(studentId, input.value);
                }
            });

            this.tbody.addEventListener('change', (e) => {
                const input = e.target.closest('.grade-input');
                if (input) {
                    this.validateGradeInput(input);
                }
            });
        }

        // Bulk save handler
        const saveAllBtn = document.getElementById('saveAllBtn');
        if (saveAllBtn) {
            saveAllBtn.addEventListener('click', () => this.saveAllGrades());
        }
    }

    validateGradeInput(input) {
        const value = parseFloat(input.value);
        if (isNaN(value) || value < 0 || value > 10) {
            input.classList.add('border-red-500');
            return false;
        }
        input.classList.remove('border-red-500');
        return true;
    }

    async loadGrades() {
        try {
            const response = await fetch(`/subjects/activities/?template=${this.activityId}`);
            if (!response.ok) throw new Error('Network response was not ok');
            
            const data = await response.json();
            // Now we expect the grades to be in the results array
            const gradesArray = data.results;
            this.renderGrades(gradesArray);
        } catch (error) {
            console.error('Error loading grades:', error);
            ToastManager.show('Error al cargar calificaciones', 'error');
        }
    }
    
    renderGrades(grades) {
        if (!this.tbody) return;
        
        this.tbody.innerHTML = grades.map(grade => this.getGradeRowTemplate(grade)).join('');
    }
    
    getGradeRowTemplate(grade) {
        const studentDetails = grade.student_details;
        return `
            <tr class="hover:bg-gray-50">
                <td class="px-6 py-4 whitespace-nowrap">
                    <div class="flex items-center">
                        <img class="h-8 w-8 rounded-full" 
                             src="${studentDetails?.photo || '/static/img/default.jpg'}" 
                             alt="${studentDetails?.full_name || 'Usuario'}">
                        <div class="ml-4">
                            <div class="text-sm font-medium text-gray-900">
                                ${studentDetails?.full_name || 'Usuario sin nombre'}
                            </div>
                        </div>
                    </div>
                </td>
                <td class="px-6 py-4 whitespace-nowrap">
                    <span class="text-sm text-gray-900">
                        ${studentDetails?.parallel?.name || '-'}
                    </span>
                </td>
                <td class="px-6 py-4 whitespace-nowrap text-center">
                    <input type="number" 
                           min="0" 
                           max="10" 
                           step="0.1" 
                           class="grade-input w-20 text-center rounded border-gray-300"
                           value="${grade.score || '0.00'}" 
                           data-student-id="${studentDetails?.id || ''}">
                </td>
                <td class="px-6 py-4 whitespace-nowrap text-center">
                    <button class="save-grade text-green-600 hover:text-green-700"
                            data-student-id="${studentDetails?.id || ''}">
                        <i class="fas fa-check"></i>
                    </button>
                </td>
            </tr>
        `;
    }

    async saveGrade(studentId, score) {
        try {
            const response = await fetch(`/subjects/activities/${this.activityId}/`, {
                method: 'PATCH',
                headers: this.getHeaders(),
                body: JSON.stringify({
                    student_id: studentId,
                    score: parseFloat(score)
                })
            });
            
            if (!response.ok) throw new Error('Network response was not ok');
            ToastManager.show('Calificación guardada exitosamente');
        } catch (error) {
            ToastManager.show('Error al guardar calificación', 'error');
        }
    }

    async saveAllGrades() {
        try {
            const scores = Array.from(document.querySelectorAll('.grade-input'))
                .filter(input => this.validateGradeInput(input))
                .map(input => ({
                    student_id: parseInt(input.dataset.studentId),
                    score: parseFloat(input.value)
                }));

            if (scores.length === 0) {
                throw new Error('No hay calificaciones válidas para guardar');
            }

            const templateId = parseInt(this.activityId);
            if (isNaN(templateId)) {
                throw new Error('ID de plantilla de actividad inválido');
            }

            const payload = {
                template_id: templateId,
                scores: scores
            };

            console.log('Enviando datos:', payload); // Para debugging

            const response = await fetch('/subjects/activities/bulk_update_scores/', {
                method: 'POST',
                headers: this.getHeaders(),
                body: JSON.stringify(payload)
            });

            const data = await response.json();

            if (!response.ok) {
                const errorMessage = data.error || 
                                   (Array.isArray(data) ? data[0]?.student_id?.[0] : null) || 
                                   data.detail || 
                                   'Error al guardar calificaciones';
                throw new Error(errorMessage);
            }

            ToastManager.show('Calificaciones guardadas exitosamente');
            await this.loadGrades();
        } catch (error) {
            console.error('Error completo:', error);
            ToastManager.show(error.message, 'error');
        }
    }

    getHeaders() {
        return {
            'Content-Type': 'application/json',
            'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
        };
    }
}

// Initialize the appropriate manager based on the current page
document.addEventListener('DOMContentLoaded', () => {
    const activitiesList = document.getElementById('activitiesList');
    const gradesTable = document.getElementById('gradesTableBody');
    
    if (activitiesList) {
        new ActivitiesManager(window.subjectId);
    }
    
    if (gradesTable) {
        new GradesManager(window.activityId);
    }
});