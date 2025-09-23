// Configuration and Constants
const CONFIG = {
    BACKEND_URL: 'http://localhost:8000',
    TOKEN_KEY: 'auth_token',
    GOOGLE_CLIENT_ID: '1088677655752-3q53kqi8iqmoflbrpt84ngm9hfbqt266.apps.googleusercontent.com'
};

// Initialize Google Client ID when DOM is ready
if (typeof document !== 'undefined') {
    document.addEventListener('DOMContentLoaded', () => {
        const googleOnload = document.getElementById('g_id_onload');
        if (googleOnload && CONFIG.GOOGLE_CLIENT_ID !== 'your-google-client-id-here') {
            googleOnload.setAttribute('data-client_id', CONFIG.GOOGLE_CLIENT_ID);
        }
    });
}

const ALL_SENDER_ACCOUNTS = [
    { id: 2, email: 'info@bhavishyamalika.com', name: 'Bhavishya Malika Info', type: 'work' },
    { id: 3, email: 'admin@kalkiavatar.org', name: 'Kalki Avatar Admin', type: 'work' }
];

// Global State
let currentState = { currentStep: 1, sender: null, template: null, recipients: [] };
let userData = null;
let SENDER_ACCOUNTS = [];