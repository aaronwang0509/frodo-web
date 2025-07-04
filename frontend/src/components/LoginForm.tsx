// src/components/LoginForm.tsx
import { useState } from 'react';
import { Button, Input, VStack, Text } from '@chakra-ui/react';
import { login } from '../api/auth';

export default function LoginForm() {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');

  const handleLogin = async () => {
    try {
      const data = await login(username, password);
      localStorage.setItem('token', data.access_token);
      localStorage.setItem('refresh_token', data.refresh_token);
      window.location.href = '/dashboard'; // Placeholder
    } catch (err) {
      setError('Login failed');
    }
  };

  return (
    <VStack spacing={4}>
      <Input placeholder="Username" value={username} onChange={(e) => setUsername(e.target.value)} />
      <Input placeholder="Password" type="password" value={password} onChange={(e) => setPassword(e.target.value)} />
      <Button onClick={handleLogin}>Login</Button>
      {error && <Text color="red.500">{error}</Text>}
    </VStack>
  );
}
