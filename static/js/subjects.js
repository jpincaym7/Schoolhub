class SubjectsManager {
    constructor(permissions) {
        this.subjects = [];
        // Update the permissions initialization to properly merge with defaults
        this.permissions = {
            can_view: false,
            can_create: false,
            can_edit: false,
            can_delete: false,
            ...permissions // This will override defaults with provided permissions
        };
        
        this.currentSubject = null;
        this.filters = {
            search: '',
            horas: '',
            especialidad: ''
        };
        
        // DOM Elements
        this.modal = document.getElementById('subjectModal');
        this.subjectsGrid = document.getElementById('subjectsGrid');
        this.filterForm = document.getElementById('filterForm');
        this.subjectForm = document.getElementById('subjectForm');
        
        // Initialize only if user has view permission
        if (this.permissions.can_view) {
            this.bindEvents();
            this.init();
        } else {
            this.showError('No tienes permisos para ver las materias');
            // Hide the grid and controls if no view permission
            if (this.subjectsGrid) this.subjectsGrid.style.display = 'none';
            if (this.filterForm) this.filterForm.style.display = 'none';
            const newSubjectBtn = document.getElementById('newSubjectBtn');
            if (newSubjectBtn) newSubjectBtn.style.display = 'none';
        }
    }

    bindEvents() {
        // Only bind "new subject" button if user has create permission
        const newSubjectBtn = document.getElementById('newSubjectBtn');
        if (newSubjectBtn) {
            if (this.permissions.can_create) {
                newSubjectBtn.addEventListener('click', () => this.openModal());
            } else {
                newSubjectBtn.style.display = 'none';
            }
        }

        // Filter events - only bind if user has view permission
        if (this.permissions.can_view) {
            this.filterForm.querySelector('[name="search"]')?.addEventListener('input', (e) => {
                this.filters.search = e.target.value;
                this.renderSubjects();
            });

            this.filterForm.querySelector('[name="horas"]')?.addEventListener('change', (e) => {
                this.filters.horas = e.target.value;
                this.renderSubjects();
            });

            this.filterForm.querySelector('[name="especialidad"]')?.addEventListener('change', (e) => {
                this.filters.especialidad = e.target.value;
                this.renderSubjects();
            });
        }

        // Modal events
        if (this.modal) {
            document.getElementById('closeModalBtn')?.addEventListener('click', () => {
                this.closeModal();
            });
            
            this.subjectForm?.addEventListener('submit', (e) => {
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

    async init() {
        if (!this.permissions.can_view) {
            this.showError('No tienes permisos para ver las materias');
            return;
        }
        await this.loadSubjects();
    }


    openModal(subject = null) {
        if (subject && !this.permissions.can_edit) {
            this.showError('No tienes permisos para editar materias');
            return;
        }
        if (!subject && !this.permissions.can_create) {
            this.showError('No tienes permisos para crear materias');
            return;
        }

        this.isEditing = !!subject;
        this.currentSubject = subject ? {...subject} : {
            nombre: '',
            codigo: '',
            descripcion: '',
            horas_semanales: '',
            especialidad: ''
        };

        // Update modal title and button text
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


    async loadSubjects() {
        try {
            const response = await fetch('/subjects/api-subjects/');
            if (!response.ok) throw new Error('Error al cargar materias');
            const data = await response.json();
            console.log(data)
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
                subject.nombre.toLowerCase().includes(this.filters.search.toLowerCase()) ||
                subject.codigo.toLowerCase().includes(this.filters.search.toLowerCase());
            
            const matchesHoras = !this.filters.horas || 
                subject.horas_semanales.toString() === this.filters.horas;
            
            const matchesEspecialidad = !this.filters.especialidad || 
                subject.especialidad.id.toString() === this.filters.especialidad;
            
            return matchesSearch && matchesHoras && matchesEspecialidad;
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
        return `
            <div id="subject-${subject.id}" class="subject-card card-hover rounded-xl overflow-hidden">
                <div class="p-6">
                    <div class="flex justify-between items-start">
                        <div>
                            <h3 class="text-xl font-bold text-gray-800">${subject.nombre}</h3>
                            <p class="text-sm text-gray-500 flex items-center mt-1">
                                <i class="fas fa-hashtag mr-2"></i>
                                <span>${subject.codigo}</span>
                            </p>
                        </div>
                        <span class="px-3 py-1 bg-blue-100 text-blue-800 rounded-full text-sm font-medium">
                            ${subject.horas_semanales} horas/semana
                        </span>
                    </div>
                    <div class="mt-4">
                        <p class="text-gray-600">${subject.descripcion}</p>
                    </div>
                    <div class="mt-4 pt-4 border-t">
                        <p class="text-sm text-gray-500">
                            <i class="fas fa-graduation-cap mr-2"></i>
                            Profesor: 
                            ${subject.profesor}
                        </p>
                    </div>
                    
                        ${this.createActionButtons(subject)}
                    </div>
                </div>
            </div>
        `;
    }

    createActionButtons(subject) {
        return `
            ${this.permissions.can_edit ? `
                <button class="edit-btn px-4 py-2 bg-blue-50 text-blue-600 rounded-lg hover:bg-blue-100 transition">
                    <i class="fas fa-edit mr-2"></i>Editar
                </button>
            ` : ''}
            ${this.permissions.can_delete ? `
                <button class="delete-btn px-4 py-2 bg-red-50 text-red-600 rounded-lg hover:bg-red-100 transition">
                    <i class="fas fa-trash mr-2"></i>Eliminar
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
        this.currentSubject = null;
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
        const subjectData = {
            nombre: formData.get('nombre'),
            codigo: formData.get('codigo'),
            descripcion: formData.get('descripcion'),
            horas_semanales: parseInt(formData.get('horas_semanales')),
            especialidad: parseInt(formData.get('especialidad'))
        };

        // Validate hours
        if (subjectData.horas_semanales < 1 || subjectData.horas_semanales > 40) {
            this.showError('Las horas semanales deben estar entre 1 y 40');
            return;
        }

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

document.addEventListener('DOMContentLoaded', () => {
    const permissions = window.PERMISSIONS_DATA || {
        can_view: false,
        can_create: false,
        can_edit: false,
        can_delete: false
    };
    
    window.subjectsManager = new SubjectsManager(permissions);
});