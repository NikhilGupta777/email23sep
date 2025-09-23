// Authentication Module
const Auth = {
    getToken() { return localStorage.getItem(CONFIG.TOKEN_KEY); },
    setToken(token) { localStorage.setItem(CONFIG.TOKEN_KEY, token); },
    
    clearAuth() {
        localStorage.removeItem(CONFIG.TOKEN_KEY);
        userData = null;
        SENDER_ACCOUNTS = [];
        document.getElementById('app').classList.add('hidden');
        document.getElementById('app-login-modal').classList.remove('hidden');
        // Logout button moved to top right profile panel
        Campaign.goToStep(1);
    },

    async handleManualLogin() {
        const username = document.getElementById('login-username').value;
        const password = document.getElementById('login-password').value;
        const errorEl = document.getElementById('login-error');
        
        if (!username || !password) {
            errorEl.textContent = 'Please enter username and password.';
            return;
        }
        
        try {
            const formData = new FormData();
            formData.append('username', username);
            formData.append('password', password);
            const response = await fetch(`${CONFIG.BACKEND_URL}/token`, { method: 'POST', body: formData });
            
            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || 'Login failed');
            }
            
            const data = await response.json();
            Auth.setToken(data.access_token);
            Auth.loadUserDataAndInitApp();
        } catch (error) {
            errorEl.textContent = error.message;
        }
    },

    handleGoogleLogin() {
        window.location.href = `${CONFIG.BACKEND_URL}/auth/google`;
    },

    switchLoginTab(tab) {
        document.querySelectorAll('.tab-btn').forEach(btn => btn.classList.remove('active'));
        document.querySelectorAll('.login-form').forEach(form => form.classList.add('hidden'));
        
        if (tab === 'manual') {
            document.getElementById('login-tab-manual').classList.add('active');
            document.getElementById('manual-login-form').classList.remove('hidden');
        } else {
            document.getElementById('login-tab-google').classList.add('active');
            document.getElementById('google-login-form').classList.remove('hidden');
        }
    },

    async loadUserData() {
        try {
            userData = await API.fetch('/users/me');
            if (userData.role === 'admin') {
                SENDER_ACCOUNTS = [...ALL_SENDER_ACCOUNTS];
            } else {
                SENDER_ACCOUNTS = [{ id: 1, email: userData.email, name: `${userData.username} Personal`, type: 'personal' }];
            }
        } catch (error) {
            console.error('Failed to load user data:', error);
            Auth.clearAuth();
            throw error;
        }
    },

    loadUserDataAndInitApp() {
        Auth.loadUserData().then(() => {
            document.getElementById('app-login-modal').classList.add('hidden');
            document.getElementById('app').classList.remove('hidden');
            document.getElementById('app').classList.add('flex');
            // Profile and logout buttons moved to top right panel
            if (userData.role === 'admin') document.getElementById('nav-admin').classList.remove('hidden');
            Profile.updateDropdownDisplay();

            // Add profile dropdown event listeners after app is visible
            document.getElementById('profile-dropdown-toggle').addEventListener('click', (e) => {
                e.preventDefault();
                e.stopPropagation();
                Profile.toggleDropdown();
            });

            App.initialize();
        }).catch(error => {
            console.error('Failed to initialize app:', error);
            Auth.clearAuth();
        });
    }
};