// static/js/user_management.js
function userManagement() {
    return {
        users: [],
        filteredUsers: [],
        searchTerm: '',
        selectedUserType: '',
        sortBy: 'name',
        showCreateModal: false,
        showEditModal: false,
        showDeleteModal: false,
        userToDelete: null,
        loading: false,
        notification: {
            show: false,
            message: '',
            type: 'success', // 'success', 'error', 'warning', 'info'
            timeout: null
        },
        formData: {
            first_name: '',
            last_name: '',
            email: '',
            user_type: '',
            phone: '',
            address: '',
            username: ''
        },
        editingUserId: null,

        init() {
            this.fetchUsers();
        },

        async fetchUsers() {
            this.loading = true;
            try {
                const response = await fetch('/users/request/api-users');
                if (!response.ok) throw new Error('Error al cargar usuarios');
                const data = await response.json();
                this.users = data;
                this.filterUsers();
            } catch (error) {
                this.showNotification('Error al cargar usuarios', 'error', 6000);
            } finally {
                this.loading = false;
            }
        },

        filterUsers() {
            this.filteredUsers = this.users.filter(user => {
                const searchFields = `${user.first_name} ${user.last_name} ${user.email}`.toLowerCase();
                const matchesSearch = searchFields.includes(this.searchTerm.toLowerCase());
                const matchesType = !this.selectedUserType || user.user_type === this.selectedUserType;
                return matchesSearch && matchesType;
            });
            this.sortUsers();
        },

        showNotification(message, type = 'success', duration = 5000) {
            // Limpiar cualquier timeout existente
            if (this.notification.timeout) {
                clearTimeout(this.notification.timeout);
            }

            // Actualizar la notificación
            this.notification = {
                show: true,
                message,
                type,
                timeout: null
            };

            // Configurar el nuevo timeout
            this.notification.timeout = setTimeout(() => {
                this.notification.show = false;
            }, duration);
        },

        sortUsers() {
            this.filteredUsers.sort((a, b) => {
                switch (this.sortBy) {
                    case 'name':
                        return `${a.first_name} ${a.last_name}`.localeCompare(`${b.first_name} ${b.last_name}`);
                    case 'type':
                        return a.user_type.localeCompare(b.user_type);
                    case 'date':
                        return new Date(b.date_joined) - new Date(a.date_joined);
                    default:
                        return 0;
                }
            });
        },

        validateForm() {
            const requiredFields = ['first_name', 'last_name', 'email', 'user_type', 'username'];
            const missingFields = requiredFields.filter(field => !this.formData[field]);
            
            if (missingFields.length > 0) {
                this.showNotification('Por favor, complete todos los campos requeridos', 'error', 6000);
                return false;
            }

            if (!this.isValidEmail(this.formData.email)) {
                this.showNotification('Por favor, ingrese un email válido', 'error', 6000);
                return false;
            }

            return true;
        },

        isValidEmail(email) {
            return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
        },

        getUserTypeBadgeClass(type) {
            const classes = {
                admin: 'bg-purple-100 text-purple-800',
                teacher: 'bg-blue-100 text-blue-800',
                parent: 'bg-orange-100 text-orange-800'
            };
            return `px-3 py-1 rounded-full text-sm font-medium ${classes[type] || ''}`;
        },

        getUserTypeLabel(type) {
            const labels = {
                admin: 'Administrador',
                teacher: 'Profesor',
                parent: 'Representante'
            };
            return labels[type] || type;
        },

        formatDate(dateString) {
            return new Date(dateString).toLocaleDateString('es-ES', {
                year: 'numeric',
                month: 'short',
                day: 'numeric'
            });
        },

        editUser(user) {
            this.formData = {
                first_name: user.first_name,
                last_name: user.last_name,
                email: user.email,
                user_type: user.user_type,
                phone: user.phone || '',
                address: user.address || '',
                username: user.username
            };
            this.editingUserId = user.id;
            this.showEditModal = true;
        },

        confirmDelete(user) {
            this.userToDelete = user;
            this.showDeleteModal = true;
        },

        cancelDelete() {
            this.userToDelete = null;
            this.showDeleteModal = false;
        },

        async deleteUser() {
            if (!this.userToDelete) return;

            try {
                const response = await fetch(`/users/request/api-users/${this.userToDelete.id}/`, {
                    method: 'DELETE',
                    headers: {
                        'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
                    }
                });

                if (!response.ok) throw new Error('Error al eliminar usuario');
                
                this.users = this.users.filter(u => u.id !== this.userToDelete.id);
                this.filterUsers();
                this.showNotification('Usuario eliminado exitosamente', 'success');
                this.cancelDelete();
            } catch (error) {
                this.showNotification('Error al eliminar usuario', 'error', 6000);
            }
        },

        async handleSubmit() {
            if (!this.validateForm()) {
                return;
            }

            const url = this.editingUserId 
                ? `/users/request/api-users/${this.editingUserId}/` 
                : '/users/request/api-users';
            const method = this.editingUserId ? 'PUT' : 'POST';

            try {
                const response = await fetch(url, {
                    method,
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
                    },
                    body: JSON.stringify({
                        first_name: this.formData.first_name.trim(),
                        last_name: this.formData.last_name.trim(),
                        email: this.formData.email.trim(),
                        user_type: this.formData.user_type,
                        phone: this.formData.phone.trim(),
                        address: this.formData.address.trim(),
                        username: this.formData.username.trim()
                    })
                });

                if (!response.ok) {
                    const errorData = await response.json();
                    throw new Error(errorData.message || 'Error al guardar usuario');
                }

                await this.fetchUsers();
                this.closeModals();
                this.showNotification(
                    this.editingUserId 
                        ? 'Usuario actualizado exitosamente' 
                        : 'Usuario creado exitosamente',
                    'success'
                );
            } catch (error) {
                this.showNotification(error.message, 'error', 6000);
            }
        },

        closeModals() {
            this.showCreateModal = false;
            this.showEditModal = false;
            this.editingUserId = null;
            this.formData = {
                first_name: '',
                last_name: '',
                email: '',
                user_type: '',
                phone: '',
                address: '',
                username: ''
            };
        },

        get modalTitle() {
            return this.editingUserId ? 'Editar Usuario' : 'Crear Nuevo Usuario';
        }
    };
}