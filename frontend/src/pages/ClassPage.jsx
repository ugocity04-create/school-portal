import { initials, useApi } from '../hooks.js'

export default function ClassPage({ classId }) {
  const { data, error, loading } = useApi(`/teacher/classes/${classId}/students/`)
  if (error) return <div className="error-box">{error.message}</div>
  if (loading) return <p className="muted">Loading...</p>
  return (
    <>
      <section className="page-head"><div>
        <p className="crumb"><a href="#/">&larr; Back</a></p>
        <h1>{data.class_name}</h1>
        <p className="muted">{data.students.length} pupils. Open a pupil to write a remark.</p></div></section>
      <section className="card">
        <ul className="list">
          {data.students.map((s) => (
            <li className="list-row" key={s.id}>
              <span className="avatar">{initials(s.name)}</span>
              <span className="grow"><b>{s.name}</b><br /><small className="muted">{s.admission_no}</small></span>
              <a className="btn btn-small" href={`#/teacher/remarks/${s.id}`}>Remarks</a>
            </li>
          ))}
        </ul>
      </section>
    </>
  )
}