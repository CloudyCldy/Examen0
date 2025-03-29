import axios from 'axios';

const API_URL = "https://13.218.99.111"; // Your FastAPI server address

// Create axios instance with default config
const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
    // Add any other default headers here
  },
  // withCredentials: true, // Uncomment if using cookies/auth
});

// Request interceptor to handle CORS preflight
api.interceptors.request.use((config) => {
  // Add CORS headers to every request
  config.headers['Access-Control-Allow-Origin'] = window.location.origin;
  return config;
}, (error) => {
  return Promise.reject(error);
});

// Response interceptor for error handling
api.interceptors.response.use((response) => {
  return response;
}, (error) => {
  if (error.response) {
    console.error('API Error:', error.response.status, error.response.data);
    
    // Handle CORS errors specifically
    if (error.response.status === 0) {
      console.error('CORS Error: Request blocked by browser policy');
      throw new Error('Cross-origin request blocked. Please check server CORS configuration.');
    }
  }
  return Promise.reject(error);
});

// API functions
export const getUsuarios = async () => {
  try {
    const response = await api.get('/usuarios');
    return response.data;
  } catch (error) {
    console.error('Error fetching usuarios:', error);
    throw error;
  }
};

export const getUsuarioById = async (id) => {
  try {
    const response = await api.get(`/usuarios/${id}`);
    return response.data;
  } catch (error) {
    console.error(`Error fetching usuario ${id}:`, error);
    throw error;
  }
};

export const createUsuario = async (usuario) => {
  try {
    const response = await api.post('/usuarios', usuario);
    return response.data;
  } catch (error) {
    console.error('Error creating usuario:', error);
    throw error;
  }
};

export const updateUsuario = async (id, usuario) => {
  try {
    const response = await api.put(`/usuarios/${id}`, usuario);
    return response.data;
  } catch (error) {
    console.error(`Error updating usuario ${id}:`, error);
    throw error;
  }
};

export const deleteUsuario = async (id) => {
  try {
    const response = await api.delete(`/usuarios/${id}`);
    return response.data;
  } catch (error) {
    console.error(`Error deleting usuario ${id}:`, error);
    throw error;
  }
};