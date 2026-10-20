import { useState } from 'react'
import { api } from '../api.js'
import { useApi } from '../hooks.js'
import { HomeworkList } from '../components/StudentTabs.jsx'

export default function Homework({ csId }) {
  const { data, error, loading, setData } = useApi(`/teacher/assignments/${csId}/homework/`)
  const [f, setF] = useState({ title: '', instructions: '', due_date: '', mode: 'notebook', max_score: 10 })
  const [problem, setProblem] = useState(null)
  const [msg, setMsg] = useState(null)

  if (error) return <div className="error-box">{error.message}</div>
  if (loading && !data) return <p className="muted">Loading...</p>
  if (!data) return null
  const todayIso = new Date().toLocaleDateString('en-CA')

  async function create(e) {
    e.preventDefault()
    setProblem(null)
    setMsg(null)
    try {
      setData(await api(`/teacher/assignments/${csId}/homework/`, { method: 'POST', body: f }))
      setF({ title: '', instructions: '', due_date: '', mode: 'notebook', max_score: 10 })
      setMsg('Homework set. Pupils and parents can see it now.')
    } catch (err) {
      setProblem(err.message)
    }
  }
  async function remove(id) {
    if (!window.confirm('Delete this homework?')) return
    try {
      await api(`/teacher/homework/${id}/delete/`, { method: 'POST' })
      setData({ ...data, homework: data.homework.filter((h) => h.id !== id) })
    } catch (err) {
      setProblem(err.message)
    }
  }

  return (
    <>
      <section className="page-head"><div><p className="crumb"><a href="#/">&larr; Back</a></p>
        <h1>Homework: {data.assignment.subject}</h1><p className="muted">{data.assignment.class_name}</p></div></section>
      {msg && <div className="flash flash-success">{msg}</div>}
      {problem && <div className="error-box">{problem}</div>}
      <form className="card form narrow" onSubmit={create}>
        <h2>Set homework</h2>
        <label htmlFor="t">Title</label>
        <input id="t" required maxLength="120" value={f.title} onChange={(e) => setF({ ...f, title: e.target.value })} />
        <label htmlFor="x">What must the pupils do?</label>
        <textarea id="x" rows="6" required maxLength="4000" value={f.instructions}
                  placeholder="Write the full task here. Pupils can open and read it."
                  onChange={(e) => setF({ ...f, instructions: e.target.value })} />
        <label>Where is it done?</label>
        <div className="mode-pick">
          <label className={'mode-opt' + (f.mode === 'notebook' ? ' on' : '')}>
            <input type="radio" name="mode" checked={f.mode === 'notebook'} onChange={() => setF({ ...f, mode: 'notebook' })} />
            <span><b>In the notebook</b><small>Pupils read the task here, write it in their notebook and bring it to you.</small></span>
          </label>
          <label className={'mode-opt' + (f.mode === 'online' ? ' on' : '')}>
            <input type="radio" name="mode" checked={f.mode === 'online'} onChange={() => setF({ ...f, mode: 'online' })} />
            <span><b>Online in the portal</b><small>Pupils type and hand in their answer here, and you mark it.</small></span>
          </label>
        </div>
        {f.mode === 'online' && (
          <>
            <label htmlFor="ms">Marks it is out of</label>
            <input id="ms" type="number" min="1" max="100" required value={f.max_score} onChange={(e) => setF({ ...f, max_score: e.target.value })} />
          </>
        )}
        <label htmlFor="w">Due date</label>
        <input id="w" type="date" required min={todayIso} value={f.due_date} onChange={(e) => setF({ ...f, due_date: e.target.value })} />
        <button className="btn" type="submit">Set homework</button>
      </form>
      <section className="card">
        <h2>Set so far</h2>
        <HomeworkList items={data.homework} hrefFor={(h) => `#/teacher/homework-work/${h.id}`} empty="You have not set any homework yet." />
        {data.homework.map((h) => (
          <button key={h.id} className="btn btn-small btn-ghost" type="button" onClick={() => remove(h.id)}>Delete "{h.title}"</button>
        ))}
      </section>
    </>
  )
}