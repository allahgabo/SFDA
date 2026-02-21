import { useState } from 'react';
import AuthLayout from './AuthLayout';
import { authLogin, saveAuth } from '../../services/api';

/* ─── Shared input component ─────────────────────────── */
function Field({ label, type='text', value, onChange, placeholder, error, isAr, font, autoComplete, rightSlot }) {
  const [focused, setFocused] = useState(false);
  return (
    <div style={{ marginBottom: 20 }}>
      <label style={{ display:'block', fontSize:12.5, fontWeight:700, color:'#374151', marginBottom:7, fontFamily:font }}>
        {label}
      </label>
      <div style={{ position:'relative' }}>
        <input
          type={type} value={value} onChange={onChange}
          placeholder={placeholder} autoComplete={autoComplete}
          onFocus={() => setFocused(true)}
          onBlur={() => setFocused(false)}
          style={{
            width:'100%', padding: rightSlot ? `12px ${isAr?'16px':'44px'} 12px ${isAr?'44px':'16px'}` : '12px 16px',
            border: `1.5px solid ${error ? '#ef4444' : focused ? '#3b82f6' : '#e2e8f0'}`,
            borderRadius: 10, fontSize: 13.5, color: '#0f172a',
            background: focused ? '#fff' : '#f8fafc',
            outline: 'none', boxSizing:'border-box', width:'100%',
            transition: 'all 0.15s', fontFamily: font,
            direction: isAr ? 'rtl' : 'ltr',
            boxShadow: focused ? '0 0 0 3px rgba(59,130,246,0.1)' : 'none',
          }}
        />
        {rightSlot && (
          <div style={{ position:'absolute', top:'50%', transform:'translateY(-50%)', [isAr?'left':'right']:14, cursor:'pointer' }}>
            {rightSlot}
          </div>
        )}
      </div>
      {error && <p style={{ margin:'5px 0 0', fontSize:11.5, color:'#ef4444', fontFamily:font }}>{error}</p>}
    </div>
  );
}

/* ─── Eye toggle icon ────────────────────────────────── */
function EyeIcon({ show }) {
  return show
    ? <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#94a3b8" strokeWidth="2" strokeLinecap="round"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/></svg>
    : <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#94a3b8" strokeWidth="2" strokeLinecap="round"><path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24"/><line x1="1" y1="1" x2="23" y2="23"/></svg>;
}

export default function LoginPage({ onLogin, onGoSignup, onGoForgot, initialLang }) {
  const [email,    setEmail]    = useState('');
  const [password, setPassword] = useState('');
  const [showPwd,  setShowPwd]  = useState(false);
  const [remember, setRemember] = useState(false);
  const [loading,  setLoading]  = useState(false);
  const [errors,   setErrors]   = useState({});
  const [apiErr,   setApiErr]   = useState('');
  const [lang,     setLang]     = useState(initialLang);

  const validate = (t) => {
    const e = {};
    if (!email)    e.email    = t.fieldRequired;
    else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) e.email = t.invalidEmail;
    if (!password) e.password = t.fieldRequired;
    return e;
  };

  const handleSubmit = async (t) => {
    const e = validate(t);
    if (Object.keys(e).length) { setErrors(e); return; }
    setLoading(true); setApiErr('');
    try {
      const res = await authLogin(email, password);
      saveAuth(res.data.token || res.data.access, res.data.user || { email });
      onLogin?.();
    } catch (err) {
      setApiErr(t.authError);
    } finally {
      setLoading(false);
    }
  };

  return (
    <AuthLayout lang={initialLang} onLangChange={setLang}>
      {({ t, isAr, dir, font }) => (
        <div style={{ direction: dir, fontFamily: font }}>

          {/* Header */}
          <div style={{ marginBottom: 36 }}>
            <div style={{ display:'inline-flex', alignItems:'center', gap:8, background:'#eff6ff', borderRadius:8, padding:'5px 12px', marginBottom:16 }}>
              <span style={{ width:6, height:6, borderRadius:'50%', background:'#3b82f6', display:'inline-block' }}/>
              <span style={{ fontSize:11.5, fontWeight:700, color:'#3b82f6', fontFamily:"'DM Sans',sans-serif", letterSpacing:'0.05em' }}>SFDA TRAVEL</span>
            </div>
            <h2 style={{ margin:'0 0 8px', fontSize:28, fontWeight:900, color:'#0d1829', lineHeight:1.2, letterSpacing: isAr?0:'-0.04em' }}>{t.loginTitle}</h2>
            <p style={{ margin:0, fontSize:13.5, color:'#64748b' }}>{t.loginSubtitle}</p>
          </div>

          {/* API error banner */}
          {apiErr && (
            <div style={{ display:'flex', alignItems:'center', gap:10, background:'#fef2f2', border:'1.5px solid #fecaca', borderRadius:10, padding:'11px 14px', marginBottom:20 }}>
              <span style={{ fontSize:16 }}>⚠️</span>
              <span style={{ fontSize:13, color:'#dc2626', fontWeight:500, fontFamily:font }}>{apiErr}</span>
            </div>
          )}

          {/* Fields */}
          <Field label={t.emailLabel} type="email" value={email}
            onChange={e => { setEmail(e.target.value); setErrors(p=>({...p,email:''})); }}
            placeholder={t.emailPlaceholder} error={errors.email}
            isAr={isAr} font={font} autoComplete="email" />

          <Field label={t.passwordLabel} type={showPwd?'text':'password'} value={password}
            onChange={e => { setPassword(e.target.value); setErrors(p=>({...p,password:''})); }}
            placeholder={t.passwordPlaceholder} error={errors.password}
            isAr={isAr} font={font} autoComplete="current-password"
            rightSlot={<span onClick={() => setShowPwd(p=>!p)}><EyeIcon show={showPwd}/></span>}
          />

          {/* Remember + Forgot */}
          <div style={{ display:'flex', justifyContent:'space-between', alignItems:'center', marginBottom:28, direction:dir }}>
            <label style={{ display:'flex', alignItems:'center', gap:8, cursor:'pointer', fontSize:13, color:'#475569', fontFamily:font }}>
              <div onClick={() => setRemember(p=>!p)}
                style={{ width:18, height:18, borderRadius:5, border:`1.5px solid ${remember?'#3b82f6':'#d1d5db'}`, background:remember?'#3b82f6':'white', display:'flex', alignItems:'center', justifyContent:'center', flexShrink:0, transition:'all 0.15s', cursor:'pointer' }}>
                {remember && <svg width="10" height="10" viewBox="0 0 12 12"><path d="M2 6l3 3 5-5" stroke="white" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" fill="none"/></svg>}
              </div>
              {t.rememberMe}
            </label>
            <button onClick={() => onGoForgot?.(lang)}
              style={{ background:'none', border:'none', cursor:'pointer', color:'#3b82f6', fontSize:12.5, fontWeight:600, fontFamily:font, padding:0 }}>
              {t.forgotPassword}
            </button>
          </div>

          {/* Submit */}
          <button onClick={() => handleSubmit(t)} disabled={loading}
            style={{
              width:'100%', padding:'13px 20px',
              background: loading ? '#93c5fd' : 'linear-gradient(135deg,#1c3370,#2d4fa6)',
              color:'white', border:'none', borderRadius:12,
              fontSize:14.5, fontWeight:700, cursor: loading?'not-allowed':'pointer',
              fontFamily:font, transition:'all 0.2s', letterSpacing: isAr?0:'0.01em',
              boxShadow: loading ? 'none' : '0 4px 16px rgba(28,51,112,0.35)',
            }}
            onMouseEnter={e => { if (!loading) e.currentTarget.style.transform='translateY(-1px)'; }}
            onMouseLeave={e => { e.currentTarget.style.transform='none'; }}>
            {loading ? (
              <span style={{ display:'flex', alignItems:'center', justifyContent:'center', gap:8 }}>
                <span style={{ width:14, height:14, border:'2px solid rgba(255,255,255,0.4)', borderTopColor:'white', borderRadius:'50%', display:'inline-block', animation:'spin 0.7s linear infinite' }}/>
                {t.loggingIn}
              </span>
            ) : t.loginBtn}
          </button>

          {/* Signup link */}
          <p style={{ textAlign:'center', marginTop:28, fontSize:13, color:'#64748b', fontFamily:font }}>
            {t.noAccount}{' '}
            <button onClick={() => onGoSignup?.(lang)}
              style={{ background:'none', border:'none', cursor:'pointer', color:'#3b82f6', fontWeight:700, fontSize:13, fontFamily:font, padding:0 }}>
              {t.signUpLink}
            </button>
          </p>

          <style>{`@keyframes spin{to{transform:rotate(360deg)}}`}</style>
        </div>
      )}
    </AuthLayout>
  );
}
