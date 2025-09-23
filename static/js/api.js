// API Module
const API = {
    async fetch(url, options = {}) {
        const token = Auth.getToken();
        const headers = { 'Content-Type': 'application/json', ...options.headers };
        if (token) headers['Authorization'] = `Bearer ${token}`;
        
        try {
            const response = await fetch(`${CONFIG.BACKEND_URL}${url}`, { ...options, headers });
            if (!response.ok) {
                if (response.status === 401) {
                    Auth.clearAuth();
                    throw new Error('Session expired. Please log in again.');
                }
                let errorData;
                try {
                    errorData = await response.json();
                } catch (jsonError) {
                    throw new Error(response.statusText || 'Request failed');
                }
                throw new Error(errorData.detail || 'Request failed');
            }
            
            if (response.status === 204) return null;
            return await response.json();
        } catch (error) {
            console.error('API fetch error:', error);
            if (error.name === 'TypeError' && error.message.includes('fetch')) {
                throw new Error('Network error: Please check your connection and try again.');
            }
            throw error;
        }
    },

    async sendEmail(fromEmail, toEmail, subject, body) {
        return await API.fetch('/api/send-email', {
            method: 'POST',
            body: JSON.stringify({ from_email: fromEmail, to_email: toEmail, subject: subject, body: body })
        });
    },

    async validateEmails(emails) {
        return await API.fetch('/email/validate', {
            method: 'POST',
            body: JSON.stringify({ emails: emails })
        });
    },

    async getTemplates() {
        return await API.fetch('/templates');
    },

    async createTemplate(template) {
        return await API.fetch('/templates', {
            method: 'POST',
            body: JSON.stringify(template)
        });
    },

    async updateTemplate(templateId, updates) {
        return await API.fetch(`/templates/${templateId}`, {
            method: 'PUT',
            body: JSON.stringify(updates)
        });
    },

    async deleteTemplate(templateId) {
        return await API.fetch(`/templates/${templateId}`, { method: 'DELETE' });
    },

    async getDashboardStats() {
        return await API.fetch('/dashboard/stats');
    },

    async getAnalytics() {
        return await API.fetch('/analytics');
    }
};