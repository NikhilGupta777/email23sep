// Profile & Admin Management Module
const Profile = {
    open() {
        if (userData) {
            document.getElementById('profile-username').value = userData.username;
            document.getElementById('profile-email').value = userData.email;
        }
        document.getElementById('profile-message').textContent = '';
        document.getElementById('password-message').textContent = '';
        document.getElementById('profile-modal').classList.remove('hidden');
    },

    toggleDropdown() {
        const dropdown = document.getElementById('profile-dropdown');
        const chevron = document.getElementById('profile-chevron');

        if (!dropdown || !chevron) return;

        const isVisible = !dropdown.classList.contains('hidden');

        if (isVisible) {
            dropdown.classList.add('hidden');
            chevron.classList.remove('rotate-180');
        } else {
            this.updateDropdownDisplay();
            dropdown.classList.remove('hidden');
            chevron.classList.add('rotate-180');
            // Add click listeners to menu items to close dropdown
            const menuItems = dropdown.querySelectorAll('button');
            menuItems.forEach(item => {
                item.addEventListener('click', () => {
                    dropdown.classList.add('hidden');
                    chevron.classList.remove('rotate-180');
                });
            });
        }
    },

    updateDropdownDisplay() {
        if (userData) {
            const usernameEl = document.getElementById('dropdown-username');
            const emailEl = document.getElementById('dropdown-email');
            const displayEl = document.getElementById('profile-username-display');

            if (usernameEl) usernameEl.textContent = userData.username;
            if (emailEl) emailEl.textContent = userData.email;
            if (displayEl) displayEl.textContent = userData.username;
        }
    },

    async save() {
        const username = document.getElementById('profile-username').value;
        const email = document.getElementById('profile-email').value;
        const messageEl = document.getElementById('profile-message');

        try {
            userData = await API.fetch('/users/me/update', {
                method: 'PUT',
                body: JSON.stringify({ username, email })
            });
            messageEl.textContent = 'Profile updated successfully!';
            messageEl.className = 'text-green-500 text-sm mt-2 text-center h-4';
            setTimeout(() => document.getElementById('profile-modal').classList.add('hidden'), 1500);
        } catch (error) {
            messageEl.textContent = error.message;
            messageEl.className = 'text-red-500 text-sm mt-2 text-center h-4';
        }
    },

    async changePassword() {
        const currentPassword = document.getElementById('current-password').value;
        const newPassword = document.getElementById('new-password').value;
        const messageEl = document.getElementById('password-message');

        if (!currentPassword || !newPassword) {
            messageEl.textContent = "Please fill in both password fields.";
            messageEl.className = 'text-red-500 text-sm mt-2 text-center h-4';
            return;
        }

        try {
            await API.fetch('/users/me/change-password', {
                method: 'PUT',
                body: JSON.stringify({
                    current_password: currentPassword,
                    new_password: newPassword
                })
            });
            messageEl.textContent = "Password updated successfully!";
            messageEl.className = 'text-green-500 text-sm mt-2 text-center h-4';
            document.getElementById('current-password').value = '';
            document.getElementById('new-password').value = '';
            setTimeout(() => document.getElementById('profile-modal').classList.add('hidden'), 1500);
        } catch (error) {
            messageEl.textContent = `Error: ${error.message}`;
            messageEl.className = 'text-red-500 text-sm mt-2 text-center h-4';
        }
    }
};

const Admin = {
    async open() {
        document.getElementById('admin-panel-modal').classList.remove('hidden');
        await Admin.refreshUserList();
    },

    async refreshUserList() {
        const userListTable = document.getElementById('user-list-table');
        userListTable.innerHTML = '<tr><td colspan="5" class="text-center p-4">Loading...</td></tr>';

        try {
            const users = await API.fetch('/admin/users');
            this.cachedUsers = users; // Cache users for edit functionality
            userListTable.innerHTML = '';
            users.forEach(user => {
                const row = document.createElement('tr');
                const escapeHtml = (text) => {
                    const div = document.createElement('div');
                    div.textContent = text;
                    return div.innerHTML;
                };
                row.innerHTML = `
                    <td class="py-2 px-4 border-b">${user.id}</td>
                    <td class="py-2 px-4 border-b">${escapeHtml(user.username)}</td>
                    <td class="py-2 px-4 border-b">${escapeHtml(user.email)}</td>
                    <td class="py-2 px-4 border-b">${escapeHtml(user.role)}</td>
                    <td class="py-2 px-4 border-b">
                        <button class="text-blue-500 hover:underline" onclick="Admin.editUser(${user.id})">Edit</button>
                        <button class="text-red-500 hover:underline ml-2" onclick="Admin.deleteUser(${user.id}, '${user.username}')">Delete</button>
                    </td>
                `;
                userListTable.appendChild(row);
            });
        } catch (error) {
            userListTable.innerHTML = `<tr><td colspan="5" class="text-center p-4 text-red-500">Error loading users: ${error.message}</td></tr>`;
        }
    },

    async addUser() {
        const username = document.getElementById('new-user-username').value;
        const email = document.getElementById('new-user-email').value;
        const password = document.getElementById('new-user-password').value;
        const role = document.getElementById('new-user-role').value;
        const messageEl = document.getElementById('admin-message');

        // Input validation
        if (!username || !email || !password || !role) {
            messageEl.textContent = "All fields are required";
            messageEl.className = 'text-red-500 text-sm mt-2 text-center h-4';
            return;
        }

        try {
            await API.fetch('/admin/users', {
                method: 'POST',
                body: JSON.stringify({ username, email, password, role })
            });
            messageEl.textContent = "User created successfully!";
            messageEl.className = 'text-green-500 text-sm mt-2 text-center h-4';
            document.getElementById('new-user-username').value = '';
            document.getElementById('new-user-email').value = '';
            document.getElementById('new-user-password').value = '';
            await Admin.refreshUserList();
        } catch (error) {
            messageEl.textContent = `Error: ${error.message}`;
            messageEl.className = 'text-red-500 text-sm mt-2 text-center h-4';
        }
    },

    async editUser(userId) {
        try {
            // Use cached users if available, otherwise fetch
            let users = this.cachedUsers;
            if (!users) {
                users = await API.fetch('/admin/users');
                this.cachedUsers = users;
            }
            const user = users.find(u => u.id === userId);
            if (user) {
                document.getElementById('edit-user-id').value = user.id;
                document.getElementById('edit-user-username').value = user.username;
                document.getElementById('edit-user-email').value = user.email;
                document.getElementById('edit-user-role').value = user.role;
                document.getElementById('edit-user-modal').classList.remove('hidden');
            }
        } catch (error) {
            this.showNotification(`Could not fetch user details: ${error.message}`, 'error');
        }
    },

    async saveEditUser() {
        const userId = document.getElementById('edit-user-id').value;
        const username = document.getElementById('edit-user-username').value;
        const email = document.getElementById('edit-user-email').value;
        const role = document.getElementById('edit-user-role').value;

        try {
            await API.fetch(`/admin/users/${userId}`, {
                method: 'PUT',
                body: JSON.stringify({ username, email, role })
            });
            document.getElementById('edit-user-modal').classList.add('hidden');
            await Admin.refreshUserList();
        } catch (error) {
            this.showNotification(`Failed to update user: ${error.message}`, 'error');
        }
    },

    async deleteUser(userId, username) {
        if (this.showConfirm(`Are you sure you want to delete the user "${username}"?`)) {
            try {
                await API.fetch(`/admin/users/${userId}`, { method: 'DELETE' });
                await Admin.refreshUserList();
            } catch (error) {
                this.showNotification(`Failed to delete user: ${error.message}`, 'error');
            }
        }
    },

    showNotification(message, type = 'info') {
        const notification = document.createElement('div');
        const bgColor = type === 'error' ? 'bg-red-100 border-red-400 text-red-700' :
            type === 'success' ? 'bg-green-100 border-green-400 text-green-700' :
                'bg-blue-100 border-blue-400 text-blue-700';
        notification.className = `fixed top-4 right-4 p-4 border rounded-lg ${bgColor} z-50`;
        notification.textContent = message;
        document.body.appendChild(notification);
        setTimeout(() => notification.remove(), 5000);
    },

    showConfirm(message) {
        return confirm(message); // Temporary - replace with modal in production
    }
};