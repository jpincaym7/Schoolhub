// static/js/modules/module-api.js

const API_ENDPOINTS = {
    modules: '/users/modules/',
    modulePermissions: '/users/module_permissions/'
};

Object.assign(API_ENDPOINTS, {
    modulePermissions: '/users/module_permissions/'
});

class ModuleAPI {
    static async getModules() {
        try {
            const response = await fetch(API_ENDPOINTS.modules);
            if (!response.ok) throw new Error('Error al obtener módulos');
            const data = await response.json();
            // DRF puede devolver los resultados en data.results si está paginado
            return Array.isArray(data) ? data : (data.results || []);
        } catch (error) {
            console.error('Error:', error);
            throw error;
        }
    }

    static async createModule(moduleData) {
        try {
            const response = await fetch(API_ENDPOINTS.modules, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
                },
                body: JSON.stringify(moduleData)
            });
            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || 'Error al crear módulo');
            }
            return await response.json();
        } catch (error) {
            console.error('Error:', error);
            throw error;
        }
    }

    static async updateModule(moduleId, moduleData) {
        try {
            const response = await fetch(`${API_ENDPOINTS.modules}${moduleId}/`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
                },
                body: JSON.stringify(moduleData)
            });
            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || 'Error al actualizar módulo');
            }
            return await response.json();
        } catch (error) {
            console.error('Error:', error);
            throw error;
        }
    }

    static async deleteModule(moduleId) {
        try {
            const response = await fetch(`${API_ENDPOINTS.modules}${moduleId}/`, {
                method: 'DELETE',
                headers: {
                    'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
                }
            });
            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || 'Error al eliminar módulo');
            }
            return true;
        } catch (error) {
            console.error('Error:', error);
            throw error;
        }
    }

    static async getModulePermissions(moduleId) {
        try {
            const response = await fetch(`${API_ENDPOINTS.modulePermissions}?module=${moduleId}`);
            if (!response.ok) throw new Error('Error al obtener permisos');
            return await response.json();
        } catch (error) {
            console.error('Error:', error);
            throw error;
        }
    }

    static async createModulePermission(permissionData) {
        try {
            const response = await fetch(API_ENDPOINTS.modulePermissions, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
                },
                body: JSON.stringify(permissionData)
            });

            const data = await response.json();

            if (!response.ok) {
                throw new Error(
                    data.detail || 
                    data.non_field_errors?.[0] || 
                    Object.values(data)[0]?.[0] || 
                    'Error al crear permiso'
                );
            }

            return data;
        } catch (error) {
            console.error('Error:', error);
            throw error;
        }
    }

    static async deleteModulePermission(permissionId) {
        try {
            const response = await fetch(`${API_ENDPOINTS.modulePermissions}${permissionId}/`, {
                method: 'DELETE',
                headers: {
                    'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
                }
            });
            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || 'Error al eliminar permiso');
            }
            return true;
        } catch (error) {
            console.error('Error:', error);
            throw error;
        }
    }

    static async toggleModuleStatus(moduleId, active) {
        try {
            const action = active ? 'activate' : 'deactivate';
            const response = await fetch(`${API_ENDPOINTS.modules}${moduleId}/${action}/`, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
                }
            });
            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || `Error al ${action} módulo`);
            }
            return await response.json();
        } catch (error) {
            console.error('Error:', error);
            throw error;
        }
    }
}