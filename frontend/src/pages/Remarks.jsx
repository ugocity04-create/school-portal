import { useState } from 'react'
import { api } from '../api.js'
import { useApi } from '../hooks.js'

export default function Remarks({ sid }) {
  const { data, error, loading, setData } = useApi(`/teacher/students/${sid}/remarks/`)
  const [body, setBody] = useState('')
  const [subjectId, setSubjectId] = useState('')
  const [msg, setMsg] = useState(null)
  const [problem, setProblem] = useState(null)

  if (error) return <div className="error-box">{error.message}</div>
  if (loading && !data) return <p className="muted">Loading...</p>
  if (!data) return null

  async function post(e) {
    e.preventDefault()
    setMsg(null)
    setProblem(null)
    try {
      const d = await api(`/teacher/students/${sid}/remarks/`, {
        method: 'POST', body: { body, subject_id: subjectId || null },
      })
      setData(d)
      setBody('')
      setMsg('Remark added. The pupil and parents can now see it.')
    } catch (err) {
      setProblem(err.message)
    }
  }

  async function remove(id) {
    if (!window.confirm('Delete this remark? Parents will no longer see it.')) return
    try {
      await api(`/teacher/remarks/${id}/delete/`, { method: 'POST' })
      setData({ ...data, remarks: data.remarks.filter((r) => r.id !== id) })
    } catch (err) {
      setProblem(err.message)
    }
  }

  return (
    <>
      <section className="page-head"><div>
        <p className="crumb"><a href={`#/teacher/class/${data.student.class_id}`}>&larr; {data.student.class_name}</a></p>
        <h1>{data.student.name}</h1><p className="muted">{data.student.class_name} &middot; {data.term}</p></div></section>

      <section className="card">
        <h2>Write a remark</h2>
        <p className="small muted">The pupil's parents will see this on the portal. Keep it kind, specific and useful.</p>
        {msg && <div className="flash flash-success">{msg}</div>}
        {problem && <div className="error-box">{problem}</div>}
        <form className="form" onSubmit={post}>
          <label htmlFor="subj">About</label>
          <select id="subj" value={subjectId} onChange={(e) => setSubjectId(e.target.value)}>
            <option value="">General (not one subject)</option>
            {data.subjects.map((s) => <option key={s.id} value={s.id}>{s.name}</option>)}
          </select>
          <label htmlFor="body">Remark</label>
          <textarea id="body" rows="4" maxLength="600" required value={body}
                    onChange={(e) => setBody(e.target.value)}
                    placeholder="For example: Chidi has improved steadily and contributes well in class." />
          <button className="btn" type="submit">Post remark</button>
        </form>
      </section>

      <section className="card">
        <h2>Your earlier remarks</h2>
        {data.remarks.length ? (
          <ul className="remarks">
            {data.remarks.map((r) => (
              <li key={r.id}>
                <p className="remark-body">&ldquo;{r.body}&rdquo;</p>
                <p className="remark-meta">{r.subject || 'General'} &middot; {r.term} &middot; {r.date}</p>
                <button className="btn btn-small btn-danger" type="button" onClick={() => remove(r.id)}>Delete</button>
              </li>
            ))}
          </ul>
        ) : <p className="muted">You have not written any remarks for this pupil yet.</p>}
      </section>
    </>
  )
}