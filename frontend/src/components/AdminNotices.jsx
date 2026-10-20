import { useState } from 'react'
import { api } from '../api.js'
import { useApi } from '../hooks.js'
import { EventList, NoticeList } from './Notices.jsx'

export default function AdminNotices() {
  const { data, error, loading, reload } = useApi('/admin/notices/')
  const [n, setN] = useState({ title: '', body: '', audience: 'all', pinned: false })
  const [e, setE] = useState({ title: '', date: '', end_date: '', description: '' })
  const [msg, setMsg] = useState(null)
  const [problem, setProblem] = useState(null)

  async function send(path, body, reset) {
    setMsg(null)
    setProblem(null)
    try {
      await api(path, { method: 'POST', body })
      reset()
      setMsg('Saved.')
      reload()
    } catch (err) {
      setProblem(err.message)
    }
  }
  async function remove(path) {
    if (!window.confirm('Delete this?')) return
    try {
      await api(path, { method: 'POST' })
      reload()
    } catch (err) {
      setProblem(err.message)
    }
  }

  if (error) return <div className="error-box">{error.message}</div>
  if (loading && !data) return <p className="muted">Loading...</p>

  return (
    <>
      {msg && <div className="flash flash-success">{msg}</div>}
      {problem && <div className="error-box">{problem}</div>}
      <section className="grid-2">
        <form className="card form" onSubmit={(ev) => { ev.preventDefault(); send('/admin/notices/create/', n, () => setN({ title: '', body: '', audience: 'all', pinned: false })) }}>
          <h2>Post a notice</h2>
          <label htmlFor="nt">Title</label>
          <input id="nt" value={n.title} maxLength="120" required onChange={(x) => setN({ ...n, title: x.target.value })} />
          <label htmlFor="nb">Message</label>
          <textarea id="nb" rows="4" maxLength="1000" required value={n.body} onChange={(x) => setN({ ...n, body: x.target.value })} />
          <label htmlFor="na">Who should see it</label>
          <select id="na" value={n.audience} onChange={(x) => setN({ ...n, audience: x.target.value })}>
            <option value="all">Everyone</option><option value="students">Students</option>
            <option value="parents">Parents</option><option value="teachers">Teachers</option>
          </select>
          <label><input type="checkbox" checked={n.pinned} onChange={(x) => setN({ ...n, pinned: x.target.checked })} /> Pin to the top</label>
          <button className="btn" type="submit">Post notice</button>
        </form>
        <form className="card form" onSubmit={(ev) => { ev.preventDefault(); send('/admin/events/create/', e, () => setE({ title: '', date: '', end_date: '', description: '' })) }}>
          <h2>Add an event</h2>
          <label htmlFor="et">Title</label>
          <input id="et" value={e.title} maxLength="120" required onChange={(x) => setE({ ...e, title: x.target.value })} />
          <label htmlFor="ed">Date</label>
          <input id="ed" type="date" required value={e.date} onChange={(x) => setE({ ...e, date: x.target.value })} />
          <label htmlFor="ee">Last day (optional)</label>
          <input id="ee" type="date" value={e.end_date} onChange={(x) => setE({ ...e, end_date: x.target.value })} />
          <label htmlFor="ex">Details (optional)</label>
          <input id="ex" value={e.description} maxLength="240" onChange={(x) => setE({ ...e, description: x.target.value })} />
          <button className="btn" type="submit">Add event</button>
        </form>
      </section>

      <section className="grid-2">
        <div className="card">
          <h2>Current notices</h2>
          {data.announcements.map((a) => (
            <div key={a.id}>
              <NoticeList items={[a]} />
              <p className="small muted">For: {a.audience} <button className="btn btn-small btn-ghost" type="button" onClick={() => remove(`/admin/notices/${a.id}/delete/`)}>Delete</button></p>
            </div>
          ))}
          {data.announcements.length === 0 && <p className="muted">No notices yet.</p>}
        </div>
        <div className="card">
          <h2>Upcoming events</h2>
          {data.events.map((ev) => (
            <div key={ev.id}>
              <EventList items={[ev]} />
              <button className="btn btn-small btn-ghost" type="button" onClick={() => remove(`/admin/events/${ev.id}/delete/`)}>Delete</button>
            </div>
          ))}
          {data.events.length === 0 && <p className="muted">No upcoming events.</p>}
        </div>
      </section>
    </>
  )
}