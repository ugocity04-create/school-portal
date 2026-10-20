import { useState } from 'react'
import { api } from '../api.js'
import { HBars, naira } from './Charts.jsx'
import { num, useApi } from '../hooks.js'

export default function AdminFees() {
  const { data, error, loading, reload } = useApi('/admin/fees/')
  const [pay, setPay] = useState({ invoice_id: '', amount: '', method: 'transfer', reference: '' })
  const [gen, setGen] = useState({ title: 'School fees', amount: '', class_id: '' })
  const [msg, setMsg] = useState(null)
  const [problem, setProblem] = useState(null)

  async function submit(path, body, done) {
    setMsg(null)
    setProblem(null)
    try {
      const d = await api(path, { method: 'POST', body })
      setMsg(done(d))
      reload()
    } catch (err) {
      setProblem(err.message)
    }
  }

  if (error) return <div className="error-box">{error.message}</div>
  if (loading && !data) return <p className="muted">Loading...</p>
  if (!data.term) return <div className="card"><p className="muted">Set a current term first.</p></div>
  const t = data.totals

  return (
    <>
      {msg && <div className="flash flash-success">{msg}</div>}
      {problem && <div className="error-box">{problem}</div>}
      <section className="stats">
        <div className="stat"><span className="stat-label">Billed</span><span className="stat-value money">{naira(t.billed)}</span><span className="stat-note">{data.term}</span></div>
        <div className="stat"><span className="stat-label">Collected</span><span className="stat-value money">{naira(t.collected)}</span><span className="stat-note">{t.rate === null ? '' : num(t.rate) + '% of billed'}</span></div>
        <div className="stat"><span className="stat-label">Outstanding</span><span className="stat-value money">{naira(t.outstanding)}</span></div>
      </section>

      <section className="card">
        <h2>Collected by class</h2>
        <HBars max={100} unit="%" items={data.classes.map((c) => ({
          label: c.name, value: c.billed ? Math.round((1000 * c.collected) / c.billed) / 10 : 0,
          note: `  ${naira(c.collected)} of ${naira(c.billed)}`,
        }))} />
      </section>

      <section className="grid-2">
        <form className="card form" onSubmit={(ev) => { ev.preventDefault(); submit('/admin/fees/payment/', pay, () => { setPay({ invoice_id: '', amount: '', method: 'transfer', reference: '' }); return 'Payment recorded.' }) }}>
          <h2>Record a payment</h2>
          <label htmlFor="inv">Pupil and charge</label>
          <select id="inv" required value={pay.invoice_id} onChange={(x) => setPay({ ...pay, invoice_id: x.target.value })}>
            <option value="">Choose...</option>
            {data.outstanding.map((o) => <option key={o.invoice_id} value={o.invoice_id}>{o.student} ({o.class_name}), {o.title}: owes {naira(o.balance)}</option>)}
          </select>
          <label htmlFor="amt">Amount paid (naira)</label>
          <input id="amt" inputMode="numeric" required value={pay.amount} onChange={(x) => setPay({ ...pay, amount: x.target.value })} />
          <label htmlFor="mth">How was it paid</label>
          <select id="mth" value={pay.method} onChange={(x) => setPay({ ...pay, method: x.target.value })}>
            <option value="transfer">Bank transfer</option><option value="cash">Cash</option><option value="pos">POS</option><option value="online">Online</option>
          </select>
          <label htmlFor="ref">Reference (optional)</label>
          <input id="ref" maxLength="40" value={pay.reference} onChange={(x) => setPay({ ...pay, reference: x.target.value })} />
          <p className="hint">This only records a payment that was already made. No money moves through this page.</p>
          <button className="btn" type="submit">Save payment</button>
        </form>

        <form className="card form" onSubmit={(ev) => { ev.preventDefault(); submit('/admin/fees/generate/', gen, (d) => `${d.created} invoices created.`) }}>
          <h2>Bill this term</h2>
          <label htmlFor="gt">Charge name</label>
          <input id="gt" required value={gen.title} maxLength="80" onChange={(x) => setGen({ ...gen, title: x.target.value })} />
          <label htmlFor="ga">Amount (naira)</label>
          <input id="ga" inputMode="numeric" required value={gen.amount} onChange={(x) => setGen({ ...gen, amount: x.target.value })} />
          <label htmlFor="gc">Who to bill</label>
          <select id="gc" value={gen.class_id} onChange={(x) => setGen({ ...gen, class_id: x.target.value })}>
            <option value="">Every pupil</option>
            {data.school_classes.map((c) => <option key={c.id} value={c.id}>{c.name}</option>)}
          </select>
          <p className="hint">Nobody is billed twice for the same charge.</p>
          <button className="btn" type="submit">Create invoices</button>
        </form>
      </section>

      <section className="card">
        <h2>Biggest balances</h2>
        <div className="table-wrap"><table className="table">
          <thead><tr><th>Pupil</th><th className="hide-sm">Class</th><th>Charge</th><th className="num">Owes</th></tr></thead>
          <tbody>{data.outstanding.slice(0, 12).map((o) => (
            <tr key={o.invoice_id}><th scope="row"><a href={`#/student/${o.student_id}`}>{o.student}</a></th>
              <td className="hide-sm">{o.class_name}</td><td>{o.title}</td><td className="num money">{naira(o.balance)}</td></tr>
          ))}</tbody>
        </table></div>
      </section>
    </>
  )
}