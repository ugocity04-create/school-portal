import { BarChart, COLORS, Delta, HBars, LineChart, naira } from './Charts.jsx'
import { num, useApi } from '../hooks.js'

const compact = (v) => (v >= 1e6 ? Math.round(v / 1e5) / 10 + 'M' : v >= 1e3 ? Math.round(v / 100) / 10 + 'k' : String(v))

function verdict(h) {
  if (!h || h.change === null) return 'Results are in for the first term, so there is nothing to compare with yet.'
  if (h.change > 0.5) return `Good news: the school average rose by ${num(h.change)} points since the last term.`
  if (h.change < -0.5) return `Take a look: the school average fell by ${num(Math.abs(h.change))} points since the last term.`
  return 'The school average is steady compared with the last term.'
}

export default function AdminAnalytics() {
  const { data, error, loading } = useApi('/admin/analytics/')
  if (error) return <div className="error-box">{error.message}</div>
  if (loading) return <p className="muted">Loading...</p>
  const { headline: h, trend } = data
  if (!h) return <div className="card"><p className="muted">Charts appear once results have been entered.</p></div>
  const labels = trend.map((t) => t.label)
  const lastMonth = data.attendance[data.attendance.length - 1]

  return (
    <>
      <section className="card">
        <p className="eyebrow">{h.term}</p>
        <h2>{verdict(h)}</h2>
        <div className="kpi-grid">
          <div className="kpi"><span className="stat-label">School average</span><div className="bignum">{num(h.average)}</div>
            <Delta value={h.change} unit=" pts" /></div>
          <div className="kpi"><span className="stat-label">Credit level or better</span><div className="bignum">{num(h.credit_rate)}%</div>
            <Delta value={h.credit_change} unit=" pts" /><div className="small muted">of all subject results (50+)</div></div>
          <div className="kpi"><span className="stat-label">Pupils enrolled</span><div className="bignum">{h.pupils}</div>
            <Delta value={h.pupils_change} /></div>
          <div className="kpi"><span className="stat-label">Attendance</span><div className="bignum">{lastMonth ? num(lastMonth.rate) + '%' : '-'}</div>
            <div className="small muted">{lastMonth ? lastMonth.label : ''}</div></div>
        </div>
      </section>

      <section className="grid-2">
        <div className="card">
          <h2>Is the school improving?</h2>
          <LineChart title="Average score per term, whole school" labels={labels} unit=""
            series={[{ name: 'School average', color: COLORS.blue, values: trend.map((t) => t.average) }]} />
        </div>
        <div className="card">
          <h2>Is the school growing?</h2>
          <BarChart title="Pupils enrolled at the end of each term" labels={labels} unit=""
            format={(v) => String(Math.round(v))}
            series={[{ name: 'Pupils', color: COLORS.aqua, values: trend.map((t) => t.pupils) }]} />
        </div>
      </section>

      <section className="card">
        <h2>Pass rates</h2>
        <LineChart title="Share of subject results at each level" labels={labels} unit="%"
          series={[
            { name: 'Credit or better (50+)', color: COLORS.blue, values: trend.map((t) => t.credit_rate) },
            { name: 'Pass or better (40+)', color: COLORS.orange, dashed: true, values: trend.map((t) => t.pass_rate) },
          ]} />
      </section>

      <section className="grid-2">
        <div className="card">
          <h2>Classes</h2>
          <p className="small muted">Average score this term.</p>
          <HBars items={data.classes.map((c) => ({ label: c.name, value: c.average }))} />
        </div>
        <div className="card">
          <h2>Subjects</h2>
          <p className="small muted">Average score this term, and the change since last term.</p>
          <HBars items={[...data.subjects].sort((a, b) => b.average - a.average).map((s) => ({
            label: s.name, value: s.average,
            note: s.change === null ? '' : `  (${s.change > 0 ? '▲ +' : s.change < 0 ? '▼ ' : ''}${s.change})`,
          }))} />
        </div>
      </section>

      <section className="grid-2">
        <div className="card">
          <BarChart title="How the grades are spread this term" labels={data.spread.map((g) => g.grade)}
            format={(v) => String(Math.round(v))}
            series={[{ name: 'Results', color: COLORS.blue, values: data.spread.map((g) => g.count) }]} />
        </div>
        <div className="card">
          <BarChart title="Attendance rate by month" labels={data.attendance.map((a) => a.label)} yMax={100} unit="%"
            series={[{ name: 'Attendance', color: COLORS.aqua, values: data.attendance.map((a) => a.rate) }]} />
        </div>
      </section>

      <section className="card">
        <BarChart title="Fees billed and collected, by term" labels={data.fees.map((f) => f.label)} format={compact}
          series={[
            { name: 'Billed', color: COLORS.blue, values: data.fees.map((f) => f.billed) },
            { name: 'Collected', color: COLORS.aqua, values: data.fees.map((f) => f.collected) },
          ]} />
        <p className="small muted">Amounts in naira. Last term: {naira(data.fees.length ? data.fees[data.fees.length - 1].collected : 0)} collected.</p>
      </section>

      <section className="grid-2">
        <div className="card">
          <h2>Top pupils this term</h2>
          <ul className="list">{data.top.map((p, i) => (
            <li className="list-row" key={p.id}><b>{i + 1}</b><a className="grow" href={`#/student/${p.id}`}>{p.name}<br /><small className="muted">{p.class_name}</small></a><b>{num(p.average)}</b></li>
          ))}</ul>
        </div>
        <div className="card">
          <h2>Pupils who may need support</h2>
          <p className="small muted">Average below 50 with every subject marked.</p>
          {data.support.length ? (
            <ul className="list">{data.support.map((p) => (
              <li className="list-row" key={p.id}><a className="grow" href={`#/student/${p.id}`}>{p.name}<br /><small className="muted">{p.class_name}</small></a><b>{num(p.average)}</b></li>
            ))}</ul>
          ) : <p className="muted">Nobody is below 50 this term.</p>}
        </div>
      </section>
    </>
  )
}