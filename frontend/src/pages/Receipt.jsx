import { naira } from '../components/Charts.jsx'
import { LogoMark } from '../components/Logo.jsx'
import { useApi } from '../hooks.js'

export default function Receipt({ pid, school }) {
  const { data: r, error, loading } = useApi(`/payments/${pid}/`)
  if (error) return <div className="error-box">{error.message}</div>
  if (loading) return <p className="muted">Loading...</p>
  return (
    <>
      <p className="no-print">
        <a className="btn btn-small btn-ghost" href={`#/student/${r.student.id}`}>&larr; Back</a>{' '}
        <button className="btn btn-small" type="button" onClick={() => window.print()}>Print receipt</button>
      </p>
      <article className="receipt">
        <header className="report-head">
          <LogoMark size={54} />
          <div><h1>{school}</h1><p>Payment receipt &middot; {r.receipt_no}</p></div>
        </header>
        <dl className="report-info">
          <div><dt>Received from</dt><dd>Parent of {r.student.name}</dd></div>
          <div><dt>Class</dt><dd>{r.student.class_name} ({r.student.admission_no})</dd></div>
          <div><dt>For</dt><dd>{r.invoice.title}, {r.invoice.term}</dd></div>
          <div><dt>Date</dt><dd>{r.date}</dd></div>
          <div><dt>Method</dt><dd>{r.method}{r.reference ? ' (' + r.reference + ')' : ''}</dd></div>
          <div><dt>Recorded by</dt><dd>{r.recorded_by}</dd></div>
        </dl>
        <table className="table">
          <tbody>
            <tr><th>Amount paid now</th><td className="num money"><b>{naira(r.amount)}</b></td></tr>
            <tr><th>Total charge</th><td className="num money">{naira(r.invoice.amount)}</td></tr>
            <tr><th>Total paid so far</th><td className="num money">{naira(r.invoice.paid)}</td></tr>
            <tr><th>Balance</th><td className="num money">{naira(r.invoice.balance)}</td></tr>
          </tbody>
        </table>
        <p className="small muted">This receipt was produced by the school portal. Keep it for your records.</p>
      </article>
    </>
  )
}