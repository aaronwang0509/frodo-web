// src/api/auth.ts
import axios from 'axios';
import config from '../config';

const API = `${config.authApi}`;

export async function login(username: string, password: string) {
  const response = await axios.post(`${API}/login`, {
    username,
    password,
  });
  return response.data;
}

export async function register(username: string, email: string, password: string) {
  const response = await axios.post(`${API}/register`, {
    username,
    email,
    password,
  });
  return response.data;
}

export async function refreshToken(refreshToken: string) {
  const response = await axios.post(`${API}/refresh`, {
    refresh_token: refreshToken,
  });
  return response.data;
}