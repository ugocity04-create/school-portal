import { initials, num, ordinal, useApi } from '../hooks.js'
import { naira } from '../components/Charts.jsx'
import About from '../components/About.jsx'
import Notices from '../components/Notices.jsx'

function FeeLine({ id }) {
  const { data } = useApi(`/students/${id}/fees/`)
  if (!data) return null
  return data.balance > 0
    ? <p className="small"><b>Fees:</b> {naira(data.balance)} outstanding</p>
    : <p className="small"><b>Fees:</b> &#10003; all clear</p>
}

export default function ParentHome({ user }) {
  const { data, error, loading } = useApi('/parent/children/')
  if (error) return <div className="error-box">{error.message}</div>
  if (loading) return <p className="muted">Loading...</p>
  return (
    <>
      <section className="page-head"><div>
        <h1>Hello, {user.name}</h1><p className="muted">{data.term}</p></div></section>
      <section className="child-grid">
        {data.children.map((c) => (
          <article className="card child" key={c.id}>
            <div className="child-top">
              <span className="avatar avatar-lg">{initials(c.name)}</span>
              <div><h2>{c.name}</h2><p className="muted small">{c.class_name} &middot; {c.admission_no}</p></div>
            </div>
            <div className="mini-stats">
              <div><span className="stat-label">Average</span><b>{num(c.average)}</b></div>
              <div><span className="stat-label">Position</span><b>{c.position ? ordinal(c.position) : '-'}</b></div>
              <div><span className="stat-label">Remarks</span><b>{c.remark_count}</b></div>
            </div>
            {!c.complete && <p className="small muted">Results in progress: {c.subjects_done} of {c.subjects_total} subjects marked.</p>}
            <FeeLine id={c.id} />
            <div className="child-actions">
              <a className="btn btn-small" href={`#/student/${c.id}`}>Open {c.name.split(' ')[0]}'s page</a>
            </div>
          </article>
        ))}
        {data.children.length === 0 && <div className="card"><p>No children are linked to your account yet. Please contact the school office.</p></div>}
      </section>
      <Notices />
      <About />
    </>
  )
}