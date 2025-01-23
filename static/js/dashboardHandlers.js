// dashboardHandlers.js

document.addEventListener('DOMContentLoaded', () => {
    // Initialize UI handlers
    initializeUserActions();
    loadUsers();
});

async function initializeUserActions() {
    // New User Form Handler
    const newUserBtn = document.querySelector('[href*="nuevo-usuario"]');
    if (newUserBtn) {
        newUserBtn.addEventListener('click', async (e) => {
            e.preventDefault();
            // Implement your new user form modal logic here
            showUserForm();
        });
    }

    // Delete User Handler
    window.confirmDelete = async (userId) => {
        const modal = document.getElementById('deleteModal');
        const deleteForm = document.getElementById('deleteForm');
        
        deleteForm.onsubmit = async (e) => {
            e.preventDefault();
            const result = await UserService.deleteUser(userId);
            
            if (result.success) {
                showNotification('success', result.message);
                closeDeleteModal();
                loadUsers(); // Refresh user list
            } else {
                showNotification('error', result.error);
            }
        };
        
        modal.classList.remove('hidden');
    };

    // Edit User Handler
    document.querySelectorAll('[href*="editar"]').forEach(editBtn => {
        editBtn.addEventListener('click', async (e) => {
            e.preventDefault();
            const userId = editBtn.dataset.userId;
            const userDetails = await UserService.getUserDetails(userId);
            
            if (userDetails.success) {
                showUserForm(userDetails.data);
            } else {
                showNotification('error', userDetails.error);
            }
        });
    });
}

async function loadUsers() {
    const result = await UserService.getUsers();
    if (result.success) {
        updateUsersGrid(result.data);
    } else {
        showNotification('error', result.error);
    }
}

function updateUsersGrid(users) {
    const usersGrid = document.querySelector('.grid');
    if (!users.length) {
        usersGrid.innerHTML = createEmptyState();
        return;
    }

    usersGrid.innerHTML = users.map(user => createUserCard(user)).join('');
}

function createUserCard(user) {
    return `
        <div class="bg-white overflow-hidden shadow-sm rounded-lg">
            <div class="p-6">
                <!-- User Avatar -->
                <div class="flex items-center">
                    ${createUserAvatar(user)}
                    <div class="ml-4">
                        <h2 class="text-xl font-semibold text-gray-900">${user.full_name}</h2>
                        <p class="text-sm text-gray-500">${user.email}</p>
                    </div>
                </div>
                <!-- User Details -->
                <div class="mt-4 space-y-2">
                    <p class="text-sm text-gray-600">
                        <span class="font-medium">Tipo:</span> 
                        <span class="px-2 py-1 text-xs rounded-full ${getUserTypeClass(user.user_type)}">
                            ${user.user_type}
                        </span>
                    </p>
                    ${user.phone ? `
                        <p class="text-sm text-gray-600">
                            <span class="font-medium">Teléfono:</span> ${user.phone}
                        </p>
                    ` : ''}
                </div>
                <!-- Action Buttons -->
                <div class="mt-6 flex space-x-3">
                    ${createActionButtons(user)}
                </div>
            </div>
        </div>
    `;
}

function showNotification(type, message) {
    // Implement your notification system here
    console.log(`${type}: ${message}`);
}

// Helper functions
function createUserAvatar(user) {
    if (user.profile_image) {
        return `<img src="${user.profile_image}" alt="${user.full_name}" class="h-16 w-16 rounded-full object-cover">`;
    }
    return `
        <div class="h-16 w-16 rounded-full bg-indigo-100 flex items-center justify-center">
            <span class="text-2xl font-medium text-indigo-600">
                ${user.first_name[0]}${user.last_name[0]}
            </span>
        </div>
    `;
}

function getUserTypeClass(userType) {
    const classes = {
        admin: 'bg-red-100 text-red-800',
        teacher: 'bg-green-100 text-green-800',
        student: 'bg-blue-100 text-blue-800'
    };
    return classes[userType] || 'bg-gray-100 text-gray-800';
}

function createActionButtons(user) {
    return `
        <button onclick="editUser(${user.id})" class="flex-1 inline-flex justify-center items-center px-4 py-2 border border-gray-300 shadow-sm text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500">
            <svg class="-ml-1 mr-2 h-5 w-5 text-gray-500" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
                <path d="M13.586 3.586a2 2 0 112.828 2.828l-.793.793-2.828-2.828.793-.793zM11.379 5.793L3 14.172V17h2.828l8.38-8.379-2.83-2.828z" />
            </svg>
            Editar
        </button>
        <button onclick="confirmDelete(${user.id})" class="flex-1 inline-flex justify-center items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-red-600 hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500">
            <svg class="-ml-1 mr-2 h-5 w-5" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
                <path fill-rule="evenodd" d="M9 2a1 1 0 00-.894.553L7.382 4H4a1 1 0 000 2v10a2 2 0 002 2h8a2 2 0 002-2V6a1 1 0 100-2h-3.382l-.724-1.447A1 1 0 0011 2H9zM7 8a1 1 0 012 0v6a1 1 0 11-2 0V8zm5-1a1 1 0 00-1 1v6a1 1 0 102 0V8a1 1 0 00-1-1z" clip-rule="evenodd" />
            </svg>
            Eliminar
        </button>
    `;
}