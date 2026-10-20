import { useCallback, useEffect, useState } from 'react'
import { api } from './api.js'

// Very small hash router, so no extra package is needed.
export function useHashRoute() {
  const read = () => window.location.hash.replace(/^#/, '') || '/'
  const [path, setPath] = useState(read)
  useEffect(() => {
    const on = () => {
      setPath(read())
      window.scrollTo(0, 0)
    }
    window.addEventListener('hashchange', on)
    return () => window.removeEventListener('hashchange', on)
  }, [])
  return path
}

export function go(path) {
  window.location.hash = path
}

// match('/student/12', '/student/:id') -> { id: '12' }, or null
export function match(path, pattern) {
  const a = path.split('?')[0].split('/').filter(Boolean)
  const b = pattern.split('/').filter(Boolean)
  if (a.length !== b.length) return null
  const out = {}
  for (let i = 0; i < b.length; i++) {
    if (b[i].startsWith(':')) out[b[i].slice(1)] = decodeURIComponent(a[i])
    else if (b[i] !== a[i]) return null
  }
  return out
}

export function useApi(path) {
  const [state, setState] = useState({ data: null, error: null, loading: true })
  const load = useCallback(() => {
    if (!path) return
    setState((s) => ({ ...s, loading: true, error: null }))
    api(path)
      .then((data) => setState({ data, error: null, loading: false }))
      .catch((error) => setState({ data: null, error, loading: false }))
  }, [path])
  useEffect(load, [load])
  return { ...state, reload: load, setData: (data) => setState({ data, error: null, loading: false }) }
}

export const num = (v) => (v === null || v === undefined ? '-' : String(Math.round(v * 10) / 10))

export const ordinal = (n) => {
  const s = n % 100 >= 11 && n % 100 <= 13 ? 'th' : { 1: 'st', 2: 'nd', 3: 'rd' }[n % 10] || 'th'
  return n + s
}

export const initials = (name) =>
  (name || '?')
    .replace(/^(Mr|Mrs|Miss|Dr|Alhaji|Chief)\.?\s+/i, '')
    .split(/\s+/)
    .slice(0, 2)
    .map((w) => w[0])
    .join('')
    .toUpperCase()