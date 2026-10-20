const VALUES = [
  ['Integrity', 'We are honest in our work, our results and our words.'],
  ['Excellence', 'We aim high and help every child reach their best.'],
  ['Respect', 'We treat pupils, parents, staff and neighbours with courtesy.'],
  ['Discipline', 'We build good habits, punctuality and self-control.'],
  ['Community', 'School and home work together for each child.'],
]

export default function About() {
  return (
    <section className="card about" aria-labelledby="about-h">
      <h2 id="about-h">About Greenfield Academy</h2>
      <div className="about-grid">
        <div>
          <h3>Our Mission</h3>
          <p>To give every child a sound education and strong character, in a safe and caring school where each pupil is known, challenged and supported to succeed.</p>
        </div>
        <div>
          <h3>Our Vision</h3>
          <p>To be a leading school that raises confident, honest and capable young people who serve their community and the nation.</p>
        </div>
      </div>
      <h3>Our Core Values</h3>
      <ul className="values">
        {VALUES.map(([t, d]) => (
          <li key={t}><strong>{t}</strong><span>{d}</span></li>
        ))}
      </ul>
    </section>
  )
}