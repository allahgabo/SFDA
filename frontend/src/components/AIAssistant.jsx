import { useState, useEffect, useRef } from 'react';
import { chatAssistant } from '../services/api';

const FONT = "'Cairo', sans-serif";

export default function AIAssistant({ reports = [], lang = 'ar' }) {
  const isAr = lang === 'ar';
  const dir  = isAr ? 'rtl' : 'ltr';

  const [messages,  setMessages]  = useState([]);
  const [input,     setInput]     = useState('');
  const [loading,   setLoading]   = useState(false);
  const [darkMode,  setDarkMode]  = useState(false);
  const bottomRef = useRef(null);
  const inputRef  = useRef(null);

  /* ── Welcome message ─────────────────────────────────── */
  useEffect(() => {
    const noReports = isAr
      ? `مرحباً! أنا مساعد السفر الذكي الخاص بك.\n\nلم تقم بإنشاء أي تقارير بعد. أنشئ تقريراً أولاً للحصول على مساعدة مخصصة. بمجرد إنشاء التقارير، سأتمكن من مساعدتك في الملخصات التنفيذية، والمتحدثين الرئيسيين، والاجتماعات الثنائية، ومعلومات الطقس، ووجهات اتصال السفارة، ونقاط النقاش، والمزيد!`
      : `Hello! I'm your Travel AI Assistant.\n\nNo reports yet. Create a report first for personalized assistance. Once reports are available, I can help with executive summaries, key speakers, bilateral meetings, weather, embassy contacts, talking points, and more!`;

    if (reports.length > 0) {
      const list = reports.map(r => `• ${r.title || r.event_name} (${r.city}, ${r.country})`).join('\n');
      const withReports = isAr
        ? `مرحباً! أنا مساعد السفر الذكي الخاص بك.\n\nلديّ وصول إلى **${reports.length} تقرير**:\n${list}\n\nيمكنني مساعدتك في:\n• **الملخصات التنفيذية وإحاطات المؤتمرات**\n• **المتحدثون الرئيسيون والمشاركون المتوقعون**\n• **الاجتماعات الثنائية المقترحة ونقاط النقاش**\n• **معلومات الطقس والتوصيات المحلية**\n• **معلومات السفارة والقنصلية**\n• **متطلبات الدخول ومعلومات التأشيرة**\n• **أوقات الصلاة في الوجهة**\n\nكيف يمكنني مساعدتك اليوم؟`
        : `Hello! I'm your Travel AI Assistant.\n\nI have access to **${reports.length} report${reports.length !== 1 ? 's' : ''}**:\n${list}\n\nI can help with executive summaries, key speakers, bilateral meetings, weather, embassy contacts, entry requirements, and prayer times.\n\nHow can I assist you today?`;
      setMessages([{ id: 1, role: 'assistant', content: withReports, ts: new Date() }]);
    } else {
      setMessages([{ id: 1, role: 'assistant', content: noReports, ts: new Date() }]);
    }
  }, [reports, lang]);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  /* ── System prompt ───────────────────────────────────── */
  const buildSystem = () => {
    const details = reports.map(r => [
      `Report: "${r.title || r.event_name}"`,
      `Location: ${r.city}, ${r.country}`,
      `Dates: ${r.start_date}${r.end_date ? ' – ' + r.end_date : ''}`,
      `Status: ${r.status}`,
      `Speakers: ${r.speakers?.length || 0}`,
      `Bilateral: ${r.bilateral_meetings?.length || 0}`,
    ].join(' | ')).join('\n');
    return `You are the Travel AI Assistant for SFDA. Available reports:\n\n${details}\n\nBe concise, professional, use bullet points. Respond in ${isAr ? 'Arabic' : 'English'}.`;
  };

  /* ── Send message ────────────────────────────────────── */
  const sendMsg = async (text) => {
    const txt = (text || input).trim();
    if (!txt || loading) return;
    const userMsg = { id: Date.now(), role: 'user', content: txt, ts: new Date() };
    setMessages(p => [...p, userMsg]);
    setInput('');
    setLoading(true);
    const history = messages.map(m => ({ role: m.role, content: m.content.replace(/<[^>]+>/g, '') }));
    try {
      const res = await chatAssistant([...history, { role: 'user', content: txt }], buildSystem());
      setMessages(p => [...p, { id: Date.now() + 1, role: 'assistant', content: res.data.content, ts: new Date() }]);
    } catch {
      setMessages(p => [...p, { id: Date.now() + 1, role: 'assistant', content: isAr ? 'خطأ في الاتصال. يرجى المحاولة مجدداً.' : 'Connection error. Please try again.', ts: new Date() }]);
    }
    setLoading(false);
  };

  /* ── Format markdown ─────────────────────────────────── */
  const fmt = (content) =>
    content
      .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
      .replace(/\*(.*?)\*/g, '<em>$1</em>')
      .split('\n')
      .map(line => {
        if (line.startsWith('• ') || line.startsWith('- '))
          return `<div style="display:flex;gap:8px;margin:4px 0;align-items:flex-start"><span style="color:#6366f1;font-size:8px;margin-top:6px;flex-shrink:0">●</span><span>${line.slice(2)}</span></div>`;
        if (line.trim() === '') return '<div style="margin:5px 0"></div>';
        return `<span>${line}</span><br/>`;
      })
      .join('');

  const fmtTime = d => new Date(d).toLocaleTimeString('ar-SA', { hour: '2-digit', minute: '2-digit' });

  /* ── Suggested questions ─────────────────────────────── */
  const suggested = reports.length > 0
    ? [
        isAr ? `لخّص تقرير ${reports[0]?.event_name || 'الأخير'}` : `Summarize the ${reports[0]?.event_name || 'latest'} report`,
        isAr ? 'من هم المتحدثون الرئيسيون؟'                       : 'Who are the key speakers?',
        isAr ? 'ما الاجتماعات الثنائية المقترحة؟'                  : 'What bilateral meetings are suggested?',
        isAr ? `الطقس ومعلومات السفارة في ${reports[0]?.city || 'الوجهة'}` : `Weather & embassy info for ${reports[0]?.city || 'destination'}`,
      ]
    : [
        isAr ? 'ما أنواع التقارير التي يمكنني إنشاؤها؟' : 'What kind of reports can I create?',
        isAr ? 'كيف أبدأ في تخطيط السفر؟'               : 'How do I get started with travel planning?',
        isAr ? 'ما المعلومات التي ستتضمنها تقاريري؟'     : 'What information will be included in my reports?',
        isAr ? 'أخبرني عن ميزات مساعد الذكاء الاصطناعي' : 'Tell me about the AI assistance features',
      ];

  const showSuggestions = messages.length <= 1 && !loading;

  /* ── Colors (light/dark) ─────────────────────────────── */
  const bg        = darkMode ? '#0d1829' : '#f4f5fb';
  const surface   = darkMode ? '#111827' : '#ffffff';
  const border    = darkMode ? 'rgba(255,255,255,0.07)' : '#eaecf4';
  const textMain  = darkMode ? '#f1f5f9' : '#1e293b';
  const textMuted = darkMode ? '#64748b' : '#94a3b8';
  const inputBg   = darkMode ? '#1e293b' : '#f8fafc';
  const inputBord = darkMode ? 'rgba(255,255,255,0.1)' : '#e2e8f0';

  /* ════════════════════════════════════════════════════════
     RENDER
  ════════════════════════════════════════════════════════ */
  return (
    <div style={{
      display: 'flex', flexDirection: 'column',
      height: '100%', background: bg,
      direction: dir, fontFamily: FONT,
      position: 'relative', overflow: 'hidden',
    }}>
      <style>{`
        @keyframes ai-fadeUp  { from{opacity:0;transform:translateY(8px)} to{opacity:1;transform:none} }
        @keyframes ai-bounce  { 0%,60%,100%{transform:translateY(0)} 30%{transform:translateY(-5px)} }
        @keyframes ai-pulse   { 0%,100%{opacity:1} 50%{opacity:0.45} }
        .ai-suggest:hover { border-color:#6366f1 !important; background:#f5f3ff !important; color:#4f46e5 !important; }
        .ai-icon-btn:hover { color:#6366f1 !important; }
      `}</style>

      {/* ══ HEADER ══════════════════════════════════════════ */}
      <div style={{
        background: surface, flexShrink: 0,
        borderBottom: `1px solid ${border}`,
        padding: '11px 20px',
        display: 'flex', alignItems: 'center',
        justifyContent: 'space-between',
        direction: dir, zIndex: 10,
      }}>

        {/* LEFT side — dark mode toggle + online badge */}
        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          <button
            onClick={() => setDarkMode(d => !d)}
            style={{
              width: 32, height: 32, borderRadius: 9,
              background: darkMode ? 'rgba(255,255,255,0.07)' : '#f1f5f9',
              border: 'none', display: 'flex', alignItems: 'center',
              justifyContent: 'center', cursor: 'pointer',
              fontSize: 15, color: textMuted, transition: 'background 0.2s',
            }}>
            {darkMode ? '☀️' : '🌙'}
          </button>

          <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
            <div style={{ width: 8, height: 8, borderRadius: '50%', background: '#22c55e', boxShadow: '0 0 0 2px rgba(34,197,94,0.2)', flexShrink: 0 }}/>
            <span style={{ fontSize: 12.5, color: textMuted, fontWeight: 600, fontFamily: FONT }}>
              {isAr ? 'متصل الآن' : 'Online'}
            </span>
          </div>
        </div>

        {/* RIGHT side — subtitle | divider | title + sparkle */}
        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
          <span style={{ fontSize: 12.5, color: textMuted, fontFamily: FONT }}>
            {isAr ? 'رفيقك الذكي لتخطيط السفر' : 'Your intelligent travel companion'}
          </span>

          <div style={{ width: 1, height: 18, background: border }}/>

          <div style={{ display: 'flex', alignItems: 'center', gap: 7 }}>
            <span style={{ fontSize: 15.5, fontWeight: 900, color: textMain, fontFamily: FONT }}>
              {isAr ? 'مساعد السفر الذكي' : 'Travel AI Assistant'}
            </span>
            {/* Sparkle / AI icon */}
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none">
              <path d="M12 2l1.8 5.5 5.6 1.8-5.6 1.8L12 16.4l-1.8-5.3L4.6 9.3l5.6-1.8L12 2z" fill="#6366f1"/>
              <path d="M18.5 15.5l1 3 3 1-3 1-1 3-1-3-3-1 3-1 1-3z" fill="#a5b4fc"/>
            </svg>
          </div>
        </div>
      </div>

      {/* ══ CHAT SCROLL AREA ════════════════════════════════ */}
      <div style={{ flex: 1, overflowY: 'auto', position: 'relative', display: 'flex', flexDirection: 'column' }}>

        {/* Purple ambient glow blob — matches screenshot */}
        <div style={{
          position: 'absolute',
          top: '38%', left: '55%',
          transform: 'translate(-50%,-50%)',
          width: 460, height: 460,
          borderRadius: '50%',
          background: 'radial-gradient(circle, rgba(99,102,241,0.22) 0%, rgba(139,92,246,0.12) 38%, rgba(99,102,241,0) 68%)',
          pointerEvents: 'none', zIndex: 0,
          filter: 'blur(4px)',
        }}/>

        {/* Message list */}
        <div style={{
          flex: 1, padding: '22px 20px 12px',
          maxWidth: 740, margin: '0 auto', width: '100%',
          position: 'relative', zIndex: 1,
          display: 'flex', flexDirection: 'column', gap: 16,
          boxSizing: 'border-box',
        }}>
          {messages.map(msg => {
            const isUser = msg.role === 'user';
            return (
              <div key={msg.id} style={{
                display: 'flex', gap: 11, alignItems: 'flex-start',
                /* user bubble → pushed to LTR-end / RTL-start */
                justifyContent: isUser
                  ? (isAr ? 'flex-start' : 'flex-end')
                  : (isAr ? 'flex-end' : 'flex-start'),
                animation: 'ai-fadeUp 0.25s ease',
                direction: dir,
              }}>

                {/* AI avatar */}
                {!isUser && (
                  <div style={{
                    width: 36, height: 36, borderRadius: 11, flexShrink: 0,
                    background: 'linear-gradient(135deg,#6366f1,#8b5cf6)',
                    display: 'flex', alignItems: 'center', justifyContent: 'center',
                    fontSize: 18, marginTop: 2,
                    boxShadow: '0 3px 10px rgba(99,102,241,0.3)',
                    /* always on the outer edge */
                    order: isAr ? 1 : 0,
                  }}>🤖</div>
                )}

                {/* Bubble */}
                <div style={{
                  maxWidth: '76%',
                  background: isUser
                    ? 'linear-gradient(135deg,#6366f1,#4f46e5)'
                    : surface,
                  color: isUser ? 'white' : textMain,
                  borderRadius: isUser
                    ? (isAr ? '18px 5px 18px 18px' : '5px 18px 18px 18px')
                    : (isAr ? '5px 18px 18px 18px' : '18px 5px 18px 18px'),
                  padding: '13px 16px',
                  fontSize: 13.5, lineHeight: 1.72,
                  boxShadow: isUser
                    ? '0 4px 14px rgba(99,102,241,0.3)'
                    : darkMode
                      ? '0 2px 10px rgba(0,0,0,0.3)'
                      : '0 2px 10px rgba(0,0,0,0.06)',
                  border: !isUser ? `1px solid ${border}` : 'none',
                  direction: dir, fontFamily: FONT,
                  order: isAr ? 0 : (isUser ? 0 : 1),
                }}>
                  {!isUser
                    ? <div dangerouslySetInnerHTML={{ __html: fmt(msg.content) }}/>
                    : <span>{msg.content}</span>}
                  <div style={{
                    fontSize: 10.5, marginTop: 7,
                    color: isUser ? 'rgba(255,255,255,0.5)' : textMuted,
                    textAlign: isAr ? 'left' : 'right',
                  }}>
                    {fmtTime(msg.ts)}
                  </div>
                </div>

                {/* User avatar */}
                {isUser && (
                  <div style={{
                    width: 34, height: 34, borderRadius: '50%', flexShrink: 0,
                    background: 'linear-gradient(135deg,#6366f1,#4f46e5)',
                    display: 'flex', alignItems: 'center', justifyContent: 'center',
                    marginTop: 2,
                    order: isAr ? 0 : 1,
                  }}>
                    <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2.2" strokeLinecap="round">
                      <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/>
                      <circle cx="12" cy="7" r="4"/>
                    </svg>
                  </div>
                )}
              </div>
            );
          })}

          {/* Typing dots */}
          {loading && (
            <div style={{
              display: 'flex', gap: 11, alignItems: 'flex-start',
              justifyContent: isAr ? 'flex-end' : 'flex-start',
              direction: dir, animation: 'ai-fadeUp 0.2s ease',
            }}>
              <div style={{ width: 36, height: 36, borderRadius: 11, background: 'linear-gradient(135deg,#6366f1,#8b5cf6)', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 18, flexShrink: 0, order: isAr ? 1 : 0 }}>🤖</div>
              <div style={{ background: surface, borderRadius: isAr ? '5px 18px 18px 18px' : '18px 5px 18px 18px', padding: '16px 20px', boxShadow: darkMode ? '0 2px 10px rgba(0,0,0,0.3)' : '0 2px 10px rgba(0,0,0,0.06)', border: `1px solid ${border}`, order: isAr ? 0 : 1 }}>
                <div style={{ display: 'flex', gap: 5, alignItems: 'center' }}>
                  {[0, 1, 2].map(i => (
                    <span key={i} style={{ width: 7, height: 7, borderRadius: '50%', background: '#a5b4fc', display: 'inline-block', animation: 'ai-bounce 1.2s ease infinite', animationDelay: `${i * 0.15}s` }}/>
                  ))}
                </div>
              </div>
            </div>
          )}
          <div ref={bottomRef}/>
        </div>

        {/* ── Suggested questions — pushed to bottom of scroll area ── */}
        {showSuggestions && (
          <div style={{
            padding: '0 20px 18px',
            maxWidth: 740, margin: '0 auto', width: '100%',
            position: 'relative', zIndex: 1, boxSizing: 'border-box',
          }}>
            {/* Label */}
            <div style={{
              display: 'flex', alignItems: 'center', gap: 6,
              marginBottom: 10,
              justifyContent: isAr ? 'flex-end' : 'flex-start',
              direction: dir,
            }}>
              <span style={{ fontSize: 12.5, color: textMuted, fontWeight: 700, fontFamily: FONT }}>
                {isAr ? 'أسئلة مقترحة' : 'Suggested questions'}
              </span>
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none">
                <path d="M12 2l1.6 5L19 9l-5.4 1.7L12 16l-1.6-5.3L5 9l5.4-1.7L12 2z" fill="#6366f1" opacity="0.8"/>
              </svg>
            </div>

            {/* 2×2 grid */}
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 9 }}>
              {suggested.map((q, i) => (
                <button
                  key={i}
                  className="ai-suggest"
                  onClick={() => sendMsg(q)}
                  style={{
                    background: surface,
                    border: `1.5px solid ${border}`,
                    borderRadius: 12, padding: '11px 15px',
                    fontSize: 13, color: textMain,
                    cursor: 'pointer',
                    textAlign: isAr ? 'right' : 'left',
                    fontFamily: FONT, lineHeight: 1.45,
                    boxShadow: '0 1px 4px rgba(0,0,0,0.04)',
                    transition: 'all 0.15s',
                  }}>
                  {q}
                </button>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* ══ INPUT BAR ════════════════════════════════════════ */}
      <div style={{
        background: surface, flexShrink: 0,
        borderTop: `1px solid ${border}`,
        padding: '11px 20px',
      }}>
        <div style={{
          maxWidth: 740, margin: '0 auto',
          display: 'flex', alignItems: 'center',
          gap: 8, direction: dir,
        }}>

          {/* Attachment icon */}
          <button
            className="ai-icon-btn"
            style={{ width: 34, height: 34, borderRadius: 9, background: 'none', border: 'none', cursor: 'pointer', display: 'flex', alignItems: 'center', justifyContent: 'center', color: textMuted, flexShrink: 0, transition: 'color 0.15s' }}>
            <svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M21.44 11.05l-9.19 9.19a6 6 0 0 1-8.49-8.49l9.19-9.19a4 4 0 0 1 5.66 5.66l-9.2 9.19a2 2 0 0 1-2.83-2.83l8.49-8.48"/>
            </svg>
          </button>

          {/* Mic icon */}
          <button
            className="ai-icon-btn"
            style={{ width: 34, height: 34, borderRadius: 9, background: 'none', border: 'none', cursor: 'pointer', display: 'flex', alignItems: 'center', justifyContent: 'center', color: textMuted, flexShrink: 0, transition: 'color 0.15s' }}>
            <svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z"/>
              <path d="M19 10v2a7 7 0 0 1-14 0v-2"/>
              <line x1="12" y1="19" x2="12" y2="23"/>
              <line x1="8"  y1="23" x2="16" y2="23"/>
            </svg>
          </button>

          {/* Text input */}
          <div
            style={{
              flex: 1, background: inputBg,
              border: `1.5px solid ${inputBord}`,
              borderRadius: 12, padding: '10px 15px',
              cursor: 'text', transition: 'border-color 0.15s',
            }}
            onClick={() => inputRef.current?.focus()}>
            <input
              ref={inputRef}
              value={input}
              onChange={e => setInput(e.target.value)}
              onKeyDown={e => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); sendMsg(); } }}
              placeholder={isAr ? 'اسألني أي شيء عن تقارير سفرك...' : 'Ask me anything about your travel reports...'}
              disabled={loading}
              style={{
                width: '100%', background: 'none', border: 'none', outline: 'none',
                fontSize: 13.5, color: textMain, fontFamily: FONT, direction: dir,
              }}
              onFocus={e => e.currentTarget.parentElement.style.borderColor = '#6366f1'}
              onBlur={e  => e.currentTarget.parentElement.style.borderColor = inputBord}
            />
          </div>

          {/* Send button */}
          <button
            onClick={() => sendMsg()}
            disabled={loading || !input.trim()}
            style={{
              width: 42, height: 42, borderRadius: 12, flexShrink: 0,
              background: loading || !input.trim()
                ? (darkMode ? 'rgba(255,255,255,0.07)' : '#e8edf4')
                : 'linear-gradient(135deg,#4f46e5,#6366f1)',
              border: 'none',
              cursor: loading || !input.trim() ? 'not-allowed' : 'pointer',
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              boxShadow: !loading && input.trim() ? '0 4px 14px rgba(99,102,241,0.4)' : 'none',
              transition: 'all 0.2s',
            }}
            onMouseEnter={e => { if (!loading && input.trim()) e.currentTarget.style.transform = 'scale(1.07)'; }}
            onMouseLeave={e => { e.currentTarget.style.transform = 'none'; }}>
            <svg width="17" height="17" viewBox="0 0 24 24" fill="none">
              {isAr
                ? <path d="M2 12l20-10L12 22l-2-8-8-2z" stroke={loading || !input.trim() ? '#94a3b8' : 'white'} strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round"/>
                : <path d="M22 2L11 13M22 2L15 22L11 13M22 2L2 9L11 13" stroke={loading || !input.trim() ? '#94a3b8' : 'white'} strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round"/>}
            </svg>
          </button>
        </div>
      </div>
    </div>
  );
}
