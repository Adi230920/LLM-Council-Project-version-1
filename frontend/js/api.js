/**
 * BouleAI — API Wrapper
 */

const API_URL = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1'
    ? ''
    : 'https://your-backend-url.railway.app'; // Replace with actual backend URL after deployment

const API = {
    async fetch(endpoint, options = {}) {
        const fullURL = endpoint.startsWith('http') ? endpoint : `${API_URL}${endpoint}`;
        const token = localStorage.getItem('access_token');
        const headers = {
            'Content-Type': 'application/json',
            ...options.headers
        };

        if (token) {
            headers['Authorization'] = `Bearer ${token}`;
        }

        const response = await fetch(fullURL, {
            ...options,
            headers
        });

        if (response.status === 401 && !endpoint.includes('/auth/')) {
            // Token expired or invalid
            localStorage.removeItem('access_token');
            window.location.href = '/login.html';
            return;
        }

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'API request failed');
        }

        return response.json();
    }
};

export default API;
