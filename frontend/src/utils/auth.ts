// src/utils/auth.ts
export function isAuthenticated(): boolean {
  return !!localStorage.getItem('token');
}

export function logout() {
  localStorage.removeItem('token');
  localStorage.removeItem('refresh_token');
  window.location.href = '/'; // Redirect to login
}