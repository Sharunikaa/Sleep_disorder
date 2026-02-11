// Security Audit Dashboard JavaScript
let lastEventCount = 0;
let autoRefreshInterval = null;
let allEvents = [];
let currentTypeFilter = 'all';
let currentLocationFilter = 'all';
let currentSortOrder = 'newest';

// Toast notification system
function showToast(title, message, type = 'success') {
    const container = document.getElementById('toastContainer');
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    
    const icons = {
        success: '✅',
        error: '❌',
        warning: '⚠️'
    };
    
    toast.innerHTML = `
        <div class="toast-icon">${icons[type] || icons.success}</div>
        <div class="toast-content">
            <div class="toast-title">${title}</div>
            <div class="toast-message">${message}</div>
        </div>
        <button class="toast-close" onclick="closeToast(this)">×</button>
    `;
    
    container.appendChild(toast);
    
    // Auto-dismiss after 10 seconds
    setTimeout(() => {
        closeToast(toast.querySelector('.toast-close'));
    }, 10000);
}

function closeToast(button) {
    const toast = button.closest('.toast');
    toast.classList.add('hiding');
    setTimeout(() => {
        toast.remove();
    }, 300);
}

// Event type configuration
const eventConfig = {
    'KEY_GENERATION': { icon: '🔑', label: 'Key Generation', location: 'Client' },
    'ENCRYPTION': { icon: '🔐', label: 'Encryption', location: 'Client' },
    'SERVER_RECEIVED': { icon: '📥', label: 'Server Received', location: 'Server' },
    'FHE_INFERENCE': { icon: '⚙️', label: 'FHE Inference', location: 'Server' },
    'SERVER_RESPONSE': { icon: '📤', label: 'Server Response', location: 'Server' },
    'DECRYPTION': { icon: '🔓', label: 'Decryption', location: 'Client' },
    'DATA_FLOW': { icon: '📊', label: 'Data Flow', location: 'Both' },
    'PRIVACY_CHECK': { icon: '🛡️', label: 'Privacy Check', location: 'Client' },
    'PERFORMANCE_METRICS': { icon: '📈', label: 'Performance', location: 'Both' }
};

// Client-side events (can see plaintext)
const clientEvents = ['KEY_GENERATION', 'ENCRYPTION', 'DECRYPTION', 'PRIVACY_CHECK'];

// Server-side events (only encrypted data)
const serverEvents = ['SERVER_RECEIVED', 'FHE_INFERENCE', 'SERVER_RESPONSE'];

function formatTimestamp(timestamp) {
    const date = new Date(timestamp);
    const time = date.toLocaleTimeString('en-US', { hour12: false });
    const ms = date.getMilliseconds().toString().padStart(3, '0');
    return `${time}.${ms}`;
}

function formatSize(bytes) {
    if (!bytes || bytes === 0) return '-';
    if (bytes > 1024 * 1024) {
        return (bytes / (1024 * 1024)).toFixed(2) + ' MB';
    } else if (bytes > 1024) {
        return (bytes / 1024).toFixed(2) + ' KB';
    }
    return bytes + ' B';
}

function formatDuration(seconds) {
    if (!seconds || seconds === 0) return '-';
    if (seconds < 1) {
        return (seconds * 1000).toFixed(0) + ' ms';
    }
    return seconds.toFixed(3) + ' s';
}

function getPrivacyLevel(event) {
    if (clientEvents.includes(event.type)) {
        return { level: 'low', label: 'Low', class: 'red' };
    } else if (serverEvents.includes(event.type)) {
        return { level: 'high', label: 'High', class: 'green' };
    } else {
        return { level: 'medium', label: 'Medium', class: 'yellow' };
    }
}

function getLocationBadge(event) {
    const config = eventConfig[event.type];
    const location = config ? config.location : 'Unknown';
    
    if (location === 'Client') {
        return '<span class="status-badge client">👤 Client</span>';
    } else if (location === 'Server') {
        return '<span class="status-badge server">🖥️ Server</span>';
    } else {
        return '<span class="status-badge plaintext">📊 Both</span>';
    }
}

function createTableRow(event, index) {
    const config = eventConfig[event.type] || { icon: '📌', label: event.type, location: 'Unknown' };
    const privacy = getPrivacyLevel(event);
    
    // Extract data size and duration
    let dataSize = 0;
    let duration = 0;
    
    if (event.data) {
        // Try to find size information
        dataSize = event.data.size || event.data.encrypted_input_size || 
                   event.data.eval_keys_size || event.data.private_key_size || 0;
        
        // Try to find duration information
        duration = event.data.duration || event.data.inference_time || 
                   event.data.generation_time || event.data.decryption_time || 0;
    }
    
    return `
        <tr onclick="showEventDetail(${index})">
            <td>
                <div class="event-type-cell">
                    <span class="event-icon">${config.icon}</span>
                    <div>
                        <div class="event-name">${config.label}</div>
                        <div class="event-timestamp">${formatTimestamp(event.timestamp)}</div>
                    </div>
                </div>
            </td>
            <td>${formatTimestamp(event.timestamp)}</td>
            <td>${getLocationBadge(event)}</td>
            <td><span class="privacy-badge ${privacy.level}">${privacy.label}</span></td>
            <td><span class="metric-badge ${privacy.class}">${formatSize(dataSize)}</span></td>
            <td><span class="metric-badge ${duration > 1 ? 'orange' : 'green'}">${formatDuration(duration)}</span></td>
        </tr>
    `;
}

async function refreshEvents() {
    try {
        const response = await fetch('/api/security/events');
        const data = await response.json();
        
        allEvents = data.events || [];
        
        // Update total count
        document.getElementById('totalEvents').textContent = allEvents.length;
        
        // Apply current filters to maintain filter state
        filterEvents();
        
        lastEventCount = allEvents.length;

    } catch (error) {
        console.error('Error fetching events:', error);
        document.getElementById('eventsTableBody').innerHTML = `
            <tr>
                <td colspan="6">
                    <div class="empty-state">
                        <div class="empty-state-icon">⚠️</div>
                        <div class="empty-state-text">Error loading events</div>
                        <div class="empty-state-subtext">${error.message}</div>
                    </div>
                </td>
            </tr>
        `;
    }
}

function renderTable(events) {
    const tbody = document.getElementById('eventsTableBody');
    
    if (!events || events.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="6">
                    <div class="empty-state">
                        <div class="empty-state-icon">📭</div>
                        <div class="empty-state-text">No events matching filters</div>
                        <div class="empty-state-subtext">Try adjusting your filters or search</div>
                    </div>
                </td>
            </tr>
        `;
        return;
    }
    
    // Sort based on current sort order
    let sortedEvents = [...events];
    if (currentSortOrder === 'newest') {
        sortedEvents.reverse();
    }
    
    // Map events to their original indices for the modal
    tbody.innerHTML = sortedEvents.map((event, displayIndex) => {
        // Find original index in allEvents array
        const originalIndex = allEvents.findIndex(e => e.timestamp === event.timestamp && e.type === event.type);
        return createTableRow(event, originalIndex);
    }).join('');
}

function filterEvents() {
    const searchTerm = document.getElementById('searchInput').value.toLowerCase();
    
    let filtered = allEvents;
    
    // Apply type filter
    if (currentTypeFilter !== 'all') {
        filtered = filtered.filter(event => event.type === currentTypeFilter);
    }
    
    // Apply location filter
    if (currentLocationFilter !== 'all') {
        filtered = filtered.filter(event => {
            const config = eventConfig[event.type] || {};
            return config.location === currentLocationFilter;
        });
    }
    
    // Apply search filter
    if (searchTerm) {
        filtered = filtered.filter(event => {
            const config = eventConfig[event.type] || {};
            const searchableText = `
                ${event.type} 
                ${config.label || ''} 
                ${config.location || ''} 
                ${JSON.stringify(event.data || {})}
            `.toLowerCase();
            
            return searchableText.includes(searchTerm);
        });
    }
    
    renderTable(filtered);
}

// Dropdown functions
function toggleDropdown(dropdownId) {
    // Close all other dropdowns
    document.querySelectorAll('.dropdown-menu').forEach(menu => {
        if (menu.id !== dropdownId) {
            menu.classList.remove('show');
        }
    });
    
    // Toggle the clicked dropdown
    const dropdown = document.getElementById(dropdownId);
    dropdown.classList.toggle('show');
}

// Close dropdowns when clicking outside
document.addEventListener('click', function(event) {
    if (!event.target.closest('.filter-dropdown')) {
        document.querySelectorAll('.dropdown-menu').forEach(menu => {
            menu.classList.remove('show');
        });
    }
});

function setTypeFilter(type) {
    currentTypeFilter = type;
    const label = type === 'all' ? 'All' : (eventConfig[type]?.label || type);
    document.getElementById('typeFilterLabel').textContent = label;
    
    // Close dropdown
    const dropdown = document.getElementById('typeFilter');
    if (dropdown) {
        dropdown.classList.remove('show');
    }
    
    // Apply filter
    filterEvents();
}

function setLocationFilter(location) {
    currentLocationFilter = location;
    const label = location === 'all' ? 'All' : location;
    document.getElementById('locationFilterLabel').textContent = label;
    
    // Close dropdown
    const dropdown = document.getElementById('locationFilter');
    if (dropdown) {
        dropdown.classList.remove('show');
    }
    
    // Apply filter
    filterEvents();
}

function setSortOrder(order) {
    currentSortOrder = order;
    const label = order === 'newest' ? 'Newest' : 'Oldest';
    document.getElementById('sortFilterLabel').textContent = label;
    
    // Close dropdown
    const dropdown = document.getElementById('sortFilter');
    if (dropdown) {
        dropdown.classList.remove('show');
    }
    
    // Apply filter
    filterEvents();
}

async function exportEvents() {
    try {
        // Create a JSON blob from current events
        const dataStr = JSON.stringify(allEvents, null, 2);
        const dataBlob = new Blob([dataStr], { type: 'application/json' });
        
        // Create download link
        const url = URL.createObjectURL(dataBlob);
        const link = document.createElement('a');
        link.href = url;
        link.download = `security_events_${new Date().toISOString().split('T')[0]}.json`;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        URL.revokeObjectURL(url);
        
        showToast('Export Successful', `Exported ${allEvents.length} events to JSON file`, 'success');
    } catch (error) {
        console.error('Error exporting events:', error);
        showToast('Export Failed', 'Could not export events. Please try again.', 'error');
    }
}

async function clearEvents() {
    if (!confirm('⚠️ Are you sure you want to clear all events? This cannot be undone.')) {
        return;
    }
    
    try {
        const response = await fetch('/api/security/clear', { method: 'POST' });
        if (response.ok) {
            allEvents = [];
            lastEventCount = 0;
            document.getElementById('totalEvents').textContent = '0';
            renderTable([]);
            showToast('Events Cleared', 'All security events have been cleared successfully', 'success');
        } else {
            showToast('Clear Failed', 'Failed to clear events. Please try again.', 'error');
        }
    } catch (error) {
        console.error('Error clearing events:', error);
        showToast('Clear Failed', 'An error occurred while clearing events', 'error');
    }
}

// Auto-refresh setup
document.addEventListener('DOMContentLoaded', function() {
    const autoRefreshCheckbox = document.getElementById('autoRefresh');
    if (autoRefreshCheckbox) {
        autoRefreshCheckbox.addEventListener('change', function() {
            if (this.checked) {
                autoRefreshInterval = setInterval(refreshEvents, 5000);
            } else {
                if (autoRefreshInterval) {
                    clearInterval(autoRefreshInterval);
                    autoRefreshInterval = null;
                }
            }
        });
    }
    
    // Initial load and start auto-refresh
    refreshEvents();
    autoRefreshInterval = setInterval(refreshEvents, 5000);
});

// Modal functions
function showEventDetail(index) {
    const event = allEvents[index];
    if (!event) return;
    
    const config = eventConfig[event.type] || { icon: '📌', label: event.type, location: 'Unknown' };
    const privacy = getPrivacyLevel(event);
    
    // Set modal title
    document.getElementById('modalIcon').textContent = config.icon;
    document.getElementById('modalEventType').textContent = config.label;
    
    // Build modal body
    let bodyHTML = '';
    
    // Basic Information Section
    bodyHTML += `
        <div class="detail-section">
            <h3>📋 Basic Information</h3>
            <div class="detail-grid">
                <div class="detail-label">Event Type:</div>
                <div class="detail-value">${config.label}</div>
                
                <div class="detail-label">Timestamp:</div>
                <div class="detail-value">${formatTimestamp(event.timestamp)}</div>
                
                <div class="detail-label">Location:</div>
                <div class="detail-value">${config.location}</div>
                
                <div class="detail-label">Privacy Level:</div>
                <div class="detail-value">
                    <span class="privacy-badge ${privacy.level}">${privacy.label}</span>
                </div>
            </div>
        </div>
    `;
    
    // Encryption Details Section
    if (event.data && Object.keys(event.data).length > 0) {
        bodyHTML += `
            <div class="detail-section">
                <h3>🔐 Encryption Details</h3>
                <div class="detail-grid">
        `;
        
        for (const [key, value] of Object.entries(event.data)) {
            let displayValue = value;
            let valueClass = 'detail-value';
            
            // Format different types of values
            if (typeof value === 'number') {
                if (key.includes('time') || key.includes('duration')) {
                    displayValue = formatDuration(value);
                } else if (key.includes('size')) {
                    displayValue = formatSize(value);
                }
            } else if (typeof value === 'string' && value.length > 100) {
                displayValue = value.substring(0, 100) + '...';
            } else if (typeof value === 'object') {
                displayValue = JSON.stringify(value, null, 2);
            }
            
            // Highlight encrypted vs plaintext data
            if (key.includes('encrypted') || key.includes('eval_keys')) {
                valueClass += ' encrypted';
            } else if (key.includes('plaintext') || key.includes('decrypted')) {
                valueClass += ' plaintext';
            }
            
            bodyHTML += `
                <div class="detail-label">${key}:</div>
                <div class="${valueClass}">${displayValue}</div>
            `;
        }
        
        bodyHTML += `
                </div>
            </div>
        `;
    }
    
    // Privacy Guarantees Section
    if (serverEvents.includes(event.type)) {
        bodyHTML += `
            <div class="detail-section">
                <h3>🛡️ Privacy Guarantees</h3>
                <div class="detail-grid">
                    <div class="detail-label">Server Access:</div>
                    <div class="detail-value encrypted">❌ Cannot see plaintext data</div>
                    
                    <div class="detail-label">Encryption:</div>
                    <div class="detail-value encrypted">✅ Fully Homomorphic Encryption (FHE)</div>
                    
                    <div class="detail-label">Data Privacy:</div>
                    <div class="detail-value encrypted">✅ Computation on encrypted data</div>
                    
                    <div class="detail-label">Key Location:</div>
                    <div class="detail-value encrypted">🔑 Private key never leaves client</div>
                </div>
            </div>
        `;
    } else if (clientEvents.includes(event.type)) {
        bodyHTML += `
            <div class="detail-section">
                <h3>🛡️ Privacy Information</h3>
                <div class="detail-grid">
                    <div class="detail-label">Client Access:</div>
                    <div class="detail-value plaintext">✅ Can see plaintext data</div>
                    
                    <div class="detail-label">Location:</div>
                    <div class="detail-value plaintext">👤 Client-side operation</div>
                    
                    <div class="detail-label">Data State:</div>
                    <div class="detail-value plaintext">📝 Plaintext available for ${event.type === 'ENCRYPTION' ? 'encryption' : 'decryption'}</div>
                </div>
            </div>
        `;
    }
    
    document.getElementById('modalBody').innerHTML = bodyHTML;
    document.getElementById('eventModal').classList.add('show');
    document.body.style.overflow = 'hidden'; // Prevent background scrolling
}

function closeModal() {
    document.getElementById('eventModal').classList.remove('show');
    document.body.style.overflow = ''; // Restore scrolling
}

function closeModalOnOverlay(event) {
    if (event.target.id === 'eventModal') {
        closeModal();
    }
}

// Close modal with Escape key
document.addEventListener('keydown', function(event) {
    if (event.key === 'Escape') {
        closeModal();
    }
});

// Cleanup on page unload
window.addEventListener('beforeunload', () => {
    if (autoRefreshInterval) {
        clearInterval(autoRefreshInterval);
    }
});
