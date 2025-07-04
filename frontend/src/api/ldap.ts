// src/api/ldap.ts
import axios from '../utils/axiosInstance';
import config from '../config';

const SEARCH_API = `${config.ldapSearchApi}`;
const MODIFY_API = `${config.ldapModifyApi}`;

export async function ldapSearch({
  connectionId,
  baseDn,
  filter,
  attributes,
}: {
  connectionId: number;
  baseDn: string;
  filter: string;
  attributes: string[];
}) {
  const response = await axios.post(SEARCH_API, {
    connection_id: connectionId,
    base_dn: baseDn,
    filter,
    attributes,
  });
  return response.data; // should be a list of entry dicts
}

export async function ldapModify({
  connectionId,
  dn,
  changes,
}: {
  connectionId: number;
  dn: string;
  changes: {
    operation: 'add' | 'delete' | 'replace';
    attribute: string;
    values: string[];
  }[];
}) {
  const response = await axios.post(MODIFY_API, {
    connection_id: connectionId,
    dn,
    changes,
  });
  return response.data;
}