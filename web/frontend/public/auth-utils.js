// auth.js - Shared authentication utilities
const AUTH_API_URL = window.location.origin;

async function checkAuthState() {
    try {
        const res = await fetch(`${AUTH_API_URL}/api/auth/me`, { credentials: 'include' });
        if (!res.ok) return null;
        const user = await res.json();
        if (user.error) return null;
        return user;
    } catch {
        return null;
    }
}

async function handleLogout() {
    await fetch(`${AUTH_API_URL}/api/auth/logout`, { method: 'POST', credentials: 'include' });
    localStorage.removeItem('user');
    window.location.href = 'login.html';
}

function updateNavForAuth(user) {
    const navLinks = document.querySelector('.nav-links');
    if (!navLinks) return;

    // Remove existing auth links
    const existingAuth = navLinks.querySelector('.auth-nav-links');
    if (existingAuth) existingAuth.remove();

    const authDiv = document.createElement('span');
    authDiv.className = 'auth-nav-links';

    if (user) {
        authDiv.innerHTML = `
            <a href="history.html" data-testid="history-link" style="color: var(--primary);">${user.name}</a>
            <a href="#" onclick="handleLogout(); return false;" data-testid="logout-btn" class="nav-btn-secondary" style="border-color: var(--destructive); color: var(--destructive);">Logout</a>
        `;
    } else {
        authDiv.innerHTML = `
            <a href="login.html" data-testid="login-link" class="nav-cta">Sign In</a>
        `;
    }
    navLinks.appendChild(authDiv);
}

// Auto-init auth state on every page
document.addEventListener('DOMContentLoaded', async () => {
    const user = await checkAuthState();
    updateNavForAuth(user);
    window.currentUser = user;
});
