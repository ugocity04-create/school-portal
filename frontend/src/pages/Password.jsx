import { useState } from 'react'
import { api } from '../api.js'
import { initials } from '../hooks.js'

function PhotoCard({ user }) {
  const [error, setError] = useState(null)
  const [busy, setBusy] = useState(false)
  async function pick(e) {
    const file = e.target.files[0]
    if (!file) return
    setBusy(true); setError(null)
    try {
      const fd = new FormData()
      fd.append('photo', file)
      await api('/me/photo/', { method: 'POST', body: fd })
      window.location.reload()
    } catch (err) { setError(err.message); setBusy(false) }
  }
  async function remove() {
    setBusy(true)
    try { await api('/me/photo/', { method: 'DELETE' }); window.location.reload() }
    catch (err) { setError(err.message); setBusy(false) }
  }
  return (
    <section className="card narrow" style={{ marginBottom: 16 }}>
      <h2>Profile picture</h2>
      <div className="photo-big">{user.photo ? <img src={user.photo} alt="Your profile" /> : initials(user.name)}</div>
      {error && <div className="error-box">{error}</div>}
      <label className="btn" style={{ cursor: 'pointer' }}>
        {busy ? 'Please wait...' : user.photo ? 'Change picture' : 'Upload picture'}
        <input type="file" accept="image/jpeg,image/png,image/webp" onChange={pick} disabled={busy} hidden />
      </label>
      {user.photo && <button className="btn btn-ghost" type="button" onClick={remove} disabled={busy} style={{ marginLeft: 8 }}>Remove</button>}
      <p className="hint">JPG, PNG or WEBP, under 2 MB.</p>
    </section>
  )
}

export default function Password({ user }) {
  const [old_password, setOld] = useState('')
  const [new_password, setNew] = useState('')
  const [msg, setMsg] = useState(null)
  const [error, setError] = useState(null)

  async function submit(e) {
    e.preventDefault()
    setMsg(null)
    setError(null)
    try {
      await api('/change-password/', { method: 'POST', body: { old_password, new_password } })
      setMsg('Password changed.')
      setOld('')
      setNew('')
    } catch (err) {
      setError(err.message)
    }
  }

  return (
    <>
      <section className="page-head"><div><h1>My profile</h1></div></section>
      <PhotoCard user={user} />
      <form className="card form narrow" onSubmit={submit}>
        {msg && <div className="flash flash-success">{msg}</div>}
        {error && <div className="error-box">{error}</div>}
        <label htmlFor="o">Current password</label>
        <input id="o" type="password" value={old_password} onChange={(e) => setOld(e.target.value)} autoComplete="current-password" required />
        <label htmlFor="n">New password</label>
        <input id="n" type="password" value={new_password} onChange={(e) => setNew(e.target.value)} autoComplete="new-password" required />
        <p className="hint">At least 8 characters, not too common and not only numbers.</p>
        <button className="btn" type="submit">Save password</button>
      </form>
    </>
  )
}