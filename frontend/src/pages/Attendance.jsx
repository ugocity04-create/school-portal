import { useEffect, useState } from 'react'
import { api } from '../api.js'
import { useApi } from '../hooks.js'

const OPTIONS = [['present', 'P', 'Present'], ['late', 'L', 'Late'], ['absent', 'A', 'Absent']]

export default function Attendance({ classId }) {
  const [date, setDate] = useState('')
  const { data, error, loading, setData } = useApi(`/teacher/classes/${classId}/attendance/${date ? '?date=' + date : ''}`)
  const [marks, setMarks] = useState({})
  const [msg, setMsg] = useState(null)
  const [problem, setProblem] = useState(null)
  const [saving, setSaving] = useState(false)

  useEffect(() => {
    if (data) {
      const m = {}
      data.rows.forEach((r) => { if (r.status) m[r.student_id] = r.status })
      setMarks(m)
    }
  }, [data])

  if (error) return <div className="error-box">{error.message}</div>
  if (loading && !data) return <p className="muted">Loading...</p>
  if (!data) return null

  const counts = { present: 0, late: 0, absent: 0 }
  Object.values(marks).forEach((s) => { counts[s] += 1 })
  const todayIso = new Date().toLocaleDateString('en-CA')

  async function save() {
    setMsg(null)
    setProblem(null)
    if (Object.keys(marks).length < data.rows.length) { setProblem('Mark every pupil before saving.'); return }
    setSaving(true)
    try {
      const d = await api(`/teacher/classes/${classId}/attendance/`, {
        method: 'POST',
        body: { date: data.date, marks: data.rows.map((r) => ({ student_id: r.student_id, status: marks[r.student_id] })) },
      })
      setData(d)
      setMsg('Register saved.')
    } catch (err) {
      setProblem(err.message)
    }
    setSaving(false)
  }

  return (
    <>
      <section className="page-head">
        <div><p className="crumb"><a href="#/">&larr; Back</a></p>
          <h1>Register: {data.class_name}</h1><p className="muted">{data.label}</p></div>
        <div className="head-actions">
          <div className="term-picker"><label htmlFor="d">Date</label>
            <input id="d" type="date" max={todayIso} value={date || data.date} onChange={(e) => setDate(e.target.value)} /></div>
        </div>
      </section>
      {msg && <div className="flash flash-success">{msg}</div>}
      {problem && <div className="error-box">{problem}</div>}
      {data.weekend ? <div className="flash flash-info">There is no school on weekends. Choose a weekday.</div> : (
        <section className="card">
          <div className="card-head">
            <p className="small muted">Present {counts.present} &middot; Late {counts.late} &middot; Absent {counts.absent}{data.marked ? ' · already saved for this day' : ''}</p>
            <button type="button" className="btn btn-small btn-ghost"
              onClick={() => setMarks(Object.fromEntries(data.rows.map((r) => [r.student_id, 'present'])))}>Mark everyone present</button>
          </div>
          {data.rows.map((r) => (
            <div className="reg-row" key={r.student_id}>
              <span className="grow"><b>{r.name}</b><br /><small className="muted">{r.admission_no}</small></span>
              <span className="seg" role="group" aria-label={'Attendance for ' + r.name}>
                {OPTIONS.map(([key, short, label]) => (
                  <button key={key} type="button" className={key[0]} aria-pressed={marks[r.student_id] === key} title={label}
                          onClick={() => setMarks({ ...marks, [r.student_id]: key })}>{short}</button>
                ))}
              </span>
            </div>
          ))}
          <div className="sticky-save"><button className="btn" type="button" disabled={saving} onClick={save}>{saving ? 'Saving...' : 'Save register'}</button></div>
        </section>
      )}
    </>
  )
}