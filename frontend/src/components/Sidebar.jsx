import { useState, useEffect } from 'react';
import { T, getLang, setLang as persistLang } from '../i18n';

const TEA  = '#0d9488';
const TEA2 = '#f0fdfa';
const TEA3 = '#ccfbf1';
const TEAD = '#134e4a';

export default function Sidebar({ page, setPage, lang: parentLang, setLang: notifyParent }) {
  const [lang, setLangState] = useState(() => getLang());
  const [hovered, setHovered] = useState(null);
  const [time, setTime] = useState(new Date());

  useEffect(() => {
    const t = setInterval(() => setTime(new Date()), 1000);
    return () => clearInterval(t);
  }, []);

  useEffect(() => {
    if (parentLang && parentLang !== lang) setLangState(parentLang);
  }, [parentLang]);

  const switchLang = (l) => {
    if (l === lang) return;
    persistLang(l); setLangState(l); notifyParent?.(l);
  };

  const isAr = lang === 'ar';
  const font = "'Cairo',sans-serif";

  const NAV = [
    {
      id: 'dashboard', label: isAr ? 'لوحة التحكم' : 'Dashboard',
      icon: <svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><rect x="3" y="3" width="7" height="7" rx="1.5"/><rect x="14" y="3" width="7" height="7" rx="1.5"/><rect x="3" y="14" width="7" height="7" rx="1.5"/><rect x="14" y="14" width="7" height="7" rx="1.5"/></svg>
    },
    {
      id: 'reports', label: isAr ? 'التقارير' : 'Reports',
      icon: <svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="8" y1="13" x2="16" y2="13"/><line x1="8" y1="17" x2="12" y2="17"/></svg>
    },
    {
      id: 'new', label: isAr ? 'تقرير جديد' : 'New Report',
      icon: <svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round"><path d="M12 5v14M5 12h14"/></svg>,
      accent: true,
    },
    {
      id: 'ai', label: isAr ? 'المساعد الذكي' : 'AI Assistant', badge: 'AI',
      icon: <svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round"><circle cx="12" cy="12" r="3"/><path d="M12 2v3M12 19v3M2 12h3M19 12h3M4.22 4.22l2.12 2.12M17.66 17.66l2.12 2.12M4.22 19.78l2.12-2.12M17.66 6.34l2.12-2.12"/></svg>
    },
  ];

  const hhmm = time.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit', hour12: false });
  const ddmm = time.toLocaleDateString('en-US', { day: '2-digit', month: 'short' }).toUpperCase();

  return (
    <aside style={{
      width: 240, minWidth: 240, height: '100vh',
      background: '#ffffff',
      display: 'flex', flexDirection: 'column',
      boxShadow: '2px 0 16px rgba(0,0,0,0.07)',
      position: 'relative', zIndex: 20, flexShrink: 0,
      fontFamily: font,
    }}>
      <style>{`
        @keyframes sb-pulse { 0%,100%{opacity:1} 50%{opacity:.4} }
        @keyframes sb-badge { 0%,100%{transform:translateY(0)} 50%{transform:translateY(-1px)} }
        .sb-nav-item:hover { background:${TEA2} !important; color:${TEAD} !important; }
        .sb-nav-item:hover .sb-nav-icon { color:${TEA} !important; }
      `}</style>

      {/* Brand */}
      <div style={{ padding: '24px 20px 18px', borderBottom: '1px solid #f3f4f6' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 18, direction: 'ltr' }}>
          <div style={{
            width: 44, height: 44, borderRadius: 13,
            background: `linear-gradient(135deg,${TEA},#0f766e)`,
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            fontSize: 22, color: 'white', flexShrink: 0,
            boxShadow: '0 4px 14px rgba(13,148,136,0.3)',
          }}>✈</div>
          <div>
            <div style={{ fontSize: 17, fontWeight: 800, color: '#0f172a', letterSpacing: '0.02em' }}>SFDA</div>
            <div style={{ fontSize: 10, color: '#94a3b8', letterSpacing: '0.18em', marginTop: 1 }}>TRAVEL INTEL</div>
          </div>
        </div>

        {/* Live Clock */}
        <div style={{
          background: TEA2, border: `1.5px solid ${TEA3}`,
          borderRadius: 13, padding: '11px 15px', direction: 'ltr',
        }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <div>
              <div style={{ fontSize: 28, fontWeight: 300, color: TEA, lineHeight: 1, letterSpacing: '0.02em' }}>{hhmm}</div>
              <div style={{ fontSize: 10, color: '#5eead4', marginTop: 3, letterSpacing: '0.1em' }}>{ddmm} · KSA</div>
            </div>
            <div style={{ textAlign: 'right' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 5, justifyContent: 'flex-end', marginBottom: 4 }}>
                <span style={{ fontSize: 9.5, fontWeight: 700, color: '#10b981', letterSpacing: '0.1em' }}>LIVE</span>
                <span style={{
                  width: 7, height: 7, borderRadius: '50%', background: '#10b981',
                  boxShadow: '0 0 0 2px #d1fae5', animation: 'sb-pulse 2s infinite',
                }}/>
              </div>
              <span style={{ fontSize: 9, color: '#94a3b8' }}>KSA TIME</span>
            </div>
          </div>
        </div>
      </div>

      {/* Navigation */}
      <nav style={{ flex: 1, padding: '16px 12px', overflowY: 'auto' }}>
        <div style={{
          fontSize: 10, fontWeight: 600, color: '#cbd5e1',
          letterSpacing: '0.2em', padding: '0 8px', marginBottom: 10,
          textTransform: 'uppercase',
        }}>
          {isAr ? 'القائمة' : 'Menu'}
        </div>
        {NAV.map(item => {
          const active = page === item.id;
          const hov = hovered === item.id;
          return (
            <button key={item.id}
              className={active ? '' : 'sb-nav-item'}
              onClick={() => setPage(item.id)}
              onMouseEnter={() => setHovered(item.id)}
              onMouseLeave={() => setHovered(null)}
              style={{
                width: '100%', display: 'flex', alignItems: 'center', gap: 12,
                padding: '13px 14px', borderRadius: 12, marginBottom: 4,
                cursor: 'pointer', transition: 'all 0.15s', textAlign: 'start',
                fontFamily: font, fontSize: 14, fontWeight: active ? 700 : 500,
                direction: isAr ? 'rtl' : 'ltr',
                border: 'none',
                background: active ? TEA3 : 'transparent',
                color: active ? TEAD : '#64748b',
                borderInlineStart: `3px solid ${active ? TEA : 'transparent'}`,
              }}>
              <span className="sb-nav-icon" style={{
                color: active ? TEA : '#94a3b8',
                flexShrink: 0, transition: 'color 0.15s',
              }}>
                {item.icon}
              </span>
              <span style={{ flex: 1 }}>{item.label}</span>
              {item.badge && (
                <span style={{
                  fontSize: 9, fontWeight: 700, padding: '2px 6px', borderRadius: 6,
                  background: '#ede9fe', color: '#7c3aed',
                  animation: 'sb-badge 3s ease-in-out infinite',
                }}>AI</span>
              )}
              {active && (
                <span style={{ width: 6, height: 6, borderRadius: '50%', background: TEA, flexShrink: 0 }}/>
              )}
            </button>
          );
        })}
      </nav>

      {/* Language toggle */}
      <div style={{ padding: '12px 14px', borderTop: '1px solid #f3f4f6' }}>
        <div style={{
          fontSize: 10, fontWeight: 600, color: '#cbd5e1',
          letterSpacing: '0.15em', marginBottom: 10,
          paddingInlineStart: 2, textTransform: 'uppercase',
        }}>
          {isAr ? 'اللغة' : 'Language'}
        </div>
        <div style={{ display: 'flex', gap: 6 }}>
          {[['ar', 'عربي'], ['en', 'EN']].map(([l, label]) => (
            <button key={l} onClick={() => switchLang(l)}
              style={{
                flex: 1, padding: '10px 8px', cursor: 'pointer',
                borderRadius: 10, transition: 'all 0.15s', fontFamily: font,
                border: `1.5px solid ${lang === l ? TEA : '#e5e7eb'}`,
                background: lang === l ? TEA3 : '#f9fafb',
                color: lang === l ? TEAD : '#94a3b8',
                fontSize: l === 'ar' ? 14 : 12,
                fontWeight: lang === l ? 700 : 500,
              }}>{label}</button>
          ))}
        </div>
      </div>

      {/* User row */}
      <div style={{
        padding: '14px 16px 22px', borderTop: '1px solid #f3f4f6',
        display: 'flex', alignItems: 'center', gap: 10, direction: 'ltr',
      }}>
        <div style={{
          width: 38, height: 38, borderRadius: 10, flexShrink: 0,
          background: `linear-gradient(135deg,${TEA},#0f766e)`,
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          fontSize: 13, fontWeight: 700, color: 'white',
        }}>{isAr ? 'هـ' : 'SU'}</div>
        <div style={{ flex: 1, minWidth: 0 }}>
          <div style={{ fontSize: 13, fontWeight: 600, color: '#1e293b', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', fontFamily: font }}>
            {isAr ? 'مستخدم النظام' : 'System User'}
          </div>
          <div style={{ fontSize: 10, color: '#94a3b8', marginTop: 1 }}>SFDA · Admin</div>
        </div>
        <div style={{
          width: 8, height: 8, borderRadius: '50%', background: '#10b981',
          boxShadow: '0 0 0 2px #d1fae5', flexShrink: 0,
        }}/>
      </div>
    </aside>
  );
}
