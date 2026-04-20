import axios from 'axios';
import { config } from '../config';
import { supabase } from './supabase';

export const getErrorMessage = (error) => {
  if (typeof error === 'string') return error;
  if (error?.message) return error.message;
  if (error?.error_description) return error.error_description;
  if (error?.msg) return error.msg;
  if (error?.response?.data?.message) return error.response.data.message;
  if (error?.response?.data?.error) return error.response.data.error;
  return 'An unexpected error occurred';
};

const api = axios.create({
  baseURL: config.apiUrl,
  headers: {
    'Content-Type': 'application/json'
  }
});

api.interceptors.request.use(
  async (config) => {
    const { data: { session } } = await supabase.auth.getSession();
    if (session?.access_token) {
      config.headers.Authorization = `Bearer ${session.access_token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

api.interceptors.response.use(
  (response) => response,
  async (error) => {
    // Normalize error.friendly for components to consume
    const status = error.response?.status;
    const data = error.response?.data;

    error.friendly = {
      status: status || 0,
      error: data?.error || 'network_error',
      message: data?.message
        || (status === 0 || !status ? 'Unable to reach the server. Check your connection.'
            : 'An unexpected error occurred. Please try again.'),
      user_action: data?.user_action || 'retry'
    };

    // Auth handling — redirect to login on 401
    if (status === 401) {
      await supabase.auth.signOut();
      window.location.href = '/login';
    }

    return Promise.reject(error);
  }
);

export default api;
