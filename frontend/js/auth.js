/**
 * BouleAI — Auth Controller
 */
import API from './api.js';

const Auth = {
    isAuthenticated() {
        return !!localStorage.getItem('access_token');
    },

    async login(username, password) {
        const formData = new FormData();
        formData.append('username', username);
        formData.append('password', password);

        const response = await fetch('/auth/login', {
            method: 'POST',
            body: formData
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Login failed');
        }

        const data = await response.json();
        localStorage.setItem('access_token', data.access_token);
        return data;
    },

    async signup(email, password) {
        const data = await API.fetch('/auth/signup', {
            method: 'POST',
            body: JSON.stringify({ email, password })
        });
        localStorage.setItem('access_token', data.access_token);
        return data;
    },

    logout() {
        localStorage.removeItem('access_token');
        window.location.href = '/login.html';
    },

    checkAuth() {
        if (!this.isAuthenticated() && !window.location.pathname.includes('login') && !window.location.pathname.includes('signup')) {
            window.location.href = '/login.html';
        }
    }
};

export default Auth;
