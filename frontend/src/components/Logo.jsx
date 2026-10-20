// Greenfield Academy mark: a shield, an open book, and a young shoot growing out of it.
export function LogoMark({ size = 40, title = 'Greenfield Academy' }) {
  return (
    <svg width={size} height={size} viewBox="0 0 64 64" role="img" aria-label={title}>
      <path d="M32 3 56 11v19c0 14-10 24-24 30C18 54 8 44 8 30V11z" fill="#2b3a8f" />
      <path d="M32 3 56 11v19c0 14-10 24-24 30C18 54 8 44 8 30V11z" fill="none" stroke="#f5b83d" strokeWidth="2" />
      <path d="M32 44c-5-3.5-11.500-4-17-2V28c5.500-2 12-1.500 17 2z" fill="#fff" />
      <path d="M32 44c5-3.5 11.500-4 17-2V28c-5.500-2-12-1.500-17 2z" fill="#e8ebfa" />
      <path d="M32 30V19" stroke="#f5b83d" strokeWidth="2.600" strokeLinecap="round" />
      <path d="M32 24c-5 0-8-3-8-7 4 0 7 2 8 7z" fill="#f5b83d" />
      <path d="M32 19c5 0 8-3 8-7-4 0-7 2-8 7z" fill="#ffd77a" />
    </svg>
  )
}

export function BrandBadge({ size = 38 }) {
  return (
    <span className="brand-badge" style={{ width: size, height: size }}>
      <LogoMark size={size - 8} />
    </span>
  )
}