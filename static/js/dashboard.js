// Update OWL statuses every 2 seconds
setInterval(updateAllOwlStats, 2000);

function updateAllOwlStats() {
    fetch('/owls')
        .then(response => response.json())
        .then(owls => {
            Object.entries(owls).forEach(([owlId, owl]) => {
                updateOwlStats(owlId);
            });
        })
        .catch(error => console.error('Error updating OWL stats:', error));
}

function updateOwlStats(owlId) {
    fetch(`/owl/${owlId}/status`)
        .then(response => response.json())
        .then(stats => {
            // Update CPU
            const cpuElement = document.getElementById(`${owlId}-cpu`);
            if (cpuElement) {
                cpuElement.textContent = `${stats.cpu_percent}%`;
                cpuElement.style.color = getColorForPercentage(stats.cpu_percent, 100);
            }

            // Update Temperature
            const tempElement = document.getElementById(`${owlId}-temp`);
            if (tempElement) {
                tempElement.textContent = `${stats.cpu_temp}°C`;
                tempElement.style.color = getColorForPercentage(stats.cpu_temp, 85);
            }

            // Update Status
            const container = document.getElementById(`owl-${owlId}`);
            if (container) {
                const statusIndicator = container.querySelector('.status-indicator');
                if (statusIndicator) {
                    statusIndicator.className = `status-indicator ${stats.status}`;
                }
            }
        })
        .catch(error => console.error(`Error updating stats for ${owlId}:`, error));
}

function getColorForPercentage(value, max) {
    const percentage = value / max;
    const hue = ((1 - percentage) * 120).toFixed(0);
    return `hsl(${hue}, 70%, 50%)`;
}