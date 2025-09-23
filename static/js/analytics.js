// Analytics Module
const Analytics = {
    async loadData() {
        try {
            const analytics = await API.getAnalytics();

            // Helper function to safely update element text
            const updateElement = (id, value) => {
                const element = document.getElementById(id);
                if (element) {
                    element.textContent = value || '0';
                } else {
                    console.warn(`Element with id '${id}' not found`);
                }
            };

            // Update key metrics
            updateElement('analytics-total-emails', analytics.total_emails);
            updateElement('analytics-delivery-rate', `${analytics.delivery_stats?.delivery_rate || 0}%`);
            updateElement('analytics-bounce-rate', `${analytics.delivery_stats?.bounce_rate || 0}%`);
            updateElement('analytics-success-rate', `${analytics.delivery_stats?.success_rate || 0}%`);

            // Update time-based stats
            updateElement('today-sent', analytics.time_based?.today?.sent);
            updateElement('today-failed', analytics.time_based?.today?.failed);
            updateElement('today-bounced', analytics.time_based?.today?.bounced);

            updateElement('week-sent', analytics.time_based?.last_7_days?.sent);
            updateElement('week-failed', analytics.time_based?.last_7_days?.failed);
            updateElement('week-bounced', analytics.time_based?.last_7_days?.bounced);

            updateElement('month-sent', analytics.time_based?.last_30_days?.sent);
            updateElement('month-failed', analytics.time_based?.last_30_days?.failed);
            updateElement('month-bounced', analytics.time_based?.last_30_days?.bounced);

            // Update email distribution
            updateElement('campaign-emails-count', analytics.campaign_emails);
            updateElement('individual-emails-count', analytics.individual_emails);

            // Update performance summary
            updateElement('total-sent', analytics.status_breakdown?.sent);
            updateElement('total-failed', analytics.status_breakdown?.failed);
            updateElement('total-bounced', analytics.status_breakdown?.bounced);

        } catch (error) {
            console.error('Failed to load analytics data:', error);
            const analyticsSection = document.getElementById('analytics-section');
            if (analyticsSection) {
                analyticsSection.innerHTML = `
                    <div class="max-w-6xl mx-auto">
                        <div class="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded">
                            <strong>Error:</strong> Failed to load analytics data. ${error.message}
                        </div>
                    </div>
                `;
            } else {
                console.error('Analytics section not found');
            }
        }
    },

};