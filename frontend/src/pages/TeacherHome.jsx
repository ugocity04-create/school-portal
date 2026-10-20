import { useApi } from '../hooks.js'
import About from '../components/About.jsx'
import Notices from '../components/Notices.jsx'
import { TimetableGrid } from '../components/StudentTabs.jsx'

function MyTimetable() {
  const { data } = useApi('/teacher/timetable/')
  if (!data) return null
  return <section className="card"><h2>My timetable</h2><TimetableGrid data={data} /></section>
}

export default function TeacherHome({ user }) {
  const { data, error, loading } = useApi('/teacher/assignments/')
  if (error) return <div className="error-box">{error.message}</div>
  if (loading) return <p className="muted">Loading...</p>
  const classes = [...new Map(data.assignments.map((a) => [a.class_id, a.class_name])).entries()]
  return (
    <>
      <section className="page-head"><div><h1>Hello, {user.name}</h1><p className="muted">{data.term}</p></div></section>

      <section className="card">
        <h2>Today's register</h2>
        <div className="child-actions">
          {classes.map(([id, name]) => <a key={id} className="btn btn-small" href={`#/teacher/attendance/${id}`}>Take register: {name}</a>)}
          {classes.length === 0 && <span className="muted">No classes yet.</span>}
        </div>
      </section>

      <section className="child-grid">
        {data.assignments.map((a) => (
          <article className="card child" key={a.id}>
            <h2>{a.subject}</h2>
            <p className="muted">{a.class_name} &middot; {a.pupils} pupils</p>
            <progress className="progress" value={a.complete} max={a.pupils || 1} aria-label="Marking progress" />
            <p className="small muted">{a.complete} of {a.pupils} fully marked this term</p>
            <div className="child-actions">
              <a className="btn btn-small" href={`#/teacher/scores/${a.id}`}>Scores</a>
              <a className="btn btn-small btn-ghost" href={`#/teacher/homework/${a.id}`}>Homework</a>
              <a className="btn btn-small btn-ghost" href={`#/teacher/class/${a.class_id}`}>Pupils</a>
            </div>
          </article>
        ))}
        {data.assignments.length === 0 && <div className="card"><p>You have not been assigned any class yet. Please contact the school office.</p></div>}
      </section>
      <MyTimetable />
      <Notices />
      <About />
    </>
  )
}