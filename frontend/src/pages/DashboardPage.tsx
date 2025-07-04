// src/pages/DashboardPage.tsx
import { Box, Container, Flex, Heading, Stack, Text, Button } from '@chakra-ui/react';
import { useState, useEffect } from 'react';
import { ldapSearch } from '../api/ldap';
import { logout } from '../utils/auth';
import ConnectionManager from '../components/ConnectionManager';
import LdapSearchPanel from '../components/LdapSearchPanel';
import LdapResultTable from '../components/LdapResultTable';

export default function DashboardPage() {
  const [connectionId, setConnectionId] = useState('');
  const [baseDn, setBaseDn] = useState('');
  const [filter, setFilter] = useState('');
  const [attributes, setAttributes] = useState('');
  const [results, setResults] = useState<any[]>([]);
  const [username, setUsername] = useState('');
  const [connectionIds, setConnectionIds] = useState<number[]>([]);

  useEffect(() => {
    const token = localStorage.getItem('token');
    if (token) {
      try {
        const payload = JSON.parse(atob(token.split('.')[1]));
        setUsername(payload.sub || payload.username || 'Unknown');
      } catch {
        setUsername('Unknown');
      }
    }
  }, []);

  const handleSearch = async () => {
    if (!connectionId) return;

    try {
      const result = await ldapSearch({
        connectionId: parseInt(connectionId),
        baseDn,
        filter,
        attributes: attributes.split(',').map(attr => attr.trim()),
      });

      const flattened = result.map((entry: { dn: string; attributes: Record<string, any> }) => ({
        dn: entry.dn,
        ...entry.attributes,
      }));

      setResults(flattened);
    } catch (err) {
      console.error("Search failed", err);
    }
  };

  return (
    <Container maxW="container.lg" py={10}>
      <Flex justify="space-between" align="center" mb={6}>
        <Heading>Dashboard</Heading>
        <Flex align="center" gap={4}>
          <Text fontSize="md" color="gray.600" fontWeight="medium">{username}</Text>
          <Button size="sm" colorScheme="red" onClick={logout}>Logout</Button>
        </Flex>
      </Flex>
      <Stack spacing={8}>
        <Box borderWidth={1} p={4} borderRadius="md">
          <ConnectionManager onUpdateConnections={setConnectionIds} />
        </Box>
        <Box borderWidth={1} p={4} borderRadius="md">
          <LdapSearchPanel
            connectionId={connectionId}
            setConnectionId={setConnectionId}
            baseDn={baseDn}
            setBaseDn={setBaseDn}
            filter={filter}
            setFilter={setFilter}
            attributes={attributes}
            setAttributes={setAttributes}
            onSearch={handleSearch}
            connectionIds={connectionIds}
          />
        </Box>
        <Box
          borderWidth={1}
          p={4}
          borderRadius="md"
          maxHeight="500px"
          overflow="auto"
        >
          <LdapResultTable
            results={results}
            onRefresh={handleSearch}
            connectionId={connectionId ? parseInt(connectionId) : null}
          />
        </Box>
      </Stack>
    </Container>
  );
}
