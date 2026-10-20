import { useApi } from '../hooks.js'

export function NoticeList({ items }) {
  if (!items.length) return <p className="muted">No notices right now.</p>
  return items.map((a) => (
    <div className={'notice' + (a.pinned ? ' pinned' : '')} key={a.id}>
      <h3>{a.title}{a.pinned && <span className="pill-soft">Pinned</span>}</h3>
      <p>{a.body}</p>
      <p className="small muted">{a.by} &middot; {a.date}</p>
    </div>
  ))
}

export function EventList({ items }) {
  if (!items.length) return <p className="muted">No upcoming events.</p>
  return items.map((e) => {
    const d = new Date(e.date + 'T00:00:00')
    return (
      <div className="event" key={e.id}>
        <div className="event-date"><b>{d.getDate()}</b>{d.toLocaleString('en-GB', { month: 'short' })}</div>
        <div className="grow">
          <b>{e.title}</b>
          <div className="small muted">{e.label}{e.days_away >= 0 ? ` · ${e.days_away === 0 ? 'today' : 'in ' + e.days_away + ' days'}` : ''}</div>
          {e.description && <div className="small">{e.description}</div>}
        </div>
      </div>
    )
  })
}

export default function Notices() {
  const { data, error } = useApi('/notices/')
  if (error || !data) return null
  return (
    <section className="grid-2">
      <div className="card"><h2>Notice board</h2><NoticeList items={data.announcements} /></div>
      <div className="card"><h2>Coming up</h2><EventList items={data.events} /></div>
    </section>
  )
}