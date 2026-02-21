import { useState } from 'react';
import { T, getLang, setLang as persistLang } from '../../i18n';

/* ── shared geometric background SVG ── */
const BG_PATTERN = `
  <svg xmlns="http://www.w3.org/2000/svg" width="600" height="600">
    <defs>
      <radialGradient id="g1" cx="30%" cy="30%">
        <stop offset="0%" stop-color="#1e4a9a" stop-opacity="0.6"/>
        <stop offset="100%" stop-color="#0c1527" stop-opacity="0"/>
      </radialGradient>
      <radialGradient id="g2" cx="80%" cy="70%">
        <stop offset="0%" stop-color="#3b5bdb" stop-opacity="0.4"/>
        <stop offset="100%" stop-color="#0c1527" stop-opacity="0"/>
      </radialGradient>
    </defs>
    <rect width="600" height="600" fill="#0c1527"/>
    <circle cx="180" cy="180" r="220" fill="url(#g1)"/>
    <circle cx="480" cy="420" r="180" fill="url(#g2)"/>
    <line x1="0" y1="150" x2="600" y2="150" stroke="rgba(59,130,246,0.08)" stroke-width="1"/>
    <line x1="0" y1="300" x2="600" y2="300" stroke="rgba(59,130,246,0.08)" stroke-width="1"/>
    <line x1="0" y1="450" x2="600" y2="450" stroke="rgba(59,130,246,0.08)" stroke-width="1"/>
    <line x1="150" y1="0" x2="150" y2="600" stroke="rgba(59,130,246,0.08)" stroke-width="1"/>
    <line x1="300" y1="0" x2="300" y2="600" stroke="rgba(59,130,246,0.08)" stroke-width="1"/>
    <line x1="450" y1="0" x2="450" y2="600" stroke="rgba(59,130,246,0.08)" stroke-width="1"/>
    <polygon points="300,80 340,150 260,150" fill="none" stroke="rgba(184,147,42,0.25)" stroke-width="1.5"/>
    <polygon points="480,320 530,400 430,400" fill="none" stroke="rgba(59,130,246,0.2)" stroke-width="1"/>
    <circle cx="300" cy="300" r="140" fill="none" stroke="rgba(59,130,246,0.06)" stroke-width="1"/>
    <circle cx="300" cy="300" r="200" fill="none" stroke="rgba(59,130,246,0.04)" stroke-width="1"/>
    <circle cx="90" cy="480" r="60" fill="none" stroke="rgba(184,147,42,0.15)" stroke-width="1"/>
  </svg>
`;

const FEATURES_AR = [
  { icon: '📄', text: 'تقارير إحاطة مدعومة بالذكاء الاصطناعي' },
  { icon: '🤝', text: 'اجتماعات ثنائية وجدول أعمال تفصيلي'    },
  { icon: '🌐', text: 'استخبارات جيوسياسية في الوقت الفعلي'    },
  { icon: '📊', text: 'لوحة بيانات تنفيذية شاملة'               },
];
const FEATURES_EN = [
  { icon: '📄', text: 'AI-powered travel intelligence briefings'  },
  { icon: '🤝', text: 'Bilateral meetings & detailed agendas'     },
  { icon: '🌐', text: 'Real-time geopolitical risk assessment'    },
  { icon: '📊', text: 'Comprehensive executive dashboard'         },
];

export default function AuthLayout({ children, lang: propLang, onLangChange }) {
  const [lang, setLang] = useState(() => propLang || getLang());
  const t    = T[lang];
  const isAr = lang === 'ar';
  const dir  = isAr ? 'rtl' : 'ltr';
  const font = isAr ? "'Cairo','Segoe UI',sans-serif" : "'DM Sans',-apple-system,sans-serif";
  const FEATURES = isAr ? FEATURES_AR : FEATURES_EN;

  const switchLang = (l) => {
    persistLang(l);
    setLang(l);
    onLangChange?.(l);
  };

  return (
    <div style={{
      display: 'flex', height: '100vh', overflow: 'hidden',
      direction: dir, fontFamily: font,
    }}>

      {/* ══ LEFT/RIGHT PANEL — Brand ══════════════════════════════════════════ */}
      <div style={{
        width: '42%', minWidth: 380, position: 'relative', overflow: 'hidden',
        background: '#0c1527',
        display: 'flex', flexDirection: 'column', justifyContent: 'center',
        padding: '48px 52px',
        order: isAr ? 1 : 0,   /* right in Arabic, left in English */
      }}>
        {/* SVG background */}
        <div style={{
          position: 'absolute', inset: 0, zIndex: 0,
          backgroundImage: `url("data:image/svg+xml,${encodeURIComponent(BG_PATTERN)}")`,
          backgroundSize: 'cover',
        }}/>

        {/* Gradient overlay bottom */}
        <div style={{
          position: 'absolute', bottom: 0, left: 0, right: 0, height: '40%', zIndex: 1,
          background: 'linear-gradient(to top, #0c1527 30%, transparent)',
        }}/>

        {/* Content */}
        <div style={{ position: 'relative', zIndex: 2 }}>

          {/* Logo */}
          <div style={{ display: 'flex', alignItems: 'center', gap: 14, marginBottom: 48, direction: 'ltr' }}>
            <div style={{
              width: 52, height: 52, borderRadius: 14,
              background: 'linear-gradient(135deg,rgba(59,130,246,0.3),rgba(99,102,241,0.2))',
              border: '1px solid rgba(99,102,241,0.4)',
              display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 26,
              boxShadow: '0 0 30px rgba(59,130,246,0.25)',
            }}>🌐</div>
            <div>
              <div style={{ color: '#f1f5f9', fontWeight: 800, fontSize: 17, letterSpacing: isAr ? 0 : '-0.03em', fontFamily: font }}>
                {t.sfdaFullName}
              </div>
              <div style={{ color: '#3b82f6', fontSize: 11, fontWeight: 600, marginTop: 3, letterSpacing: '0.06em', fontFamily: "'DM Sans',sans-serif" }}>
                SFDA TRAVEL INTELLIGENCE
              </div>
            </div>
          </div>

          {/* Headline */}
          <div style={{ marginBottom: 40 }}>
            <h1 style={{
              margin: '0 0 14px', color: '#f8fafc', fontWeight: 900,
              fontSize: isAr ? 34 : 32,
              lineHeight: 1.2, letterSpacing: isAr ? 0 : '-0.04em',
              fontFamily: font,
            }}>
              {t.authBrandLine}
            </h1>
            <div style={{
              width: 48, height: 3,
              background: 'linear-gradient(90deg,#b8932a,#f59e0b)',
              borderRadius: 2,
            }}/>
          </div>

          {/* Feature list */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
            {FEATURES.map((f, i) => (
              <div key={i} style={{ display: 'flex', alignItems: 'center', gap: 14, direction: isAr ? 'rtl' : 'ltr' }}>
                <div style={{
                  width: 38, height: 38, borderRadius: 10, flexShrink: 0,
                  background: 'rgba(59,130,246,0.12)',
                  border: '1px solid rgba(59,130,246,0.2)',
                  display: 'flex', alignItems: 'center', justifyContent: 'center',
                  fontSize: 17,
                }}>{f.icon}</div>
                <span style={{ color: 'rgba(255,255,255,0.75)', fontSize: 13.5, fontFamily: font, lineHeight: 1.4 }}>
                  {f.text}
                </span>
              </div>
            ))}
          </div>

          {/* Bottom badge */}
          <div style={{
            marginTop: 52, display: 'inline-flex', alignItems: 'center', gap: 8,
            background: 'rgba(184,147,42,0.1)', border: '1px solid rgba(184,147,42,0.25)',
            borderRadius: 30, padding: '7px 16px',
          }}>
            <span style={{ width: 7, height: 7, borderRadius: '50%', background: '#22c55e', boxShadow: '0 0 8px #22c55e', display: 'inline-block' }}/>
            <span style={{ color: '#b8932a', fontSize: 11.5, fontWeight: 700, fontFamily: "'DM Sans',sans-serif", letterSpacing: '0.04em' }}>
              SYSTEM ONLINE — SECURE
            </span>
          </div>
        </div>
      </div>

      {/* ══ RIGHT/LEFT PANEL — Form ═══════════════════════════════════════════ */}
      <div style={{
        flex: 1, background: '#f8fafc',
        display: 'flex', flexDirection: 'column', justifyContent: 'center', alignItems: 'center',
        padding: '40px 24px', overflowY: 'auto', position: 'relative',
        order: isAr ? 0 : 1,
      }}>

        {/* Lang toggle — top corner */}
        <div style={{
          position: 'absolute', top: 24,
          [isAr ? 'left' : 'right']: 28,
          display: 'flex', background: 'white', borderRadius: 10,
          border: '1px solid #e2e8f0', overflow: 'hidden',
          boxShadow: '0 1px 4px rgba(0,0,0,0.07)',
        }}>
          {['ar','en'].map(l => (
            <button key={l} onClick={() => switchLang(l)}
              style={{
                padding: '6px 14px', border: 'none', cursor: 'pointer',
                fontSize: l === 'ar' ? 13 : 11, fontWeight: 700,
                fontFamily: l === 'ar' ? "'Cairo',sans-serif" : "'DM Sans',sans-serif",
                background: lang === l ? '#0d1829' : 'white',
                color:      lang === l ? 'white'   : '#64748b',
                transition: 'all 0.15s',
              }}>
              {l === 'ar' ? 'ع' : 'EN'}
            </button>
          ))}
        </div>

        {/* The actual form content is injected here */}
        <div style={{ width: '100%', maxWidth: 420 }}>
          {typeof children === 'function' ? children({ lang, t, isAr, dir, font }) : children}
        </div>
      </div>

    </div>
  );
}
