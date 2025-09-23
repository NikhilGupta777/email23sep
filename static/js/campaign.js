// Campaign Management Module
const Campaign = {
    populateSenderAccounts() {
        const select = document.getElementById('sender-account');
        if (!select) {
            console.error('Sender account select element not found');
            return;
        }
        select.innerHTML = '';
        SENDER_ACCOUNTS.forEach((acc) => {
            const option = document.createElement('option');
            option.value = acc.id;
            option.textContent = `${acc.name} (${acc.email})`;
            select.appendChild(option);
        });
        if (SENDER_ACCOUNTS.length === 0) select.innerHTML = '<option disabled>No senders available</option>';
    },

    handleStep1Next() {
        const senderSelect = document.getElementById('sender-account');
        if (!senderSelect) return;
        const senderId = senderSelect.value;
        const selectedSender = SENDER_ACCOUNTS.find(s => s.id == senderId);
        if (!selectedSender) { 
            this.showNotification('Please select a sender.', 'error'); 
            return; 
        }
        currentState.sender = selectedSender;
        Campaign.goToStep(2);
    },

    populateTemplates(templates) {
        const container = document.getElementById('template-options');
        container.innerHTML = '';
        templates.forEach(tmpl => {
            const card = document.createElement('div');
            card.className = 'p-4 border rounded-lg cursor-pointer hover:bg-blue-50 hover:border-blue-500 transition';
            card.dataset.templateId = tmpl.id;
            const escapeHtml = (text) => {
                const div = document.createElement('div');
                div.textContent = text;
                return div.innerHTML;
            };
            card.innerHTML = `<div class="flex items-center"><i data-lucide="file-text" class="w-8 h-8 text-blue-600 mr-4"></i><div><h4 class="font-bold text-gray-800">${escapeHtml(tmpl.name)}</h4><p class="text-sm text-gray-500">${escapeHtml(tmpl.category)}</p></div></div>`;
            card.addEventListener('click', () => Campaign.selectTemplate(tmpl));
            container.appendChild(card);
        });
        lucide.createIcons();
    },

    selectTemplate(templateObject) {
        currentState.template = templateObject;
        document.querySelectorAll('#template-options > div').forEach(div => {
            div.classList.remove('bg-blue-100', 'border-blue-500');
            if (div.dataset.templateId === templateObject.id) div.classList.add('bg-blue-100', 'border-blue-500');
        });
        const escapeHtml = (text) => {
            const div = document.createElement('div');
            div.textContent = text;
            return div.innerHTML;
        };
        document.getElementById('preview-subject').textContent = `Subject: ${currentState.template.subject}`;
        document.getElementById('preview-body').textContent = currentState.template.body;
        document.getElementById('template-preview-container').classList.remove('hidden');
        document.getElementById('step2-next').disabled = false;
    },

    handleRecipientInput() {
        const lines = document.getElementById('recipient-input').value.trim().split('\n').filter(line => line);
        currentState.recipients = lines.map(line => {
            const parts = line.split(',');
            return { 
                email: parts[0]?.trim() || '', 
                name: parts[1]?.trim() || 'Valued Contact', 
                organization: parts[2]?.trim() || 'Your Organization' 
            };
        }).filter(r => r.email && r.email.includes('@'));
        document.getElementById('recipient-count').textContent = currentState.recipients.length;
        document.getElementById('step3-next').disabled = currentState.recipients.length === 0;
    },

    goToStep(stepNumber) {
        currentState.currentStep = stepNumber;
        document.querySelectorAll('.step-card').forEach(card => card.classList.add('hidden'));
        const currentStepCard = document.getElementById(`step-${stepNumber}`);
        if (currentStepCard) currentStepCard.classList.remove('hidden');
        if (stepNumber === 4) Campaign.prepareReview();
    },

    prepareReview() {
        document.getElementById('review-sender').textContent = currentState.sender.email;
        document.getElementById('review-template').textContent = currentState.template.name;
        document.getElementById('review-recipient-count').textContent = currentState.recipients.length;
        const samplesContainer = document.getElementById('review-samples');
        samplesContainer.innerHTML = '';
        const escapeHtml = (text) => {
            const div = document.createElement('div');
            div.textContent = text;
            return div.innerHTML;
        };
        currentState.recipients.slice(0, 3).forEach(recipient => {
            const filledSubject = Campaign.fillTemplate(currentState.template.subject, recipient);
            const filledBody = Campaign.fillTemplate(currentState.template.body, recipient);
            samplesContainer.innerHTML += `<div class="p-3 border-t first:border-t-0"><p class="text-sm text-gray-500">To: ${escapeHtml(recipient.email)}</p><p class="font-bold text-gray-800">${escapeHtml(filledSubject)}</p><hr class="my-1"><p class="text-gray-600 text-sm whitespace-pre-wrap">${escapeHtml(filledBody)}</p></div>`;
        });
        Campaign.checkPreflight();
    },

    checkPreflight() {
        const allChecked = [...document.querySelectorAll('.preflight-check')].every(c => c.checked);
        document.getElementById('send-button').disabled = !allChecked;
    },

    fillTemplate(templateString, recipient) {
        return templateString
            .replace(/\{\{name\}\}/g, recipient.name)
            .replace(/\{\{organization\}\}/g, recipient.organization)
            .replace(/\{\{email\}\}/g, recipient.email);
    },

    async startExecution() {
        Campaign.goToStep(5);
        const sendButton = document.getElementById('send-button');
        sendButton.disabled = true;
        sendButton.innerHTML = `<div class="lds-dual-ring"></div><span>Sending...</span>`;
        const logContainer = document.getElementById('sending-log');
        logContainer.innerHTML = '';
        let sentCount = 0, failCount = 0;
        const totalRecipients = currentState.recipients.length;
        
        const logMessage = (message, color = 'text-gray-400') => {
            logContainer.innerHTML += `<p><span class="text-gray-500">${new Date().toLocaleTimeString()}:</span> <span class="${color}">${message}</span></p>`;
            logContainer.scrollTop = logContainer.scrollHeight;
        };
        
        logMessage(`Starting campaign from ${currentState.sender.email}...`);
        
        for (let i = 0; i < totalRecipients; i++) {
            const recipient = currentState.recipients[i];
            document.getElementById('progress-text').textContent = `Sending ${i + 1} of ${totalRecipients}...`;
            const subject = Campaign.fillTemplate(currentState.template.subject, recipient);
            const body = Campaign.fillTemplate(currentState.template.body, recipient);
            
            try {
                await API.sendEmail(currentState.sender.email, recipient.email, subject, body);
                logMessage(`SUCCESS: Sent to ${recipient.email}.`, 'text-green-400');
                sentCount++;
            } catch (error) {
                logMessage(`FAILED: ${recipient.email}. (Reason: ${error.message})`, 'text-red-400');
                failCount++;
            }
            document.getElementById('progress-bar').style.width = `${((i + 1) / totalRecipients) * 100}%`;
        }
        
        logMessage(`Campaign finished!`, 'text-blue-400');
        document.getElementById('campaign-complete').classList.remove('hidden');
        document.getElementById('final-sent-count').textContent = sentCount;
        document.getElementById('final-fail-count').textContent = failCount;
    },

    reset() {
        Object.assign(currentState, { currentStep: 1, sender: null, template: null, recipients: [] });
        document.getElementById('recipient-input').value = '';
        Campaign.handleRecipientInput();
        document.querySelectorAll('.preflight-check').forEach(c => c.checked = false);
        Campaign.goToStep(1);
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
    }
};