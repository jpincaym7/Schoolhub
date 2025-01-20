// static/js/modules/module-form.js

let currentModule = null;

// Función para editar módulo
async function editModule(moduleId) {
    try {
        const response = await fetch(`${API_ENDPOINTS.modules}${moduleId}/`);
        if (!response.ok) throw new Error('Error al obtener datos del módulo');
        
        const module = await response.json();
        currentModule = moduleId;
        
        // Rellenar el formulario con los datos del módulo
        document.getElementById('moduleId').value = module.id;
        document.getElementById('moduleName').value = module.name;
        document.getElementById('moduleCode').value = module.code;
        document.getElementById('moduleDescription').value = module.description || '';
        document.getElementById('moduleIcon').value = module.icon || '';
        document.getElementById('moduleUrl').value = module.url || '';
        document.getElementById('moduleOrder').value = module.order || 0;
        document.getElementById('moduleStatus').value = module.is_active.toString();

        // Abrir el modal
        const modal = document.getElementById('moduleModal');
        const title = document.getElementById('modalTitle');
        title.textContent = 'Editar Módulo';
        modal.classList.remove('hidden');
        modal.classList.add('flex');
    } catch (error) {
        console.error('Error al cargar el módulo:', error);
        Swal.fire({
            icon: 'error',
            title: 'Error',
            text: 'No se pudo cargar la información del módulo'
        });
    }
}

function openModuleModal(moduleId = null) {
    currentModule = moduleId;
    const modal = document.getElementById('moduleModal');
    const title = document.getElementById('modalTitle');
    
    if (!moduleId) {
        // Nuevo módulo
        title.textContent = 'Nuevo Módulo';
        document.getElementById('moduleForm').reset();
        document.getElementById('moduleId').value = '';
    }
    
    modal.classList.remove('hidden');
    modal.classList.add('flex');
}

function closeModuleModal() {
    const modal = document.getElementById('moduleModal');
    modal.classList.remove('flex');
    modal.classList.add('hidden');
    currentModule = null;
    document.getElementById('moduleForm').reset();
}

async function handleModuleSubmit(event) {
    event.preventDefault();
    
    const moduleData = {
        name: document.getElementById('moduleName').value,
        code: document.getElementById('moduleCode').value,
        description: document.getElementById('moduleDescription').value,
        icon: document.getElementById('moduleIcon').value,
        url: document.getElementById('moduleUrl').value,
        order: parseInt(document.getElementById('moduleOrder').value) || 0,
        is_active: document.getElementById('moduleStatus').value === 'true'
    };

    try {
        let result;
        if (currentModule) {
            result = await ModuleAPI.updateModule(currentModule, moduleData);
        } else {
            result = await ModuleAPI.createModule(moduleData);
        }
        
        const modules = await ModuleAPI.getModules();
        ModuleCard.updateModulesContainer(modules);
        closeModuleModal();
        
        Swal.fire({
            icon: 'success',
            title: currentModule ? 'Módulo actualizado' : 'Módulo creado',
            text: 'La operación se realizó exitosamente',
            showConfirmButton: false,
            timer: 1500
        });
    } catch (error) {
        console.error('Error:', error);
        Swal.fire({
            icon: 'error',
            title: 'Error',
            text: error.message || 'Hubo un error al procesar la operación'
        });
    }
}

async function deleteModule(moduleId) {
    try {
        const result = await Swal.fire({
            title: '¿Estás seguro?',
            text: "Esta acción no se puede deshacer",
            icon: 'warning',
            showCancelButton: true,
            confirmButtonColor: '#3085d6',
            cancelButtonColor: '#d33',
            confirmButtonText: 'Sí, eliminar',
            cancelButtonText: 'Cancelar'
        });

        if (result.isConfirmed) {
            await ModuleAPI.deleteModule(moduleId);
            const modules = await ModuleAPI.getModules();
            ModuleCard.updateModulesContainer(modules);
            
            Swal.fire({
                icon: 'success',
                title: '¡Eliminado!',
                text: 'El módulo ha sido eliminado.',
                timer: 1500
            });
        }
    } catch (error) {
        console.error('Error:', error);
        Swal.fire({
            icon: 'error',
            title: 'Error',
            text: error.message || 'No se pudo eliminar el módulo'
        });
    }
}

async function toggleModuleStatus(moduleId, active) {
    try {
        await ModuleAPI.toggleModuleStatus(moduleId, active);
        
        Swal.fire({
            icon: 'success',
            title: active ? 'Módulo activado' : 'Módulo desactivado',
            toast: true,
            position: 'top-end',
            showConfirmButton: false,
            timer: 3000
        });
    } catch (error) {
        console.error('Error:', error);
        Swal.fire({
            icon: 'error',
            title: 'Error',
            text: error.message || 'No se pudo cambiar el estado del módulo'
        });
    }
}

// Event Listeners
document.addEventListener('DOMContentLoaded', async () => {
    try {
        const modules = await ModuleAPI.getModules();
        ModuleCard.updateModulesContainer(modules);
    } catch (error) {
        console.error('Error al cargar módulos:', error);
        Swal.fire({
            icon: 'error',
            title: 'Error',
            text: 'No se pudieron cargar los módulos'
        });
    }
});

document.getElementById('moduleForm').addEventListener('submit', handleModuleSubmit);

// Cerrar modal con Escape
document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') closeModuleModal();
});

// Hacer las funciones disponibles globalmente
window.editModule = editModule;
window.deleteModule = deleteModule;
window.toggleModuleStatus = toggleModuleStatus;
window.openModuleModal = openModuleModal;
window.closeModuleModal = closeModuleModal;


// Agregar al final de module-form.js

let currentModuleForPermissions = null;

function closePermissionsModal() {
    const modal = document.getElementById('permissionsModal');
    modal.classList.remove('flex');
    modal.classList.add('hidden');
    currentModuleForPermissions = null;
}

async function loadUserTypes() {
    const userTypes = [
        {value: 'admin', label: 'Administrador'},
        {value: 'teacher', label: 'Profesor'},
        {value: 'parent', label: 'Padre/Representante'}
    ];
    
    const select = document.getElementById('permissionUserType');
    select.innerHTML = userTypes.map(type => 
        `<option value="${type.value}">${type.label}</option>`
    ).join('');
}


async function loadCurrentPermissions() {
    try {
        const permissions = await ModuleAPI.getModulePermissions(currentModuleForPermissions);
        const container = document.getElementById('currentPermissions');
        
        const permissionsList = Array.isArray(permissions) ? permissions : permissions.results || [];
        
        if (!permissionsList.length) {
            container.innerHTML = '<p class="text-center text-gray-500">No hay permisos asignados</p>';
            return;
        }

        container.innerHTML = permissionsList.map(permission => {
            // Obtener la etiqueta en español del tipo de usuario
            const userTypeLabels = {
                'admin': 'Administrador',
                'teacher': 'Profesor',
                'parent': 'Padre/Representante'
            };

            return `
                <div class="flex justify-between items-center p-2 border-b">
                    <div>
                        <span class="font-medium">${userTypeLabels[permission.user_type] || permission.user_type}</span>
                        <span class="text-sm text-gray-500 ml-2">
                            ${permission.can_view ? '👁️' : ''}
                            ${permission.can_create ? '➕' : ''}
                            ${permission.can_edit ? '✏️' : ''}
                            ${permission.can_delete ? '🗑️' : ''}
                        </span>
                    </div>
                    <button onclick="removePermission(${permission.id})" class="text-red-600 hover:text-red-800">
                        <i class="fas fa-times"></i>
                    </button>
                </div>
            `;
        }).join('');
    } catch (error) {
        console.error('Error al cargar permisos:', error);
        Swal.fire({
            icon: 'error',
            title: 'Error',
            text: 'No se pudieron cargar los permisos'
        });
    }
}

// Modificar la función managePermissions para manejar errores de forma más robusta
async function managePermissions(moduleId) {
    if (!moduleId) {
        console.error('ID de módulo no válido');
        return;
    }

    currentModuleForPermissions = moduleId;
    const modal = document.getElementById('permissionsModal');
    
    if (!modal) {
        console.error('Modal no encontrado');
        return;
    }

    modal.classList.remove('hidden');
    modal.classList.add('flex');
    
    try {
        await Promise.all([loadUserTypes(), loadCurrentPermissions()]);
    } catch (error) {
        console.error('Error al cargar datos:', error);
        Swal.fire({
            icon: 'error',
            title: 'Error',
            text: 'Hubo un problema al cargar los datos'
        });
    }
}

async function addModulePermission() {
    try {
        const userType = document.getElementById('permissionUserType').value;
        if (!userType) {
            throw new Error('Debe seleccionar un tipo de usuario');
        }

        if (!currentModuleForPermissions) {
            throw new Error('No se ha seleccionado un módulo');
        }

        const permissionData = {
            module: parseInt(currentModuleForPermissions),
            user_type: userType,
            can_view: document.getElementById('canView').checked || false,
            can_create: document.getElementById('canCreate').checked || false,
            can_edit: document.getElementById('canEdit').checked || false,
            can_delete: document.getElementById('canDelete').checked || false
        };

        const result = await ModuleAPI.createModulePermission(permissionData);
        await loadCurrentPermissions();
        
        // Limpiar checkboxes después de crear exitosamente
        document.getElementById('canView').checked = false;
        document.getElementById('canCreate').checked = false;
        document.getElementById('canEdit').checked = false;
        document.getElementById('canDelete').checked = false;
        
        Swal.fire({
            icon: 'success',
            title: 'Permiso agregado',
            toast: true,
            position: 'top-end',
            showConfirmButton: false,
            timer: 3000
        });
    } catch (error) {
        console.error('Error:', error);
        Swal.fire({
            icon: 'error',
            title: 'Error',
            text: error.message || 'No se pudo agregar el permiso'
        });
    }
}

async function removePermission(permissionId) {
    try {
        const result = await Swal.fire({
            title: '¿Eliminar permiso?',
            text: "Esta acción no se puede deshacer",
            icon: 'warning',
            showCancelButton: true,
            confirmButtonColor: '#3085d6',
            cancelButtonColor: '#d33',
            confirmButtonText: 'Sí, eliminar',
            cancelButtonText: 'Cancelar'
        });

        if (result.isConfirmed) {
            await ModuleAPI.deleteModulePermission(permissionId);
            await loadCurrentPermissions();
            
            Swal.fire({
                icon: 'success',
                title: 'Permiso eliminado',
                toast: true,
                position: 'top-end',
                showConfirmButton: false,
                timer: 3000
            });
        }
    } catch (error) {
        console.error('Error:', error);
        Swal.fire({
            icon: 'error',
            title: 'Error',
            text: error.message || 'No se pudo eliminar el permiso'
        });
    }
}

// Hacer las funciones disponibles globalmente
window.managePermissions = managePermissions;
window.closePermissionsModal = closePermissionsModal;
window.addModulePermission = addModulePermission;
window.removePermission = removePermission;