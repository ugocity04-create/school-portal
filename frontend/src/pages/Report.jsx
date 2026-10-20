import { useState } from 'react'
import { num, ordinal, useApi } from '../hooks.js'
import Notices from '../components/Notices.jsx'
import { AttendanceTab, FeesTab, HomeworkTab, ProgressTab, TimetableTab } from '../components/StudentTabs.jsx'

const Badge = ({ grade }) =>
  grade ? <span className={'grade g-' + grade[0].toLowerCase()}>{grade}</span> : <span className="muted">-</span>

export default function Report({ sid, user }) {
  const [termId, setTermId] = useState('')
  const [tab, setTab] = useState('results')
  const terms = useApi('/terms/')
  const { data: r, error, loading } = useApi(`/students/${sid}/report/${termId ? '?term=' + termId : ''}`)

  if (error) return <div className="error-box">{error.message}</div>
  if (loading && !r) return <p className="muted">Loading...</p>
  if (!r) return null
  const s = r.student
  const tabs = [['results', 'Results'], ['progress', 'Progress'], ['subjects', 'Subjects'],
    ['attendance', 'Attendance'], ['timetable', 'Timetable'], ['homework', 'Homework']]
  if (user.role === 'parent' || user.role === 'admin') tabs.push(['fees', 'Fees'])

  return (
    <>
      <section className="page-head">
        <div>
          {user.role === 'parent' && <p className="crumb"><a href="#/">&larr; My children</a></p>}
          {user.role === 'admin' && <p className="crumb"><a href="#/">&larr; Overview</a></p>}
          <h1>{s.photo && <img className="head-photo" src={s.photo} alt="" />}{s.name}</h1>
          <p className="muted">{s.class_name} &middot; Admission no. {s.admission_no}</p>
        </div>
        {tab === 'results' && (
          <div className="head-actions no-print">
            <div className="term-picker">
              <label htmlFor="term">Term</label>
              <select id="term" value={termId || r.term.id} onChange={(e) => setTermId(e.target.value)}>
                {(terms.data?.terms || []).map((t) => (
                  <option key={t.id} value={t.id}>{t.label}{t.is_current ? ' (current)' : ''}</option>
                ))}
              </select>
            </div>
          </div>
        )}
      </section>

      <div className="tabs no-print" role="tablist">
        {tabs.map(([key, label]) => (
          <button key={key} className="tab" role="tab" aria-selected={tab === key} onClick={() => setTab(key)}>{label}</button>
        ))}
      </div>

      {tab === 'results' && (
        <>
          <section className="stats">
            <div className="stat"><span className="stat-label">Average</span>
              <span className="stat-value">{num(r.average)}</span>
              {r.overall_grade && <span className="stat-note">{r.overall_grade} &middot; {r.overall_meaning}</span>}</div>
            <div className="stat"><span className="stat-label">Position in class</span>
              <span className="stat-value">{r.position ? ordinal(r.position) : '-'}</span>
              <span className="stat-note">{r.position ? `out of ${r.ranked} pupils` : 'Shown when every subject is marked'}</span></div>
            <div className="stat"><span className="stat-label">Subjects marked</span>
              <span className="stat-value">{r.subjects_done}/{r.subjects_total}</span>
              <span className="stat-note">{r.complete ? 'Results complete' : 'Results in progress'}</span></div>
          </section>

          <section className="card">
            <div className="card-head">
              <h2>Results: {r.term.label}</h2>
              <button className="btn btn-small btn-ghost no-print" type="button" onClick={() => window.print()}>Print report card</button>
            </div>
            <div className="table-wrap">
              <table className="table">
                <thead><tr>
                  <th>Subject</th><th className="num">1st test<br /><small>/20</small></th>
                  <th className="num">2nd test<br /><small>/20</small></th><th className="num">Exam<br /><small>/60</small></th>
                  <th className="num">Total<br /><small>/100</small></th><th>Grade</th><th className="hide-sm">Teacher</th>
                </tr></thead>
                <tbody>
                  {r.rows.map((x) => (
                    <tr key={x.subject_id}>
                      <th scope="row">{x.subject}</th>
                      <td className="num">{num(x.ca1)}</td><td className="num">{num(x.ca2)}</td><td className="num">{num(x.exam)}</td>
                      <td className="num"><b>{num(x.total)}</b></td>
                      <td><Badge grade={x.grade} /> <span className="small muted hide-sm">{x.meaning || ''}</span></td>
                      <td className="hide-sm muted">{x.teacher || 'Not assigned'}</td>
                    </tr>
                  ))}
                  {r.rows.length === 0 && <tr><td colSpan="7" className="muted">No subjects have been set up for this class yet.</td></tr>}
                </tbody>
              </table>
            </div>
            {!r.complete && <p className="small muted">A dash means that mark has not been entered yet. A total and grade appear when both tests and the exam are in.</p>}
          </section>

          <section className="card">
            <h2>Teachers' remarks</h2>
            {r.remarks.length ? (
              <ul className="remarks">
                {r.remarks.map((m) => (
                  <li key={m.id}>
                    <p className="remark-body">&ldquo;{m.body}&rdquo;</p>
                    <p className="remark-meta"><b>{m.teacher || 'A teacher'}</b> &middot; {m.subject || 'General'} &middot; {m.date}</p>
                  </li>
                ))}
              </ul>
            ) : <p className="muted">No remarks for this term yet.</p>}
          </section>
          {user.role === 'student' && <Notices />}
        </>
      )}

      {tab === 'progress' && <ProgressTab sid={sid} />}
      {tab === 'subjects' && (
        <section className="subject-grid">
          {r.rows.map((x) => (
            <article className="card subject" key={x.subject_id}>
              <span className="subject-icon">{x.subject[0]}</span>
              <h3>{x.subject}</h3>
              <p className="muted small">Taught by</p>
              <p>{x.teacher || 'Not assigned yet'}</p>
            </article>
          ))}
        </section>
      )}
      {tab === 'attendance' && <AttendanceTab sid={sid} />}
      {tab === 'timetable' && <TimetableTab sid={sid} />}
      {tab === 'homework' && <HomeworkTab sid={sid} />}
      {tab === 'fees' && <FeesTab sid={sid} />}
    </>
  )
}