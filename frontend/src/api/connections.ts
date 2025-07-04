// src/api/connections.ts
import axios from '../utils/axiosInstance';
import config from '../config';

const API = `${config.connectionsApi}`;

export async function getConnections() {
  const response = await axios.get(API);
  return response.data;
}

export async function createConnection(conn: {
  name: string;
  hostname: string;
  port: number;
  bind_dn: string;
  password: string;
  use_ssl: boolean;
}) {
  const response = await axios.post(API, conn, {
    headers: {
      'Content-Type': 'application/json',
    },
  });
  return response.data;
}

export async function updateConnection(id: number, updates: any) {
  const response = await axios.patch(`${API}/${id}`, updates);
  return response.data;
}

export async function deleteConnection(id: number) {
  const response = await axios.delete(`${API}/${id}`);
  return response.data;
}
