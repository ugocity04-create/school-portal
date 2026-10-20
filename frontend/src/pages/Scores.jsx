import { useEffect, useState } from 'react'
import { api } from '../api.js'
import { num, useApi } from '../hooks.js'
import { BarChart, COLORS, LineChart } from '../components/Charts.jsx'

const FIELDS = ['ca1', 'ca2', 'exam']
const BANDS = [[75, 'A1'], [70, 'B2'], [65, 'B3'], [60, 'C4'], [55, 'C5'], [50, 'C6'], [45, 'D7'], [40, 'E8']]
const gradeFor = (t) => (BANDS.find(([min]) => t >= min) || [0, 'F9'])[1]

// What the teacher has typed -> a number, or null when empty, or undefined when not valid.
function read(text, max) {
  const t = String(text ?? '').trim().replace(',', '.')
  if (t === '') return null
  const v = Number(t)
  return Number.isNaN(v) || v < 0 || v > max ? undefined : v
}

export default function Scores({ csId }) {
  const [termId, setTermId] = useState('')
  const terms = useApi('/terms/')
  const stats = useApi(`/teacher/assignments/${csId}/analytics/${termId ? '?term=' + termId : ''}`)
  const { data, error, loading, setData } = useApi(`/teacher/assignments/${csId}/scores/${termId ? '?term=' + termId : ''}`)
  const [rows, setRows] = useState([])
  const [problems, setProblems] = useState({})
  const [msg, setMsg] = useState(null)
  const [fail, setFail] = useState(null)
  const [saving, setSaving] = useState(false)

  useEffect(() => {
    if (data) {
      setRows(data.rows.map((r) => ({ ...r, ca1: r.ca1 ?? '', ca2: r.ca2 ?? '', exam: r.exam ?? '' })))
      setProblems({})
    }
  }, [data])

  if (error) return <div className="error-box">{error.message}</div>
  if (loading && !data) return <p className="muted">Loading...</p>
  if (!data) return null
  const { assignment, term, editable, maxes } = data

  function change(i, field, value) {
    setRows((rs) => rs.map((r, idx) => (idx === i ? { ...r, [field]: value } : r)))
  }

  async function save(e) {
    e.preventDefault()
    setSaving(true)
    setMsg(null)
    setFail(null)
    try {
      const d = await api(`/teacher/assignments/${csId}/scores/`, {
        method: 'POST',
        body: {
          term_id: term.id,
          scores: rows.map((r) => ({ student_id: r.student_id, ca1: r.ca1, ca2: r.ca2, exam: r.exam })),
        },
      })
      setData(d)
      setMsg('Scores saved.')
    } catch (err) {
      setFail(err.message)
      setProblems(err.data?.problems || {})
    }
    setSaving(false)
  }

  return (
    <>
      <section className="page-head">
        <div>
          <p className="crumb"><a href="#/">&larr; Back</a></p>
          <h1>{assignment.subject} <span className="muted">&middot; {assignment.class_name}</span></h1>
          <p className="muted">{term.label}</p>
        </div>
        <div className="head-actions">
          <div className="term-picker">
            <label htmlFor="term">Term</label>
            <select id="term" value={termId || term.id} onChange={(e) => setTermId(e.target.value)}>
              {(terms.data?.terms || []).map((t) => (
                <option key={t.id} value={t.id}>{t.label}{t.is_current ? ' (current)' : ''}</option>
              ))}
            </select>
          </div>
        </div>
      </section>

      {!editable && <div className="flash flash-info">This is a past term, so scores are view-only. Switch to the current term to enter marks.</div>}
      {msg && <div className="flash flash-success">{msg}</div>}
      {fail && <div className="error-box">{fail}</div>}

      <form className="card" onSubmit={save} noValidate>
        <p className="small muted">1st test is out of {maxes.ca1}, 2nd test out of {maxes.ca2}, exam out of {maxes.exam}. Leave a box empty if the mark is not ready. Decimals like 14.5 are fine.</p>
        <div className="table-wrap">
          <table className="table scores">
            <thead><tr><th>Pupil</th>
              {FIELDS.map((f) => <th className="num" key={f}>{{ ca1: '1st test', ca2: '2nd test', exam: 'Exam' }[f]}<br /><small>/{maxes[f]}</small></th>)}
              <th className="num">Total</th><th>Grade</th></tr></thead>
            <tbody>
              {rows.map((r, i) => {
                const vals = FIELDS.map((f) => read(r[f], maxes[f]))
                const complete = vals.every((v) => v !== null && v !== undefined)
                const total = complete ? Math.round(vals.reduce((a, b) => a + b, 0) * 10) / 10 : null
                const g = total === null ? null : gradeFor(total)
                return (
                  <tr key={r.student_id}>
                    <th scope="row">{r.name}<br /><small className="muted">{r.admission_no}</small></th>
                    {FIELDS.map((f, k) => {
                      const bad = vals[k] === undefined || problems[r.student_id]?.[f]
                      return (
                        <td className="num" key={f}>
                          <input className={'score-input' + (bad ? ' has-error' : '')} type="text" inputMode="decimal"
                                 autoComplete="off" value={r[f]} disabled={!editable}
                                 onChange={(e) => change(i, f, e.target.value)}
                                 aria-label={`${f} for ${r.name}`} />
                          {problems[r.student_id]?.[f] && <span className="field-error">{problems[r.student_id][f]}</span>}
                        </td>
                      )
                    })}
                    <td className="num"><b>{num(total)}</b></td>
                    <td>{g ? <span className={'grade g-' + g[0].toLowerCase()}>{g}</span> : <span className="muted">-</span>}</td>
                  </tr>
                )
              })}
              {rows.length === 0 && <tr><td colSpan="6" className="muted">No pupils in this class yet.</td></tr>}
            </tbody>
          </table>
        </div>
        {editable && rows.length > 0 && (
          <div className="sticky-save"><button className="btn" type="submit" disabled={saving}>{saving ? 'Saving...' : 'Save scores'}</button></div>
        )}
      </form>

      {stats.data && stats.data.trend.length > 0 && (
        <section className="grid-2">
          <div className="card">
            <LineChart title="Class average in this subject, term by term" height={200}
              labels={stats.data.trend.map((t) => t.label)}
              series={[{ name: 'Class average', color: COLORS.blue, values: stats.data.trend.map((t) => t.average) }]} />
          </div>
          <div className="card">
            <BarChart title="Grades this term" height={200} labels={stats.data.spread.map((g) => g.grade)}
              format={(v) => String(Math.round(v))}
              series={[{ name: 'Pupils', color: COLORS.blue, values: stats.data.spread.map((g) => g.count) }]} />
          </div>
        </section>
      )}
    </>
  )
}