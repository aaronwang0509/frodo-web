// src/pages/LoginPage.tsx
import { Container, Heading, Button, VStack } from '@chakra-ui/react';
import { useNavigate } from 'react-router-dom';
import LoginForm from '../components/LoginForm';

export default function LoginPage() {
  const navigate = useNavigate();

  return (
    <Container centerContent mt={20}>
      <Heading mb={6}>Login</Heading>
      <VStack spacing={4}>
        <LoginForm />
        <Button variant="link" colorScheme="blue" onClick={() => navigate('/register')}>
          Don&apos;t have an account? Register
        </Button>
      </VStack>
    </Container>
  );
}
