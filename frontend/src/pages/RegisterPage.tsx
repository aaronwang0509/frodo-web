// src/pages/RegisterPage.tsx
import { Container, Heading } from '@chakra-ui/react';
import RegisterForm from '../components/RegisterForm';

export default function RegisterPage() {
  return (
    <Container centerContent mt={20}>
      <Heading mb={6}>Register</Heading>
      <RegisterForm />
    </Container>
  );
}