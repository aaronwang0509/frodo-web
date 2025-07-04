// src/components/RegisterForm.tsx
import { useState } from 'react';
import { Button, Input, VStack, Text } from '@chakra-ui/react';
import { register } from '../api/auth';
import { useNavigate } from 'react-router-dom';

export default function RegisterForm() {
  const [username, setUsername] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const navigate = useNavigate();

  const handleRegister = async () => {
    try {
      await register(username, email, password);
      setSuccess('Registration successful! Redirecting...');
      setTimeout(() => navigate('/'), 1500);
    } catch (err: any) {
      setError(err.message || 'Registration failed');
    }
  };

  return (
    <VStack spacing={4}>
      <Input placeholder="Username" value={username} onChange={(e) => setUsername(e.target.value)} />
      <Input placeholder="Email" value={email} onChange={(e) => setEmail(e.target.value)} />
      <Input placeholder="Password" type="password" value={password} onChange={(e) => setPassword(e.target.value)} />
      <Button onClick={handleRegister}>Register</Button>
      {error && <Text color="red.500">{error}</Text>}
      {success && <Text color="green.500">{success}</Text>}
    </VStack>
  );
}