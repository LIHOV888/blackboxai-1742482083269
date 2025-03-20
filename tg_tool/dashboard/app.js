// Dashboard frontend application

// Constants
const API_ENDPOINTS = {
    stats: '/api/stats',
    logs: '/api/logs',
    uids: '/api/uids'
};

const UPDATE_INTERVAL = 1000; // Update every second

// State
let stats = {
    total_processed: 0,
    successful_scrapes: 0,
    failed_scrapes: 0,
    current_rate: 0,
    bandwidth_used: 0,
    estimated_time_remaining: 0,
    auto_add_stats: null,
    start_time: null
};

let recentUids = [];
let logs = [];

// UI Elements
const totalProcessedEl = document.querySelector('#total-processed');
const successfulEl = document.querySelector('#successful');
const failedEl = document.querySelector('#failed');
const autoAddEl = document.querySelector('#auto-add');
const uidsTableEl = document.querySelector('#uids-table');
const logsEl = document.querySelector('#logs');

// Fetch data from API
async function fetchData() {
    try {
        // Fetch stats
        const statsResponse = await fetch(API_ENDPOINTS.stats);
        if (statsResponse.ok) {
            stats = await statsResponse.json();
            updateStats();
        } else {
            console.error('Error fetching stats:', statsResponse.statusText);
        }

        // Fetch UIDs
        const uidsResponse = await fetch(API_ENDPOINTS.uids);
        if (uidsResponse.ok) {
            recentUids = await uidsResponse.json();
            updateUids();
        } else {
            console.error('Error fetching UIDs:', uidsResponse.statusText);
        }

        // Fetch logs
        const logsResponse = await fetch(API_ENDPOINTS.logs);
        if (logsResponse.ok) {
            logs = await logsResponse.json();
            updateLogs();
        } else {
            console.error('Error fetching logs:', logsResponse.statusText);
        }
    } catch (error) {
        console.error('Error fetching data:', error);
    }
}

// Update UI elements
function updateStats() {
    if (!stats) return;

    totalProcessedEl.textContent = stats.total_processed;
    totalProcessedEl.nextElementSibling.textContent = 
        `${stats.current_rate.toFixed(1)} UIDs/sec`;

    successfulEl.textContent = stats.successful_scrapes;
    successfulEl.nextElementSibling.textContent = 
        `${((stats.successful_scrapes / stats.total_processed) * 100).toFixed(1)}% success rate`;

    failedEl.textContent = stats.failed_scrapes;
    failedEl.nextElementSibling.textContent = 
        `${((stats.failed_scrapes / stats.total_processed) * 100).toFixed(1)}% failure rate`;

    if (stats.auto_add_stats) {
        autoAddEl.textContent = stats.auto_add_stats.successful_adds;
        autoAddEl.nextElementSibling.textContent = 
            `${((stats.auto_add_stats.successful_adds / stats.auto_add_stats.total_attempts) * 100).toFixed(1)}% success rate`;
    }
}

function updateUids() {
    if (!recentUids.length) return;

    const rows = recentUids.map(uid => `
        <tr>
            <td>${uid.uid}</td>
            <td>${uid.username || 'N/A'}</td>
            <td>${uid.status}</td>
            <td>${uid.activity_level}</td>
            <td>${uid.auto_add ? 'Yes' : 'No'}</td>
        </tr>
    `).join('');

    uidsTableEl.querySelector('tbody').innerHTML = rows;
}

function updateLogs() {
    if (!logs.length) return;

    const entries = logs.map(log => `
        <div class="log-entry ${log.level.toLowerCase()}">
            <span class="timestamp">${new Date(log.timestamp).toLocaleTimeString()}</span>
            <span class="level">${log.level}</span>
            <span class="message">${log.message}</span>
        </div>
    `).join('');

    logsEl.innerHTML = entries;
}

// Start periodic updates
setInterval(fetchData, UPDATE_INTERVAL);

// Initial fetch
fetchData();