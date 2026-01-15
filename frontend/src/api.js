import axios from 'axios';

const api = axios.create({
    baseURL: 'http://localhost:8000/api/v1',
    headers: {
        'Content-Type': 'application/json',
    },
});

// Add a request interceptor to include API Key
api.interceptors.request.use((config) => {
    const apiKey = import.meta.env.VITE_API_KEY || 'default-dev-key';
    config.headers['X-API-Key'] = apiKey;
    return config;
}, (error) => {
    return Promise.reject(error);
});

export default api;
