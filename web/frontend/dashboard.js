const API_URL = window.location.origin;

// Load all dashboard data
async function loadDashboardData() {
    try {
        // Load statistics
        const statsResponse = await fetch(`${API_URL}/api/admin/statistics`);
        if (!statsResponse.ok) throw new Error('Failed to load statistics');
        const stats = await statsResponse.json();
        
        displayKeyMetrics(stats);
        displayClimateImpact(stats.climate_impact);
        displayVIPStats(stats.vip);
        displayReservationStats(stats.reservations);
        
        // Load zone occupancy
        const zoneResponse = await fetch(`${API_URL}/api/admin/occupancy-by-zone`);
        if (!zoneResponse.ok) throw new Error('Failed to load zone data');
        const zoneData = await zoneResponse.json();
        displayZoneOccupancy(zoneData.zones);
        
        // Load sensors
        const sensorsResponse = await fetch(`${API_URL}/api/admin/sensors`);
        if (!sensorsResponse.ok) throw new Error('Failed to load sensors');
        const sensorsData = await sensorsResponse.json();
        displaySensors(sensorsData.sensors);
        
        // Load recent activity
        const activityResponse = await fetch(`${API_URL}/api/admin/recent-activity?limit=10`);
        if (!activityResponse.ok) throw new Error('Failed to load activity');
        const activityData = await activityResponse.json();
        displayRecentActivity(activityData.activities);
        
    } catch (error) {
        console.error('Error loading dashboard data:', error);
    }
}

// Display key metrics
function displayKeyMetrics(stats) {
    document.getElementById('occupancyRate').textContent = `${stats.occupancy.occupancy_rate}%`;
    document.getElementById('occupancyDetail').textContent = 
        `${stats.occupancy.occupied} / ${stats.occupancy.total} slots`;
    
    document.getElementById('totalRevenue').textContent = `Rs ${stats.revenue.total.toFixed(2)}`;
    document.getElementById('avgRevenue').textContent = 
        `Rs ${stats.revenue.average_per_vehicle.toFixed(2)} avg`;
    
    document.getElementById('activeVehicles').textContent = stats.vehicles.currently_parked;
    document.getElementById('totalVehicles').textContent = `${stats.vehicles.total_processed} total`;
    
    document.getElementById('sensorHealth').textContent = `${stats.sensors.health_percentage}%`;
    document.getElementById('sensorDetail').textContent = 
        `${stats.sensors.active} / ${stats.sensors.total} active`;
}

// Display zone occupancy
function displayZoneOccupancy(zones) {
    const container = document.getElementById('occupancyByZone');
    
    const zoneEntries = Object.entries(zones).sort((a, b) => a[0].localeCompare(b[0]));
    
    const html = `
        <div class=\"zone-list\">
            ${zoneEntries.map(([zoneName, data]) => {
                const occupancyPercent = (data.occupied / data.total * 100).toFixed(0);
                return `
                    <div class=\"zone-item\" data-testid=\"zone-${zoneName}\">
                        <div class=\"zone-info\">
                            <div class=\"zone-name\">Zone ${zoneName}</div>
                            <div class=\"zone-stats\">
                                ${data.occupied} occupied, ${data.available} available, ${data.reserved} reserved
                            </div>
                        </div>
                        <div class=\"zone-bar\">
                            <div class=\"zone-bar-fill\" style=\"width: ${occupancyPercent}%\"></div>
                        </div>
                    </div>
                `;
            }).join('')}
        </div>
    `;
    
    container.innerHTML = html;
}

// Display VIP stats
function displayVIPStats(vipData) {
    const container = document.getElementById('vipStats');
    
    container.innerHTML = `
        <div class=\"vip-stat-item\" data-testid=\"vip-total\">
            <div class=\"vip-stat-value\">${vipData.total_slots}</div>
            <div class=\"vip-stat-label\">Total VIP Slots</div>
        </div>
        <div class=\"vip-stat-item\" data-testid=\"vip-occupied\">
            <div class=\"vip-stat-value\">${vipData.occupied}</div>
            <div class=\"vip-stat-label\">Occupied</div>
        </div>
        <div class=\"vip-stat-item\" data-testid=\"vip-available\">
            <div class=\"vip-stat-value\">${vipData.available}</div>
            <div class=\"vip-stat-label\">Available</div>
        </div>
    `;
}

// Display climate impact
function displayClimateImpact(climateData) {
    const container = document.getElementById('climateStats');
    
    container.innerHTML = `
        <div class=\"climate-stat-item\" data-testid=\"climate-co2\">
            <div class=\"climate-stat-icon\"><i class=\"fas fa-leaf\"></i></div>
            <div class=\"climate-stat-value\">${climateData.co2_saved_kg.toFixed(0)}</div>
            <div class=\"climate-stat-label\">kg CO₂ Saved</div>
        </div>
        <div class=\"climate-stat-item\" data-testid=\"climate-time\">
            <div class=\"climate-stat-icon\"><i class=\"fas fa-clock\"></i></div>
            <div class=\"climate-stat-value\">${climateData.search_time_saved_hours.toFixed(0)}</div>
            <div class=\"climate-stat-label\">Hours Saved</div>
        </div>
        <div class=\"climate-stat-item\" data-testid=\"climate-vehicles\">
            <div class=\"climate-stat-icon\"><i class=\"fas fa-car\"></i></div>
            <div class=\"climate-stat-value\">${climateData.vehicles_served}</div>
            <div class=\"climate-stat-label\">Vehicles Served</div>
        </div>
    `;
}

// Display reservation stats
function displayReservationStats(reservationData) {
    const container = document.getElementById('reservationStats');
    
    container.innerHTML = `
        <div class=\"reservation-stat-item\" data-testid=\"reservations-active\">
            <div class=\"reservation-stat-value\">${reservationData.active}</div>
            <div class=\"reservation-stat-label\">Active Reservations</div>
        </div>
        <div class=\"reservation-stat-item\" data-testid=\"reservations-total\">
            <div class=\"reservation-stat-value\">${reservationData.total}</div>
            <div class=\"reservation-stat-label\">Total Reservations</div>
        </div>
    `;
}

// Display sensors
function displaySensors(sensors) {
    const container = document.getElementById('sensorGrid');
    
    const html = sensors.map(sensor => `
        <div class=\"sensor-card\" data-testid=\"sensor-${sensor.sensor_id}\">
            <div class=\"sensor-header\">
                <div class=\"sensor-id\">${sensor.sensor_id}</div>
                <div class=\"sensor-status ${sensor.status}\">
                    <i class=\"fas fa-circle\"></i>
                    ${sensor.status}
                </div>
            </div>
            <div class=\"sensor-info\">
                <div class=\"sensor-info-item\">
                    <span class=\"sensor-info-label\">Zone</span>
                    <span class=\"sensor-info-value\">${sensor.zone}</span>
                </div>
                <div class=\"sensor-info-item\">
                    <span class=\"sensor-info-label\">Battery</span>
                    <span class=\"sensor-info-value\">${sensor.battery}%</span>
                </div>
            </div>
        </div>
    `).join('');
    
    container.innerHTML = html;
}

// Display recent activity
function displayRecentActivity(activities) {
    const container = document.getElementById('activityTable');
    
    if (activities.length === 0) {
        container.innerHTML = '<p style=\"text-align: center; color: var(--text-secondary); padding: 2rem;\">No recent activity</p>';
        return;
    }
    
    const html = `
        <table>
            <thead>
                <tr>
                    <th>Vehicle</th>
                    <th>Slot</th>
                    <th>Status</th>
                    <th>VIP</th>
                    <th>Entry Time</th>
                    <th>Fee</th>
                </tr>
            </thead>
            <tbody>
                ${activities.map(activity => `
                    <tr data-testid=\"activity-${activity.vehicle_id}\">
                        <td><strong>${activity.vehicle_number}</strong></td>
                        <td>${activity.slot_id}</td>
                        <td>
                            <span class=\"status-badge ${activity.status}\">${activity.status}</span>
                        </td>
                        <td>
                            ${activity.is_vip ? '<i class=\"fas fa-crown vip-badge-small\"></i>' : '-'}
                        </td>
                        <td>${new Date(activity.created_at).toLocaleString()}</td>
                        <td>${activity.total_fee ? 'Rs ' + activity.total_fee.toFixed(2) : '-'}</td>
                    </tr>
                `).join('')}
            </tbody>
        </table>
    `;
    
    container.innerHTML = html;
}

// Refresh dashboard
document.getElementById('refreshDashboard').addEventListener('click', () => {
    loadDashboardData();
});

// Auto-refresh every 30 seconds
setInterval(loadDashboardData, 30000);

// Initialize
loadDashboardData();
