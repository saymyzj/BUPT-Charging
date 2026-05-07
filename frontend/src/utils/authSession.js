const LEGACY_BUSINESS_KEYS = ['request_id', 'request_ids', 'active_request_conflict']

export function getAuthToken() {
  return sessionStorage.getItem('auth_token')
}

export function setAuthSession({ token }) {
  sessionStorage.setItem('auth_token', token || '')
  clearLegacyLocalState()
}

export function clearAuthSession() {
  sessionStorage.removeItem('auth_token')
  ;['auth_token', 'user_role', 'user_id', 'username'].forEach((key) => localStorage.removeItem(key))
  clearLegacyLocalState()
}

export function clearLegacyLocalState() {
  LEGACY_BUSINESS_KEYS.forEach((key) => {
    sessionStorage.removeItem(key)
    localStorage.removeItem(key)
  })
}
