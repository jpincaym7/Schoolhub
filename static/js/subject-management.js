class SubjectsManager {
    constructor(teachersList, permissions, isTeacher = false) {
        this.subjects = [];
        this.teachers = teachersList || [];
        this.permissions = permissions || {
            can_view: false,
            can_create: false,
            can_edit: false,
            can_delete: false
        };
        this.isTeacher = isTeacher;
        this.currentSubject = {
            name: '',
            code: '',
            credits: '3',
            teacher: ''
        };
        this.filters = {
            search: '',
            credits: '',
            teacher: ''
        };
        
        // DOM Elements
        this.modal = document.getElementById('subjectModal');
        this.subjectsGrid = document.getElementById('subjectsGrid');
        this.filterForm = document.getElementById('filterForm');
        this.subjectForm = document.getElementById('subjectForm');
        
        this.bindEvents();
        this.init();
    }

    renderSubjects() {
        const filteredSubjects = this.filterSubjects();
        this.subjectsGrid.innerHTML = filteredSubjects.map(subject => this.createSubjectCard(subject)).join('');
        
        // Agregar event listeners usando arrow functions para mantener el contexto
        filteredSubjects.forEach(subject => {
            const card = document.getElementById(`subject-${subject.id}`);
            if (card) {
                const editBtn = card.querySelector('.edit-btn');
                const deleteBtn = card.querySelector('.delete-btn');
                
                // Usar arrow functions para mantener el contexto de 'this'
                if (editBtn) {
                    editBtn.addEventListener('click', () => {
                        this.editSubject(subject);
                    });
                }
                
                if (deleteBtn) {
                    deleteBtn.addEventListener('click', () => {
                        this.deleteSubject(subject.id);
                    });
                }
            }
        });
    }

    // Asegurarnos de que el método editSubject está definido
    editSubject(subject) {
        if (!this.permissions.can_edit) {
            this.showError('No tienes permisos para editar materias');
            return;
        }
        
        // Llamar a openModal con el subject para edición
        this.openModal(subject);
        
        // Actualizar el título del modal y el texto del botón
        document.getElementById('modalTitle').textContent = 'Editar Materia';
        document.getElementById('submitButtonText').textContent = 'Guardar Cambios';
    }

    bindEvents() {
        // Usar arrow functions en todos los event listeners
        this.filterForm.querySelector('[name="search"]').addEventListener('input', (e) => {
            this.filters.search = e.target.value;
            this.renderSubjects();
        });

        this.filterForm.querySelector('[name="credits"]').addEventListener('change', (e) => {
            this.filters.credits = e.target.value;
            this.renderSubjects();
        });

        this.filterForm.querySelector('[name="teacher"]').addEventListener('change', (e) => {
            this.filters.teacher = e.target.value;
            this.renderSubjects();
        });

        // Modal events con arrow functions
        document.getElementById('newSubjectBtn').addEventListener('click', () => {
            this.openModal();
        });
        
        document.getElementById('closeModalBtn').addEventListener('click', () => {
            this.closeModal();
        });
        
        this.subjectForm.addEventListener('submit', (e) => {
            e.preventDefault();
            this.saveSubject();
        });

        // Close modal on outside click
        window.addEventListener('click', (e) => {
            if (e.target === this.modal) {
                this.closeModal();
            }
        });
    }

    openModal(subject = null) {
        if (subject && !this.permissions.can_edit) {
            this.showError('No tienes permisos para editar materias');
            return;
        }
        if (this.isTeacher) {
            this.showError('No tienes permisos para crear materias');
            return;
        }

        this.isEditing = !!subject;
        this.currentSubject = subject ? {...subject} : {
            name: '',
            code: '',
            credits: '3',
            teacher: ''
        };

        // Actualizar título del modal y texto del botón
        document.getElementById('modalTitle').textContent = this.isEditing ? 'Editar Materia' : 'Nueva Materia';
        document.getElementById('submitButtonText').textContent = this.isEditing ? 'Guardar Cambios' : 'Crear Materia';

        // Fill form fields
        Object.keys(this.currentSubject).forEach(key => {
            const input = this.subjectForm.querySelector(`[name="${key}"]`);
            if (input) {
                input.value = this.currentSubject[key];
            }
        });

        this.modal.classList.remove('hidden');
    }

    async init() {
        if (!this.permissions.can_view) {
            this.showError('No tienes permisos para ver las materias');
            return;
        }
        await this.loadSubjects();
    }

    async loadSubjects() {
        try {
            const response = await fetch('/subjects/api-subjects/');
            if (!response.ok) throw new Error('Error al cargar materias');
            const data = await response.json();
            this.subjects = Array.isArray(data) ? data : (data.results || []);
            this.renderSubjects();
        } catch (error) {
            this.showError('Error al cargar las materias');
            console.error(error);
            this.subjects = [];
        }
    }

    filterSubjects() {
        return this.subjects.filter(subject => {
            const matchesSearch = !this.filters.search || 
                subject.name.toLowerCase().includes(this.filters.search.toLowerCase()) ||
                subject.code.toLowerCase().includes(this.filters.search.toLowerCase());
            
            const matchesCredits = !this.filters.credits || 
                subject.credits.toString() === this.filters.credits;
            
            const matchesTeacher = !this.filters.teacher || 
                subject.teacher.toString() === this.filters.teacher;
            
            return matchesSearch && matchesCredits && matchesTeacher;
        });
    }

    renderSubjects() {
        const filteredSubjects = this.filterSubjects();
        this.subjectsGrid.innerHTML = filteredSubjects.map(subject => this.createSubjectCard(subject)).join('');
        
        // Add event listeners to the new cards
        filteredSubjects.forEach(subject => {
            const card = document.getElementById(`subject-${subject.id}`);
            if (card) {
                card.querySelector('.edit-btn')?.addEventListener('click', () => this.editSubject(subject));
                card.querySelector('.delete-btn')?.addEventListener('click', () => this.deleteSubject(subject.id));
            }
        });
    }

    createSubjectCard(subject) {
        const actionButtons = this.isTeacher ? 
            this.createTeacherButtons(subject) : 
            this.createAdminButtons(subject);

        return `
            <div id="subject-${subject.id}" class="subject-card card-hover rounded-xl overflow-hidden">
                <div class="h-24 bg-gradient-to-r from-blue-500 to-purple-500 relative">
                    <span class="status-badge bg-green-100 text-green-800">
                        <i class="fas fa-check-circle mr-1"></i>
                        Activo
                    </span>
                </div>
                <div class="p-6 relative">
                    <div class="absolute -top-12 left-6">
                        <img src="${subject.teacher_details.profile_image || '/static/img/9334176.jpg'}"
                             alt="${subject.teacher_details.first_name}"
                             class="teacher-avatar w-24 h-24 rounded-full object-cover">
                    </div>
                    <div class="mt-14">
                        <div class="flex justify-between items-start">
                            <div>
                                <h3 class="text-xl font-bold text-gray-800">${subject.name}</h3>
                                <p class="text-sm text-gray-500 flex items-center mt-1">
                                    <i class="fas fa-hashtag mr-2"></i>
                                    <span>${subject.code}</span>
                                </p>
                            </div>
                            <span class="px-3 py-1 bg-blue-100 text-blue-800 rounded-full text-sm font-medium">
                                <i class="fas fa-star mr-1"></i>
                                ${subject.credits} créditos
                            </span>
                        </div>
                        <div class="mt-4 border-t pt-4">
                            <h4 class="text-sm font-medium text-gray-500 mb-2">Profesor Asignado</h4>
                            <div class="flex items-center">
                                <div>
                                    <p class="text-gray-800 font-medium">
                                        ${subject.teacher_details.first_name} ${subject.teacher_details.last_name}
                                    </p>
                                    <p class="text-sm text-gray-500">${subject.teacher_details.email}</p>
                                </div>
                            </div>
                        </div>
                        <div class="mt-6 flex justify-end space-x-2">
                            ${actionButtons}
                        </div>
                    </div>
                </div>
            </div>
        `;
    }

    createAdminButtons(subject) {
        return `
            ${this.permissions.can_edit ? `
                <button class="edit-btn px-4 py-2 bg-blue-50 text-blue-600 rounded-lg hover:bg-blue-100 transition flex items-center">
                    <i class="fas fa-edit mr-2"></i>
                    Editar
                </button>
            ` : ''}
            ${this.permissions.can_delete ? `
                <button class="delete-btn px-4 py-2 bg-red-50 text-red-600 rounded-lg hover:bg-red-100 transition flex items-center">
                    <i class="fas fa-trash mr-2"></i>
                    Eliminar
                </button>
            ` : ''}
        `;
    }

    createTeacherButtons(subject) {
        return `
            <a href="/subjects/${subject.id}/api-activities/" 
               class="view-activities-btn px-4 py-2 bg-green-50 text-green-600 rounded-lg hover:bg-green-100 transition flex items-center">
                <i class="fas fa-tasks mr-2"></i>
                Ver Actividades
            </a>
        `;
    }

    closeModal() {
        this.modal.classList.add('hidden');
        this.subjectForm.reset();
    }

    async saveSubject() {
        if (this.isEditing && !this.permissions.can_edit) {
            this.showError('No tienes permisos para editar materias');
            return;
        }
        if (!this.isEditing && !this.permissions.can_create) {
            this.showError('No tienes permisos para crear materias');
            return;
        }

        const formData = new FormData(this.subjectForm);
        const subjectData = Object.fromEntries(formData.entries());

        const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;
        const url = this.isEditing ? 
            `/subjects/api-subjects/${this.currentSubject.id}/` : 
            '/subjects/api-subjects/';
        const method = this.isEditing ? 'PUT' : 'POST';

        try {
            const response = await fetch(url, {
                method,
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrfToken
                },
                body: JSON.stringify(subjectData)
            });

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.message || 'Error al guardar la materia');
            }

            await this.loadSubjects();
            this.closeModal();
            this.showSuccess(this.isEditing ? 'Materia actualizada exitosamente' : 'Materia creada exitosamente');
        } catch (error) {
            this.showError(error.message);
            console.error(error);
        }
    }

    async deleteSubject(id) {
        if (!this.permissions.can_delete) {
            this.showError('No tienes permisos para eliminar materias');
            return;
        }

        const result = await Swal.fire({
            title: '¿Estás seguro?',
            text: "Esta acción no se puede deshacer",
            icon: 'warning',
            showCancelButton: true,
            confirmButtonColor: '#d33',
            cancelButtonColor: '#3085d6',
            confirmButtonText: 'Sí, eliminar',
            cancelButtonText: 'Cancelar'
        });

        if (result.isConfirmed) {
            const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;
            try {
                const response = await fetch(`/subjects/api-subjects/${id}/`, {
                    method: 'DELETE',
                    headers: {
                        'X-CSRFToken': csrfToken
                    }
                });

                if (!response.ok) throw new Error('Error al eliminar la materia');
                
                await this.loadSubjects();
                this.showSuccess('Materia eliminada exitosamente');
            } catch (error) {
                this.showError('Error al eliminar la materia');
                console.error(error);
            }
        }
    }

    showSuccess(message) {
        Swal.fire({
            icon: 'success',
            title: '¡Éxito!',
            text: message,
            timer: 2000,
            showConfirmButton: false
        });
    }

    showError(message) {
        Swal.fire({
            icon: 'error',
            title: 'Error',
            text: message
        });
    }
}

// Initialize the manager when the DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    const teachersList = window.TEACHERS_DATA || [];
    const permissions = window.PERMISSIONS_DATA || {
        can_view: false,
        can_create: false,
        can_edit: false,
        can_delete: false
    };
    const isTeacher = document.body.dataset.userType === 'teacher';
    
    window.subjectsManager = new SubjectsManager(teachersList, permissions, isTeacher);
});