import { useState } from 'react'
import { useApi } from '../hooks.js'
import AdminAnalytics from '../components/AdminAnalytics.jsx'
import AdminFees from '../components/AdminFees.jsx'
import About from '../components/About.jsx'
import AdminNotices from '../components/AdminNotices.jsx'

export default function AdminHome() {
  const { data, error, loading } = useApi('/admin/overview/')
  const [tab, setTab] = useState('overview')
  const [q, setQ] = useState('')
  if (error) return <div className="error-box">{error.message}</div>
  if (loading) return <p className="muted">Loading...</p>
  const { stats, todo, term, students } = data
  const shown = students.filter((s) => (s.name + s.class_name).toLowerCase().includes(q.toLowerCase()))
  const tabs = [['overview', 'School progress'], ['notices', 'Notices and events'], ['fees', 'Fees'], ['pupils', 'People'], ['about', 'About']]

  return (
    <>
      <section className="page-head">
        <div><h1>Overview</h1><p className="muted">{term ? 'Current: ' + term : 'No current term set. Set one in Manage people > Terms.'}</p></div>
        <div className="head-actions"><a className="btn" href="/admin/" target="_blank" rel="noreferrer">Add or manage people</a></div>
      </section>

      <div className="tabs" role="tablist">
        {tabs.map(([key, label]) => (
          <button key={key} className="tab" role="tab" aria-selected={tab === key} onClick={() => setTab(key)}>{label}</button>
        ))}
      </div>

      {tab === 'overview' && <AdminAnalytics />}
      {tab === 'notices' && <AdminNotices />}
      {tab === 'about' && <About />}
      {tab === 'fees' && <AdminFees />}
      {tab === 'pupils' && (
        <>
          <section className="stats stats-5">
            {Object.entries(stats).map(([k, v]) => (
              <div className="stat" key={k}><span className="stat-label">{k}</span><span className="stat-value">{v}</span></div>
            ))}
          </section>
          <section className="card">
            <h2>Needs attention</h2>
            <ul className="list">
              <li className="list-row"><span className="grow">Subjects with no teacher</span><b>{todo.no_teacher}</b></li>
              <li className="list-row"><span className="grow">Students with no parent linked</span><b>{todo.unlinked_students}</b></li>
            </ul>
            <p className="small muted">Fix these in Manage people.</p>
          </section>
          <section className="card">
            <h2>Pupils</h2>
            <input type="search" placeholder="Search name or class" value={q} onChange={(e) => setQ(e.target.value)} aria-label="Search pupils" />
            <ul className="list">
              {shown.map((s) => (
                <li className="list-row" key={s.id}>
                  <span className="grow"><b>{s.name}</b> <span className="muted">{s.class_name}</span></span>
                  <a className="btn btn-small btn-ghost" href={`#/student/${s.id}`}>View</a>
                </li>
              ))}
            </ul>
          </section>
        </>
      )}
    </>
  )
}