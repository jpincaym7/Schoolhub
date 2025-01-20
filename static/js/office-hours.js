document.addEventListener('DOMContentLoaded', function() {
    const modal = document.getElementById('officeHourModal');
    const addBtn = document.getElementById('addOfficeHourBtn');
    const closeBtn = document.getElementById('closeModal');
    const form = document.getElementById('officeHoursForm');
    const deleteBtn = document.getElementById('deleteOfficeHour');
    const modalTitle = document.getElementById('modalTitle');
    const submitButtonText = document.getElementById('submitButtonText');
    
    let currentEditId = null;

    // Generate time slots from 7:00 to 22:00
    function generateTimeSlots() {
        const calendarGrid = document.getElementById('calendarGrid');
        const startHour = 7;
        const endHour = 22;

        for (let hour = startHour; hour < endHour; hour++) {
            const timeSlot = document.createElement('div');
            timeSlot.className = 'grid grid-cols-8';
            
            // Time column
            const timeCol = document.createElement('div');
            timeCol.className = 'p-4 border-r text-gray-600';
            timeCol.textContent = `${hour.toString().padStart(2, '0')}:00`;
            timeSlot.appendChild(timeCol);

            // Day columns
            for (let day = 0; day < 7; day++) {
                const dayCol = document.createElement('div');
                dayCol.className = 'p-2 border-r min-h-[5rem] relative';
                dayCol.setAttribute('data-day', day);
                dayCol.setAttribute('data-hour', hour);
                timeSlot.appendChild(dayCol);
            }

            calendarGrid.appendChild(timeSlot);
        }
    }

    // Load and display office hours
    async function loadOfficeHours() {
        try {
            const response = await fetch('/communications/office-api/my_office_hours/');
            const data = await response.json();
            console.log(data)
            // Clear existing appointments
            const slots = document.querySelectorAll('[data-day]');
            slots.forEach(slot => slot.innerHTML = '');

            // Display appointments
            data.forEach(hour => {
                const startHour = parseInt(hour.start_time.split(':')[0]);
                const slot = document.querySelector(`[data-day="${hour.day_of_week}"][data-hour="${startHour}"]`);
                
                if (slot) {
                    const appointment = document.createElement('div');
                    appointment.className = 'absolute inset-0 m-1 p-2 bg-blue-100 rounded text-sm';
                    appointment.innerHTML = `
                        <div class="font-semibold text-blue-800">${hour.subject_name}</div>
                        <div class="text-blue-600">${hour.start_time} - ${hour.end_time}</div>
                        <div class="text-blue-500 text-xs">${hour.location}</div>
                        <button onclick="editOfficeHour(${hour.id})" class="absolute top-1 right-1 text-blue-700 hover:text-blue-900">
                            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15.232 5.232l3.536 3.536m-2.036-5.036a2.5 2.5 0 113.536 3.536L6.5 21.036H3v-3.572L16.732 3.732z" />
                            </svg>
                        </button>
                    `;
                    slot.appendChild(appointment);
                }
            });
        } catch (error) {
            showToast('Error al cargar los horarios', 'error');
        }
    }

    // Modal handlers
    addBtn.onclick = () => {
        currentEditId = null;
        form.reset();
        modalTitle.textContent = '{% trans "Agregar Horario de Atención" %}';
        submitButtonText.textContent = '{% trans "Guardar" %}';
        deleteBtn.classList.add('hidden');
        modal.classList.remove('hidden');
    };

    closeBtn.onclick = () => modal.classList.add('hidden');

    // Close modal when clicking outside
    modal.onclick = (e) => {
        if (e.target === modal) modal.classList.add('hidden');
    };

    // Form submission
    form.onsubmit = async (e) => {
        e.preventDefault();
        const formData = new FormData(form);
        const data = Object.fromEntries(formData.entries());

        try {
            const url = '/communications/office-api/' + (currentEditId ? `${currentEditId}/` : '');
            const method = currentEditId ? 'PUT' : 'POST';

            const response = await fetch(url, {
                method: method,
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCookie('csrftoken')
                },
                body: JSON.stringify(data)
            });

            if (!response.ok) throw new Error('Error en la solicitud');

            showToast(currentEditId ? 'Horario actualizado exitosamente' : 'Horario agregado exitosamente');
            modal.classList.add('hidden');
            loadOfficeHours();
        } catch (error) {
            showToast('Error al procesar la solicitud', 'error');
        }
    };

    // Delete handler
    deleteBtn.onclick = async () => {
        if (!currentEditId) return;

        if (confirm('¿Está seguro de eliminar este horario?')) {
            try {
                const response = await fetch(`/communications/office-api/${currentEditId}/`, {
                    method: 'DELETE',
                    headers: {
                        'X-CSRFToken': getCookie('csrftoken')
                    }
                });

                if (!response.ok) throw new Error('Error en la solicitud');

                showToast('Horario eliminado exitosamente');
                modal.classList.add('hidden');
                loadOfficeHours();
            } catch (error) {
                showToast('Error al eliminar el horario', 'error');
            }
        }
    };

    // Edit office hour
    window.editOfficeHour = async (id) => {
        try {
            const response = await fetch(`/communications/office-api/${id}/`);
            const data = await response.json();

            currentEditId = id;
            form.elements.subject.value = data.subject;
            form.elements.day_of_week.value = data.day_of_week;
            form.elements.start_time.value = data.start_time;
            form.elements.end_time.value = data.end_time;
            form.elements.location.value = data.location;
            form.elements.id.value = data.id;

            modalTitle.textContent = '{% trans "Editar Horario de Atención" %}';
            submitButtonText.textContent = '{% trans "Actualizar" %}';
            deleteBtn.classList.remove('hidden');
            modal.classList.remove('hidden');
        } catch (error) {
            showToast('Error al cargar el horario', 'error');
        }
    };

    // Toast notification
    function showToast(message, type = 'success') {
        const toast = document.getElementById('toast');
        const toastMessage = document.getElementById('toastMessage');
        
        toast.className = `fixed bottom-4 right-4 transform transition-all duration-300 ${
            type === 'success' ? 'bg-green-500' : 'bg-red-500'
        } text-white px-6 py-3 rounded-lg shadow-lg`;
        
        toastMessage.textContent = message;
        toast.style.transform = 'translateY(0)';
        toast.style.opacity = '1';

        setTimeout(() => {
            toast.style.transform = 'translateY(100%)';
            toast.style.opacity = '0';
        }, 3000);
    }

    // Cookie helper
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

    // Validation functions
    function validateTimeRange() {
        const startTime = form.elements.start_time.value;
        const endTime = form.elements.end_time.value;

        if (startTime && endTime && startTime >= endTime) {
            showToast('La hora de inicio debe ser anterior a la hora de fin', 'error');
            return false;
        }
        return true;
    }

    // Add time input validation
    form.elements.start_time.onchange = validateTimeRange;
    form.elements.end_time.onchange = validateTimeRange;

    // Check for overlapping schedules
    async function checkOverlap(dayOfWeek, startTime, endTime, excludeId = null) {
        try {
            const response = await fetch('/communications/office-api/my_office_hours/');
            const hours = await response.json();
            
            return hours.some(hour => {
                if (excludeId && hour.id === excludeId) return false;
                
                if (hour.day_of_week === parseInt(dayOfWeek)) {
                    const hourStart = hour.start_time;
                    const hourEnd = hour.end_time;
                    
                    return (startTime < hourEnd && endTime > hourStart);
                }
                return false;
            });
        } catch (error) {
            console.error('Error checking overlap:', error);
            return false;
        }
    }

    // Enhanced form validation
    form.onsubmit = async (e) => {
        e.preventDefault();
        
        if (!validateTimeRange()) return;

        const formData = new FormData(form);
        const data = Object.fromEntries(formData.entries());

        // Check for overlapping schedules
        const hasOverlap = await checkOverlap(
            data.day_of_week,
            data.start_time,
            data.end_time,
            currentEditId
        );

        if (hasOverlap) {
            showToast('Ya existe un horario programado en este período', 'error');
            return;
        }

        try {
            const url = '/communications/office-api/' + (currentEditId ? `${currentEditId}/` : '');
            const method = currentEditId ? 'PUT' : 'POST';

            const response = await fetch(url, {
                method: method,
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCookie('csrftoken')
                },
                body: JSON.stringify(data)
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.message || 'Error en la solicitud');
            }

            showToast(currentEditId ? 'Horario actualizado exitosamente' : 'Horario agregado exitosamente');
            modal.classList.add('hidden');
            loadOfficeHours();
        } catch (error) {
            showToast(error.message || 'Error al procesar la solicitud', 'error');
        }
    };

    // Add drag and drop functionality
    function initializeDragAndDrop() {
        const slots = document.querySelectorAll('[data-day]');
        
        slots.forEach(slot => {
            slot.ondragover = (e) => {
                e.preventDefault();
                slot.classList.add('bg-blue-50');
            };

            slot.ondragleave = () => {
                slot.classList.remove('bg-blue-50');
            };

            slot.ondrop = async (e) => {
                e.preventDefault();
                slot.classList.remove('bg-blue-50');
                
                const id = e.dataTransfer.getData('text');
                const day = slot.getAttribute('data-day');
                const hour = slot.getAttribute('data-hour');
                
                try {
                    // Update the office hour with new time/day
                    const response = await fetch(`/communications/office-api/${id}/`, {
                        method: 'PATCH',
                        headers: {
                            'Content-Type': 'application/json',
                            'X-CSRFToken': getCookie('csrftoken')
                        },
                        body: JSON.stringify({
                            day_of_week: parseInt(day),
                            start_time: `${hour.padStart(2, '0')}:00`
                        })
                    });

                    if (!response.ok) throw new Error('Error al actualizar el horario');

                    loadOfficeHours();
                    showToast('Horario actualizado exitosamente');
                } catch (error) {
                    showToast('Error al actualizar el horario', 'error');
                }
            };
        });
    }

    // Initialize calendar and load data
    generateTimeSlots();
    loadOfficeHours();
    initializeDragAndDrop();

    // Refresh calendar periodically
    setInterval(loadOfficeHours, 300000); // Refresh every 5 minutes
});