import { useState } from 'react'
import { api } from '../api.js'
import { useApi } from '../hooks.js'

function Row({ hid, max, row, onSaved }) {
  const sub = row.submission
  const [score, setScore] = useState(sub && sub.score != null ? String(sub.score) : '')
  const [feedback, setFeedback] = useState(sub ? sub.feedback : '')
  const [problem, setProblem] = useState(null)
  const [busy, setBusy] = useState(false)
  const [open, setOpen] = useState(false)

  async function save(e) {
    e.preventDefault()
    setProblem(null); setBusy(true)
    try {
      const r = await api(`/teacher/homework/${hid}/grade/${row.student_id}/`, { method: 'POST', body: { score, feedback } })
      onSaved(row.student_id, r.submission)
    } catch (err) { setProblem(err.message) }
    setBusy(false)
  }

  return (
    <div className="work-row">
      <div className="card-head">
        <div><b>{row.name}</b> <span className="muted small">{row.admission_no}</span></div>
        {!sub ? <span className="pill pill-off">Not handed in</span>
          : sub.graded ? <span className="pill pill-ok">Marked {sub.score}/{max}</span>
          : <span className="pill pill-warn">Needs marking</span>}
      </div>
      {sub && (
        <>
          <p className="small muted">Handed in {sub.submitted_at}{sub.late ? ' · late' : ''}
            {' '}<button type="button" className="btn btn-small btn-ghost" onClick={() => setOpen(!open)}>{open ? 'Hide answer' : 'Read answer'}</button></p>
          {(open || !sub.graded) && <div className="work-answer">{sub.answer}</div>}
          {problem && <div className="error-box">{problem}</div>}
          <form className="grade-row" onSubmit={save}>
            <div><label htmlFor={'s' + row.student_id}>Mark /{max}</label>
              <input id={'s' + row.student_id} type="number" min="0" max={max} step="0.5" required value={score} onChange={(e) => setScore(e.target.value)} /></div>
            <div className="grow"><label htmlFor={'f' + row.student_id}>Comment (optional)</label>
              <input id={'f' + row.student_id} maxLength="1000" value={feedback} onChange={(e) => setFeedback(e.target.value)} /></div>
            <button className="btn btn-small" type="submit" disabled={busy}>{sub.graded ? 'Update mark' : 'Save mark'}</button>
          </form>
        </>
      )}
    </div>
  )
}

export default function HomeworkWork({ hid }) {
  const { data, error, loading, setData } = useApi(`/teacher/homework/${hid}/submissions/`)
  if (error) return <div className="error-box">{error.message}</div>
  if (loading && !data) return <p className="muted">Loading...</p>
  if (!data) return null
  const h = data.homework
  const online = h.mode === 'online'
  const handed = data.rows.filter((r) => r.submission).length
  const marked = data.rows.filter((r) => r.submission && r.submission.graded).length

  function saved(sid, submission) {
    setData({ ...data, rows: data.rows.map((r) => (r.student_id === sid ? { ...r, submission } : r)) })
  }

  return (
    <>
      <section className="page-head"><div>
        <p className="crumb"><a href="#/">&larr; Back</a></p>
        <h1>{h.title}</h1>
        <p className="muted">{h.subject} &middot; {h.class_name} &middot; Due {h.due_label}</p>
      </div></section>
      <section className="card">
        <div className="card-head"><h2>The task</h2>
          <span className={'pill ' + (online ? 'pill-warn' : 'pill-soft')}>{online ? 'Online in the portal' : 'In the notebook'}</span></div>
        <div className="task-box">{h.instructions}</div>
      </section>
      {online ? (
        <section className="card">
          <h2>Pupils' work</h2>
          <p className="muted small">{handed} of {data.rows.length} handed in &middot; {marked} marked &middot; out of {h.max_score}</p>
          {data.rows.map((r) => <Row key={r.student_id} hid={hid} max={h.max_score} row={r} onSaved={saved} />)}
        </section>
      ) : (
        <section className="card"><p className="muted">This homework is done in the notebook, so pupils do not hand anything in here. Mark the notebooks in class.</p></section>
      )}
    </>
  )
}