// ------------- Shared UI primitives -------------

function DogeAvatar({ size = 120, expression = 'default' }) {
  // 戴墨镜的柴犬 - CSS/SVG
  return (
    <div style={{ position: 'relative', width: size, height: size }} className="no-select">
      <svg viewBox="0 0 120 120" width={size} height={size}>
        {/* ears */}
        <path d="M22 30 L32 12 L42 32 Z" fill="#D98C3B"/>
        <path d="M78 32 L88 12 L98 30 Z" fill="#D98C3B"/>
        <path d="M26 28 L33 18 L40 30 Z" fill="#F5A65D"/>
        <path d="M80 30 L87 18 L94 28 Z" fill="#F5A65D"/>
        {/* face */}
        <ellipse cx="60" cy="62" rx="42" ry="40" fill="#E8A05C"/>
        {/* cheek white */}
        <ellipse cx="40" cy="72" rx="16" ry="14" fill="#FFF8EC"/>
        <ellipse cx="80" cy="72" rx="16" ry="14" fill="#FFF8EC"/>
        <ellipse cx="60" cy="78" rx="22" ry="12" fill="#FFF8EC"/>
        {/* crown */}
        <path d="M36 22 L44 10 L52 20 L60 6 L68 20 L76 10 L84 22 L84 30 L36 30 Z" fill="#F5C542" stroke="#B8860B" strokeWidth="1.5"/>
        <circle cx="60" cy="15" r="2.5" fill="#E5534B"/>
        <circle cx="44" cy="20" r="1.8" fill="#4A8FE7"/>
        <circle cx="76" cy="20" r="1.8" fill="#52C17A"/>
        {/* sunglasses */}
        <rect x="22" y="48" width="76" height="4" rx="2" fill="#1A1A1A"/>
        <ellipse cx="40" cy="58" rx="15" ry="11" fill="#1A1A1A"/>
        <ellipse cx="80" cy="58" rx="15" ry="11" fill="#1A1A1A"/>
        <ellipse cx="36" cy="55" rx="4" ry="3" fill="#FFFFFF" opacity="0.5"/>
        <ellipse cx="76" cy="55" rx="4" ry="3" fill="#FFFFFF" opacity="0.5"/>
        {/* nose */}
        <ellipse cx="60" cy="78" rx="4" ry="3" fill="#1A1A1A"/>
        {/* mouth */}
        {expression === 'default' && (
          <path d="M60 82 Q54 90 48 86 M60 82 Q66 90 72 86" stroke="#1A1A1A" strokeWidth="2.5" fill="none" strokeLinecap="round"/>
        )}
        {expression === 'smile' && (
          <path d="M48 84 Q60 96 72 84" stroke="#1A1A1A" strokeWidth="2.5" fill="none" strokeLinecap="round"/>
        )}
        {expression === 'smirk' && (
          <path d="M50 86 Q60 88 72 82" stroke="#1A1A1A" strokeWidth="2.5" fill="none" strokeLinecap="round"/>
        )}
        {/* tongue */}
        {expression === 'smile' && <ellipse cx="60" cy="91" rx="5" ry="3" fill="#E5534B"/>}
      </svg>
    </div>
  );
}

function RotatingCTA({ text, centerEmoji = '▶', color = '#1A1A1A', onClick, size = 120 }) {
  const chars = (text + ' ').split('');
  const N = chars.length;
  const R = size / 2 - 8;
  return (
    <button
      onClick={onClick}
      style={{
        position: 'relative', width: size, height: size, borderRadius: '50%',
        border: '1.5px solid #E0E0E0', background: 'transparent',
        transition: 'transform 120ms',
      }}
      onMouseDown={e => e.currentTarget.style.transform = 'scale(0.94)'}
      onMouseUp={e => e.currentTarget.style.transform = 'scale(1)'}
      onMouseLeave={e => e.currentTarget.style.transform = 'scale(1)'}
      className="no-select"
    >
      <div className="spin-text" style={{
        position: 'absolute', inset: 0, width: '100%', height: '100%',
      }}>
        {chars.map((c, i) => {
          const angle = (i / N) * 360;
          return (
            <span key={i} style={{
              position: 'absolute', left: '50%', top: '50%',
              transform: `translate(-50%, -50%) rotate(${angle}deg) translateY(-${R}px)`,
              fontSize: 11, fontWeight: 700, letterSpacing: '0.5px',
              color: '#888',
              textTransform: 'uppercase',
            }}>{c}</span>
          );
        })}
      </div>
      <div style={{
        position: 'absolute', left: '50%', top: '50%',
        transform: 'translate(-50%, -50%)',
        width: size * 0.66, height: size * 0.66, borderRadius: '50%',
        background: '#fff',
        boxShadow: '0 4px 14px rgba(0,0,0,0.08), 0 0 0 1px rgba(0,0,0,0.04)',
        display: 'flex', alignItems: 'center', justifyContent: 'center',
        fontSize: 28,
      }}>{centerEmoji}</div>
    </button>
  );
}

function Badge({ children, accent = 'red', size = 'sm' }) {
  const colors = {
    red: { bg: '#FDE6E4', fg: '#C0392B' },
    blue: { bg: '#E3EEFB', fg: '#2E6FCC' },
    green: { bg: '#DFF4E7', fg: '#2E9E59' },
    purple: { bg: '#EEE6FA', fg: '#5A3E8A' },
    amber: { bg: '#FBECCF', fg: '#B8711C' },
  };
  const c = colors[accent] || colors.red;
  return (
    <span style={{
      display: 'inline-flex', alignItems: 'center',
      background: c.bg, color: c.fg,
      fontSize: size === 'xs' ? 10 : 11, fontWeight: 700,
      padding: '3px 8px', borderRadius: 999,
      letterSpacing: '0.3px',
    }}>{children}</span>
  );
}

function LevelTag({ level }) {
  return (
    <span style={{
      fontSize: 10, fontWeight: 700,
      padding: '2px 8px', borderRadius: 999,
      background: '#F5F0E4', color: '#8B6914',
      letterSpacing: '0.2px',
    }}>{level}</span>
  );
}

function MemePlaceholder({ label, aspect = '1/1', bg }) {
  return (
    <div className="meme-placeholder" style={{
      aspectRatio: aspect,
      background: bg || undefined,
    }}>
      <div className="tag" style={{ whiteSpace: 'pre-line', maxWidth: '80%' }}>
        {label}
      </div>
    </div>
  );
}

// Floating +N animation
function PointFloat({ n, show }) {
  if (!show) return null;
  return (
    <div className="float-up" style={{
      position: 'absolute', left: '50%', top: '50%',
      transform: 'translateX(-50%)',
      fontSize: 18, fontWeight: 800, color: '#F5A623',
      pointerEvents: 'none', zIndex: 100,
    }}>+{n} 梗值</div>
  );
}

Object.assign(window, { DogeAvatar, RotatingCTA, Badge, LevelTag, MemePlaceholder, PointFloat });
