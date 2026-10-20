import { useState } from 'react'
import { api } from '../api.js'
import { useApi } from '../hooks.js'

export default function HomeworkDetail({ sid, hid, user }) {
  const { data, error, loading, setData } = useApi(`/students/${sid}/homework/${hid}/`)
  const [answer, setAnswer] = useState(null)
  const [problem, setProblem] = useState(null)
  const [busy, setBusy] = useState(false)
  const [msg, setMsg] = useState(null)

  if (error) return <div className="error-box">{error.message}</div>
  if (loading && !data) return <p className="muted">Loading...</p>
  if (!data) return null

  const sub = data.submission
  const text = answer === null ? (sub ? sub.answer : '') : answer
  const back = user.role === 'student' ? '#/' : `#/student/${sid}`

  async function submit(e) {
    e.preventDefault()
    setProblem(null); setMsg(null); setBusy(true)
    try {
      const r = await api(`/students/${sid}/homework/${hid}/submit/`, { method: 'POST', body: { answer: text } })
      setData({ ...data, submission: r.submission, status: 'submitted' })
      setAnswer(null)
      setMsg('Handed in. Your teacher can see it now. You can still change it until it is marked.')
    } catch (err) { setProblem(err.message) }
    setBusy(false)
  }

  return (
    <>
      <section className="page-head"><div>
        <p className="crumb"><a href={back}>&larr; Back to homework</a></p>
        <h1>{data.title}</h1>
        <p className="muted">{data.subject} &middot; {data.class_name}{data.teacher ? ' · ' + data.teacher : ''}</p>
      </div></section>

      <section className="card">
        <div className="card-head">
          <h2>What to do</h2>
          <span className={'pill ' + (data.mode === 'online' ? 'pill-warn' : 'pill-soft')}>
            {data.mode === 'online' ? 'Do it online here' : 'Do it in your notebook'}
          </span>
        </div>
        <p className="small muted">Due {data.due_label}{data.overdue ? ' (past)' : data.days_left === 0 ? ' (today)' : ` (${data.days_left} day${data.days_left === 1 ? '' : 's'} left)`}
          {data.mode === 'online' ? ` · Marked out of ${data.max_score}` : ''}</p>
        <div className="task-box">{data.instructions}</div>
        {data.mode === 'notebook' && (
          <p className="small" style={{ marginTop: 10 }}>Write this in your notebook and hand the notebook to your teacher on the due date. There is nothing to submit here.</p>
        )}
      </section>

      {data.mode === 'online' && (
        <section className="card">
          <h2>Your answer</h2>
          {msg && <div className="flash flash-success">{msg}</div>}
          {problem && <div className="error-box">{problem}</div>}
          {sub && (
            <p className="small muted">Handed in {sub.submitted_at}{sub.late ? ' · late' : ''}</p>
          )}
          {sub && sub.graded && (
            <div className="flash flash-success">
              <b>Mark: {sub.score} / {data.max_score}</b>
              {sub.feedback && <div>Teacher's comment: {sub.feedback}</div>}
            </div>
          )}
          {data.can_submit ? (
            <form className="form" onSubmit={submit}>
              <label htmlFor="ans">Type your answer</label>
              <textarea id="ans" className="answer-box" maxLength="8000" value={text}
                        onChange={(e) => setAnswer(e.target.value)} placeholder="Write your answer here..." />
              <p className="hint">{text.length} / 8000 characters{data.overdue ? ' · The due date has passed, so this will be marked as late.' : ''}</p>
              <button className="btn" type="submit" disabled={busy}>{busy ? 'Handing in...' : sub ? 'Hand in again' : 'Hand in'}</button>
            </form>
          ) : (
            sub ? <div className="work-answer">{sub.answer}</div>
              : <p className="muted">{user.role === 'student' ? 'Nothing handed in.' : 'Your child has not handed this in yet.'}</p>
          )}
        </section>
      )}
    </>
  )
}