import { useState } from 'react'
import { BarChart, COLORS, Delta, HBars, LineChart, naira } from './Charts.jsx'
import { num, ordinal, useApi } from '../hooks.js'

const Loading = () => <p className="muted">Loading...</p>
const Oops = ({ error }) => <div className="error-box">{error.message}</div>

// ------------------------------------------------------------------ progress

export function ProgressTab({ sid }) {
  const { data, error, loading } = useApi(`/students/${sid}/progress/`)
  const [pick, setPick] = useState('')
  if (error) return <Oops error={error} />
  if (loading) return <Loading />
  const pts = data.points
  if (pts.length === 0) return <div className="card"><p className="muted">Progress charts appear once results have been entered.</p></div>
  const labels = pts.map((p) => p.label)
  const last = pts[pts.length - 1]
  const subject = data.subjects.find((s) => s.name === pick) || data.subjects[0]
  const latestSubjects = data.subjects
    .map((s) => ({ label: s.name, value: s.values[s.values.length - 1] }))
    .filter((s) => s.value !== null && s.value !== undefined)
    .sort((a, b) => b.value - a.value)

  return (
    <>
      <section className="card">
        <div className="card-head">
          <h2>Average score, term by term</h2>
          <Delta value={data.change} unit=" points" label="since last term" />
        </div>
        <LineChart title="Pupil average compared with the class average" labels={labels} unit="" yMin={0} yMax={100}
          series={[
            { name: 'This pupil', color: COLORS.blue, values: pts.map((p) => p.average) },
            { name: 'Class average', color: COLORS.orange, dashed: true, values: pts.map((p) => p.class_average) },
          ]} />
        <p className="small muted">
          Latest: average {num(last.average)} against a class average of {num(last.class_average)}
          {last.position ? `, ${ordinal(last.position)} of ${last.ranked} in class.` : '.'}
        </p>
      </section>

      <section className="grid-2">
        <div className="card">
          <h2>Subjects now</h2>
          <p className="small muted">Latest total out of 100, best first.</p>
          <HBars items={latestSubjects} max={100} />
        </div>
        <div className="card">
          <div className="card-head">
            <h2>One subject over time</h2>
            <select aria-label="Subject" value={subject ? subject.name : ''} onChange={(e) => setPick(e.target.value)}>
              {data.subjects.map((s) => <option key={s.name}>{s.name}</option>)}
            </select>
          </div>
          {subject && (
            <LineChart labels={labels} height={200}
              series={[{ name: subject.name, color: COLORS.blue, values: subject.values }]} />
          )}
        </div>
      </section>

      <section className="card">
        <h2>Position in class</h2>
        <div className="table-wrap"><table className="table">
          <thead><tr><th>Term</th><th className="num">Average</th><th className="num">Class average</th><th className="num">Position</th></tr></thead>
          <tbody>
            {[...pts].reverse().map((p) => (
              <tr key={p.term_id}><th scope="row">{p.full_label}</th><td className="num">{num(p.average)}</td>
                <td className="num">{num(p.class_average)}</td>
                <td className="num">{p.position ? `${ordinal(p.position)} of ${p.ranked}` : '-'}</td></tr>
            ))}
          </tbody>
        </table></div>
      </section>
    </>
  )
}

// ------------------------------------------------------------------ attendance

const STATUS = { present: 'Present', late: 'Late', absent: 'Absent' }

export function AttendanceTab({ sid }) {
  const { data, error, loading } = useApi(`/students/${sid}/attendance/`)
  if (error) return <Oops error={error} />
  if (loading) return <Loading />
  if (!data.total) return <div className="card"><p className="muted">No attendance has been recorded yet.</p></div>
  return (
    <>
      <section className="stats">
        <div className="stat"><span className="stat-label">Attendance</span><span className="stat-value">{num(data.rate)}%</span>
          <span className="stat-note">of {data.total} school days</span></div>
        <div className="stat"><span className="stat-label">Late</span><span className="stat-value">{data.late}</span>
          <span className="stat-note">days</span></div>
        <div className="stat"><span className="stat-label">Absent</span><span className="stat-value">{data.absent}</span>
          <span className="stat-note">days</span></div>
      </section>
      <section className="card">
        <BarChart title="Attendance rate by month" labels={data.months.map((m) => m.label)} yMax={100} unit="%"
          series={[{ name: 'Attendance', color: COLORS.blue, values: data.months.map((m) => m.rate) }]} />
      </section>
      <section className="card">
        <h2>Last two weeks</h2>
        <ul className="list">
          {data.recent.map((r) => (
            <li className="list-row" key={r.date}>
              <span className="grow">{r.label}</span>
              <span className={'pill ' + (r.status === 'present' ? 'pill-ok' : 'pill-off')}>
                {r.status === 'present' ? '✓ ' : r.status === 'late' ? '○ ' : '✗ '}{STATUS[r.status]}
              </span>
            </li>
          ))}
        </ul>
      </section>
    </>
  )
}

// ------------------------------------------------------------------ timetable

export function TimetableGrid({ data }) {
  const todayIdx = (new Date().getDay() + 6) % 7          // Monday = 0
  return (
    <div className="table-wrap">
      <table className="tt">
        <thead><tr><th></th>{data.days.map((d, i) => <th key={d}>{d}{i === todayIdx ? ' (today)' : ''}</th>)}</tr></thead>
        <tbody>
          {data.rows.map((r) => r.break ? (
            <tr className="break" key="break"><td className="time">{r.label}</td><td colSpan={data.days.length}>Break</td></tr>
          ) : (
            <tr key={r.period}>
              <td className="time">{r.label}</td>
              {r.cells.map((c, i) => c
                ? <td key={i}>{c.subject}{c.teacher && <small>{c.teacher}</small>}</td>
                : <td className="empty" key={i}>-</td>)}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

export function TimetableTab({ sid }) {
  const { data, error, loading } = useApi(`/students/${sid}/timetable/`)
  if (error) return <Oops error={error} />
  if (loading) return <Loading />
  return <section className="card"><h2>Weekly timetable, {data.class_name}</h2><TimetableGrid data={data} /></section>
}

// ------------------------------------------------------------------ homework

const HW_STATUS = {
  notebook: ['In notebook', 'pill-soft'],
  todo: ['To do online', 'pill-warn'],
  submitted: ['Handed in', 'pill-ok'],
  graded: ['Marked', 'pill-ok'],
}

function HwRow({ h, href }) {
  const soon = !h.overdue && h.days_left <= 2
  const st = h.status ? HW_STATUS[h.status] : null
  const mode = h.mode === 'online' ? 'Online' : 'Notebook'
  const body = (
    <>
      <div className="grow"><b>{h.title}</b>
        <div className="small">
          <span className="pill-soft" style={{ marginLeft: 0 }}>{mode}</span>
          {st && h.status !== 'notebook' && <span className={'pill ' + st[1]} style={{ marginLeft: 6 }}>{st[0]}{h.status === 'graded' && h.score != null ? ` ${h.score}/${h.max_score}` : ''}</span>}
          {h.submitted != null && <span className="muted"> {h.submitted} of {h.pupils} handed in</span>}
        </div>
        {h.description && <div className="small muted">{h.description}</div>}
      </div>
      {href && <span className="hw-go" aria-hidden="true">Open &rsaquo;</span>}
    </>
  )
  return (
    <div className="hw">
      <div className={'hw-when' + (h.overdue ? ' late' : soon ? ' soon' : '')}>
        <b>{h.overdue ? 'Past' : h.days_left === 0 ? 'Today' : h.days_left + 'd'}</b>{h.due_label}
      </div>
      {href ? <a className="hw-link" href={href}>{body}</a> : <div className="hw-link">{body}</div>}
    </div>
  )
}

export function HomeworkList({ items, empty, hrefFor }) {
  return items.length ? items.map((h) => <HwRow key={h.id} h={h} href={hrefFor ? hrefFor(h) : null} />) : <p className="muted">{empty}</p>
}

export function HomeworkTab({ sid }) {
  const { data, error, loading } = useApi(`/students/${sid}/homework/`)
  if (error) return <Oops error={error} />
  if (loading) return <Loading />
  return (
    <>
      <section className="card"><h2>Due soon</h2><HomeworkList items={data.upcoming} hrefFor={(h) => `#/student/${sid}/homework/${h.id}`} empty="No homework is due. Enjoy the break." /></section>
      <section className="card"><h2>Recently due</h2><HomeworkList items={data.recent} hrefFor={(h) => `#/student/${sid}/homework/${h.id}`} empty="Nothing in the last two weeks." /></section>
    </>
  )
}

// ------------------------------------------------------------------ fees (parents and the school office)

const FEE_LABEL = { paid: '✓ Paid', part: '◐ Part paid', unpaid: '✗ Unpaid' }

export function FeesTab({ sid }) {
  const { data, error, loading } = useApi(`/students/${sid}/fees/`)
  if (error) return <Oops error={error} />
  if (loading) return <Loading />
  return (
    <>
      <section className="stats">
        <div className="stat"><span className="stat-label">Billed</span><span className="stat-value money">{naira(data.billed)}</span></div>
        <div className="stat"><span className="stat-label">Paid</span><span className="stat-value money">{naira(data.paid)}</span></div>
        <div className="stat"><span className="stat-label">Balance</span><span className="stat-value money">{naira(data.balance)}</span>
          <span className="stat-note">{data.balance > 0 ? 'Please clear before exams' : 'All clear'}</span></div>
      </section>
      {data.invoices.map((inv) => (
        <section className="card" key={inv.id}>
          <div className="card-head">
            <div><h2>{inv.title}</h2><p className="muted small">{inv.term}</p></div>
            <span className={'pill ' + (inv.status === 'paid' ? 'pill-ok' : 'pill-off')}>{FEE_LABEL[inv.status]}</span>
          </div>
          <p className="money">Amount {naira(inv.amount)} &middot; Paid {naira(inv.paid)} &middot; <b>Balance {naira(inv.balance)}</b></p>
          {inv.payments.map((p) => (
            <div className="list-row" key={p.id}>
              <span className="grow small">{p.date} &middot; {p.method}{p.reference ? ' · ' + p.reference : ''}</span>
              <b className="money">{naira(p.amount)}</b>
              <a className="btn btn-small btn-ghost" href={`#/receipt/${p.id}`}>Receipt</a>
            </div>
          ))}
        </section>
      ))}
      {data.invoices.length === 0 && <div className="card"><p className="muted">No fees have been billed yet.</p></div>}
    </>
  )
}