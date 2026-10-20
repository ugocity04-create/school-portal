import { useRef, useState } from 'react'

// Colours follow the entity, not the rank: blue = the pupil / the school, orange = the comparison.
export const COLORS = { blue: '#2a78d6', orange: '#eb6834', aqua: '#1baf7a' }

const round1 = (v) => Math.round(v * 10) / 10
const plain = (v) => (v === null || v === undefined ? '-' : String(round1(v)))

function niceMax(max) {
  if (!max || max <= 0) return 10
  const pow = Math.pow(10, Math.floor(Math.log10(max)))
  for (const m of [1, 2, 2.5, 5, 10]) if (m * pow >= max) return m * pow
  return 10 * pow
}

function Legend({ series }) {
  if (series.length < 2) return null
  return (
    <ul className="legend">
      {series.map((s) => (
        <li key={s.name}><span className="swatch" style={{ background: s.color }} />{s.name}</li>
      ))}
    </ul>
  )
}

function DataTable({ labels, series, format }) {
  return (
    <details className="viz-table">
      <summary>View as table</summary>
      <div className="table-wrap">
        <table className="table">
          <thead><tr><th>Period</th>{series.map((s) => <th className="num" key={s.name}>{s.name}</th>)}</tr></thead>
          <tbody>
            {labels.map((l, i) => (
              <tr key={l + i}><th scope="row">{l}</th>
                {series.map((s) => <td className="num" key={s.name}>{format(s.values[i])}</td>)}</tr>
            ))}
          </tbody>
        </table>
      </div>
    </details>
  )
}

// ---------------------------------------------------------------- line chart

export function LineChart({ labels, series, yMin = 0, yMax = 100, unit = '', height = 240, format = plain, title }) {
  const W = 640, H = height, L = 52, R = 18, T = 14, B = 34
  const n = labels.length
  const ref = useRef(null)
  const [hover, setHover] = useState(null)
  const x = (i) => (n <= 1 ? L + (W - L - R) / 2 : L + ((W - L - R) * i) / (n - 1))
  const y = (v) => T + (H - T - B) * (1 - (v - yMin) / (yMax - yMin || 1))
  const ticks = [0, 1, 2, 3, 4].map((k) => yMin + ((yMax - yMin) * k) / 4)
  const every = Math.ceil(n / 5)

  function onMove(e) {
    const box = ref.current.getBoundingClientRect()
    const px = ((e.clientX - box.left) / box.width) * W
    let best = 0, dist = Infinity
    for (let i = 0; i < n; i++) {
      const d = Math.abs(x(i) - px)
      if (d < dist) { dist = d; best = i }
    }
    setHover(best)
  }

  const paths = series.map((s) => {
    const segs = []
    let cur = []
    s.values.forEach((v, i) => {
      if (v === null || v === undefined) { if (cur.length) segs.push(cur); cur = [] }
      else cur.push([x(i), y(v)])
    })
    if (cur.length) segs.push(cur)
    return segs
  })

  return (
    <figure className="viz">
      {title && <figcaption className="viz-title">{title}</figcaption>}
      <div className="viz-box" ref={ref} onPointerMove={onMove} onPointerLeave={() => setHover(null)}>
        <svg viewBox={`0 0 ${W} ${H}`} role="img" aria-label={title || 'Line chart'} className="viz-svg">
          {ticks.map((t) => (
            <g key={t}>
              <line x1={L} x2={W - R} y1={y(t)} y2={y(t)} className="grid" />
              <text x={L - 8} y={y(t) + 4} textAnchor="end" className="axis">{round1(t)}{unit}</text>
            </g>
          ))}
          {labels.map((l, i) => (i % every === 0 || i === n - 1) && (
            <text key={l + i} x={x(i)} y={H - 9} textAnchor="middle" className="axis">{l}</text>
          ))}
          {hover !== null && <line x1={x(hover)} x2={x(hover)} y1={T} y2={H - B} className="crosshair" />}
          {series.map((s, si) => (
            <g key={s.name}>
              {paths[si].map((seg, k) => (
                <path key={k} d={seg.map((p, j) => (j ? 'L' : 'M') + p[0] + ' ' + p[1]).join(' ')}
                      fill="none" stroke={s.color} strokeWidth="2" strokeLinejoin="round" strokeLinecap="round"
                      strokeDasharray={s.dashed ? '5 4' : undefined} />
              ))}
              {s.values.map((v, i) => v !== null && v !== undefined && (
                <circle key={i} cx={x(i)} cy={y(v)} r={hover === i ? 5 : (n > 14 ? 0 : 3.500)}
                        fill={s.color} stroke="#fff" strokeWidth="2" />
              ))}
            </g>
          ))}
        </svg>
        {hover !== null && (
          <div className="tooltip" style={{ left: Math.min(Math.max((x(hover) / W) * 100, 14), 86) + '%' }}>
            <b>{labels[hover]}</b>
            {series.map((s) => (
              <div key={s.name}><span className="swatch" style={{ background: s.color }} />
                {s.name}: <b>{format(s.values[hover])}{s.values[hover] != null ? unit : ''}</b></div>
            ))}
          </div>
        )}
      </div>
      <Legend series={series} />
      <DataTable labels={labels} series={series} format={(v) => (v == null ? '-' : format(v) + unit)} />
    </figure>
  )
}

// ---------------------------------------------------------------- bars (one or more series per group)

export function BarChart({ labels, series, yMax, unit = '', height = 220, format = plain, title, showValues = true }) {
  const W = 640, H = height, L = 56, R = 12, T = 22, B = 34
  const [hover, setHover] = useState(null)
  const max = yMax || niceMax(Math.max(...series.flatMap((s) => s.values.map((v) => v || 0)), 1))
  const y = (v) => T + (H - T - B) * (1 - v / max)
  const ticks = [0, 1, 2, 3, 4].map((k) => (max * k) / 4)
  const slot = (W - L - R) / labels.length
  const k = series.length
  const barW = Math.min(44, (slot * 0.7 - (k - 1) * 2) / k)
  const groupW = barW * k + (k - 1) * 2

  const bar = (cx, v, color) => {
    const top = y(v), base = y(0), h = Math.max(base - top, 0), r = Math.min(4, h / 2)
    return (
      <path d={`M${cx} ${base} V${top + r} Q${cx} ${top} ${cx + r} ${top} H${cx + barW - r} Q${cx + barW} ${top} ${cx + barW} ${top + r} V${base} Z`}
            fill={color} />
    )
  }

  return (
    <figure className="viz">
      {title && <figcaption className="viz-title">{title}</figcaption>}
      <div className="viz-box" onPointerLeave={() => setHover(null)}>
        <svg viewBox={`0 0 ${W} ${H}`} role="img" aria-label={title || 'Bar chart'} className="viz-svg">
          {ticks.map((t) => (
            <g key={t}>
              <line x1={L} x2={W - R} y1={y(t)} y2={y(t)} className="grid" />
              <text x={L - 8} y={y(t) + 4} textAnchor="end" className="axis">{format(t)}</text>
            </g>
          ))}
          {labels.map((l, i) => {
            const start = L + slot * i + (slot - groupW) / 2
            return (
              <g key={l + i} onPointerEnter={() => setHover(i)}>
                <rect x={L + slot * i} y={T} width={slot} height={H - T - B} fill="transparent" />
                {series.map((s, si) => {
                  const v = s.values[i] || 0
                  const cx = start + si * (barW + 2)
                  return (
                    <g key={s.name}>
                      {bar(cx, v, s.color)}
                      {showValues && labels.length <= 12 && k === 1 && v > 0 && (
                        <text x={cx + barW / 2} y={y(v) - 5} textAnchor="middle" className="value">{format(v)}{unit}</text>
                      )}
                    </g>
                  )
                })}
                <text x={L + slot * i + slot / 2} y={H - 9} textAnchor="middle" className="axis">{l}</text>
              </g>
            )
          })}
        </svg>
        {hover !== null && (
          <div className="tooltip" style={{ left: Math.min(Math.max(((L + slot * hover + slot / 2) / W) * 100, 14), 86) + '%' }}>
            <b>{labels[hover]}</b>
            {series.map((s) => (
              <div key={s.name}><span className="swatch" style={{ background: s.color }} />
                {s.name}: <b>{format(s.values[hover] || 0)}{unit}</b></div>
            ))}
          </div>
        )}
      </div>
      <Legend series={series} />
      <DataTable labels={labels} series={series} format={(v) => (v == null ? '-' : format(v) + unit)} />
    </figure>
  )
}

// ---------------------------------------------------------------- horizontal bars (ranked lists)

export function HBars({ items, max = 100, unit = '', color = COLORS.blue, format = plain }) {
  return (
    <ul className="hbars">
      {items.map((it) => (
        <li key={it.label}>
          <span className="hb-label">{it.label}</span>
          <span className="hb-track"><span className="hb-fill" style={{ width: Math.min(100, (it.value / max) * 100) + '%', background: color }} /></span>
          <span className="hb-value">{format(it.value)}{unit}{it.note}</span>
        </li>
      ))}
    </ul>
  )
}

// ---------------------------------------------------------------- change indicator (icon + sign + words)

export function Delta({ value, unit = '', goodWhenUp = true, label = '' }) {
  if (value === null || value === undefined) return <span className="delta flat">No earlier term to compare</span>
  if (Math.abs(value) < 0.05) return <span className="delta flat">&#9644; No change {label}</span>
  const up = value > 0
  const good = up === goodWhenUp
  return (
    <span className={'delta ' + (good ? 'good' : 'bad')}>
      {up ? '▲' : '▼'} {up ? '+' : ''}{round1(value)}{unit} {label}
    </span>
  )
}

export const naira = (v) => '₦' + Number(v || 0).toLocaleString('en-NG')