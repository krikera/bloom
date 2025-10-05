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
    const isRealData = data.real_data || false;
    
    let html = '<div class="results-container">';
    
    // Data quality indicator
    const dataQualityBadge = isRealData ? 
        '<span class="badge bg-success data-quality-badge"><i class="fas fa-satellite"></i> Real Satellite Data</span>' :
        '<span class="badge bg-warning data-quality-badge"><i class="fas fa-flask"></i> Demo Mode</span>';
    
    // Summary card
    html += `
        <div class="card mb-3">
            <div class="card-header bg-primary text-white">
                <h5 class="mb-0">
                    <i class="fas fa-chart-line"></i> Bloom Analysis Results
                    <span class="float-end">${dataQualityBadge}</span>
                </h5>
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
    
    // NDVI Color Scale Legend
    html += `
        <div class="card mb-3">
            <div class="card-header">
                <h6 class="mb-0"><i class="fas fa-palette"></i> NDVI Scale Reference</h6>
            </div>
            <div class="card-body">
                <div class="ndvi-scale">
                    <div class="ndvi-scale-item" style="background: #d73027;">< 0<br>Water</div>
                    <div class="ndvi-scale-item" style="background: #fee08b;">0-0.2<br>Bare</div>
                    <div class="ndvi-scale-item" style="background: #d9ef8b;">0.2-0.4<br>Sparse</div>
                    <div class="ndvi-scale-item" style="background: #91cf60;">0.4-0.6<br>Moderate</div>
                    <div class="ndvi-scale-item" style="background: #1a9850;">0.6-0.8<br>Dense</div>
                    <div class="ndvi-scale-item" style="background: #006837;">> 0.8<br>Very Dense</div>
                </div>
            </div>
        </div>
    `;
    
    // NDVI Time Series Chart
    if (blooms.length > 0 && blooms.some(b => b.peak_date)) {
        html += `
            <div class="card mb-3">
                <div class="card-header bg-info text-white">
                    <h5 class="mb-0"><i class="fas fa-chart-area"></i> NDVI Time Series</h5>
                </div>
                <div class="card-body">
                    <div id="ndviChart" style="width:100%; height:400px;"></div>
                </div>
            </div>
        `;
    }
    
    // Species Identification
    if (data.species_identification && data.species_identification.vegetation_type !== 'unknown') {
        const species = data.species_identification;
        const confidenceColor = species.confidence >= 0.75 ? 'success' : 
                               species.confidence >= 0.5 ? 'info' : 'warning';
        
        html += `
            <div class="card mb-3 border-${confidenceColor}">
                <div class="card-header bg-${confidenceColor} text-white">
                    <h5 class="mb-0"><i class="fas fa-leaf"></i> Vegetation Type Identified</h5>
                </div>
                <div class="card-body">
                    <div class="row">
                        <div class="col-md-6">
                            <h4>${species.vegetation_type_display}</h4>
                            <p><strong>Confidence:</strong> ${species.confidence_level} (${(species.confidence * 100).toFixed(0)}%)</p>
                            <p><strong>Characteristics:</strong></p>
                            <ul>
                                <li>Peak NDVI: ${species.characteristics.peak_ndvi.toFixed(3)}</li>
                                <li>Bloom Duration: ${species.characteristics.bloom_duration_days} days</li>
                                ${species.characteristics.bloom_month ? `<li>Peak Month: ${species.characteristics.bloom_month}</li>` : ''}
                            </ul>
                        </div>
                        <div class="col-md-6">
                            <h6><i class="fas fa-seedling"></i> Likely Species:</h6>
                            <ul>
                                ${species.likely_species.slice(0, 5).map(s => `<li>${s}</li>`).join('')}
                            </ul>
                        </div>
                    </div>
                    ${species.reasoning && species.reasoning.length > 0 ? `
                        <hr>
                        <h6>Analysis Reasoning:</h6>
                        <ul>
                            ${species.reasoning.map(r => `<li>${r}</li>`).join('')}
                        </ul>
                    ` : ''}
                </div>
            </div>
        `;
    }
    
    // Ecological Context
    if (data.ecological_context && data.ecological_context.region) {
        const context = data.ecological_context;
        
        html += `
            <div class="card mb-3">
                <div class="card-header bg-info text-white">
                    <h5 class="mb-0"><i class="fas fa-globe-americas"></i> Ecological Context & Conservation</h5>
                </div>
                <div class="card-body">
                    <h6><i class="fas fa-map-marker-alt"></i> Region: ${context.region}</h6>
                    
                    ${context.interpretation ? `
                        <div class="alert alert-light mt-3">
                            <h6>Bloom Assessment:</h6>
                            <p><strong>${context.interpretation.bloom_strength}</strong></p>
                        </div>
                    ` : ''}
                    
                    <div class="row mt-3">
                        <div class="col-md-6">
                            <h6><i class="fas fa-info-circle"></i> Ecological Significance:</h6>
                            <ul>
                                ${context.ecological_significance.map(sig => `<li>${sig}</li>`).join('')}
                            </ul>
                            
                            ${context.interpretation && context.interpretation.ecological_impact ? `
                                <h6 class="mt-3"><i class="fas fa-leaf"></i> Current Impact:</h6>
                                <ul>
                                    ${context.interpretation.ecological_impact.map(imp => `<li>${imp}</li>`).join('')}
                                </ul>
                            ` : ''}
                        </div>
                        <div class="col-md-6">
                            <h6><i class="fas fa-exclamation-triangle"></i> Conservation Concerns:</h6>
                            <ul>
                                ${context.conservation_concerns.map(con => `<li>${con}</li>`).join('')}
                            </ul>
                        </div>
                    </div>
                    
                    ${context.management_recommendations ? `
                        <hr>
                        <h6><i class="fas fa-tasks"></i> Management Recommendations:</h6>
                        <div class="row">
                            <div class="col-md-4">
                                <strong>Pre-Bloom:</strong>
                                <ul class="small">
                                    ${context.management_recommendations.pre_bloom.slice(0, 3).map(rec => `<li>${rec}</li>`).join('')}
                                </ul>
                            </div>
                            <div class="col-md-4">
                                <strong>During Bloom:</strong>
                                <ul class="small">
                                    ${context.management_recommendations.during_bloom.slice(0, 3).map(rec => `<li>${rec}</li>`).join('')}
                                </ul>
                            </div>
                            <div class="col-md-4">
                                <strong>Post-Bloom:</strong>
                                <ul class="small">
                                    ${context.management_recommendations.post_bloom.slice(0, 3).map(rec => `<li>${rec}</li>`).join('')}
                                </ul>
                            </div>
                        </div>
                    ` : ''}
                </div>
            </div>
        `;
    }
    
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
                    <p class="mb-1"><strong>Duration:</strong> ${bloom.duration_observations || 0} observations</p>
                    <p class="mb-1"><strong>Peak NDVI:</strong> ${(bloom.peak_ndvi || 0).toFixed(3)}</p>
                    <p class="mb-1"><strong>Intensity:</strong> <span class="badge bg-${getIntensityColor(bloom.intensity)}">${bloom.intensity || 'moderate'}</span></p>
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
    
    // Create NDVI chart if we have bloom data with dates
    if (blooms.length > 0 && blooms.some(b => b.peak_date)) {
        createNDVIChart(blooms);
    }
}

/**
 * Create NDVI time series chart using Plotly
 */
function createNDVIChart(bloomEvents) {
    if (!bloomEvents || bloomEvents.length === 0) return;
    
    // Extract dates and NDVI values from bloom events
    const dates = [];
    const ndviValues = [];
    const markers = [];
    
    bloomEvents.forEach(bloom => {
        if (bloom.peak_date && bloom.peak_ndvi) {
            dates.push(bloom.peak_date);
            ndviValues.push(bloom.peak_ndvi);
            markers.push(bloom.peak_ndvi);
        }
        // Add start and end points if available
        if (bloom.start_date && bloom.start_ndvi) {
            dates.push(bloom.start_date);
            ndviValues.push(bloom.start_ndvi);
            markers.push(bloom.start_ndvi);
        }
        if (bloom.end_date && bloom.end_ndvi) {
            dates.push(bloom.end_date);
            ndviValues.push(bloom.end_ndvi);
            markers.push(bloom.end_ndvi);
        }
    });
    
    if (dates.length === 0) return;
    
    // Sort by date
    const combined = dates.map((date, i) => ({ date, ndvi: ndviValues[i], marker: markers[i] }));
    combined.sort((a, b) => new Date(a.date) - new Date(b.date));
    
    const sortedDates = combined.map(c => c.date);
    const sortedNDVI = combined.map(c => c.ndvi);
    const sortedMarkers = combined.map(c => c.marker);
    
    // Create the main trace
    const trace = {
        x: sortedDates,
        y: sortedNDVI,
        mode: 'lines+markers',
        type: 'scatter',
        name: 'NDVI',
        line: {
            color: '#27ae60',
            width: 3
        },
        marker: {
            size: 10,
            color: sortedMarkers,
            colorscale: [
                [0, '#d73027'],
                [0.2, '#fee08b'],
                [0.4, '#d9ef8b'],
                [0.6, '#91cf60'],
                [0.8, '#1a9850'],
                [1, '#006837']
            ],
            showscale: true,
            colorbar: {
                title: 'NDVI',
                titleside: 'right'
            },
            line: {
                color: 'white',
                width: 2
            }
        }
    };
    
    // Add bloom threshold line
    const thresholdTrace = {
        x: sortedDates,
        y: Array(sortedDates.length).fill(0.4),
        mode: 'lines',
        type: 'scatter',
        name: 'Bloom Threshold',
        line: {
            color: 'rgba(231, 76, 60, 0.7)',
            width: 2,
            dash: 'dash'
        }
    };
    
    const layout = {
        title: {
            text: 'NDVI Time Series - Vegetation Health Tracking',
            font: { size: 18, color: '#2c3e50' }
        },
        xaxis: {
            title: 'Date',
            type: 'date',
            gridcolor: '#ecf0f1'
        },
        yaxis: {
            title: 'NDVI Value',
            range: [-0.1, 1.0],
            gridcolor: '#ecf0f1'
        },
        hovermode: 'closest',
        showlegend: true,
        legend: {
            x: 0,
            y: 1,
            bgcolor: 'rgba(255, 255, 255, 0.8)'
        },
        plot_bgcolor: '#fafafa',
        paper_bgcolor: 'white'
    };
    
    const config = {
        responsive: true,
        displayModeBar: true,
        displaylogo: false
    };
    
    Plotly.newPlot('ndviChart', [trace, thresholdTrace], layout, config);
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
        }
    } catch (error) {
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
            document.getElementById('apiStatus').innerHTML = 
                '<span class="badge bg-success"><i class="fas fa-check-circle"></i> API Connected</span>';
        }
    } catch (error) {
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
    
    const dataSource = data.data_source || {};

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

    if (dataSource.demo_mode) {
        html += `
            <div class="alert alert-warning">
                <h6 class="mb-1"><i class="fas fa-exclamation-triangle"></i> Heads up: simulated data</h6>
                <p class="mb-0 small">Real satellite pixels were unavailable for this request. Results are generated from historical scene metadata.${dataSource.notes ? ` ${dataSource.notes}` : ''}</p>
            </div>
        `;
    } else if (dataSource.real_data) {
        html += `
            <div class="alert alert-success">
                <h6 class="mb-1"><i class="fas fa-satellite"></i> Real satellite data used</h6>
                <p class="mb-0 small">Bloom metrics are derived from ${dataSource.satellite || 'satellite'} surface reflectance pixels.</p>
            </div>
        `;
    }
    
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

/**
 * Multi-Year Trend Analysis
 */
async function runMultiYearAnalysis() {
    const lat = parseFloat(document.getElementById('latitude').value);
    const lon = parseFloat(document.getElementById('longitude').value);
    const season = 'spring'; // Default to spring
    
    if (!lat || !lon) {
        showNotification('Please enter location coordinates first', 'warning');
        return;
    }
    
    const loading = document.getElementById('loading');
    const results = document.getElementById('results');
    
    loading.style.display = 'block';
    results.innerHTML = '<div class="alert alert-info"><i class="fas fa-clock"></i> Analyzing multiple years of bloom data... This may take 1-2 minutes.</div>';
    
    try {
        // Request 5 years of data
        const currentYear = new Date().getFullYear();
        const years = [currentYear - 4, currentYear - 3, currentYear - 2, currentYear - 1, currentYear];
        
        const response = await fetch(`${API_BASE_URL}/bloom/timeseries`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                lat: lat,
                lon: lon,
                years: years,
                season: season
            })
        });
        
        const data = await response.json();
        loading.style.display = 'none';
        
        if (data.status === 'success') {
            displayMultiYearResults(data, lat, lon);
        } else {
            results.innerHTML = `<div class="alert alert-danger">Error: ${data.error || 'Could not retrieve multi-year data'}</div>`;
        }
        
    } catch (error) {
        loading.style.display = 'none';
        console.error('Error in multi-year analysis:', error);
        results.innerHTML = `<div class="alert alert-danger">Error: ${error.message}</div>`;
    }
}

/**
 * Display multi-year trend results
 */
function displayMultiYearResults(data, lat, lon) {
    const results = document.getElementById('results');
    const timeseries = data.timeseries || [];
    const trends = data.trends || {};
    const dataSources = data.data_sources || [];
    const hasRealData = dataSources.some(src => src.real_data);
    const hasDemoData = dataSources.some(src => src.demo_mode);
    
    let html = '<div class="results-container">';
    
    // Header
    html += `
        <div class="card mb-3">
            <div class="card-header bg-success text-white">
                <h5 class="mb-0"><i class="fas fa-chart-line"></i> Multi-Year Bloom Trend Analysis</h5>
            </div>
            <div class="card-body">
                <p><strong>Location:</strong> ${lat.toFixed(4)}°, ${lon.toFixed(4)}°</p>
                <p><strong>Years Analyzed:</strong> ${timeseries.map(t => t.year).join(', ')}</p>
                <p><strong>Season:</strong> Spring (March-May)</p>
            </div>
        </div>
    `;

    if (dataSources.length > 0) {
        if (hasDemoData && !hasRealData) {
            html += `
                <div class="alert alert-warning">
                    <h6 class="mb-1"><i class="fas fa-info-circle"></i> Simulated historical data</h6>
                    <p class="mb-0 small">All historical years used synthesized NDVI derived from scene metadata. Interpret trends cautiously.</p>
                </div>
            `;
        } else if (hasDemoData) {
            html += `
                <div class="alert alert-warning">
                    <h6 class="mb-1"><i class="fas fa-adjust"></i> Mixed data quality</h6>
                    <p class="mb-0 small">Some years used synthesized NDVI because raw pixels were unavailable. Real-data years: ${dataSources.filter(src => src.real_data).map(src => src.year).join(', ') || 'none'}.</p>
                </div>
            `;
        } else if (hasRealData) {
            html += `
                <div class="alert alert-success">
                    <h6 class="mb-1"><i class="fas fa-satellite"></i> Real satellite data</h6>
                    <p class="mb-0 small">All analyzed years are based on real satellite pixels.</p>
                </div>
            `;
        }
    }
    
    // Yearly breakdown
    html += `
        <div class="card mb-3">
            <div class="card-header">
                <h6 class="mb-0"><i class="fas fa-calendar"></i> Year-by-Year Results</h6>
            </div>
            <div class="card-body">
                <div class="table-responsive">
                    <table class="table table-hover">
                        <thead>
                            <tr>
                                <th>Year</th>
                                <th>Bloom Events</th>
                                <th>Peak NDVI</th>
                                <th>Average NDVI</th>
                                <th>Assessment</th>
                            </tr>
                        </thead>
                        <tbody>
    `;
    
    timeseries.forEach(yearData => {
        const assessment = yearData.peak_ndvi > 0.6 ? 'Excellent' : 
                          yearData.peak_ndvi > 0.5 ? 'Good' : 
                          yearData.peak_ndvi > 0.4 ? 'Moderate' : 'Weak';
        const badgeClass = yearData.peak_ndvi > 0.6 ? 'success' : 
                          yearData.peak_ndvi > 0.5 ? 'info' : 
                          yearData.peak_ndvi > 0.4 ? 'warning' : 'secondary';
        
        html += `
            <tr>
                <td><strong>${yearData.year}</strong></td>
                <td>${yearData.bloom_events.length}</td>
                <td>${yearData.peak_ndvi.toFixed(3)}</td>
                <td>${yearData.average_ndvi.toFixed(3)}</td>
                <td><span class="badge bg-${badgeClass}">${assessment}</span></td>
            </tr>
        `;
    });
    
    html += `
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    `;
    
    // Trend analysis
    if (trends.peak_ndvi_trend) {
        const trend = trends.peak_ndvi_trend;
        const trendIcon = trend.direction === 'increasing' ? 'fa-arrow-up text-success' : 'fa-arrow-down text-danger';
        
        html += `
            <div class="card mb-3">
                <div class="card-header bg-info text-white">
                    <h6 class="mb-0"><i class="fas fa-chart-area"></i> Trend Analysis</h6>
                </div>
                <div class="card-body">
                    <div class="row">
                        <div class="col-md-6">
                            <h6>Peak NDVI Trend <i class="fas ${trendIcon}"></i></h6>
                            <p><strong>Direction:</strong> ${trend.direction.charAt(0).toUpperCase() + trend.direction.slice(1)}</p>
                            <p><strong>Rate:</strong> ${Math.abs(trend.slope).toFixed(4)} per year</p>
                            <p><strong>R²:</strong> ${trend.r_squared.toFixed(3)} (${trend.r_squared > 0.7 ? 'Strong' : trend.r_squared > 0.4 ? 'Moderate' : 'Weak'} correlation)</p>
                        </div>
                        <div class="col-md-6">
                            <h6>Interpretation</h6>
                            <p>${trend.interpretation}</p>
                        </div>
                    </div>
                </div>
            </div>
        `;
    }
    
    // Year-over-year changes
    if (trends.year_over_year_changes && trends.year_over_year_changes.length > 0) {
        html += `
            <div class="card mb-3">
                <div class="card-header">
                    <h6 class="mb-0"><i class="fas fa-exchange-alt"></i> Year-over-Year Changes</h6>
                </div>
                <div class="card-body">
                    <ul class="list-group list-group-flush">
        `;
        
        trends.year_over_year_changes.forEach(change => {
            const changeIcon = change.percent_change > 0 ? 'fa-arrow-up text-success' : 'fa-arrow-down text-danger';
            html += `
                <li class="list-group-item">
                    <i class="fas ${changeIcon}"></i>
                    ${change.from_year} to ${change.to_year}: 
                    <strong>${Math.abs(change.percent_change).toFixed(1)}%</strong>
                    ${change.percent_change > 0 ? 'increase' : 'decrease'}
                </li>
            `;
        });
        
        html += `
                    </ul>
                </div>
            </div>
        `;
    }
    
    html += '</div>';
    results.innerHTML = html;
}

/**
 * Bloom Prediction
 */
async function predictNextBloom() {
    const lat = parseFloat(document.getElementById('latitude').value);
    const lon = parseFloat(document.getElementById('longitude').value);
    
    if (!lat || !lon) {
        showNotification('Please enter location coordinates first', 'warning');
        return;
    }
    
    const loading = document.getElementById('loading');
    const results = document.getElementById('results');
    
    loading.style.display = 'block';
    results.innerHTML = '<div class="alert alert-info"><i class="fas fa-clock"></i> Analyzing historical patterns and generating prediction... This may take 1-2 minutes.</div>';
    
    try {
        const currentYear = new Date().getFullYear();
        const historicalYears = [currentYear - 4, currentYear - 3, currentYear - 2, currentYear - 1, currentYear];
        
        const response = await fetch(`${API_BASE_URL}/bloom/predict`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                lat: lat,
                lon: lon,
                historical_years: historicalYears,
                season: 'spring'
            })
        });
        
        const data = await response.json();
        loading.style.display = 'none';
        
        if (data.status === 'success') {
            displayPredictionResults(data, lat, lon);
        } else if (data.status === 'insufficient_data') {
            results.innerHTML = `
                <div class="alert alert-warning">
                    <h5><i class="fas fa-exclamation-triangle"></i> Insufficient Data</h5>
                    <p>${data.message}</p>
                    <p>Try a location with known historical blooms, such as California desert regions.</p>
                </div>
            `;
        } else {
            results.innerHTML = `<div class="alert alert-danger">Error: ${data.message || 'Could not generate prediction'}</div>`;
        }
        
    } catch (error) {
        loading.style.display = 'none';
        console.error('Error predicting bloom:', error);
        results.innerHTML = `<div class="alert alert-danger">Error: ${error.message}</div>`;
    }
}

/**
 * Display bloom prediction results
 */
function displayPredictionResults(data, lat, lon) {
    const results = document.getElementById('results');
    const dataSources = data.data_sources || [];
    const hasRealData = dataSources.some(src => src.real_data);
    const hasDemoData = dataSources.some(src => src.demo_mode);
    
    const confidenceColor = data.confidence >= 0.75 ? 'success' : 
                           data.confidence >= 0.55 ? 'info' : 
                           data.confidence >= 0.35 ? 'warning' : 'danger';
    
    let html = '<div class="results-container">';
    
    if (dataSources.length > 0) {
        if (hasDemoData && !hasRealData) {
            html += `
                <div class="alert alert-warning">
                    <h6 class="mb-1"><i class="fas fa-info-circle"></i> Prediction based on simulated history</h6>
                    <p class="mb-0 small">Historical years lacked raw pixel data, so this forecast uses synthesized NDVI derived from scene metadata.</p>
                </div>
            `;
        } else if (hasDemoData) {
            const realYears = dataSources.filter(src => src.real_data).map(src => src.year).join(', ');
            html += `
                <div class="alert alert-warning">
                    <h6 class="mb-1"><i class="fas fa-adjust"></i> Mixed data quality</h6>
                    <p class="mb-0 small">Some historical years used synthesized NDVI due to missing pixels. Real-data years: ${realYears || 'none'}.</p>
                </div>
            `;
        } else if (hasRealData) {
            html += `
                <div class="alert alert-success">
                    <h6 class="mb-1"><i class="fas fa-satellite"></i> Real historical data</h6>
                    <p class="mb-0 small">Predictions are based entirely on real satellite pixel observations.</p>
                </div>
            `;
        }
    }
    
    // Prediction card
    html += `
        <div class="card mb-3 border-${confidenceColor}">
            <div class="card-header bg-${confidenceColor} text-white">
                <h5 class="mb-0"><i class="fas fa-crystal-ball"></i> Bloom Prediction</h5>
            </div>
            <div class="card-body">
                <div class="row text-center mb-3">
                    <div class="col-md-4">
                        <h2 class="text-${confidenceColor}">${data.predicted_date}</h2>
                        <p class="text-muted">Predicted Peak Bloom Date</p>
                    </div>
                    <div class="col-md-4">
                        <h2 class="text-${confidenceColor}">${(data.confidence * 100).toFixed(0)}%</h2>
                        <p class="text-muted">Confidence Level: ${data.confidence_level}</p>
                    </div>
                    <div class="col-md-4">
                        <h2 class="text-${confidenceColor}">±${data.uncertainty_days}</h2>
                        <p class="text-muted">Uncertainty (days)</p>
                    </div>
                </div>
                <div class="row">
                    <div class="col-md-12">
                        <h6>Expected Date Range:</h6>
                        <ul>
                            <li><strong>Earliest:</strong> ${data.date_range.earliest}</li>
                            <li><strong>Most Likely:</strong> ${data.date_range.most_likely}</li>
                            <li><strong>Latest:</strong> ${data.date_range.latest}</li>
                        </ul>
                    </div>
                </div>
            </div>
        </div>
    `;
    
    // Historical reference
    if (data.historical_bloom_dates && data.historical_bloom_dates.length > 0) {
        html += `
            <div class="card mb-3">
                <div class="card-header">
                    <h6 class="mb-0"><i class="fas fa-history"></i> Based on Historical Data</h6>
                </div>
                <div class="card-body">
                    <p><strong>Years Analyzed:</strong> ${data.based_on_years}</p>
                    <p><strong>Recent Bloom Dates:</strong></p>
                    <ul>
                        ${data.historical_bloom_dates.map(date => `<li>${date}</li>`).join('')}
                    </ul>
                </div>
            </div>
        `;
    }
    
    // Prediction methods
    if (data.prediction_methods) {
        html += `
            <div class="card mb-3">
                <div class="card-header">
                    <h6 class="mb-0"><i class="fas fa-cogs"></i> Prediction Methods (Ensemble)</h6>
                </div>
                <div class="card-body">
                    <div class="table-responsive">
                        <table class="table table-sm">
                            <thead>
                                <tr>
                                    <th>Method</th>
                                    <th>Predicted Date</th>
                                    <th>Confidence</th>
                                    <th>Weight</th>
                                </tr>
                            </thead>
                            <tbody>
        `;
        
        for (const [method, details] of Object.entries(data.prediction_methods)) {
            html += `
                <tr>
                    <td>${method.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())}</td>
                    <td>${details.date}</td>
                    <td>${(details.confidence * 100).toFixed(0)}%</td>
                    <td>${(details.weight * 100).toFixed(0)}%</td>
                </tr>
            `;
        }
        
        html += `
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>
        `;
    }
    
    // Recommendations
    if (data.recommendations && data.recommendations.length > 0) {
        html += `
            <div class="card mb-3">
                <div class="card-header bg-warning">
                    <h6 class="mb-0"><i class="fas fa-lightbulb"></i> Recommendations</h6>
                </div>
                <div class="card-body">
                    <ul>
                        ${data.recommendations.map(rec => `<li>${rec}</li>`).join('')}
                    </ul>
                </div>
            </div>
        `;
    }
    
    html += '</div>';
    results.innerHTML = html;
}

/**
 * Regional Bloom Scanning
 */
async function scanRegion() {
    const regionName = document.getElementById('regionSelect').value;
    const startDate = document.getElementById('regionalStartDate').value;
    const endDate = document.getElementById('regionalEndDate').value;
    
    if (!startDate || !endDate) {
        showNotification('Please enter date range', 'warning');
        return;
    }
    
    const loading = document.getElementById('regionalLoading');
    const results = document.getElementById('regionalResults');
    
    loading.style.display = 'block';
    results.innerHTML = '';
    
    try {
        const response = await fetch(`${API_BASE_URL}/regional/scan`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                region_name: regionName,
                start_date: startDate,
                end_date: endDate
            })
        });
        
        const data = await response.json();
        loading.style.display = 'none';
        
        if (data.status === 'success') {
            displayRegionalResults(data);
        } else {
            results.innerHTML = `<div class="alert alert-danger">Error: ${data.message || 'Could not scan region'}</div>`;
        }
        
    } catch (error) {
        loading.style.display = 'none';
        console.error('Error scanning region:', error);
        results.innerHTML = `<div class="alert alert-danger">Error: ${error.message}</div>`;
    }
}

/**
 * Display regional scan results
 */
function displayRegionalResults(data) {
    const results = document.getElementById('regionalResults');
    
    if (!data.bloom_detected) {
        results.innerHTML = `
            <div class="alert alert-info">
                <h6><i class="fas fa-info-circle"></i> No Blooms Detected</h6>
                <p>${data.message}</p>
            </div>
        `;
        return;
    }
    
    const stats = data.statistics;
    const interpretation = data.interpretation;
    const provenance = data.data_sources || {};
    
    let html = '';
    
    // Summary
    html += `
        <div class="card mb-3">
            <div class="card-header bg-success text-white">
                <h6 class="mb-0"><i class="fas fa-check-circle"></i> Regional Bloom Detected!</h6>
            </div>
            <div class="card-body">
                <h5>${interpretation.overall_assessment}</h5>
                <div class="row text-center mt-3">
                    <div class="col-md-3">
                        <h3 class="text-success">${stats.total_bloom_locations}</h3>
                        <small>Locations</small>
                    </div>
                    <div class="col-md-3">
                        <h3 class="text-success">${stats.average_peak_ndvi.toFixed(3)}</h3>
                        <small>Avg Peak NDVI</small>
                    </div>
                    <div class="col-md-3">
                        <h3 class="text-success">${stats.max_peak_ndvi.toFixed(3)}</h3>
                        <small>Max Peak NDVI</small>
                    </div>
                    <div class="col-md-3">
                        <h3 class="text-success">${interpretation.bloom_quality}</h3>
                        <small>Bloom Quality</small>
                    </div>
                </div>
                <hr>
                <p><strong>Spatial Pattern:</strong> ${interpretation.spatial_pattern}</p>
                <p><strong>Coverage:</strong> ${data.bloom_coverage.description}</p>
            </div>
        </div>
    `;
    
    if (provenance.total_points) {
        if (provenance.real_data_points === 0) {
            html += `
                <div class="alert alert-warning">
                    <h6 class="mb-1"><i class="fas fa-exclamation-triangle"></i> Simulated regional coverage</h6>
                    <p class="mb-0 small">Every grid point relied on synthesized NDVI (no raw pixels available). Use these regional insights as illustrative only.</p>
                </div>
            `;
        } else if (provenance.demo_data_points > 0) {
            html += `
                <div class="alert alert-warning">
                    <h6 class="mb-1"><i class="fas fa-adjust"></i> Mixed data quality</h6>
                    <p class="mb-0 small">${provenance.real_data_points} of ${provenance.total_points} hotspots used real pixels; the rest relied on synthesized NDVI due to missing data.</p>
                </div>
            `;
        } else {
            html += `
                <div class="alert alert-success">
                    <h6 class="mb-1"><i class="fas fa-satellite"></i> Real satellite coverage</h6>
                    <p class="mb-0 small">All analyzed hotspots are based on real satellite pixels.</p>
                </div>
            `;
        }
    }
    
    // Hotspots
    if (data.hotspots && data.hotspots.length > 0) {
        html += `
            <div class="card mb-3">
                <div class="card-header bg-warning">
                    <h6 class="mb-0"><i class="fas fa-fire"></i> Top Bloom Hotspots</h6>
                </div>
                <div class="card-body">
                    <div class="table-responsive">
                        <table class="table table-hover">
                            <thead>
                                <tr>
                                    <th>#</th>
                                    <th>Location</th>
                                    <th>Peak NDVI</th>
                                    <th>Intensity</th>
                                </tr>
                            </thead>
                            <tbody>
        `;
        
        data.hotspots.slice(0, 5).forEach((hotspot, index) => {
            html += `
                <tr>
                    <td>${index + 1}</td>
                    <td>${hotspot.lat.toFixed(4)}°, ${hotspot.lon.toFixed(4)}°</td>
                    <td><strong>${hotspot.peak_ndvi.toFixed(3)}</strong></td>
                    <td><span class="badge bg-${getIntensityColor(hotspot.intensity)}">${hotspot.intensity}</span></td>
                </tr>
            `;
        });
        
        html += `
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>
        `;
    }
    
    // Recommendations
    if (interpretation.recommendations && interpretation.recommendations.length > 0) {
        html += `
            <div class="card mb-3">
                <div class="card-header bg-info text-white">
                    <h6 class="mb-0"><i class="fas fa-lightbulb"></i> Management Recommendations</h6>
                </div>
                <div class="card-body">
                    <ul>
                        ${interpretation.recommendations.map(rec => `<li>${rec}</li>`).join('')}
                    </ul>
                </div>
            </div>
        `;
    }
    
    results.innerHTML = html;
}

// Event listeners
document.addEventListener('DOMContentLoaded', function() {
    // Multi-year analysis button
    const multiYearBtn = document.getElementById('multiYearBtn');
    if (multiYearBtn) {
        multiYearBtn.addEventListener('click', runMultiYearAnalysis);
    }
    
    // Prediction button
    const predictBtn = document.getElementById('predictBtn');
    if (predictBtn) {
        predictBtn.addEventListener('click', predictNextBloom);
    }
    
    // Regional scan button
    const scanRegionBtn = document.getElementById('scanRegionBtn');
    if (scanRegionBtn) {
        scanRegionBtn.addEventListener('click', scanRegion);
    }
});

// Export functions for global access
window.scrollToMap = scrollToMap;
window.selectRegion = selectRegion;
window.runMultiYearAnalysis = runMultiYearAnalysis;
window.predictNextBloom = predictNextBloom;
window.scanRegion = scanRegion;
