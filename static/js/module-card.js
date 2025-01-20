class ModuleCard {
    static createCard(module) {
        if (!module) return '';

        return `
            <div class="bg-white rounded-lg shadow-lg hover-scale transition-transform duration-200" data-module-id="${module.id || ''}">
                <div class="p-6 space-y-4">
                    <div class="flex justify-between items-start">
                        <div class="flex items-center space-x-3">
                            <div class="w-10 h-10 rounded-full bg-blue-100 flex items-center justify-center">
                                <i class="${module.icon || 'fas fa-cube'} text-blue-600 text-xl"></i>
                            </div>
                            <div>
                                <h3 class="text-xl font-semibold text-gray-800">${module.name || 'Sin nombre'}</h3>
                                <p class="text-sm text-gray-500">${module.code || 'Sin código'}</p>
                            </div>
                        </div>
                        <div class="flex items-center space-x-2">
                            <button onclick="editModule(${module.id})" class="text-blue-600 hover:text-blue-800">
                                <i class="fas fa-edit"></i>
                            </button>
                            <button onclick="managePermissions(${module.id})" class="text-green-600 hover:text-green-800">
                                <i class="fas fa-user-lock"></i>
                            </button>
                            <button onclick="deleteModule(${module.id})" class="text-red-600 hover:text-red-800">
                                <i class="fas fa-trash"></i>
                            </button>
                        </div>
                    </div>
                    <p class="text-gray-600 line-clamp-2">${module.description || 'Sin descripción'}</p>
                    <div class="flex justify-between items-center pt-4 border-t">
                        <div class="flex items-center space-x-2">
                            <i class="fas fa-link text-gray-400"></i>
                            <span class="text-sm text-gray-500">${module.url || '/'}</span>
                        </div>
                        <div class="flex items-center space-x-3">
                            <span class="text-sm text-gray-500">Orden: ${module.order || 0}</span>
                            <label class="relative inline-flex items-center cursor-pointer">
                                <input type="checkbox" class="sr-only peer" ${module.is_active ? 'checked' : ''}
                                       onchange="toggleModuleStatus(${module.id}, this.checked)">
                                <div class="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 
                                          peer-focus:ring-blue-300 rounded-full peer 
                                          peer-checked:after:translate-x-full peer-checked:after:border-white 
                                          after:content-[''] after:absolute after:top-[2px] after:left-[2px] 
                                          after:bg-white after:border-gray-300 after:border after:rounded-full 
                                          after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600"></div>
                            </label>
                        </div>
                    </div>
                </div>
            </div>
        `;
    }

    static updateModulesContainer(modules) {
        const container = document.getElementById('modules-container');
        
        // Verificar si modules es un array y tiene elementos
        if (!Array.isArray(modules)) {
            console.error('Los módulos no son un array:', modules);
            container.innerHTML = '<p class="text-center text-gray-500">No se pudieron cargar los módulos</p>';
            return;
        }

        if (modules.length === 0) {
            container.innerHTML = '<p class="text-center text-gray-500">No hay módulos disponibles</p>';
            return;
        }

        container.innerHTML = modules.map(module => this.createCard(module)).join('');
    }
}