// Template Management Module
const Templates = {
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    },
    async load() {
        const grid = document.getElementById('templates-grid');
        grid.innerHTML = '<div class="col-span-full text-center p-8"><div class="lds-dual-ring mx-auto mb-4"></div><p>Loading templates...</p></div>';

        try {
            const templates = await API.getTemplates();
            const grid = document.getElementById('templates-grid');
            grid.innerHTML = '';
            templates.forEach(template => {
                const card = document.createElement('div');
                card.className = 'p-4 rounded-lg shadow hover:shadow-lg transition';
                card.style.backgroundColor = 'var(--bg-primary)';
                card.innerHTML = `
                    <h3 class="font-bold text-lg template-title">${this.escapeHtml(template.name)}</h3>
                    <p class="text-sm template-description">${this.escapeHtml(template.category)}</p>
                    <p class="mt-2 template-description">${this.escapeHtml(template.subject)}</p>
                    <div class="mt-4 flex justify-between">
                        <button class="text-blue-500 hover:underline" onclick="Templates.edit('${template.id}')">Edit</button>
                        <button class="text-red-500 hover:underline" onclick="Templates.delete('${template.id}', '${template.name}')">Delete</button>
                    </div>
                `;
                grid.appendChild(card);
            });
        } catch (error) {
            document.getElementById('templates-grid').innerHTML = `<div class="text-red-500 p-4">Error loading templates: ${this.escapeHtml(error.message)}</div>`;
        }
    },

    async showCreateModal() {
        const name = this.showPrompt('Template name:');
        if (!name) {
            this.showNotification('Template creation cancelled', 'info');
            return;
        }

        const subject = this.showPrompt('Email subject:');
        if (!subject) {
            this.showNotification('Template creation cancelled', 'info');
            return;
        }

        const body = this.showPrompt('Email body:');
        if (!body) {
            this.showNotification('Template creation cancelled', 'info');
            return;
        }

        const category = this.showPrompt('Category:');
        if (!category) {
            this.showNotification('Template creation cancelled', 'info');
            return;
        }

        try {
            await API.createTemplate({ name, subject, body, category });
            Templates.load();
            this.showNotification('Template created successfully!', 'success');
        } catch (error) {
            this.showNotification(`Failed to create template: ${error.message}`, 'error');
        }
    },

    async edit(templateId) {
        const newName = this.showPrompt('New template name:');
        if (newName) {
            try {
                await API.updateTemplate(templateId, { name: newName });
                Templates.load();
            } catch (error) {
                this.showNotification(`Failed to update template: ${error.message}`, 'error');
            }
        }
    },

    async delete(templateId, name) {
        if (this.showConfirm(`Delete template "${name}"?`)) {
            try {
                await API.deleteTemplate(templateId);
                Templates.load();
            } catch (error) {
                this.showNotification(`Failed to delete template: ${error.message}`, 'error');
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
    },

    showPrompt(message) {
        return prompt(message); // Temporary - replace with modal in production
    }
};