// Main Application Module
const App = {
    initialize() {
        Campaign.populateSenderAccounts();
        App.loadTemplates();
        App.loadDashboardData();
        Navigation.showPage('dashboard-section', 'Dashboard');
    },

    async loadTemplates() {
        try {
            const apiTemplates = await API.getTemplates();
            Campaign.populateTemplates(apiTemplates);
        } catch (error) {
            console.error("Could not populate templates:", error);
        }
    },

    async loadDashboardData() {
        try {
            const stats = await API.getDashboardStats();
            document.getElementById('stats-today').textContent = stats.email_stats.today;
            document.getElementById('stats-week').textContent = stats.email_stats.last_7_days;
            document.getElementById('stats-month').textContent = stats.email_stats.last_30_days;
            document.getElementById('stats-this-month').textContent = stats.email_stats.this_month;
            
            const recentCampaignsEl = document.getElementById('recent-campaigns');
            recentCampaignsEl.innerHTML = '';
            stats.recent_campaigns.forEach(campaign => {
                const div = document.createElement('div');
                div.className = 'p-3 bg-gray-50 rounded';
                const escapeHtml = (text) => {
                    const div = document.createElement('div');
                    div.textContent = text;
                    return div.innerHTML;
                };
                div.innerHTML = `<p class="font-semibold">${escapeHtml(campaign.name)}</p><p class="text-sm text-gray-600">${new Date(campaign.created_at).toLocaleDateString()}</p>`;
                recentCampaignsEl.appendChild(div);
            });
        } catch (error) {
            console.error('Failed to load dashboard data:', error);
        }
    }
};

// Navigation Module
const Navigation = {
    showPage(pageId, title) {
        document.querySelectorAll('.page-section').forEach(section => section.classList.add('hidden'));
        const targetSection = document.getElementById(pageId);
        if (targetSection) targetSection.classList.remove('hidden');
        
        document.querySelectorAll('.nav-link').forEach(link => link.classList.remove('active'));
        const navLink = document.getElementById('nav-' + pageId.replace('-section', ''));
        if (navLink) navLink.classList.add('active');
        
        document.getElementById('page-title').textContent = title;

        if (pageId === 'templates-section') Templates.load();
        else if (pageId === 'dashboard-section') App.loadDashboardData();
        else if (pageId === 'analytics-section') Analytics.loadData();
    }
};

// Event Handlers Setup
document.addEventListener('DOMContentLoaded', () => {
    lucide.createIcons();
    
    // Auth events
    document.getElementById('login-tab-manual').addEventListener('click', () => Auth.switchLoginTab('manual'));
    document.getElementById('login-tab-google').addEventListener('click', () => Auth.switchLoginTab('google'));
    document.getElementById('login-button').addEventListener('click', Auth.handleManualLogin);
    document.getElementById('google-login-button').addEventListener('click', Auth.handleGoogleLogin);
    // Logout button moved to top right profile panel
    
    // Navigation events
    document.querySelectorAll('.nav-link').forEach(link => {
        link.addEventListener('click', (e) => {
            e.preventDefault();
            const page = link.id.replace('nav-', '');
            const titles = { 
                'dashboard': 'Dashboard', 
                'campaign': 'New Campaign', 
                'templates': 'Email Templates', 
                'validation': 'Email Validation', 
                'analytics': 'Analytics' 
            };
            Navigation.showPage(page + '-section', titles[page]);
        });
    });
    
    // Quick actions
    document.getElementById('quick-new-campaign').addEventListener('click', () => Navigation.showPage('campaign-section', 'New Campaign'));
    document.getElementById('quick-manage-templates').addEventListener('click', () => Navigation.showPage('templates-section', 'Email Templates'));
    document.getElementById('quick-validate-emails').addEventListener('click', () => Navigation.showPage('validation-section', 'Email Validation'));
    document.getElementById('back-to-dashboard').addEventListener('click', () => Navigation.showPage('dashboard-section', 'Dashboard'));
    
    // Campaign events
    document.getElementById('step1-next').addEventListener('click', Campaign.handleStep1Next);
    document.getElementById('recipient-input').addEventListener('input', Campaign.handleRecipientInput);
    document.querySelectorAll('.preflight-check').forEach(el => el.addEventListener('change', Campaign.checkPreflight));
    
    // Template events
    document.getElementById('create-template-btn').addEventListener('click', Templates.showCreateModal);
    
    // Validation events
    document.getElementById('emails-to-validate').addEventListener('input', Validation.updateEmailCount);
    document.getElementById('validate-emails-btn').addEventListener('click', Validation.handleValidate);
    document.getElementById('clear-input-btn').addEventListener('click', Validation.clearInput);
    document.getElementById('back-to-dashboard-from-validation').addEventListener('click', () => Navigation.showPage('dashboard-section', 'Dashboard'));
    
    // Profile modal events (profile button moved to top right panel)
    document.getElementById('profile-close-btn').addEventListener('click', () => document.getElementById('profile-modal').classList.add('hidden'));
    document.getElementById('profile-save-btn').addEventListener('click', Profile.save);
    document.getElementById('change-password-btn').addEventListener('click', Profile.changePassword);

    // Profile dropdown events (toggle is added in auth.js after login)
    document.getElementById('dropdown-view-profile').addEventListener('click', Profile.open);
    document.getElementById('dropdown-edit-profile').addEventListener('click', Profile.open);
    document.getElementById('dropdown-change-password').addEventListener('click', () => {
        Profile.open();
        // Switch to password tab if modal has tabs, or just open modal
        setTimeout(() => {
            // Focus on password section
            document.getElementById('current-password').focus();
        }, 100);
    });
    document.getElementById('dropdown-logout').addEventListener('click', Auth.clearAuth);

    // Close dropdown when clicking outside
    document.addEventListener('click', (e) => {
        const dropdown = document.getElementById('profile-dropdown');
        const toggle = document.getElementById('profile-dropdown-toggle');
        const chevron = document.getElementById('profile-chevron');
        if (dropdown && !dropdown.classList.contains('hidden') && !dropdown.contains(e.target) && !toggle.contains(e.target)) {
            dropdown.classList.add('hidden');
            if (chevron) chevron.classList.remove('rotate-180');
        }
    });
    
    // Admin events
    document.getElementById('nav-admin').addEventListener('click', (e) => { e.preventDefault(); Admin.open(); Navigation.showPage('dashboard-section', 'Dashboard'); });
    document.getElementById('admin-panel-close-btn').addEventListener('click', () => document.getElementById('admin-panel-modal').classList.add('hidden'));
    document.getElementById('add-user-btn').addEventListener('click', Admin.addUser);
    document.getElementById('edit-user-close-btn').addEventListener('click', () => document.getElementById('edit-user-modal').classList.add('hidden'));
    document.getElementById('edit-user-save-btn').addEventListener('click', Admin.saveEditUser);
    
    // Contact modal events
    document.getElementById('contact-admin-link').addEventListener('click', (e) => {
        e.preventDefault();
        document.getElementById('contact-modal').classList.remove('hidden');
    });
    document.getElementById('contact-close-btn').addEventListener('click', () => document.getElementById('contact-modal').classList.add('hidden'));
    document.getElementById('email-admin-btn').addEventListener('click', () => {
        const subject = encodeURIComponent('I want to do the email karya too! Please guide me further!');
        const body = encodeURIComponent('Hello Admin,\n\nI am interested in joining the email karya group. Please guide me on how to get started.\n\nThanks!');
        window.location.href = `mailto:admin@kalkiavatar.org?subject=${subject}&body=${body}`;
    });

    // Initialize app
    const urlParams = new URLSearchParams(window.location.search);
    const tokenFromUrl = urlParams.get('token');
    const contactAdminFlag = urlParams.get('contact_admin');
    
    if (contactAdminFlag) {
        document.getElementById('contact-modal').classList.remove('hidden');
        window.history.replaceState({}, document.title, window.location.pathname);
    } else if (tokenFromUrl) {
        Auth.setToken(tokenFromUrl);
        window.history.replaceState({}, document.title, window.location.pathname);
        Auth.loadUserDataAndInitApp();
    } else if (Auth.getToken()) {
        Auth.loadUserDataAndInitApp();
    }
});

// Global functions for onclick handlers - organized in GlobalHandlers module
const GlobalHandlers = {
    goToStep: (step) => Campaign.goToStep(step),
    startCampaignExecution: () => Campaign.startExecution(),
    resetApp: () => Campaign.reset()
};

// Expose to global scope for onclick handlers
window.goToStep = GlobalHandlers.goToStep;
window.startCampaignExecution = GlobalHandlers.startCampaignExecution;
window.resetApp = GlobalHandlers.resetApp;