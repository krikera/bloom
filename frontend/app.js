/**
 * BloomWatch Frontend Application
 * Connects to NASA satellite data API
 */

// Configuration
const API_BASE_URL = window.location.origin + '/api';

// Global map instance
let map = null;
let markers = [];
let blo/**
 * Display bloom detection results
 */
function displayBloomResults(data, formData) {
    const results = document.getElementById('results');
    
    console.log('📊 DISPLAYING RESULTS:');
    console.log('  Data:', data);
    console.log('  Form Data:', formData);
    
    if (!data || data.status !== 'success') {
        results.innerHTML = `
            <div class="alert alert-warning">
                <h5><i class="fas fa-info-circle"></i> No Data Available</h5>
                <p>Could not retrieve bloom data for this location and time period.</p>
            </div>
        `;
        return;
    }
    
    const stats = data.statistics || {};
    const blooms = data.bloom_events || [];
    
    console.log('  Statistics:', stats);
    console.log('  Bloom Events Count:', blooms.length);
    blooms.forEach((bloom, i) => {
        console.log(`  Bloom #${i+1}:`, bloom);
        console.log(`    - Start Date: ${bloom.start_date || 'N/A'}`);
        console.log(`    - Peak Date: ${bloom.peak_date || 'N/A'}`);
        console.log(`    - End Date: ${bloom.end_date || 'N/A'}`);
        console.log(`    - Peak NDVI: ${bloom.peak_ndvi || 'N/A'}`);
    });
    
    let html = '<div class="results-container">';
    
    // Summary card
    html += `
        <div class="card mb-3">
            <div class="card-header bg-primary text-white">
                <h5 class="mb-0"><i class="fas fa-chart-line"></i> Bloom Analysis Results</h5>
            </div>
            <div class="card-body">
                <div class="row">
                    <div class="col-md-6">
                        <p><strong>Location:</strong> ${formData.lat.toFixed(4)}°, ${formData.lon.toFixed(4)}°</p>
                        <p><strong>Date Range:</strong> ${formData.start_date} to ${formData.end_date}</p>
                        <p><strong>Satellite:</strong> ${getSatelliteName(formData.satellite)}</p>
                    </div>
                    <div class="col-md-6">
                        <p><strong>Average NDVI:</strong> ${(stats.average_ndvi || 0).toFixed(3)}</p>
                        <p><strong>Peak Bloom Date:</strong> ${stats.peak_bloom_date || 'N/A'}</p>
                        <p><strong>Total Bloom Events:</strong> ${stats.total_events || 0}</p>
                    </div>
                </div>
            </div>
        </div>
    `;
    
    // Bloom events
    if (blooms.length > 0) {
        html += `
            <div class="card mb-3">
                <div class="card-header bg-success text-white">
                    <h5 class="mb-0"><i class="fas fa-flower"></i> Detected Bloom Events (${blooms.length})</h5>
                </div>
                <div class="card-body">
                    <div class="list-group">
        `;
        
        blooms.forEach((bloom, index) => {
            html += `
                <div class="list-group-item">
                    <h6>Bloom Event #${index + 1}</h6>
                    <p class="mb-1"><strong>Start:</strong> ${bloom.start_date || 'N/A'}</p>
                    <p class="mb-1"><strong>Peak:</strong> ${bloom.peak_date || 'N/A'}</p>
                    <p class="mb-1"><strong>End:</strong> ${bloom.end_date || 'N/A'}</p>
                    <p class="mb-1"><strong>Duration:</strong> ${bloom.duration_observations || 0} days</p>
                    <p class="mb-1"><strong>Intensity:</strong> <span class="badge bg-${getIntensityColor(bloom.intensity)}">${bloom.intensity || 'unknown'}</span></p>
                </div>
            `;
        });
        
        html += `
                    </div>
                </div>
            </div>
        `;
    } else {
        html += `
            <div class="alert alert-info">
                <h5><i class="fas fa-info-circle"></i> No Blooms Detected</h5>
                <p>No significant bloom events were detected during this period.</p>
                <p>This could mean:</p>
                <ul>
                    <li>The location doesn't have flowering vegetation</li>
                    <li>The bloom season is outside the selected date range</li>
                    <li>Cloud cover prevented clear observations</li>
                </ul>
            </div>
        `;
    }
    
    html += '</div>';
    results.innerHTML = html;
}

// Initialize application when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    initializeMap();
    loadFamousBloomRegions();
    setupEventListeners();
    checkAPIConnection();
});

/**
 * Initialize Leaflet map
 */
function initializeMap() {
    // Create map centered on world view
    map = L.map('map').setView([20, 0], 2);
    
    // Add OpenStreetMap tile layer
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '© OpenStreetMap contributors',
        maxZoom: 18
    }).addTo(map);
    
    // Add click handler to map
    map.on('click', function(e) {
        document.getElementById('latitude').value = e.latlng.lat.toFixed(6);
        document.getElementById('longitude').value = e.latlng.lng.toFixed(6);
        
        // Add temporary marker
        L.marker([e.latlng.lat, e.latlng.lng])
            .addTo(map)
            .bindPopup(`Selected: ${e.latlng.lat.toFixed(4)}°, ${e.latlng.lng.toFixed(4)}°`)
            .openPopup();
    });
}

/**
 * Load famous bloom regions from API
 */
async function loadFamousBloomRegions() {
    try {
        const response = await fetch(`${API_BASE_URL}/regions/suggest`);
        const data = await response.json();
        
        if (data.regions) {
            data.regions.forEach(region => {
                const marker = L.marker([region.lat, region.lon], {
                    icon: L.divIcon({
                        className: 'bloom-marker',
                        html: '<i class="fas fa-flower" style="color: #e91e63; font-size: 24px;"></i>',
                        iconSize: [30, 30]
                    })
                }).addTo(map);
                
                marker.bindPopup(`
                    <div style="min-width: 200px;">
                        <h6><strong>${region.name}</strong></h6>
                        <p class="mb-1"><small>${region.description}</small></p>
                        <p class="mb-1"><small><strong>Best Season:</strong> ${region.best_season}</small></p>
                        <p class="mb-1"><small><strong>Type:</strong> ${region.bloom_type}</small></p>
                        <button class="btn btn-sm btn-primary mt-2" onclick="selectRegion(${region.lat}, ${region.lon}, '${region.name}')">
                            Select This Location
                        </button>
                    </div>
                `);
                
                markers.push(marker);
            });
            
            console.log(`✅ Loaded ${data.regions.length} famous bloom locations`);
        }
    } catch (error) {
        console.error('Error loading bloom regions:', error);
        showNotification('Could not load famous bloom locations', 'warning');
    }
}

/**
 * Select a region and populate form
 */
window.selectRegion = function(lat, lon, name) {
    document.getElementById('latitude').value = lat;
    document.getElementById('longitude').value = lon;
    map.setView([lat, lon], 10);
    
    showNotification(`Selected: ${name}`, 'success');
    
    // Scroll to form
    document.getElementById('bloom-form-section').scrollIntoView({ behavior: 'smooth' });
};

/**
 * Setup event listeners
 */
function setupEventListeners() {
    // Main bloom detection form
    document.getElementById('bloomForm').addEventListener('submit', handleBloomDetection);
    
    // Data availability check button
    const checkDataBtn = document.getElementById('checkDataBtn');
    if (checkDataBtn) {
        checkDataBtn.addEventListener('click', checkDataAvailability);
    }
    
    // Satellite selector change
    document.getElementById('satellite').addEventListener('change', function(e) {
        if (e.target.value === 'combined') {
            showNotification('Using combined mode for maximum coverage (~3 day revisit)!', 'info');
        }
    });
}

/**
 * Check API connection status
 */
async function checkAPIConnection() {
    try {
        const response = await fetch(`${API_BASE_URL}`);
        const data = await response.json();
        
        if (data.name === 'BloomWatch API') {
            console.log('✅ API Connected:', data.version);
            document.getElementById('apiStatus').innerHTML = 
                '<span class="badge bg-success"><i class="fas fa-check-circle"></i> API Connected</span>';
        }
    } catch (error) {
        console.error('❌ API Connection Failed:', error);
        document.getElementById('apiStatus').innerHTML = 
            '<span class="badge bg-danger"><i class="fas fa-times-circle"></i> API Offline</span>';
    }
}

/**
 * Handle bloom detection form submission
 */
async function handleBloomDetection(e) {
    e.preventDefault();
    
    const loading = document.getElementById('loading');
    const results = document.getElementById('results');
    const progressBar = document.getElementById('progressBar');
    
    // Show loading
    loading.style.display = 'block';
    results.innerHTML = '';
    progressBar.style.width = '0%';
    
    // Collect form data
    const formData = {
        lat: parseFloat(document.getElementById('latitude').value),
        lon: parseFloat(document.getElementById('longitude').value),
        start_date: document.getElementById('startDate').value,
        end_date: document.getElementById('endDate').value,
        satellite: document.getElementById('satellite').value
    };
    
    try {
        // Simulate progress
        let progress = 0;
        const progressInterval = setInterval(() => {
            progress += 10;
            progressBar.style.width = `${Math.min(progress, 90)}%`;
        }, 200);
        
        // Call bloom detection API
        const response = await fetch(`${API_BASE_URL}/bloom/detect`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(formData)
        });
        
        clearInterval(progressInterval);
        progressBar.style.width = '100%';
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        
        // Log the API response for debugging
        console.log('🌸 BLOOM DETECTION API RESPONSE:');
        console.log('  Full Response:', data);
        console.log('  Status:', data.status);
        console.log('  Bloom Events:', data.bloom_events);
        console.log('  Statistics:', data.statistics);
        
        // Hide loading
        setTimeout(() => {
            loading.style.display = 'none';
            displayBloomResults(data, formData);
        }, 500);
        
    } catch (error) {
        loading.style.display = 'none';
        console.error('Error detecting blooms:', error);
        results.innerHTML = `
            <div class="alert alert-danger">
                <h5><i class="fas fa-exclamation-triangle"></i> Error</h5>
                <p>${error.message}</p>
                <p><small>Please check your internet connection and try again.</small></p>
            </div>
        `;
    }
}

/**
 * Display bloom detection results
 */
function displayBloomResults(data, formData) {
    const results = document.getElementById('results');
    
    if (!data || data.status !== 'success') {
        results.innerHTML = `
            <div class="alert alert-warning">
                <h5><i class="fas fa-info-circle"></i> No Data Available</h5>
                <p>Could not retrieve bloom data for this location and time period.</p>
            </div>
        `;
        return;
    }
    
    const stats = data.statistics || {};
    const blooms = data.bloom_events || [];
    
    let html = '<div class="results-container">';
    
    // Summary card
    html += `
        <div class="card mb-3">
            <div class="card-header bg-primary text-white">
                <h5 class="mb-0"><i class="fas fa-chart-line"></i> Bloom Analysis Results</h5>
            </div>
            <div class="card-body">
                <div class="row">
                    <div class="col-md-6">
                        <p><strong>Location:</strong> ${formData.lat.toFixed(4)}°, ${formData.lon.toFixed(4)}°</p>
                        <p><strong>Date Range:</strong> ${formData.start_date} to ${formData.end_date}</p>
                        <p><strong>Satellite:</strong> ${getSatelliteName(formData.satellite)}</p>
                    </div>
                    <div class="col-md-6">
                        <p><strong>Average NDVI:</strong> ${(stats.average_ndvi || 0).toFixed(3)}</p>
                        <p><strong>Peak Bloom Date:</strong> ${stats.peak_bloom_date || 'N/A'}</p>
                        <p><strong>Total Bloom Events:</strong> ${stats.total_events || 0}</p>
                    </div>
                </div>
            </div>
        </div>
    `;
    
    // Bloom events
    if (blooms.length > 0) {
        html += `
            <div class="card mb-3">
                <div class="card-header bg-success text-white">
                    <h5 class="mb-0"><i class="fas fa-flower"></i> Detected Bloom Events (${blooms.length})</h5>
                </div>
                <div class="card-body">
                    <div class="list-group">
        `;
        
        blooms.forEach((bloom, index) => {
            html += `
                <div class="list-group-item">
                    <h6>Bloom Event #${index + 1}</h6>
                    <p class="mb-1"><strong>Start:</strong> ${bloom.start_date || 'N/A'}</p>
                    <p class="mb-1"><strong>Peak:</strong> ${bloom.peak_date || 'N/A'}</p>
                    <p class="mb-1"><strong>End:</strong> ${bloom.end_date || 'N/A'}</p>
                    <p class="mb-1"><strong>Duration:</strong> ${bloom.duration || 0} days</p>
                    <p class="mb-0"><strong>Intensity:</strong> 
                        <span class="badge bg-${getIntensityColor(bloom.intensity)}">${bloom.intensity || 'Medium'}</span>
                    </p>
                </div>
            `;
        });
        
        html += `
                    </div>
                </div>
            </div>
        `;
    } else {
        html += `
            <div class="alert alert-info">
                <h5><i class="fas fa-info-circle"></i> No Blooms Detected</h5>
                <p>No significant bloom events were detected during this period.</p>
                <p><small>This could mean:</small></p>
                <ul class="small mb-0">
                    <li>The location doesn't have flowering vegetation</li>
                    <li>The bloom season is outside the selected date range</li>
                    <li>Cloud cover prevented clear observations</li>
                </ul>
            </div>
        `;
    }
    
    html += '</div>';
    results.innerHTML = html;
    
    // Scroll to results
    results.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
}

/**
 * Check data availability for location
 */
async function checkDataAvailability() {
    const lat = parseFloat(document.getElementById('latitude').value);
    const lon = parseFloat(document.getElementById('longitude').value);
    const startDate = document.getElementById('startDate').value;
    const endDate = document.getElementById('endDate').value;
    
    if (!lat || !lon || !startDate || !endDate) {
        showNotification('Please fill in all location and date fields first', 'warning');
        return;
    }
    
    try {
        showNotification('Checking satellite data availability...', 'info');
        
        const response = await fetch(`${API_BASE_URL}/data/available`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                lat: lat,
                lon: lon,
                start_date: startDate,
                end_date: endDate
            })
        });
        
        const data = await response.json();
        
        if (data.availability) {
            const avail = data.availability;
            let message = `✅ Data Available!\n\n`;
            
            if (avail.details) {
                if (avail.details.landsat) {
                    message += `Landsat: ${avail.details.landsat.scenes} scenes\n`;
                }
                if (avail.details.sentinel) {
                    message += `Sentinel-2: ${avail.details.sentinel.scenes} scenes\n`;
                }
            }
            
            message += `\nRecommendation: ${avail.recommendation || 'Use combined mode'}`;
            
            alert(message);
        }
    } catch (error) {
        console.error('Error checking data availability:', error);
        showNotification('Could not check data availability', 'danger');
    }
}

/**
 * Helper functions
 */
function getSatelliteName(satellite) {
    const names = {
        'landsat': 'Landsat 8/9',
        'sentinel': 'Sentinel-2',
        'combined': '🌟 Combined (Landsat + Sentinel-2)'
    };
    return names[satellite] || satellite;
}

function getIntensityColor(intensity) {
    const colors = {
        'Low': 'secondary',
        'Medium': 'info',
        'High': 'warning',
        'Very High': 'danger'
    };
    return colors[intensity] || 'info';
}

function showNotification(message, type = 'info') {
    // Create notification element
    const notification = document.createElement('div');
    notification.className = `alert alert-${type} alert-dismissible fade show notification-toast`;
    notification.style.cssText = 'position: fixed; top: 80px; right: 20px; z-index: 9999; min-width: 300px;';
    notification.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    document.body.appendChild(notification);
    
    // Auto-remove after 5 seconds
    setTimeout(() => {
        notification.remove();
    }, 5000);
}

function scrollToMap() {
    document.getElementById('map-section').scrollIntoView({ behavior: 'smooth' });
}

// Export functions for global access
window.scrollToMap = scrollToMap;
window.selectRegion = selectRegion;
