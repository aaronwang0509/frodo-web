// src/components/LdapResultTable.tsx
import {
  Box,
  Table,
  Thead,
  Tbody,
  Tr,
  Th,
  Td,
  Input,
  IconButton,
  HStack,
  useToast,
} from '@chakra-ui/react';
import { useState, useEffect } from 'react';
import { ldapModify } from '../api/ldap';
import { CheckIcon, CloseIcon, DeleteIcon } from '@chakra-ui/icons';

interface Props {
  results: any[];
  onRefresh: () => void;
  connectionId: number | null;
}

export default function LdapResultTable({ results, onRefresh, connectionId }: Props) {
  const [editing, setEditing] = useState<{ [dn: string]: any }>({});
  const [resultsRefresh, setResultsRefresh] = useState(Date.now());
  const toast = useToast();

  useEffect(() => {
    setEditing({});
    setResultsRefresh(Date.now());
    console.log('[LdapResultTable] Results updated, clearing edits and refreshing table');
  }, [results]);

  if (!results || results.length === 0) return null;

  const allAttributes = Array.from(
    new Set(
      results.flatMap(entry =>
        Object.keys(entry).filter(key => key !== 'dn')
      )
    )
  );

  const handleEdit = (dn: string, attr: string, value: string) => {
    setEditing(prev => ({
      ...prev,
      [dn]: {
        ...(prev[dn] || {}),
        [attr]: value,
      },
    }));
    console.log(`[LdapResultTable] Edited ${attr} for ${dn} to ${value}`);
  };

  return (
    <Box key={resultsRefresh} mt={8} maxHeight="500px" overflow="auto">
      <Box overflowX="auto" overflowY="auto">
        <Table
          variant="simple"
          size="sm"
          sx={{
            'th, td': {
              minWidth: '160px',
              maxWidth: '160px',
              overflow: 'hidden',
              textOverflow: 'ellipsis',
              whiteSpace: 'nowrap',
            }
          }}
        >
          <Thead>
            <Tr bg="gray.100">
              <Th textTransform="none" minWidth="180px" maxWidth="180px">dn</Th>
              {allAttributes.map(attr => (
                <Th key={attr} textTransform="none" minWidth="180px" maxWidth="180px">{attr}</Th>
              ))}
              <Th>Action</Th>
            </Tr>
          </Thead>
          <Tbody>
            {results.map(entry => {
              const dn = entry.dn;
              const attrs = { ...entry };
              delete attrs.dn;

              return (
                <Tr key={dn}>
                  <Td fontSize="xs">{entry.dn}</Td>
                  {allAttributes.map(attr => {
                    const value = attrs[attr];
                    const currentValue = Array.isArray(value) ? value.join(', ') : value ?? '';
                    const editedValue =
                      editing[dn]?.[attr] ?? currentValue;

                    return (
                      <Td key={attr} width="180px" minWidth="180px" maxWidth="180px">
                        {currentValue === '' ? (
                          <Input
                            size="sm"
                            height="24px"
                            padding="4px"
                            width="100%"
                            value=""
                            isDisabled
                          />
                        ) : (
                          <Input
                            size="sm"
                            height="24px"
                            padding="4px"
                            width="100%"
                            value={editedValue}
                            onChange={e =>
                              handleEdit(dn, attr, e.target.value)
                            }
                          />
                        )}
                      </Td>
                    );
                  })}
                  <Td>
                    <HStack spacing={1}>
                      <IconButton
                        icon={<CheckIcon />}
                        aria-label="Save"
                        size="xs"
                        colorScheme="green"
                        onClick={async () => {
                          if (!connectionId) {
                            toast({
                              title: 'Missing connection ID',
                              status: 'error',
                              duration: 3000,
                              isClosable: true,
                            });
                            return;
                          }

                          const changes = Object.entries(editing[dn] || {}).map(([attribute, value]): {
                            operation: 'replace';
                            attribute: string;
                            values: string[];
                          } => ({
                            operation: 'replace',
                            attribute,
                            values: String(value).trim() === '' ? [] : String(value).split(',').map((v: string) => v.trim()),
                          }));

                          console.log('[LdapResultTable] Sending modify request:', { connectionId, dn, changes });

                          try {
                            await ldapModify({
                              connectionId,
                              dn,
                              changes,
                            });

                            toast({
                              title: `Modified ${dn}`,
                              status: 'success',
                              duration: 2000,
                              isClosable: true,
                            });

                            setEditing({});
                            onRefresh(); // Force re-search from backend for updated values
                            console.log('[LdapResultTable] Called onRefresh directly after modify');
                          } catch (err) {
                            toast({
                              title: `Modify failed for ${dn}`,
                              description: (err as Error)?.message || 'Check if attribute is editable.',
                              status: 'error',
                              duration: 4000,
                              isClosable: true,
                            });
                            setEditing({});
                            onRefresh(); // Trigger refresh on error too
                          }
                        }}
                      />
                      <IconButton
                        icon={<CloseIcon />}
                        aria-label="Cancel"
                        size="xs"
                        onClick={() => {
                          setEditing(prev => {
                            const copy = { ...prev };
                            delete copy[dn];
                            return copy;
                          });
                          onRefresh(); // Refresh the row to original state
                        }}
                      />
                      <IconButton
                        icon={<DeleteIcon />}
                        aria-label="Delete"
                        size="xs"
                        colorScheme="red"
                        onClick={() => {
                          toast({
                            title: 'Delete not supported',
                            description: 'Removing LDAP entries is not implemented yet.',
                            status: 'info',
                            duration: 3000,
                            isClosable: true,
                          });
                        }}
                      />
                    </HStack>
                  </Td>
                </Tr>
              );
            })}
          </Tbody>
        </Table>
      </Box>
    </Box>
  );
}