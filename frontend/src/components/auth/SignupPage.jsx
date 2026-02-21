import { useState } from 'react';
import AuthLayout from './AuthLayout';
import { authSignup, saveAuth } from '../../services/api';

function Field({ label, type='text', value, onChange, placeholder, error, isAr, font, autoComplete, rightSlot }) {
  const [focused, setFocused] = useState(false);
  return (
    <div style={{ marginBottom: 16 }}>
      <label style={{ display:'block', fontSize:12.5, fontWeight:700, color:'#374151', marginBottom:6, fontFamily:font }}>{label}</label>
      <div style={{ position:'relative' }}>
        <input
          type={type} value={value} onChange={onChange} placeholder={placeholder}
          autoComplete={autoComplete}
          onFocus={() => setFocused(true)} onBlur={() => setFocused(false)}
          style={{
            width:'100%',
            padding: rightSlot ? `11px ${isAr?'16px':'44px'} 11px ${isAr?'44px':'16px'}` : '11px 16px',
            border:`1.5px solid ${error?'#ef4444':focused?'#3b82f6':'#e2e8f0'}`,
            borderRadius:10, fontSize:13.5, color:'#0f172a',
            background: focused?'#fff':'#f8fafc',
            outline:'none', boxSizing:'border-box',
            transition:'all 0.15s', fontFamily:font,
            direction: isAr?'rtl':'ltr',
            boxShadow: focused?'0 0 0 3px rgba(59,130,246,0.1)':'none',
          }}
        />
        {rightSlot && (
          <div style={{ position:'absolute', top:'50%', transform:'translateY(-50%)', [isAr?'left':'right']:14, cursor:'pointer' }}>
            {rightSlot}
          </div>
        )}
      </div>
      {error && <p style={{ margin:'4px 0 0', fontSize:11.5, color:'#ef4444', fontFamily:font }}>{error}</p>}
    </div>
  );
}

function EyeIcon({ show }) {
  return show
    ? <svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="#94a3b8" strokeWidth="2" strokeLinecap="round"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/></svg>
    : <svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="#94a3b8" strokeWidth="2" strokeLinecap="round"><path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24"/><line x1="1" y1="1" x2="23" y2="23"/></svg>;
}

export default function SignupPage({ onSignup, onGoLogin, initialLang }) {
  const [form, setForm] = useState({ fullName:'', email:'', jobTitle:'', department:'', password:'', confirmPassword:'' });
  const [showPwd,  setShowPwd]  = useState(false);
  const [showConf, setShowConf] = useState(false);
  const [agreed,   setAgreed]   = useState(false);
  const [loading,  setLoading]  = useState(false);
  const [errors,   setErrors]   = useState({});
  const [apiErr,   setApiErr]   = useState('');
  const [lang,     setLang]     = useState(initialLang);

  const set = (k) => (e) => { setForm(p=>({...p,[k]:e.target.value})); setErrors(p=>({...p,[k]:''})); };

  const validate = (t) => {
    const e = {};
    if (!form.fullName)    e.fullName = t.fieldRequired;
    if (!form.email)       e.email    = t.fieldRequired;
    else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(form.email)) e.email = t.invalidEmail;
    if (!form.password)    e.password = t.fieldRequired;
    else if (form.password.length < 8) e.password = t.passwordTooShort;
    if (!form.confirmPassword) e.confirmPassword = t.fieldRequired;
    else if (form.password !== form.confirmPassword) e.confirmPassword = t.passwordMismatch;
    return e;
  };

  const handleSubmit = async (t) => {
    const e = validate(t);
    if (Object.keys(e).length) { setErrors(e); return; }
    setLoading(true); setApiErr('');
    try {
      const res = await authSignup(form);
      saveAuth(res.data.token || res.data.access, res.data.user || { email: form.email });
      onSignup?.();
    } catch (err) {
      setApiErr(err?.response?.data?.message || err?.response?.data?.email?.[0] || t.authError);
    } finally {
      setLoading(false);
    }
  };

  return (
    <AuthLayout lang={initialLang} onLangChange={setLang}>
      {({ t, isAr, dir, font }) => (
        <div style={{ direction:dir, fontFamily:font }}>

          {/* Header */}
          <div style={{ marginBottom:28 }}>
            <div style={{ display:'inline-flex', alignItems:'center', gap:8, background:'#eff6ff', borderRadius:8, padding:'5px 12px', marginBottom:14 }}>
              <span style={{ width:6, height:6, borderRadius:'50%', background:'#3b82f6', display:'inline-block' }}/>
              <span style={{ fontSize:11.5, fontWeight:700, color:'#3b82f6', fontFamily:"'DM Sans',sans-serif", letterSpacing:'0.05em' }}>SFDA TRAVEL</span>
            </div>
            <h2 style={{ margin:'0 0 6px', fontSize:26, fontWeight:900, color:'#0d1829', lineHeight:1.2, letterSpacing:isAr?0:'-0.04em' }}>{t.signUpTitle}</h2>
            <p style={{ margin:0, fontSize:13, color:'#64748b' }}>{t.signUpSubtitle}</p>
          </div>

          {/* API error */}
          {apiErr && (
            <div style={{ display:'flex', alignItems:'center', gap:10, background:'#fef2f2', border:'1.5px solid #fecaca', borderRadius:10, padding:'10px 14px', marginBottom:18 }}>
              <span style={{ fontSize:15 }}>⚠️</span>
              <span style={{ fontSize:13, color:'#dc2626', fontWeight:500, fontFamily:font }}>{apiErr}</span>
            </div>
          )}

          {/* Two-column row: name + job title */}
          <div style={{ display:'grid', gridTemplateColumns:'1fr 1fr', gap:12 }}>
            <Field label={t.fullNameLabel} value={form.fullName} onChange={set('fullName')}
              placeholder={t.fullNamePlaceholder} error={errors.fullName} isAr={isAr} font={font} autoComplete="name"/>
            <Field label={t.jobTitleLabel} value={form.jobTitle} onChange={set('jobTitle')}
              placeholder={t.jobTitlePlaceholder} error={errors.jobTitle} isAr={isAr} font={font}/>
          </div>

          <Field label={t.emailLabel} type="email" value={form.email} onChange={set('email')}
            placeholder={t.emailPlaceholder} error={errors.email} isAr={isAr} font={font} autoComplete="email"/>

          <Field label={t.departmentLabel} value={form.department} onChange={set('department')}
            placeholder={t.departmentPlaceholder} isAr={isAr} font={font}/>

          <div style={{ display:'grid', gridTemplateColumns:'1fr 1fr', gap:12 }}>
            <Field label={t.passwordLabel} type={showPwd?'text':'password'} value={form.password} onChange={set('password')}
              placeholder={t.passwordPlaceholder} error={errors.password} isAr={isAr} font={font} autoComplete="new-password"
              rightSlot={<span onClick={() => setShowPwd(p=>!p)}><EyeIcon show={showPwd}/></span>}/>
            <Field label={t.confirmPasswordLabel} type={showConf?'text':'password'} value={form.confirmPassword} onChange={set('confirmPassword')}
              placeholder={t.confirmPasswordPlaceholder} error={errors.confirmPassword} isAr={isAr} font={font} autoComplete="new-password"
              rightSlot={<span onClick={() => setShowConf(p=>!p)}><EyeIcon show={showConf}/></span>}/>
          </div>

          {/* Password strength bar */}
          {form.password && (() => {
            const len = form.password.length;
            const strength = len >= 12 ? 3 : len >= 8 ? 2 : 1;
            const colors = ['#ef4444','#f59e0b','#22c55e'];
            const labels = { ar:['ضعيفة','متوسطة','قوية'], en:['Weak','Fair','Strong'] };
            return (
              <div style={{ marginBottom:14 }}>
                <div style={{ display:'flex', gap:4, marginBottom:4 }}>
                  {[1,2,3].map(s => (
                    <div key={s} style={{ flex:1, height:3, borderRadius:2, background: s<=strength ? colors[strength-1] : '#e2e8f0', transition:'all 0.3s' }}/>
                  ))}
                </div>
                <span style={{ fontSize:11, color:colors[strength-1], fontWeight:600, fontFamily:font }}>
                  {labels[isAr?'ar':'en'][strength-1]}
                </span>
              </div>
            );
          })()}

          {/* Terms agreement */}
          <label style={{ display:'flex', alignItems:'flex-start', gap:10, cursor:'pointer', marginBottom:22, direction:dir }}>
            <div onClick={() => setAgreed(p=>!p)}
              style={{ width:18, height:18, borderRadius:5, border:`1.5px solid ${agreed?'#3b82f6':'#d1d5db'}`, background:agreed?'#3b82f6':'white', display:'flex', alignItems:'center', justifyContent:'center', flexShrink:0, marginTop:1, transition:'all 0.15s', cursor:'pointer' }}>
              {agreed && <svg width="10" height="10" viewBox="0 0 12 12"><path d="M2 6l3 3 5-5" stroke="white" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" fill="none"/></svg>}
            </div>
            <span style={{ fontSize:12.5, color:'#475569', lineHeight:1.5, fontFamily:font }}>
              {t.agreeTerms}{' '}
              <span style={{ color:'#3b82f6', fontWeight:600 }}>{t.termsLink}</span>
              {' '}{t.andText}{' '}
              <span style={{ color:'#3b82f6', fontWeight:600 }}>{t.privacyLink}</span>
            </span>
          </label>

          {/* Submit */}
          <button onClick={() => handleSubmit(t)} disabled={loading || !agreed}
            style={{
              width:'100%', padding:'13px 20px',
              background: (loading||!agreed) ? '#93c5fd' : 'linear-gradient(135deg,#1c3370,#2d4fa6)',
              color:'white', border:'none', borderRadius:12,
              fontSize:14.5, fontWeight:700, cursor:(loading||!agreed)?'not-allowed':'pointer',
              fontFamily:font, transition:'all 0.2s',
              boxShadow: (loading||!agreed) ? 'none' : '0 4px 16px rgba(28,51,112,0.35)',
            }}
            onMouseEnter={e => { if (!loading&&agreed) e.currentTarget.style.transform='translateY(-1px)'; }}
            onMouseLeave={e => { e.currentTarget.style.transform='none'; }}>
            {loading ? (
              <span style={{ display:'flex', alignItems:'center', justifyContent:'center', gap:8 }}>
                <span style={{ width:14, height:14, border:'2px solid rgba(255,255,255,0.4)', borderTopColor:'white', borderRadius:'50%', display:'inline-block', animation:'spin 0.7s linear infinite' }}/>
                {t.signingUp}
              </span>
            ) : t.signUpBtn}
          </button>

          {/* Login link */}
          <p style={{ textAlign:'center', marginTop:22, fontSize:13, color:'#64748b', fontFamily:font }}>
            {t.hasAccount}{' '}
            <button onClick={() => onGoLogin?.(lang)}
              style={{ background:'none', border:'none', cursor:'pointer', color:'#3b82f6', fontWeight:700, fontSize:13, fontFamily:font, padding:0 }}>
              {t.loginLink}
            </button>
          </p>

          <style>{`@keyframes spin{to{transform:rotate(360deg)}}`}</style>
        </div>
      )}
    </AuthLayout>
  );
}
