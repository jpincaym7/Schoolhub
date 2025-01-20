const state = {
    activeFilters: {
        academicPeriod: '',
        subject: '',
        partial: '',
        scoreStatus: '',
        search: ''
    }
};

document.addEventListener('DOMContentLoaded', function() {
    // Check if the main app container exists
    const appContainer = document.getElementById('gradesApp');
    if (!appContainer) {
        console.error('Main app container not found');
        return;
    }

    // Initialize the application
    initializeApp();
});

function initializeApp() {
    // Initialize all components
    initializeFilters();
    initializeSearch();
    initializeCreateActivity();
    initializeFormSubmissions();
    
    // Load initial data
    loadActivities();
}

function initializeFilters() {
    const filterIds = ['academicPeriod', 'subject', 'partial', 'scoreStatus'];
    
    filterIds.forEach(filterId => {
        const element = document.getElementById(filterId);
        if (element) {
            element.addEventListener('change', function() {
                state.activeFilters[filterId] = this.value;
                updateActiveFiltersDisplay();
                loadActivities();
            });
        } else {
            console.warn(`Filter element ${filterId} not found`);
        }
    });
}

function initializeSearch() {
    const searchInput = document.getElementById('searchInput');
    if (!searchInput) {
        console.warn('Search input not found');
        return;
    }

    let debounceTimeout;
    searchInput.addEventListener('input', function() {
        clearTimeout(debounceTimeout);
        debounceTimeout = setTimeout(() => {
            state.activeFilters.search = this.value;
            updateActiveFiltersDisplay();
            loadActivities();
        }, 300);
    });
}

function initializeCreateActivity() {
    const createButton = document.getElementById('createActivity');
    if (createButton) {
        createButton.addEventListener('click', () => openModal('createActivityModal'));
    }
}

function initializeFormSubmissions() {
    const createForm = document.getElementById('createActivityForm');
    const editForm = document.getElementById('editScoreForm');

    if (createForm) {
        createForm.addEventListener('submit', handleCreateActivity);
    }
    if (editForm) {
        editForm.addEventListener('submit', handleEditScore);
    }
}

function updateActiveFiltersDisplay() {
    const activeFiltersDiv = document.getElementById('activeFilters');
    if (!activeFiltersDiv) {
        console.warn('Active filters container not found');
        return;
    }

    activeFiltersDiv.innerHTML = '';
    
    Object.entries(state.activeFilters).forEach(([key, value]) => {
        if (value) {
            const filterTag = createFilterTag(key, value);
            activeFiltersDiv.appendChild(filterTag);
        }
    });
}

function createFilterTag(key, value) {
    const filterTag = document.createElement('div');
    filterTag.className = 'inline-flex items-center px-3 py-1 rounded-full text-sm bg-indigo-100 text-indigo-700';
    
    const filterText = getFilterDisplayText(key, value);
    
    filterTag.innerHTML = `
        ${filterText}
        <button class="ml-2 focus:outline-none" onclick="removeFilter('${key}')">
            <svg class="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/>
            </svg>
        </button>
    `;
    return filterTag;
}

function getFilterDisplayText(key, value) {
    const select = document.getElementById(key);
    if (select && select.options) {
        const option = Array.from(select.options).find(opt => opt.value === value);
        return option ? option.text : value;
    }
    return value;
}

function removeFilter(filterKey) {
    const element = document.getElementById(filterKey);
    if (element) {
        element.value = '';
    }
    state.activeFilters[filterKey] = '';
    updateActiveFiltersDisplay();
    loadActivities();
}

function loadActivities() {
    const params = new URLSearchParams();
    Object.entries(state.activeFilters).forEach(([key, value]) => {
        if (value) params.append(key, value);
    });

    fetch(`/subjects/activities/?${params.toString()}`)
        .then(response => response.json())
        .then(data => {
            console.log(data)
            updateActivityStats(data.statistics || {});
            updateActivityTable(data.results || []);
            if (data.pagination) {
                updatePagination(data.pagination);
            }
        })
        .catch(error => {
            console.error('Error:', error);
            showNotification('Error al cargar las actividades', 'error');
        });
}

function updateActivityStats(statistics) {
    const stats = {
        totalActivities: statistics.total || 0,
        pendingActivities: statistics.pending || 0,
        gradedActivities: statistics.graded || 0,
        averageScore: statistics.average ? statistics.average.toFixed(2) : '0.00'
    };

    Object.entries(stats).forEach(([id, value]) => {
        const element = document.getElementById(id);
        if (element) {
            element.textContent = value;
        }
    });
}

function createActivityRow(activity) {
    const row = document.createElement('tr');
    const studentDetails = activity.student_details || {};
    const parallel = studentDetails.parallel || {};

    row.className = 'hover:bg-gray-50 transition-colors';
    row.innerHTML = `
        <td class="px-6 py-4 whitespace-nowrap">
            <div class="flex items-center">
                <img src="${studentDetails.photo || '/static/img/9334176.jpg'}" 
                     alt="Foto de ${studentDetails.first_name || 'Estudiante'}" 
                     class="h-10 w-10 rounded-full object-cover">
                <div class="ml-4">
                    <div class="text-sm font-medium text-gray-900">
                        ${studentDetails.full_name || 'Sin nombre'}
                    </div>
                    <div class="text-sm text-gray-500">
                        ${parallel.name || '-'}
                    </div>
                </div>
            </div>
        </td>
        <td class="px-6 py-4 whitespace-nowrap">
            <span class="px-2 inline-flex text-xs leading-5 font-semibold rounded-full 
                ${activity.score ? 'bg-green-100 text-green-800' : 'bg-yellow-100 text-yellow-800'}">
                Parcial ${activity.partial_number}
            </span>
        </td>
        <td class="px-6 py-4">
            <div class="text-sm text-gray-900">${activity.name}</div>
            <div class="text-sm text-gray-500">${activity.description || ''}</div>
        </td>
        <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
            ${formatScore(activity.score)}
        </td>
        <td class="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
            <button onclick="openEditScoreModal(${activity.id}, '${studentDetails.full_name || 'Estudiante'}', ${activity.score || 0})"
                    class="text-indigo-600 hover:text-indigo-900">
                ${activity.score ? 'Editar' : 'Agregar'} Nota
            </button>
        </td>
    `;
    return row;
}

function formatScore(score) {
    if (!score) return '-';
    return `<span class="px-2 py-1 inline-flex text-sm leading-5 font-semibold rounded-full ${
        score >= 7 ? 'bg-green-100 text-green-800' : 
        score >= 5 ? 'bg-yellow-100 text-yellow-800' : 
        'bg-red-100 text-red-800'
    }">${score}</span>`;
}

function updateActivityTable(activities) {
    const tbody = document.querySelector('#activitiesTable tbody');
    if (!tbody) {
        console.error('Activities table body not found');
        return;
    }

    tbody.innerHTML = '';
    activities.forEach(activity => {
        const row = createActivityRow(activity);
        tbody.appendChild(row);
    });
}

// Existing utility functions remain the same...

// Show notification function
function showNotification(message, type = 'success') {
    const notification = document.createElement('div');
    notification.className = `fixed bottom-4 right-4 px-6 py-3 rounded-lg text-white ${
        type === 'success' ? 'bg-green-500' : 'bg-red-500'
    } transition-opacity duration-500 z-50`;
    notification.textContent = message;
    
    document.body.appendChild(notification);
    
    setTimeout(() => {
        notification.style.opacity = '0';
        setTimeout(() => notification.remove(), 500);
    }, 3000);
}

function handleFiltersChange() {
    const academicPeriod = document.getElementById('academicPeriod').value;
    const subject = document.getElementById('subject').value;

    // Update URL with new parameters
    const url = new URL(window.location.href);
    url.searchParams.set('academic_period', academicPeriod);
    url.searchParams.set('subject', subject);
    window.history.pushState({}, '', url);

    // Reload the page to update the context
    window.location.reload();
}



function updatePagination(data) {
    // Remove existing pagination if any
    const existingPagination = document.getElementById('pagination-controls');
    if (existingPagination) {
        existingPagination.remove();
    }

    // If there's no need for pagination, return early
    if (!data.next && !data.previous) {
        return;
    }

    // Create pagination controls
    const paginationDiv = document.createElement('div');
    paginationDiv.id = 'pagination-controls';
    paginationDiv.className = 'flex justify-between items-center mt-4 px-6 py-4 bg-white border-t border-gray-200';

    // Calculate current page and total pages
    const currentPage = data.previous 
        ? new URL(data.previous).searchParams.get('page') 
        ? parseInt(new URL(data.previous).searchParams.get('page')) + 1 
        : 1 
        : 1;
    const totalPages = Math.ceil(data.count / 10); // Assuming 10 items per page

    paginationDiv.innerHTML = `
        <div class="flex-1 flex justify-between items-center">
            <div>
                <p class="text-sm text-gray-700">
                    Mostrando página <span class="font-medium">${currentPage}</span>
                    de <span class="font-medium">${totalPages}</span>
                </p>
            </div>
            <div>
                <nav class="relative z-0 inline-flex rounded-md shadow-sm -space-x-px" aria-label="Pagination">
                    <button 
                        class="relative inline-flex items-center px-2 py-2 rounded-l-md border border-gray-300 bg-white text-sm font-medium text-gray-500 hover:bg-gray-50 ${!data.previous ? 'opacity-50 cursor-not-allowed' : ''}"
                        ${data.previous ? `onclick="loadActivities('${data.previous}')"` : 'disabled'}
                    >
                        Anterior
                    </button>
                    <button 
                        class="relative inline-flex items-center px-2 py-2 rounded-r-md border border-gray-300 bg-white text-sm font-medium text-gray-500 hover:bg-gray-50 ${!data.next ? 'opacity-50 cursor-not-allowed' : ''}"
                        ${data.next ? `onclick="loadActivities('${data.next}')"` : 'disabled'}
                    >
                        Siguiente
                    </button>
                </nav>
            </div>
        </div>
    `;

    // Add pagination controls to the table container
    document.getElementById('activitiesTable').parentNode.appendChild(paginationDiv);
}


async function handleCreateActivity(e) {
    e.preventDefault();
    const formData = new FormData(e.target);
    const academicPeriod = document.getElementById('academicPeriod').value;
    const subject = document.getElementById('subject').value;

    try {
        // First create the activity template
        const templateResponse = await fetch('/subjects/activity-templates/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken')
            },
            body: JSON.stringify({
                name: formData.get('name'),
                description: formData.get('description'),
                activity_type: formData.get('activity_type'),
                partial_number: formData.get('partial_number'),
                sequence_number: formData.get('sequence_number'),
                subject: subject,
                academic_period: academicPeriod
            })
        });

        if (!templateResponse.ok) {
            const error = await templateResponse.json();
            throw new Error(error.detail || 'Error creating template');
        }
        
        const template = await templateResponse.json();

        // Then create activities for all students
        const createActivitiesResponse = await fetch(`/subjects/activity-templates/${template.id}/create_activities/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken')
            },
            body: JSON.stringify({
                students: [] // The backend will get all students for the subject
            })
        });

        if (!createActivitiesResponse.ok) {
            const error = await createActivitiesResponse.json();
            throw new Error(error.detail || 'Error creating activities');
        }

        closeModal('createActivityModal');
        loadActivities();
        e.target.reset();
        showNotification('Actividad creada exitosamente', 'success');
    } catch (error) {
        console.error('Error:', error);
        showNotification(error.message, 'error');
    }
}

async function handleEditScore(e) {
    e.preventDefault();
    const formData = new FormData(e.target);
    const activityId = formData.get('activity_id');

    try {
        const response = await fetch(`/subjects/activities/${activityId}/`, {
            method: 'PATCH',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken')
            },
            body: JSON.stringify({
                score: formData.get('score')
            })
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Error updating score');
        }

        closeModal('editScoreModal');
        loadActivities();
        showNotification('Calificación actualizada exitosamente', 'success');
    } catch (error) {
        console.error('Error:', error);
        showNotification(error.message, 'error');
    }
}

function openEditScoreModal(activityId, studentName, currentScore) {
    const modal = document.getElementById('editScoreModal');
    const form = document.getElementById('editScoreForm');
    
    form.elements['activity_id'].value = activityId;
    form.elements['score'].value = currentScore;
    document.getElementById('studentName').textContent = studentName;
    
    openModal('editScoreModal');
}

// Utility functions
function openModal(modalId) {
    const modal = document.getElementById(modalId);
    modal.classList.remove('hidden');
    setTimeout(() => {
        modal.querySelector('.modal-content').classList.add('show');
    }, 10);
}

function closeModal(modalId) {
    const modal = document.getElementById(modalId);
    const modalContent = modal.querySelector('.modal-content');
    modalContent.classList.remove('show');
    setTimeout(() => {
        modal.classList.add('hidden');
    }, 200);
    }

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
