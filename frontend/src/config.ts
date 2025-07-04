// src/config.ts
const baseApi = 'http://localhost:8000';

const config = {
  baseApi,
  authApi: `${baseApi}/auth`,
  connectionsApi: `${baseApi}/api/connections`,
  ldapSearchApi: `${baseApi}/api/ldap/search`,
  ldapModifyApi: `${baseApi}/api/ldap/modify`,
};

export default config;