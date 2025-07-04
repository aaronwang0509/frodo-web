// src/utils/axiosInstance.ts
import axios from 'axios';
import config from '../config';
import { refreshToken } from '../api/auth';
import { logout } from './auth';

const instance = axios.create({
  baseURL: config.baseApi,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Flag to avoid multiple refresh calls simultaneously
let isRefreshing = false;
let refreshSubscribers: Array<(token: string) => void> = [];

function subscribeTokenRefresh(cb: (token: string) => void) {
  refreshSubscribers.push(cb);
}

function onRefreshed(token: string) {
  refreshSubscribers.forEach(cb => cb(token));
  refreshSubscribers = [];
}

// Request interceptor to add Authorization header
instance.interceptors.request.use(config => {
  const token = localStorage.getItem('token');
  if (token && config.headers) {
    config.headers['Authorization'] = `Bearer ${token}`;
  }
  return config;
});

// Response interceptor to handle 401
instance.interceptors.response.use(
  response => response,
  async error => {
    const originalRequest = error.config;

    if (
      error.response?.status === 401 &&
      !originalRequest._retry &&
      localStorage.getItem('refresh_token')
    ) {
      originalRequest._retry = true;

      if (isRefreshing) {
        return new Promise((resolve, reject) => {
          subscribeTokenRefresh((newToken: string) => {
            originalRequest.headers['Authorization'] = `Bearer ${newToken}`;
            resolve(instance(originalRequest));
          });
        });
      }

      isRefreshing = true;
      const refresh_token = localStorage.getItem('refresh_token')!;

      try {
        const data = await refreshToken(refresh_token);
        localStorage.setItem('token', data.access_token);
        onRefreshed(data.access_token);
        originalRequest.headers['Authorization'] = `Bearer ${data.access_token}`;
        return instance(originalRequest);
      } catch (err) {
        logout(); // Clear tokens and redirect to login
        return Promise.reject(err);
      } finally {
        isRefreshing = false;
      }
    }

    return Promise.reject(error);
  }
);

export default instance;