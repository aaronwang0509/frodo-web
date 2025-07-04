// src/components/PrivateRoute.tsx
import React from 'react';
import { Navigate, Outlet } from 'react-router-dom';
import { isAuthenticated } from '../utils/auth';

export default function PrivateRoute() {
  return isAuthenticated() ? <Outlet /> : <Navigate to="/" />;
}
