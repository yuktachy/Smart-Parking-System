const API_URL = window.location.origin;

let selectedSlot = null;
let allSlots = [];

// Load available slots
async function loadSlots(type = 'all') {
    try {
        const response = await fetch(`${API_URL}/api/slots/all`);
        if (!response.ok) throw new Error('Failed to load slots');
        
        const data = await response.json();
        allSlots = data.slots;
        
        // Filter by type
        let filteredSlots = allSlots;
        if (type !== 'all') {
            filteredSlots = allSlots.filter(slot => slot.type === type);
        }
        
        displaySlots(filteredSlots);
        updateStats(allSlots);
        updateSlotSelector(allSlots.filter(s => s.status === 'available'));
        
    } catch (error) {
        console.error('Error loading slots:', error);
    }
}

// Display slots in grid
function displaySlots(slots) {
    const grid = document.getElementById('slotsGrid');
    grid.innerHTML = '';
    
    slots.forEach(slot => {
        const slotDiv = document.createElement('div');
        slotDiv.className = `slot-item ${slot.status}`;
        slotDiv.dataset.slotId = slot.slot_id;
        slotDiv.dataset.testid = `slot-${slot.slot_id}`;
        
        if (slot.status === 'available') {
            slotDiv.addEventListener('click', () => selectSlot(slot));
        }
        
        slotDiv.innerHTML = `
            ${slot.type === 'VIP' ? '<i class="fas fa-crown vip-badge"></i>' : ''}
            <div class="slot-type">${slot.type}</div>
            <div class="slot-number">${slot.slot_number}</div>
            <div class="slot-status">${slot.status}</div>
        `;
        
        grid.appendChild(slotDiv);
    });
}

// Update statistics
function updateStats(slots) {
    const available = slots.filter(s => s.status === 'available').length;
    const occupied = slots.filter(s => s.status === 'occupied').length;
    const reserved = slots.filter(s => s.status === 'reserved').length;
    
    document.getElementById('availableCount').textContent = available;
    document.getElementById('occupiedCount').textContent = occupied;
    document.getElementById('reservedCount').textContent = reserved;
}

// Update slot selector dropdown
function updateSlotSelector(availableSlots) {
    const select = document.getElementById('slotSelect');
    select.innerHTML = '<option value="">Choose a parking slot</option>';
    
    availableSlots.forEach(slot => {
        const option = document.createElement('option');
        option.value = slot.slot_id;
        option.textContent = `${slot.slot_id} - ${slot.type} (Floor ${slot.floor}, Zone ${slot.zone})`;
        select.appendChild(option);
    });
}

// Select slot from grid
function selectSlot(slot) {
    if (slot.status !== 'available') return;
    
    // Remove previous selection
    document.querySelectorAll('.slot-item').forEach(item => {
        item.classList.remove('selected');
    });
    
    // Add selection
    const slotDiv = document.querySelector(`[data-slot-id="${slot.slot_id}"]`);
    if (slotDiv) {
        slotDiv.classList.add('selected');
    }
    
    // Update dropdown
    document.getElementById('slotSelect').value = slot.slot_id;
    selectedSlot = slot;
    
    // Update cost estimate
    updateCostEstimate();
}

// Update cost estimate
async function updateCostEstimate() {
    const duration = parseInt(document.getElementById('estimatedDuration').value) || 60;
    const isVIP = document.getElementById('isVIP').checked;
    
    try {
        const response = await fetch(`${API_URL}/api/fee/estimate`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                estimated_minutes: duration,
                is_vip: isVIP
            })
        });
        
        if (!response.ok) throw new Error('Failed to estimate cost');
        
        const data = await response.json();
        document.getElementById('estimatedCost').textContent = `Rs ${data.estimated_cost.toFixed(2)}`;
        
    } catch (error) {
        console.error('Error estimating cost:', error);
    }
}

// Handle booking form submission
document.getElementById('bookingForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const vehicleNumber = document.getElementById('vehicleNumber').value.trim();
    const slotId = document.getElementById('slotSelect').value;
    const isVIP = document.getElementById('isVIP').checked;
    
    if (!vehicleNumber || !slotId) {
        showResult('Please fill in all required fields', 'error');
        return;
    }
    
    try {
        const response = await fetch(`${API_URL}/api/vehicles/register`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                vehicle_number: vehicleNumber,
                slot_id: slotId,
                is_vip: isVIP
            })
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.error || 'Booking failed');
        }
        
        const data = await response.json();
        
        showResult(`✓ Booking successful! Vehicle ${vehicleNumber} parked at ${slotId}`, 'success');
        showQRCode(data.qr_code);
        
        // Refresh slots
        loadSlots(document.getElementById('slotTypeFilter').value);
        
        // Reset form
        document.getElementById('bookingForm').reset();
        selectedSlot = null;
        
    } catch (error) {
        showResult(error.message, 'error');
    }
});

// Show result message
function showResult(message, type) {
    const resultDiv = document.getElementById('bookingResult');
    resultDiv.textContent = message;
    resultDiv.className = `result-message ${type} show`;
    resultDiv.style.display = 'block';
    
    setTimeout(() => {
        resultDiv.style.display = 'none';
    }, 5000);
}

// Show QR code
function showQRCode(qrCode) {
    const qrDiv = document.getElementById('qrCode');
    qrDiv.innerHTML = `
        <div style="font-size: 0.875rem; color: var(--text-secondary); margin-bottom: 1rem; text-transform: uppercase;">Your QR Entry Code</div>
        <div class="qr-code-text">${qrCode}</div>
        <div style="margin-top: 1rem; font-size: 0.75rem; color: var(--text-disabled);">Use this code for entry and exit</div>
    `;
    qrDiv.style.display = 'block';
    
    setTimeout(() => {
        qrDiv.style.display = 'none';
    }, 10000);
}

// Check vehicle status
document.getElementById('checkVehicle').addEventListener('click', async () => {
    const vehicleNumber = document.getElementById('checkVehicleNumber').value.trim();
    
    if (!vehicleNumber) {
        alert('Please enter vehicle number');
        return;
    }
    
    try {
        const response = await fetch(`${API_URL}/api/vehicles/${vehicleNumber}`);
        
        if (!response.ok) {
            throw new Error('Vehicle not found');
        }
        
        const data = await response.json();
        displayVehicleStatus(data);
        
    } catch (error) {
        alert(error.message);
    }
});

// Display vehicle status
function displayVehicleStatus(vehicle) {
    const statusDiv = document.getElementById('vehicleStatus');
    
    const parkedTime = Math.floor((Date.now() / 1000 - vehicle.entry_time) / 60);
    
    statusDiv.innerHTML = `
        <div style="margin-bottom: 1rem;">
            <strong style="color: var(--primary);">Vehicle: ${vehicle.vehicle_number}</strong>
        </div>
        <div class="vehicle-info">
            <div class="info-item">
                <div class="info-label">Slot</div>
                <div class="info-value">${vehicle.slot_id}</div>
            </div>
            <div class="info-item">
                <div class="info-label">Status</div>
                <div class="info-value">${vehicle.status}</div>
            </div>
            <div class="info-item">
                <div class="info-label">Parked Time</div>
                <div class="info-value">${parkedTime} min</div>
            </div>
            <div class="info-item">
                <div class="info-label">Current Fee</div>
                <div class="info-value" style="color: var(--primary);">Rs ${vehicle.current_fee.toFixed(2)}</div>
            </div>
            <div class="info-item">
                <div class="info-label">VIP</div>
                <div class="info-value">${vehicle.is_vip ? '✓ Yes' : 'No'}</div>
            </div>
            <div class="info-item">
                <div class="info-label">QR Code</div>
                <div class="info-value" style="font-size: 0.75rem;">${vehicle.qr_code}</div>
            </div>
        </div>
    `;
    
    statusDiv.classList.add('show');
    statusDiv.style.display = 'block';
}

// Exit vehicle
document.getElementById('exitVehicle').addEventListener('click', async () => {
    const vehicleNumber = document.getElementById('exitVehicleNumber').value.trim();
    
    if (!vehicleNumber) {
        alert('Please enter vehicle number');
        return;
    }
    
    if (!confirm(`Confirm exit for vehicle ${vehicleNumber}?`)) {
        return;
    }
    
    try {
        const response = await fetch(`${API_URL}/api/vehicles/${vehicleNumber}/exit`, {
            method: 'POST'
        });
        
        if (!response.ok) {
            throw new Error('Exit failed');
        }
        
        const data = await response.json();
        displayExitResult(data);
        
        // Refresh slots
        loadSlots(document.getElementById('slotTypeFilter').value);
        
    } catch (error) {
        alert(error.message);
    }
});

// Display exit result
function displayExitResult(data) {
    const resultDiv = document.getElementById('exitResult');
    
    resultDiv.innerHTML = `
        <div class="payment-card">
            <div style="font-size: 0.875rem; color: var(--text-secondary); text-transform: uppercase;">Total Parking Fee</div>
            <div class="payment-amount">Rs ${data.fee.toFixed(2)}</div>
            <div class="payment-details">
                Vehicle: ${data.vehicle_number}<br>
                Duration: ${data.minutes} minutes
            </div>
            <button onclick="window.location.href='payment.html?amount=${data.fee}&vehicle=${data.vehicle_number}'" class="btn-submit">
                <i class="fas fa-credit-card"></i> PROCEED TO PAYMENT
            </button>
        </div>
    `;
    
    resultDiv.classList.add('show');
    resultDiv.style.display = 'block';
}

// Event listeners
document.getElementById('slotTypeFilter').addEventListener('change', (e) => {
    loadSlots(e.target.value);
});

document.getElementById('refreshSlots').addEventListener('click', () => {
    loadSlots(document.getElementById('slotTypeFilter').value);
});

document.getElementById('slotSelect').addEventListener('change', (e) => {
    const slot = allSlots.find(s => s.slot_id === e.target.value);
    if (slot) {
        selectSlot(slot);
    }
});

document.getElementById('estimatedDuration').addEventListener('input', updateCostEstimate);
document.getElementById('isVIP').addEventListener('change', updateCostEstimate);

// Initialize
loadSlots();

// WebSocket real-time updates
window.addEventListener('ws-slots-update', (e) => {
    const data = e.detail;
    allSlots = data.slots;
    const filterType = document.getElementById('slotTypeFilter').value;
    let filtered = allSlots;
    if (filterType !== 'all') {
        filtered = allSlots.filter(s => s.type === filterType);
    }
    displaySlots(filtered);
    updateStats(allSlots);
    updateSlotSelector(allSlots.filter(s => s.status === 'available'));
});
