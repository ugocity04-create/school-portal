// Talks to the Django JSON API. Uses Django's session cookie and CSRF token.
const BASE = import.meta.env.VITE_API_URL || ''

function csrfToken() {
  const m = document.cookie.match(/(?:^|; )csrftoken=([^;]*)/)
  return m ? decodeURIComponent(m[1]) : ''
}

let onUnauthorized = () => {}
export function setUnauthorizedHandler(fn) {
  onUnauthorized = fn
}

export async function api(path, { method = 'GET', body } = {}) {
  const isForm = typeof FormData !== 'undefined' && body instanceof FormData
  const headers = { 'X-CSRFToken': csrfToken() }
  if (!isForm) headers['Content-Type'] = 'application/json'
  const res = await fetch(BASE + '/api' + path, {
    method,
    credentials: BASE ? 'include' : 'same-origin',
    headers,
    body: body === undefined ? undefined : isForm ? body : JSON.stringify(body),
  })
  let data = null
  try {
    data = await res.json()
  } catch {
    /* not JSON */
  }
  if (!res.ok) {
    if (res.status === 401 && path !== '/login/') onUnauthorized()
    const err = new Error((data && data.error) || 'Something went wrong. Please try again.')
    err.status = res.status
    err.data = data
    throw err
  }
  return data
}