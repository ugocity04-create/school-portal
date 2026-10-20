import About from '../components/About.jsx'
import { useState } from 'react'
import { api } from '../api.js'
import { LogoMark } from '../components/Logo.jsx'

const DEMO = [
  ['ada.nwosu', 'Student'],
  ['emeka.nwosu', 'Parent'],
  ['ngozi.eze', 'Teacher'],
  ['school.admin', 'Admin'],
]
const SHOW_DEMO = import.meta.env.VITE_DEMO !== '0'

const FEATURES = [
  ['↑', 'Progress charts', 'See how every pupil, class and the whole school is doing, term by term.'],
  ['✓', 'Daily attendance', 'Teachers take the register; parents see it the same day.'],
  ['✎', 'Homework and remarks', 'Set work, track deadlines and share teachers\' remarks.'],
  ['₦', 'Fees and receipts', 'Balances, payments and printable receipts for every child.'],
]

export default function Login({ school, onLogin }) {
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState(null)
  const [busy, setBusy] = useState(false)

  async function submit(e, u = username, p = password) {
    e && e.preventDefault()
    setBusy(true)
    setError(null)
    try {
      const d = await api('/login/', { method: 'POST', body: { username: u, password: p } })
      onLogin(d.user)
    } catch (err) {
      setError(err.message)
      setBusy(false)
    }
  }

  return (
    <div className="wrap main">
      <div className="login-grid">
        <div className="hero-login">
          <LogoMark size={64} />
          <p className="eyebrow" style={{ marginTop: 14 }}>{school}</p>
          <h1>Everything about school life, in one place.</h1>
          <p className="lead">A safe portal for pupils, parents, teachers and the school office.</p>
          <ul className="feature-list">
            {FEATURES.map(([icon, title, text]) => (
              <li key={title}><i aria-hidden="true">{icon}</i><span><b>{title}</b><br /><span style={{ opacity: 0.85 }}>{text}</span></span></li>
            ))}
          </ul>
        </div>
        <div>
          <form className="card form" onSubmit={submit}>
            <h2>Sign in</h2>
            {error && <div className="error-box" role="alert">{error}</div>}
            <label htmlFor="u">Username</label>
            <input id="u" value={username} onChange={(e) => setUsername(e.target.value)}
                   autoCapitalize="none" autoComplete="username" spellCheck="false" required />
            <label htmlFor="p">Password</label>
            <input id="p" type="password" value={password} onChange={(e) => setPassword(e.target.value)}
                   autoComplete="current-password" required />
            <button className="btn btn-block" type="submit" disabled={busy}>{busy ? 'Signing in...' : 'Sign in'}</button>
          </form>
          {SHOW_DEMO && (
            <div className="card demo-card">
              <h2>Try the demo</h2>
              <p className="small muted">Invented pupils and marks. Tap a role to sign in (password: demo1234).</p>
              <div className="demo-buttons">
                {DEMO.map(([u, label]) => (
                  <button key={u} type="button" className="demo-btn" disabled={busy}
                          onClick={() => submit(null, u, 'demo1234')}>{label}</button>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
      <div style={{ marginTop: 16 }}><About /></div>
    </div>
  )
}