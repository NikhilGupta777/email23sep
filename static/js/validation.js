// ULTRA-FAST EMAIL VALIDATOR - LIGHTNING SPEED
const Validation = {
    elements: {},
    lastResults: null,
    cache: new Map(),
    performance: { startTime: 0, endTime: 0, totalEmails: 0, processedEmails: 0 },

    // Email validation patterns
    patterns: {
        basic: /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/,
        strict: /^[a-zA-Z0-9]([a-zA-Z0-9._-]*[a-zA-Z0-9])?@[a-zA-Z0-9]([a-zA-Z0-9-]*[a-zA-Z0-9])?(\.[a-zA-Z]{2,})+$/
    },

    // Common domain typos
    domainCorrections: {
        'gmail.co': 'gmail.com',
        'gmail.cm': 'gmail.com',
        'gmai.com': 'gmail.com',
        'gmial.com': 'gmail.com',
        'yahoo.co': 'yahoo.com',
        'yahoo.cm': 'yahoo.com',
        'hotmail.co': 'hotmail.com',
        'hotmail.cm': 'hotmail.com',
        'outlook.co': 'outlook.com',
        'outlook.cm': 'outlook.com'
    },

    init() {
        this.elements = {
            emailsInput: document.getElementById('emails-to-validate'),
            emailCount: document.getElementById('email-count'),
            validationStatus: document.getElementById('validation-status'),
            validateBtn: document.getElementById('validate-emails-btn'),
            clearBtn: document.getElementById('clear-input-btn'),
            resultsContainer: document.getElementById('validation-results')
        };
        this.bindEvents();
        this.loadCache();
    },

    bindEvents() {
        if (this.elements.emailsInput) {
            this.elements.emailsInput.addEventListener('input', this.debounce(() => this.updateEmailCount(), 50));
            this.elements.emailsInput.addEventListener('paste', () => setTimeout(() => this.updateEmailCount(), 1));
        }
        if (this.elements.validateBtn) {
            this.elements.validateBtn.addEventListener('click', () => this.handleValidate());
        }
        if (this.elements.clearBtn) {
            this.elements.clearBtn.addEventListener('click', () => this.clearInput());
        }
    },

    debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    },

    getEmailsFromInput() {
        if (!this.elements.emailsInput) return [];

        const text = this.elements.emailsInput.value;
        if (!text.trim()) return [];

        // Extract emails using regex
        const emailRegex = /[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}/g;
        const matches = text.match(emailRegex);

        if (!matches) return [];

        // Remove duplicates and normalize
        return [...new Set(matches.map(email => email.toLowerCase().trim()))];
    },

    updateEmailCount() {
        if (!this.elements.emailsInput || !this.elements.emailCount || !this.elements.validationStatus || !this.elements.validateBtn) return;

        const emails = this.getEmailsFromInput();
        const count = emails.length;

        this.elements.emailCount.textContent = count.toLocaleString();

        if (count > 0) {
            this.elements.emailCount.className = 'text-blue-600 font-bold';
            this.elements.validationStatus.textContent = `⚡ ${count.toLocaleString()} emails ready - ULTRA FAST!`;
            this.elements.validationStatus.className = 'text-green-600 font-bold';
            this.elements.validateBtn.disabled = false;
        } else {
            this.elements.emailCount.className = 'text-gray-500';
            this.elements.validationStatus.textContent = 'Enter emails to validate';
            this.elements.validationStatus.className = 'text-gray-500';
            this.elements.validateBtn.disabled = true;
        }
    },

    // Client-side pre-validation
    validateEmailFormat(email) {
        const result = {
            email: email,
            valid: false,
            clientValid: false,
            reason: '',
            risk: 'low'
        };

        // Basic format check
        if (!this.patterns.basic.test(email)) {
            result.reason = 'Invalid format';
            return result;
        }

        // Length checks
        if (email.length > 254) {
            result.reason = 'Email too long';
            return result;
        }

        const [localPart, domain] = email.split('@');

        // Local part validation
        if (localPart.length > 64) {
            result.reason = 'Local part too long';
            return result;
        }

        if (localPart.startsWith('.') || localPart.endsWith('.')) {
            result.reason = 'Invalid local part';
            return result;
        }

        if (localPart.includes('..')) {
            result.reason = 'Invalid local part';
            return result;
        }

        // Domain validation
        if (domain.length > 253) {
            result.reason = 'Domain too long';
            return result;
        }

        if (domain.startsWith('-') || domain.endsWith('-')) {
            result.reason = 'Invalid domain';
            return result;
        }

        // Check for common typos
        const suggestion = this.domainCorrections[domain];
        if (suggestion) {
            result.reason = `Did you mean @${suggestion}?`;
            result.risk = 'medium';
        }

        // Strict validation
        if (this.patterns.strict.test(email) && result.reason === '') {
            result.clientValid = true;
            result.valid = true;
            result.reason = 'Format valid';
        } else if (result.reason === '') {
            result.clientValid = true;
            result.valid = true;
            result.reason = 'Basic format valid';
        }

        return result;
    },

    async handleValidate() {
        const emails = this.getEmailsFromInput();

        if (emails.length === 0) {
            this.showNotification('Please enter some emails to validate', 'error');
            return;
        }

        this.performance.startTime = Date.now();
        this.performance.totalEmails = emails.length;
        this.performance.processedEmails = 0;

        this.setLoadingState(true);

        try {
            // Step 1: Client-side pre-validation (instant)
            const clientResults = emails.map(email => this.validateEmailFormat(email));
            const validEmails = clientResults.filter(r => r.clientValid).map(r => r.email);

            this.updateProgress(clientResults.filter(r => r.valid).length, emails.length, 'Client validation complete');

            // Step 2: Server-side validation for valid emails only
            let serverResults = [];
            if (validEmails.length > 0) {
                serverResults = await this.validateEmailsServer(validEmails);
            }

            // Step 3: Combine results
            const allResults = this.combineResults(clientResults, serverResults);

            // Cache results
            allResults.forEach(result => {
                this.cache.set(result.email, { ...result, timestamp: Date.now() });
            });
            this.saveCache();

            this.displayResults(allResults);
            this.lastResults = allResults;

            this.performance.endTime = Date.now();
            const totalTime = this.performance.endTime - this.performance.startTime;
            this.showNotification(`⚡ Validated ${emails.length.toLocaleString()} emails in ${totalTime}ms!`, 'success');

        } catch (error) {
            console.error('Validation error:', error);
            this.showNotification(`Validation failed: ${error.message}`, 'error');
        } finally {
            this.setLoadingState(false);
        }
    },

    // Ultra-fast server validation with smart batching
    async validateEmailsServer(emails) {
        const batchSize = 50; // Much larger batches
        const results = [];
        const batches = [];

        // Create batches
        for (let i = 0; i < emails.length; i += batchSize) {
            batches.push(emails.slice(i, i + batchSize));
        }

        // Process batches in parallel (up to 3 concurrent)
        const concurrentLimit = 3;
        for (let i = 0; i < batches.length; i += concurrentLimit) {
            const batchPromises = batches.slice(i, i + concurrentLimit).map(async (batch, batchIndex) => {
                const globalBatchIndex = i + batchIndex;
                try {
                    this.updateProgress(
                        Math.floor((globalBatchIndex * batchSize + batch.length) / emails.length * 50) + 50,
                        emails.length,
                        `Processing batch ${globalBatchIndex + 1}/${batches.length}`
                    );

                    const response = await API.validateEmails(batch);
                    this.updateProgress(0, 0, `Processing batch ${globalBatchIndex + 1}/${batches.length}`);
                    return response.results || [];
                } catch (error) {
                    console.error(`Batch ${globalBatchIndex + 1} failed:`, error);
                    // Return failed results for this batch
                    return batch.map(email => ({
                        email: email,
                        valid: false,
                        deliverable: false,
                        reason: 'Server error - try again'
                    }));
                }
            });

            const batchResults = await Promise.all(batchPromises);
            results.push(...batchResults.flat());
        }

        return results;
    },

    combineResults(clientResults, serverResults) {
        const serverMap = new Map(serverResults.map(r => [r.email, r]));

        return clientResults.map(clientResult => {
            const serverResult = serverMap.get(clientResult.email);

            if (serverResult) {
                return {
                    ...clientResult,
                    valid: serverResult.valid,
                    deliverable: serverResult.deliverable || false,
                    reason: serverResult.deliverable ? 'Deliverable' : serverResult.reason || clientResult.reason
                };
            }

            return clientResult;
        });
    },

    updateProgress(current, total, message = '') {
        if (this.elements.validationStatus) {
            if (total > 0) {
                const percentage = Math.round((current / total) * 100);
                this.elements.validationStatus.textContent = `🚀 ${message} (${percentage}%)`;
            } else {
                this.elements.validationStatus.textContent = `🚀 ${message}`;
            }
        }
    },

    displayResults(results) {
        if (!this.elements.resultsContainer) return;

        const validCount = results.filter(r => r.valid).length;
        const invalidCount = results.filter(r => !r.valid).length;

        const html = `
            <div class="mb-6 bg-gradient-to-r from-blue-50 to-green-50 p-6 rounded-xl border">
                <h3 class="text-2xl font-bold mb-4 text-gray-800">Results:</h3>
                <div class="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
                    <div class="bg-white p-4 rounded-lg shadow border-l-4 border-green-500">
                        <div class="text-3xl font-bold text-green-600">${validCount.toLocaleString()}</div>
                        <div class="text-sm text-green-700 font-medium">Valid Format</div>
                    </div>
                    <div class="bg-white p-4 rounded-lg shadow border-l-4 border-red-500">
                        <div class="text-3xl font-bold text-red-600">${invalidCount.toLocaleString()}</div>
                        <div class="text-sm text-red-700 font-medium">Invalid Format</div>
                    </div>
                    <div class="bg-white p-4 rounded-lg shadow border-l-4 border-purple-500">
                        <div class="text-3xl font-bold text-purple-600">${results.length.toLocaleString()}</div>
                        <div class="text-sm text-purple-700 font-medium">Total Processed</div>
                    </div>
                </div>

                <div class="flex flex-wrap gap-2 mb-4">
                    <button onclick="Validation.exportResults('valid')" class="bg-green-600 text-white px-4 py-2 rounded-lg hover:bg-green-700 transition-colors font-medium">
                        📥 Export Valid (${validCount.toLocaleString()})
                    </button>
                    <button onclick="Validation.exportResults('all')" class="bg-gray-600 text-white px-4 py-2 rounded-lg hover:bg-gray-700 transition-colors font-medium">
                        📥 Export All (${results.length.toLocaleString()})
                    </button>
                    <button onclick="Validation.showStats()" class="bg-purple-600 text-white px-4 py-2 rounded-lg hover:bg-purple-700 transition-colors font-medium">
                        📊 Statistics
                    </button>
                    <button onclick="Validation.clearCache()" class="bg-orange-600 text-white px-4 py-2 rounded-lg hover:bg-orange-700 transition-colors font-medium">
                        🗑️ Clear Cache
                    </button>
                </div>
            </div>

            <div class="bg-white rounded-lg border shadow">
                <div class="p-4 border-b bg-gray-50 flex justify-between items-center">
                    <h4 class="font-bold text-gray-800">Detailed Results (${results.length.toLocaleString()} emails)</h4>
                    <div class="flex gap-2">
                        <select id="filter-select" onchange="Validation.filterResults()" class="text-sm border rounded px-3 py-1 bg-white">
                            <option value="all">All Results</option>
                            <option value="valid">Valid Only</option>
                            <option value="deliverable">Deliverable Only</option>
                            <option value="invalid">Invalid Only</option>
                        </select>
                        <input type="text" id="search-input" placeholder="Search..." onkeyup="Validation.searchResults()" class="text-sm border rounded px-3 py-1 w-32">
                    </div>
                </div>

                <div class="max-h-96 overflow-y-auto" id="results-list">
                    ${this.renderResultsList(results)}
                </div>
            </div>
        `;

        this.elements.resultsContainer.innerHTML = html;
        this.elements.resultsContainer.classList.remove('hidden');
    },

    renderResultsList(results) {
        return results.map(result => {
            const isValid = result.valid;
            const isDeliverable = result.deliverable;

            let statusClass, statusText, bgClass;

            if (isDeliverable) {
                statusClass = 'text-green-600';
                statusText = '✅ Deliverable';
                bgClass = 'bg-green-50 border-l-4 border-green-500';
            } else if (isValid) {
                statusClass = 'text-blue-600';
                statusText = '📧 Valid';
                bgClass = 'bg-blue-50 border-l-4 border-blue-500';
            } else {
                statusClass = 'text-red-600';
                statusText = '❌ Invalid';
                bgClass = 'bg-red-50 border-l-4 border-red-500';
            }

            return `
                <div class="p-3 border-b hover:bg-gray-50 result-item ${bgClass}" data-status="${isDeliverable ? 'deliverable' : isValid ? 'valid' : 'invalid'}" data-email="${result.email.toLowerCase()}">
                    <div class="flex items-center justify-between">
                        <div class="flex-1 min-w-0">
                            <div class="font-mono text-sm font-medium text-gray-900 truncate">${this.escapeHtml(result.email)}</div>
                            <div class="text-xs text-gray-600 mt-1">${this.escapeHtml(result.reason || 'No details')}</div>
                        </div>
                        <div class="text-right ml-4">
                            <div class="font-bold ${statusClass} text-sm">${statusText}</div>
                        </div>
                    </div>
                </div>
            `;
        }).join('');
    },

    filterResults() {
        const filter = document.getElementById('filter-select')?.value || 'all';
        const items = document.querySelectorAll('.result-item');

        items.forEach(item => {
            const status = item.dataset.status;
            item.style.display = (filter === 'all' || filter === status) ? 'block' : 'none';
        });
    },

    searchResults() {
        const query = (document.getElementById('search-input')?.value || '').toLowerCase();
        const items = document.querySelectorAll('.result-item');

        items.forEach(item => {
            const email = item.dataset.email;
            item.style.display = email.includes(query) ? 'block' : 'none';
        });
    },

    exportResults(type = 'all') {
        if (!this.lastResults) return;

        let dataToExport = this.lastResults;

        if (type === 'valid') {
            dataToExport = this.lastResults.filter(r => r.valid);
        }

        const csv = this.convertToCSV(dataToExport);
        this.downloadCSV(csv, `emails-${type}-${Date.now()}.csv`);

        this.showNotification(`⚡ Exported ${dataToExport.length.toLocaleString()} emails instantly!`, 'success');
    },

    convertToCSV(results) {
        const headers = ['Email', 'Valid', 'Deliverable', 'Reason'];
        const rows = results.map(r => [r.email, r.valid ? 'Yes' : 'No', r.deliverable ? 'Yes' : 'No', r.reason || '']);
        return [headers, ...rows].map(row => row.map(field => `"${String(field).replace(/"/g, '""')}"`).join(',')).join('\n');
    },

    downloadCSV(csv, filename) {
        const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
        const link = document.createElement('a');
        const url = URL.createObjectURL(blob);
        link.href = url;
        link.download = filename;
        link.style.display = 'none';
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        URL.revokeObjectURL(url);
    },

    showStats() {
        if (!this.lastResults) return;

        const total = this.lastResults.length;
        const valid = this.lastResults.filter(r => r.valid).length;
        const invalid = total - valid;

        const modal = document.createElement('div');
        modal.className = 'fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50';
        modal.innerHTML = `
            <div class="bg-white rounded-xl p-6 max-w-md w-full mx-4">
                <h3 class="text-xl font-bold mb-4">📊 Validation Statistics</h3>
                <div class="space-y-3">
                    <div class="flex justify-between"><span>Total Processed:</span><span class="font-bold">${total.toLocaleString()}</span></div>
                    <div class="flex justify-between"><span>Valid Format:</span><span class="font-bold text-blue-600">${valid.toLocaleString()} (${Math.round(valid / total * 100)}%)</span></div>
                    <div class="flex justify-between"><span>Invalid Format:</span><span class="font-bold text-red-600">${invalid.toLocaleString()} (${Math.round(invalid / total * 100)}%)</span></div>
                </div>
                <button onclick="this.parentElement.parentElement.remove()" class="w-full mt-4 bg-blue-600 text-white py-2 rounded-lg hover:bg-blue-700">Close</button>
            </div>
        `;
        document.body.appendChild(modal);
    },

    setLoadingState(loading) {
        if (!this.elements.validateBtn) return;

        if (loading) {
            this.elements.validateBtn.disabled = true;
            this.elements.validateBtn.innerHTML = `<div class="inline-block animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>Validating...`;
            if (this.elements.validationStatus) {
                this.elements.validationStatus.textContent = '🚀 Lightning fast validation in progress...';
                this.elements.validationStatus.className = 'text-blue-600 font-bold';
            }
        } else {
            this.elements.validateBtn.disabled = false;
            this.elements.validateBtn.innerHTML = `<i data-lucide="check-circle" class="w-4 h-4 mr-2"></i>Validate Emails`;
            if (window.lucide) lucide.createIcons();
        }
    },

    clearInput() {
        if (this.elements.emailsInput) this.elements.emailsInput.value = '';
        if (this.elements.resultsContainer) this.elements.resultsContainer.classList.add('hidden');
        this.updateEmailCount();
        this.lastResults = null;
    },

    clearCache() {
        this.cache.clear();
        localStorage.removeItem('email_validation_cache');
        this.showNotification('Cache cleared!', 'info');
    },

    loadCache() {
        try {
            const cached = localStorage.getItem('email_validation_cache');
            if (cached) {
                const parsed = JSON.parse(cached);
                this.cache = new Map(parsed);
            }
        } catch (error) {
            console.warn('Failed to load cache:', error);
            this.cache = new Map();
        }
    },

    saveCache() {
        try {
            // Only keep recent cache entries (last 24 hours)
            const now = Date.now();
            const recentEntries = Array.from(this.cache.entries())
                .filter(([_, data]) => now - data.timestamp < 24 * 60 * 60 * 1000)
                .slice(-1000); // Keep only last 1000 entries

            localStorage.setItem('email_validation_cache', JSON.stringify(recentEntries));
        } catch (error) {
            console.warn('Failed to save cache:', error);
        }
    },

    showNotification(message, type = 'info') {
        const colors = {
            success: 'bg-green-100 border-green-400 text-green-700',
            error: 'bg-red-100 border-red-400 text-red-700',
            info: 'bg-blue-100 border-blue-400 text-blue-700'
        };

        const notification = document.createElement('div');
        notification.className = `fixed top-4 right-4 p-4 border rounded-lg ${colors[type]} z-50 max-w-sm shadow-lg`;
        notification.textContent = message;
        document.body.appendChild(notification);
        setTimeout(() => notification.remove(), 3000);
    },

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
};

// Initialize
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => Validation.init());
} else {
    Validation.init();
}