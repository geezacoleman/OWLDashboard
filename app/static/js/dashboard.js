// State management
let detectionActive = false;
let recordingActive = false;
let selectedOwl = null;

// Update systems stats every 2 seconds
setInterval(updateSystemStats, 2000);

function updateSystemStats() {
    fetch('/system_stats')
        .then(response => response.json())
        .then(owls => {
            updateBoomVisualization(owls);
            updateOwlGrid(owls);
        })
        .catch(error => console.error('Error updating stats:', error));
}

function updateBoomVisualization(owls) {
    const container = document.getElementById('owlPositions');
    container.innerHTML = '';

    Object.entries(owls).forEach(([id, owl]) => {
        const marker = document.createElement('div');
        marker.className = `owl-marker ${owl.detecting ? 'detecting' : ''} ${owl.error ? 'error' : ''}`;
        marker.textContent = parseInt(id) + 1;
        container.appendChild(marker);
    });
}

function updateOwlGrid(owls) {
    const grid = document.getElementById('owlGrid');
    grid.innerHTML = '';

    Object.entries(owls).forEach(([id, owl]) => {
        grid.appendChild(createOwlCard(id, owl));
    });
}

function createOwlCard(id, owl) {
    const card = document.createElement('div');
    card.className = 'owl-card';
    card.onclick = () => showVideo(id);

    card.innerHTML = `
        <div class="owl-card-header">
            <h3>OWL ${parseInt(id) + 1}</h3>
            ${owl.error ? '<span class="error-indicator">⚠️</span>' : ''}
        </div>
        <div class="owl-card-stats">
            <div>Temperature: ${owl.temp}°C</div>
            <div>CPU: ${owl.cpu}%</div>
        </div>
    `;

    return card;
}

function toggleDetection() {
    detectionActive = !detectionActive;
    const btn = document.getElementById('detectionButton');
    btn.classList.toggle('active');
    btn.innerHTML = `
        <span class="icon">⊕</span>
        Detection ${detectionActive ? 'Active' : 'Off'}
    `;
}

function toggleRecording() {
    recordingActive = !recordingActive;
    const btn = document.getElementById('recordButton');
    btn.classList.toggle('active');
    btn.innerHTML = `
        <span class="icon">⏺</span>
        ${recordingActive ? 'Recording' : 'Record'}
    `;
}

function showVideo(owlId) {
    selectedOwl = owlId;
    const videoFeed = document.getElementById('videoFeed');
    videoFeed.classList.remove('hidden');
    document.getElementById('videoTitle').textContent = `OWL ${parseInt(owlId) + 1} Video Feed`;
}

function closeVideo() {
    selectedOwl = null;
    document.getElementById('videoFeed').classList.add('hidden');
}