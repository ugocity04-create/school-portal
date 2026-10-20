import About from './components/About.jsx'
import { useEffect, useState } from 'react'
import { api, setUnauthorizedHandler } from './api.js'
import { go, initials, match, useHashRoute } from './hooks.js'
import Login from './pages/Login.jsx'
import Password from './pages/Password.jsx'
import Report from './pages/Report.jsx'
import ParentHome from './pages/ParentHome.jsx'
import TeacherHome from './pages/TeacherHome.jsx'
import Scores from './pages/Scores.jsx'
import ClassPage from './pages/ClassPage.jsx'
import Remarks from './pages/Remarks.jsx'
import AdminHome from './pages/AdminHome.jsx'
import Attendance from './pages/Attendance.jsx'
import Homework from './pages/Homework.jsx'
import HomeworkDetail from './pages/HomeworkDetail.jsx'
import HomeworkWork from './pages/HomeworkWork.jsx'
import Receipt from './pages/Receipt.jsx'
import { BrandBadge } from './components/Logo.jsx'

const SCHOOL = 'Greenfield Academy'

function StudentHome() {
  const [id, setId] = useState(null)
  const [error, setError] = useState(null)
  useEffect(() => {
    api('/student/me/').then((d) => setId(d.student_id)).catch(setError)
  }, [])
  if (error) return <div className="error-box">{error.message}</div>
  if (!id) return <p className="muted">Loading...</p>
  return <><Report sid={id} user={{ role: 'student' }} /><div className="wrap"><About /></div></>
}

function Home({ user }) {
  if (user.role === 'student') return <StudentHome />
  if (user.role === 'parent') return <ParentHome user={user} />
  if (user.role === 'teacher') return <TeacherHome user={user} />
  return <AdminHome user={user} />
}

function Routes({ user, path }) {
  let m
  if (path === '/password') return <Password user={user} />
  if ((m = match(path, '/student/:sid/homework/:hid'))) return <HomeworkDetail sid={m.sid} hid={m.hid} user={user} />
  if ((m = match(path, '/teacher/homework-work/:id')) && user.role === 'teacher') return <HomeworkWork hid={m.id} />
  if ((m = match(path, '/student/:id'))) return <Report sid={m.id} user={user} />
  if ((m = match(path, '/teacher/scores/:id')) && user.role === 'teacher') return <Scores csId={m.id} />
  if ((m = match(path, '/teacher/class/:id')) && user.role === 'teacher') return <ClassPage classId={m.id} />
  if ((m = match(path, '/teacher/remarks/:id')) && user.role === 'teacher') return <Remarks sid={m.id} />
  if ((m = match(path, '/teacher/attendance/:id')) && user.role === 'teacher') return <Attendance classId={m.id} />
  if ((m = match(path, '/teacher/homework/:id')) && user.role === 'teacher') return <Homework csId={m.id} />
  if ((m = match(path, '/receipt/:id')) && (user.role === 'parent' || user.role === 'admin')) return <Receipt pid={m.id} school={SCHOOL} />
  return <Home user={user} />
}

export default function App() {
  const path = useHashRoute()
  const [user, setUser] = useState(undefined) // undefined = still checking

  useEffect(() => {
    setUnauthorizedHandler(() => setUser(null))
    api('/me/').then((d) => setUser(d.user)).catch(() => setUser(null))
  }, [])

  async function signOut() {
    try {
      await api('/logout/', { method: 'POST' })
    } catch {
      /* already signed out */
    }
    setUser(null)
    go('/')
  }

  if (user === undefined) return <div className="splash">Loading...</div>
  if (!user) return <Login school={SCHOOL} onLogin={(u) => { setUser(u); go('/') }} />

  return (
    <>
      <header className="topbar no-print">
        <div className="wrap topbar-inner">
          <a className="brand" href="#/">
            <BrandBadge size={40} />
            <span className="brand-text"><b>{SCHOOL}</b><small>School portal</small></span>
          </a>
          <nav className="nav" aria-label="Main">
            <a href="#/" className={path === '/' ? 'active' : ''}>
              {{ student: 'My results', parent: 'My children', teacher: 'My classes', admin: 'Overview' }[user.role]}
            </a>
            {user.role === 'admin' && <a href="/admin/" target="_blank" rel="noreferrer">Manage people</a>}
          </nav>
          <div className="who">
            <a className="who-link" href="#/password" title="My profile">
              <span className="avatar">{user.photo ? <img src={user.photo} alt="" /> : initials(user.name)}</span>
              <span className="who-name">{user.name}</span>
            </a>
            <button className="btn btn-small btn-ghost" type="button" onClick={signOut}>Sign out</button>
          </div>
        </div>
      </header>
      <main className="wrap main">
        <Routes user={user} path={path} />
      </main>
      <footer className="footer no-print">
        <div className="wrap"><p>{SCHOOL} school portal. Your records are private to you and your school. Designed by Chibuike</p></div>
      </footer>
    </>
  )
}