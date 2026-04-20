import axios from 'axios';
import { config } from '../config';
import { supabase } from './supabase';

const FRIENDLY_FALLBACKS = {
  network: 'Unable to reach the server. Check your connection and try again.',
  401: 'Your session has expired. Please sign in again.',
  403: "You don't have permission to perform this action.",
  404: 'The requested resource was not found.',
  409: 'This action cannot be completed yet. Prerequisites may be missing.',
  422: 'The request could not be processed. Please check your input.',
  500: 'An unexpected error occurred. Please try again.',
  502: 'An upstream service is temporarily unavailable. Please try again shortly.',
  503: 'This feature is still being prepared. Please try again shortly.',
};

const detailToString = (detail) => {
  if (!detail) return null;
  if (typeof detail === 'string') return detail;
  if (typeof detail === 'object') {
    if (typeof detail.detail === 'string') return detail.detail;
    if (typeof detail.message === 'string') return detail.message;
  }
  return null;
};

// Normalize any backend error response into { error, message, user_action, status }
// so callers can show consistent, friendly UI without repeating parse logic.
export const normalizeApiError = (error) => {
  if (!error || !error.response) {
    return {
      error: 'network_error',
      message: FRIENDLY_FALLBACKS.network,
      user_action: 'retry',
      status: 0,
    };
  }

  const { status, data } = error.response;
  const payload = data && typeof data === 'object' ? data : {};
  const message =
    (typeof payload.message === 'string' && payload.message) ||
    detailToString(payload.detail) ||
    (typeof payload.error === 'string' && payload.error) ||
    FRIENDLY_FALLBACKS[status] ||
    'Request failed.';

  return {
    error: payload.error || `http_${status}`,
    message,
    user_action:
      payload.user_action ||
      (status === 401 ? 'sign_in' : status === 409 ? 'check_prerequisites' : status >= 500 ? 'retry' : 'check_input'),
    status,
  };
};

export const getErrorMessage = (error) => {
  if (typeof error === 'string') return error;
  if (error?.friendly?.message) return error.friendly.message;
  if (error?.response) return normalizeApiError(error).message;
  if (error?.message) return error.message;
  if (error?.error_description) return error.error_description;
  if (error?.msg) return error.msg;
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
    // Attach a normalized friendly payload so callers can read err.friendly.*
    // without duplicating parse logic. Existing code that reads
    // err.response.data.detail continues to work because the backend
    // preserves that field alongside the new shape.
    const friendly = normalizeApiError(error);
    error.friendly = friendly;

    if (friendly.status === 401) {
      await supabase.auth.signOut();
      window.location.href = '/login';
    }

    return Promise.reject(error);
  }
);

export default api;
