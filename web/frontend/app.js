const API_URL = window.location.origin;

// Animate counter
function animateCounter(element, target, duration = 2000) {
    const start = 0;
    const increment = target / (duration / 16);
    let current = start;
    
    const timer = setInterval(() => {
        current += increment;
        if (current >= target) {
            element.textContent = Math.round(target);
            clearInterval(timer);
        } else {
            element.textContent = Math.round(current);
        }
    }, 16);
}

// Load statistics
async function loadStatistics() {
    try {
        const response = await fetch(`${API_URL}/api/admin/statistics`);
        if (!response.ok) throw new Error('Failed to load statistics');
        
        const data = await response.json();
        
        // Animate hero stats
        const timeSavedEl = document.getElementById('timeSaved');
        const co2SavedEl = document.getElementById('co2Saved');
        const vehiclesServedEl = document.getElementById('vehiclesServed');
        
        if (timeSavedEl) animateCounter(timeSavedEl, data.climate_impact.search_time_saved_hours);
        if (co2SavedEl) animateCounter(co2SavedEl, data.climate_impact.co2_saved_kg);
        if (vehiclesServedEl) animateCounter(vehiclesServedEl, data.climate_impact.vehicles_served);
        
        // Climate metrics
        const climateEmissionsEl = document.getElementById('climateEmissions');
        const climateFuelEl = document.getElementById('climateFuel');
        
        if (climateEmissionsEl) {
            animateCounter(climateEmissionsEl, data.climate_impact.co2_saved_kg);
        }
        if (climateFuelEl) {
            // Estimate fuel saved (1 liter = ~2.3 kg CO2)
            const fuelSaved = Math.round(data.climate_impact.co2_saved_kg / 2.3);
            animateCounter(climateFuelEl, fuelSaved);
        }
        
    } catch (error) {
        console.error('Error loading statistics:', error);
    }
}

// Smooth scroll
document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function (e) {
        e.preventDefault();
        const target = document.querySelector(this.getAttribute('href'));
        if (target) {
            target.scrollIntoView({ behavior: 'smooth' });
        }
    });
});

// Initialize
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', loadStatistics);
} else {
    loadStatistics();
}