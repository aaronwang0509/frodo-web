// src/components/ConnectionManager.tsx
import { useEffect, useState, useCallback } from 'react';
import {
  Box,
  Heading,
  Spinner,
  Table,
  Thead,
  Tbody,
  Tr,
  Th,
  Td,
  Switch,
  Input,
  Button,
  IconButton,
  TableContainer,
  useToast,
} from '@chakra-ui/react';
import { AddIcon, CloseIcon, DeleteIcon } from '@chakra-ui/icons';
import {
  getConnections,
  updateConnection,
  createConnection,
  deleteConnection,
} from '../api/connections';

declare global {
  interface Window {
    connectionIds: number[];
  }
}

interface ConnectionManagerProps {
  onUpdateConnections?: (ids: number[]) => void;
}

export default function ConnectionManager({ onUpdateConnections }: ConnectionManagerProps) {
  const [connections, setConnections] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [edited, setEdited] = useState<{ [id: number]: any }>({});
  const [adding, setAdding] = useState(false);
  const [newConn, setNewConn] = useState({
    name: '',
    hostname: '',
    port: '',
    bind_dn: '',
    password: '',
    use_ssl: true,
  });

  const toast = useToast();

  const refreshConnections = useCallback(async () => {
    const updated = await getConnections();
    setConnections(updated);
    const ids = updated.map((conn: any) => conn.id);
    window.connectionIds = ids;
    if (onUpdateConnections) {
      onUpdateConnections(ids);
    }
  }, [onUpdateConnections]);

  useEffect(() => {
    refreshConnections().finally(() => setLoading(false));
  }, [refreshConnections]);

  const handleChange = (id: number, field: string, value: any) => {
    setEdited(prev => ({
      ...prev,
      [id]: { ...prev[id], [field]: value },
    }));
  };

  const handleSave = async (id: number) => {
    const changes = edited[id];
    if (!changes) return;
    try {
      await updateConnection(id, changes);
      toast({
        title: 'Connection updated',
        status: 'success',
        duration: 2000,
        isClosable: true,
      });
      setEdited(prev => {
        const copy = { ...prev };
        delete copy[id];
        return copy;
      });
      await refreshConnections();
    } catch (err) {
      toast({
        title: 'Failed to update connection',
        status: 'error',
        duration: 3000,
        isClosable: true,
      });
    }
  };

  const handleAdd = async () => {
    try {
      await createConnection({ ...newConn, port: parseInt(newConn.port) });
      toast({
        title: 'Connection created',
        status: 'success',
        duration: 2000,
        isClosable: true,
      });
      setNewConn({
        name: '',
        hostname: '',
        port: '',
        bind_dn: '',
        password: '',
        use_ssl: true,
      });
      setAdding(false);
      await refreshConnections();
    } catch (err) {
      toast({
        title: 'Failed to create connection',
        status: 'error',
        duration: 3000,
        isClosable: true,
      });
    }
  };

  const handleDelete = async (id: number) => {
    try {
      await deleteConnection(id);
      toast({
        title: 'Connection deleted',
        status: 'success',
        duration: 2000,
        isClosable: true,
      });
      await refreshConnections();
    } catch (err) {
      toast({
        title: 'Failed to delete connection',
        status: 'error',
        duration: 3000,
        isClosable: true,
      });
    }
  };

  if (loading) return <Spinner />;

  return (
    <Box>
      <Heading size="md" mb={4}>
        LDAP Connections
      </Heading>

      <TableContainer border="1px solid" borderColor="gray.100" borderRadius="md">
        <Table variant="simple" size="sm">
          <Thead bg="gray.100">
            <Tr>
              <Th>ID</Th>
              <Th>Name</Th>
              <Th>Hostname</Th>
              <Th>Port</Th>
              <Th>Bind DN</Th>
              <Th>SSL</Th>
              {adding ? <Th>Password</Th> : null}
              <Th>Action</Th>
            </Tr>
          </Thead>
          <Tbody>
            {connections.map(conn => {
              const edit = edited[conn.id] || {};
              return (
                <Tr key={conn.id}>
                  <Td>{conn.id}</Td>
                  <Td>
                    <Input
                      size="sm"
                      value={edit.name ?? conn.name}
                      onChange={e =>
                        handleChange(conn.id, 'name', e.target.value)
                      }
                    />
                  </Td>
                  <Td>
                    <Input
                      size="sm"
                      value={edit.hostname ?? conn.hostname}
                      onChange={e =>
                        handleChange(conn.id, 'hostname', e.target.value)
                      }
                    />
                  </Td>
                  <Td>
                    <Input
                      size="sm"
                      type="number"
                      value={edit.port ?? conn.port}
                      onChange={e =>
                        handleChange(conn.id, 'port', parseInt(e.target.value))
                      }
                    />
                  </Td>
                  <Td>
                    <Input
                      size="sm"
                      value={edit.bind_dn ?? conn.bind_dn}
                      onChange={e =>
                        handleChange(conn.id, 'bind_dn', e.target.value)
                      }
                    />
                  </Td>
                  <Td>
                    <Box display="flex" alignItems="center" justifyContent="center">
                      <Switch
                        isChecked={edit.use_ssl ?? conn.use_ssl}
                        onChange={e =>
                          handleChange(conn.id, 'use_ssl', e.target.checked)
                        }
                        colorScheme="green"
                      />
                    </Box>
                  </Td>
                  {adding ? <Td /> : null}
                  <Td>
                    <Button
                      size="sm"
                      colorScheme="blue"
                      mr={2}
                      onClick={() => handleSave(conn.id)}
                    >
                      Save
                    </Button>
                    <IconButton
                      aria-label="Delete"
                      icon={<DeleteIcon />}
                      size="sm"
                      colorScheme="red"
                      onClick={() => handleDelete(conn.id)}
                    />
                  </Td>
                </Tr>
              );
            })}

            {adding && (
              <Tr>
                <Td>New</Td>
                <Td>
                  <Input
                    size="sm"
                    value={newConn.name}
                    onChange={e =>
                      setNewConn({ ...newConn, name: e.target.value })
                    }
                  />
                </Td>
                <Td>
                  <Input
                    size="sm"
                    value={newConn.hostname}
                    onChange={e =>
                      setNewConn({ ...newConn, hostname: e.target.value })
                    }
                  />
                </Td>
                <Td>
                  <Input
                    size="sm"
                    type="number"
                    value={newConn.port}
                    onChange={e =>
                      setNewConn({ ...newConn, port: e.target.value })
                    }
                  />
                </Td>
                <Td>
                  <Input
                    size="sm"
                    value={newConn.bind_dn}
                    onChange={e =>
                      setNewConn({ ...newConn, bind_dn: e.target.value })
                    }
                  />
                </Td>
                <Td>
                  <Box display="flex" alignItems="center" justifyContent="center">
                    <Switch
                      isChecked={newConn.use_ssl}
                      onChange={e =>
                        setNewConn({ ...newConn, use_ssl: e.target.checked })
                      }
                      colorScheme="green"
                    />
                  </Box>
                </Td>
                <Td>
                  <Input
                    size="sm"
                    type="password"
                    value={newConn.password}
                    onChange={e =>
                      setNewConn({ ...newConn, password: e.target.value })
                    }
                  />
                </Td>
                <Td>
                  <Button size="sm" colorScheme="green" mr={2} onClick={handleAdd}>
                    Save
                  </Button>
                  <IconButton
                    aria-label="Cancel"
                    icon={<CloseIcon />}
                    size="sm"
                    onClick={() => {
                      setAdding(false);
                      setNewConn({
                        name: '',
                        hostname: '',
                        port: '',
                        bind_dn: '',
                        password: '',
                        use_ssl: true,
                      });
                    }}
                  />
                </Td>
              </Tr>
            )}
          </Tbody>
        </Table>
      </TableContainer>

      {!adding && (
        <Button
          leftIcon={<AddIcon />}
          colorScheme="blue"
          mt={4}
          onClick={() => setAdding(true)}
        >
          Add Connection
        </Button>
      )}
    </Box>
  );
}