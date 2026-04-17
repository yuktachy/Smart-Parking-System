// ws-client.js - WebSocket client for real-time updates
(function() {
    const BACKEND_URL = window.location.origin;
    let socket = null;
    let reconnectAttempts = 0;
    const MAX_RECONNECT = 5;

    function connectWebSocket() {
        // Load socket.io client
        if (typeof io === 'undefined') {
            const script = document.createElement('script');
            script.src = 'https://cdn.socket.io/4.7.5/socket.io.min.js';
            script.onload = () => initSocket();
            document.head.appendChild(script);
        } else {
            initSocket();
        }
    }

    function initSocket() {
        try {
            socket = io(BACKEND_URL, {
                path: '/api/socket.io',
                transports: ['websocket', 'polling'],
                reconnection: true,
                reconnectionAttempts: MAX_RECONNECT,
                reconnectionDelay: 2000
            });

            socket.on('connect', () => {
                console.log('WebSocket connected');
                reconnectAttempts = 0;
                showConnectionStatus(true);
            });

            socket.on('disconnect', () => {
                console.log('WebSocket disconnected');
                showConnectionStatus(false);
            });

            // Slot updates
            socket.on('slots_update', (data) => {
                if (typeof window.onSlotsUpdate === 'function') {
                    window.onSlotsUpdate(data);
                }
                // Dispatch custom event
                window.dispatchEvent(new CustomEvent('ws-slots-update', { detail: data }));
            });

            // Stats updates
            socket.on('stats_update', (data) => {
                if (typeof window.onStatsUpdate === 'function') {
                    window.onStatsUpdate(data);
                }
                window.dispatchEvent(new CustomEvent('ws-stats-update', { detail: data }));
            });

            // Reservation notifications
            socket.on('reservation_notification', (data) => {
                showNotification(data.message);
                window.dispatchEvent(new CustomEvent('ws-reservation-notification', { detail: data }));
            });

            socket.on('connect_error', (err) => {
                console.log('WebSocket connection error, falling back to polling');
                reconnectAttempts++;
            });

            window.wsSocket = socket;
        } catch (err) {
            console.log('WebSocket not available, using polling fallback');
        }
    }

    function showConnectionStatus(connected) {
        let indicator = document.getElementById('ws-status');
        if (!indicator) {
            indicator = document.createElement('div');
            indicator.id = 'ws-status';
            indicator.style.cssText = 'position:fixed;bottom:1rem;right:1rem;padding:0.5rem 1rem;font-size:0.75rem;z-index:100;border:1px solid;display:flex;align-items:center;gap:0.5rem;font-family:JetBrains Mono,monospace;';
            document.body.appendChild(indicator);
        }
        if (connected) {
            indicator.style.background = 'rgba(57,255,20,0.1)';
            indicator.style.borderColor = 'rgba(57,255,20,0.3)';
            indicator.style.color = '#39FF14';
            indicator.innerHTML = '<span style="width:8px;height:8px;background:#39FF14;border-radius:50;display:inline-block;animation:pulse 2s infinite;"></span> LIVE';
        } else {
            indicator.style.background = 'rgba(255,184,0,0.1)';
            indicator.style.borderColor = 'rgba(255,184,0,0.3)';
            indicator.style.color = '#FFB800';
            indicator.innerHTML = '<span style="width:8px;height:8px;background:#FFB800;border-radius:50%;display:inline-block;"></span> RECONNECTING';
        }
        // Auto-hide after 3 seconds if connected
        if (connected) {
            setTimeout(() => { indicator.style.opacity = '0.3'; }, 3000);
            indicator.onmouseenter = () => { indicator.style.opacity = '1'; };
            indicator.onmouseleave = () => { indicator.style.opacity = '0.3'; };
        }
    }

    function showNotification(message) {
        const notif = document.createElement('div');
        notif.style.cssText = 'position:fixed;top:5rem;right:1rem;background:#0A0B10;border:1px solid #FFB800;color:#FFB800;padding:1rem 1.5rem;z-index:200;max-width:350px;font-size:0.875rem;animation:slideIn 0.3s ease;';
        notif.innerHTML = `<div style="display:flex;align-items:center;gap:0.75rem;"><i class="fas fa-bell" style="font-size:1.25rem;"></i><div>${message}</div></div>`;
        document.body.appendChild(notif);
        setTimeout(() => {
            notif.style.opacity = '0';
            notif.style.transition = 'opacity 0.3s';
            setTimeout(() => notif.remove(), 300);
        }, 5000);
    }

    // Check for expiring reservations every 60 seconds
    function startExpiryChecker() {
        setInterval(async () => {
            try {
                const res = await fetch(`${BACKEND_URL}/api/reservations/check-expiring`);
                if (res.ok) {
                    const data = await res.json();
                    if (data.count > 0) {
                        data.expiring.forEach(r => {
                            showNotification(`Reservation for ${r.vehicle_number} at ${r.slot_id} is expiring soon!`);
                        });
                    }
                }
            } catch (e) {
                // silent fail
            }
        }, 60000);
    }

    // Init
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', () => {
            connectWebSocket();
            startExpiryChecker();
        });
    } else {
        connectWebSocket();
        startExpiryChecker();
    }
})();
