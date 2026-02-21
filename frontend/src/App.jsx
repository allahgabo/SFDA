import { useState, useEffect } from 'react';
import ReactDOM from 'react-dom';
import Sidebar from './components/Sidebar';
import WorldMap from './components/WorldMap';
import NewReportForm from './components/NewReportForm';
import ReportDetail from './components/ReportDetail';
import AIAssistant from './components/AIAssistant';
import LoginPage from './components/auth/LoginPage';
import SignupPage from './components/auth/SignupPage';
import ForgotPasswordPage from './components/auth/ForgotPasswordPage';
import { getReports, getStats, deleteReport as apiDelete, getInlinePDFUrl, getPreviewUrl, clearAuth, isAuthenticated } from './services/api';
import { downloadPDF, fetchPreviewBlobUrl, revokePreviewUrl } from './utils/downloadPDF';
import { T, getLang, setLang as saveLang, translateCountry } from './i18n';

// ─── Design tokens ────────────────────────────────────────────────────────────
const C = {
  bg:        '#f7f8fa',
  surface:   '#ffffff',
  elevated:  '#ffffff',
  border:    '#f1f5f9',
  borderHi:  '#ccfbf1',
  teal:      '#0d9488',
  teal2:     '#f0fdfa',
  teal3:     '#ccfbf1',
  tealDark:  '#134e4a',
  textPrim:  '#0f172a',
  textSec:   '#374151',
  textMuted: '#94a3b8',
  success:   '#10b981',
  warning:   '#f59e0b',
  danger:    '#ef4444',
  purple:    '#7c3aed',
  successBg: '#ecfdf5',
  successBd: '#a7f3d0',
  warnBg:    '#fffbeb',
  warnBd:    '#fde68a',
  dangerBg:  '#fef2f2',
  dangerBd:  '#fecaca',
  // compat aliases
  blue:      '#0d9488',
  blueDim:   'rgba(13,148,136,0.55)',
  gold:      '#f59e0b',
  goldLight: '#fcd34d',
  goldDim:   'rgba(245,158,11,0.55)',
  amber:     '#f59e0b',
  amberBg:   '#fffbeb',
  green:     '#10b981',
  greenBg:   '#ecfdf5',
  coral:     '#ef4444',
  coralBg:   '#fef2f2',
  borderGold:'#ccfbf1',
  blueGlow:  'rgba(13,148,136,0.12)',
  ink:       '#0f172a',
  ink2:      '#374151',
  ink3:      '#64748b',
  ink4:      '#94a3b8',
  surface2:  '#f8fafc',
  tealLight: '#f0fdfa',
  tealMid:   '#ccfbf1',
};

const FONT = "'Cairo',sans-serif";
const SHADOW = '0 1px 4px rgba(0,0,0,0.06), 0 1px 2px rgba(0,0,0,0.04)';
const SHADOW_MD = '0 4px 14px rgba(0,0,0,0.08), 0 2px 4px rgba(0,0,0,0.04)';
const SHADOW_LG = '0 8px 32px rgba(0,0,0,0.10)';

const GLOBAL_CSS = `
  @keyframes fadeUp   { from{opacity:0;transform:translateY(16px)} to{opacity:1;transform:none} }
  @keyframes toastIn  { from{opacity:0;transform:translateY(-8px) scale(0.97)} to{opacity:1;transform:none} }
  @keyframes spin     { to{transform:rotate(360deg)} }
  @keyframes pulse    { 0%,100%{opacity:1} 50%{opacity:0.4} }
  @keyframes blink    { 0%,100%{opacity:1} 50%{opacity:0.3} }
  * { box-sizing:border-box }
  input,select,textarea { color-scheme:light; }
  ::selection { background:rgba(13,148,136,0.15); }
`;

// ─── Shared input style ───────────────────────────────────────────────────────
const inputStyle = (focused) => ({
  width: '100%', padding: '11px 14px',
  border: `1.5px solid ${focused ? C.teal : C.border}`,
  borderRadius: 10, fontSize: 13, color: C.ink,
  background: focused ? C.surface : C.surface2,
  outline: 'none', fontFamily: FONT, transition: 'all 0.15s',
  boxShadow: focused ? '0 0 0 3px rgba(13,148,136,0.1)' : 'none',
});

// ─── Section label ────────────────────────────────────────────────────────────
function SectionLabel({ children, dir, onViewAll }) {
  return (
    <div style={{ display:'flex', alignItems:'center', gap:9, marginBottom:14, direction:dir }}>
      <div style={{ width:3, height:15, borderRadius:2, background:C.blue }}/>
      <span style={{ fontSize:11, fontWeight:700, color:C.blue, letterSpacing:'0.14em', textTransform:'uppercase', fontFamily:FONT }}>
        {children}
      </span>
      {onViewAll && (
        <button onClick={onViewAll} style={{ marginInlineStart:'auto', fontSize:12, fontWeight:600, color:C.teal, background:'none', border:'none', cursor:'pointer', fontFamily:FONT, padding:0 }}>
          {dir==='rtl' ? '← عرض الكل' : 'View all →'}
        </button>
      )}
    </div>
  );
}

// ─── Status badge ─────────────────────────────────────────────────────────────
function StatusBadge({ status, t }) {
  const ready = status === 'ready';
  return (
    <span style={{
      display:'inline-flex', alignItems:'center', gap:5, padding:'3px 10px', borderRadius:20,
      fontSize:10.5, fontWeight:600, fontFamily:FONT,
      background: ready ? C.greenBg : C.amberBg,
      color: ready ? C.green : C.amber,
      border: `1px solid ${ready ? '#A7F3D0' : '#FDE68A'}`,
    }}>
      <span style={{ width:5, height:5, borderRadius:'50%', background:ready?C.green:C.amber, display:'inline-block' }}/>
      {ready ? t.ready : t.draft}
    </span>
  );
}

// ─── Card ─────────────────────────────────────────────────────────────────────
function Card({ children, style={}, onClick, hoverable }) {
  const [hov, setHov] = useState(false);
  return (
    <div onClick={onClick}
      onMouseEnter={() => hoverable && setHov(true)}
      onMouseLeave={() => hoverable && setHov(false)}
      style={{ background:C.surface, border:`1px solid ${hov?C.borderHi:C.border}`, borderRadius:14, transition:'all 0.2s', boxShadow:hov?SHADOW_MD:SHADOW, ...style }}>
      {children}
    </div>
  );
}

// ─── Toast ────────────────────────────────────────────────────────────────────
function Toast({ toast }) {
  if (!toast) return null;
  const ok = !toast.color || toast.color===C.success||toast.color==='#22c55e'||toast.color==='#4ade80';
  return ReactDOM.createPortal(
    <div style={{ position:'fixed', top:18, insetInlineEnd:18, zIndex:99999, animation:'toastIn 0.2s ease' }}>
      <div style={{ background:C.surface, border:`1px solid ${ok?'rgba(34,134,58,0.25)':'rgba(232,86,58,0.25)'}`, borderRadius:12, padding:'12px 18px', display:'flex', alignItems:'center', gap:10, boxShadow:SHADOW_LG, maxWidth:380 }}>
        <div style={{ width:32, height:32, borderRadius:8, flexShrink:0, display:'flex', alignItems:'center', justifyContent:'center', fontSize:15, background:ok?C.greenBg:C.coralBg }}>
          {ok?'✓':'⚠'}
        </div>
        <span style={{ fontSize:13, fontWeight:500, color:C.ink, fontFamily:FONT }}>{toast.msg}</span>
      </div>
    </div>,
    document.body
  );
}

// ─── Reports Page ─────────────────────────────────────────────────────────────
function ReportsPage({ reports, lang, t, isAr, dir, setPage, handleDelete, openDetail }) {
  const [search, setSearch] = useState('');
  const [filter, setFilter] = useState('all');
  const [focusSearch, setFocusSearch] = useState(false);

  const filtered = reports.filter(r => {
    const q = search.toLowerCase();
    const ms = !q || (r.title||r.event_name||'').toLowerCase().includes(q) || (r.city||'').toLowerCase().includes(q) || (r.country||'').toLowerCase().includes(q);
    return ms && (filter==='all' || r.status===filter);
  });

  return (
    <div style={{ direction:dir, animation:'fadeUp 0.35s ease both' }}>
      <div style={{ display:'flex', gap:10, marginBottom:22 }}>
        <div style={{ flex:1, position:'relative' }}>
          <span style={{ position:'absolute', [isAr?'insetInlineEnd':'insetInlineStart']:14, top:'50%', transform:'translateY(-50%)', color:C.ink4, pointerEvents:'none' }}>
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>
          </span>
          <input value={search} onChange={e=>setSearch(e.target.value)} placeholder={t.searchPlaceholder}
            style={{ ...inputStyle(focusSearch), padding:isAr?'11px 42px 11px 14px':'11px 14px 11px 42px', direction:dir }}
            onFocus={()=>setFocusSearch(true)} onBlur={()=>setFocusSearch(false)}/>
        </div>
        <div style={{ display:'flex', gap:3, background:C.surface, borderRadius:10, padding:3, border:`1px solid ${C.border}`, boxShadow:SHADOW }}>
          {['all','ready','draft'].map(f=>(
            <button key={f} onClick={()=>setFilter(f)}
              style={{ padding:'7px 14px', borderRadius:7, border:'none', cursor:'pointer', fontFamily:FONT, fontSize:12, fontWeight:600, transition:'all 0.15s',
                background:filter===f?C.teal:'transparent', color:filter===f?'white':C.ink3 }}>
              {f==='all'?t.filterAll:f==='ready'?t.ready:t.draft}
            </button>
          ))}
        </div>
      </div>

      {filtered.length===0 ? (
        <div style={{ textAlign:'center', padding:'80px 20px' }}>
          <div style={{ fontSize:36, marginBottom:12 }}>✈️</div>
          <div style={{ fontSize:17, fontWeight:700, color:C.ink, marginBottom:8, fontFamily:FONT }}>No reports found</div>
          <div style={{ fontSize:13.5, color:C.ink3, marginBottom:20 }}>Create your first travel intelligence briefing</div>
          <button onClick={()=>setPage('new')} style={{ padding:'10px 24px', background:C.teal, color:'white', border:'none', borderRadius:9, cursor:'pointer', fontSize:13.5, fontWeight:700, fontFamily:FONT, boxShadow:`0 4px 16px rgba(10,102,85,0.3)` }}>
            {t.createFirstBtn}
          </button>
        </div>
      ) : (
        <div style={{ display:'grid', gridTemplateColumns:'repeat(auto-fill,minmax(320px,1fr))', gap:14 }}>
          {filtered.map(r => <ReportCard key={r.id} r={r} lang={lang} t={t} isAr={isAr} dir={dir} openDetail={openDetail} handleDelete={handleDelete}/>)}
        </div>
      )}
    </div>
  );
}

function ReportCard({ r, lang, t, isAr, dir, openDetail, handleDelete }) {
  const [hov, setHov] = useState(false);
  const ready = r.status==='ready';
  return (
    <div onClick={()=>openDetail(r.id)}
      onMouseEnter={()=>setHov(true)} onMouseLeave={()=>setHov(false)}
      style={{ position:'relative', borderRadius:12, overflow:'hidden', cursor:'pointer', transition:'all 0.2s', background:C.surface, border:`1px solid ${hov?C.tealMid:C.border}`, boxShadow:hov?SHADOW_MD:SHADOW, transform:hov?'translateY(-3px)':'none', direction:dir }}>
      <div style={{ height:3, background:`linear-gradient(90deg,${ready?C.green:'#d4952a'},${ready?'#4ade80':'#fbbf24'})` }}/>
      <div style={{ padding:'16px 18px 18px' }}>
        <div style={{ display:'flex', justifyContent:'space-between', alignItems:'center', marginBottom:12 }}>
          <StatusBadge status={r.status} t={t}/>
          <button onClick={e=>handleDelete(r.id,e)}
            style={{ width:30, height:30, borderRadius:7, background:'rgba(232,86,58,0.07)', border:'1px solid rgba(232,86,58,0.18)', display:'flex', alignItems:'center', justifyContent:'center', cursor:'pointer', transition:'all 0.15s', color:C.coral }}
            onMouseEnter={e=>{e.stopPropagation();e.currentTarget.style.background='rgba(232,86,58,0.15)';}}
            onMouseLeave={e=>{e.currentTarget.style.background='rgba(232,86,58,0.07)';}}>
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round"><polyline points="3 6 5 6 21 6"/><path d="M19 6l-1 14a2 2 0 0 1-2 2H8a2 2 0 0 1-2-2L5 6"/><path d="M10 11v6M14 11v6"/></svg>
          </button>
        </div>
        <div style={{ fontWeight:700, fontSize:14.5, color:C.ink, marginBottom:12, lineHeight:1.35, fontFamily:FONT }}>{r.title||r.event_name}</div>
        <div style={{ height:1, marginBottom:12, background:`repeating-linear-gradient(${isAr?'270deg':'90deg'},transparent 0,transparent 5px,${C.border} 5px,${C.border} 10px)` }}/>
        <div style={{ display:'flex', flexWrap:'wrap', gap:8, fontSize:11.5, color:C.ink3 }}>
          <span style={{ display:'flex', alignItems:'center', gap:4 }}>
            <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke={C.teal} strokeWidth="2.5" strokeLinecap="round"><path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"/><circle cx="12" cy="10" r="3"/></svg>
            {r.city}, {translateCountry(r.country,lang)}
          </span>
          <span style={{ fontFamily:FONT, fontSize:11 }}>{r.start_date}</span>
          {r.ai_generated && <span style={{ color:'#7c3aed', fontWeight:700, fontSize:10, background:'#f5f3ff', padding:'2px 6px', borderRadius:4, border:'1px solid rgba(124,58,237,0.2)' }}>✦ AI</span>}
        </div>
      </div>
    </div>
  );
}

// ─── Main App ─────────────────────────────────────────────────────────────────
export default function App() {
  const [authScreen,     setAuthScreen]  = useState(()=>isAuthenticated()?null:'login');
  const [page,           setPageRaw]     = useState('dashboard');
  const [selectedReport, setSelected]    = useState(null);
  const [reports,        setReports]     = useState([]);
  const [stats,          setStats]       = useState({total:0,ready:0,draft:0});
  const [toast,          setToast]       = useState(null);
  const [loading,        setLoading]     = useState(true);
  const [lang,           setLangState]   = useState(getLang());

  const setLang = l => { saveLang(l); setLangState(l); };

  const [liveFeed,      setLiveFeed]     = useState(null);
  const [feedLoading,   setFeedLoading]  = useState(false);
  const [feedCountdown, setFeedCountdown]= useState(300);
  const [activeNewsIdx, setActiveNewsIdx]= useState(0);
  const [newItemIds,    setNewItemIds]   = useState(new Set());
  const FEED_MS = 5*60*1000;

  const STATIC = {
    feed:[
      {icon:'💊',title:'FDA Approves Novel Gene Therapy for Rare Metabolic Disorder',summary:'The US FDA granted accelerated approval for a first-in-class gene therapy targeting a rare inherited metabolic condition, benefiting an estimated 12,000 patients globally.',source:'FDA.gov',time:'2 hours ago',impact:'HIGH IMPACT',url:'https://www.fda.gov/news-events/press-announcements'},
      {icon:'🇸🇦',title:'SFDA Signs Regulatory Cooperation Agreement with EMA',summary:'The Saudi Food and Drug Authority formalized a bilateral regulatory cooperation framework with the European Medicines Agency.',source:'SFDA',time:'4 hours ago',impact:'HIGH IMPACT',url:'https://www.sfda.gov.sa/en/news'},
      {icon:'🌍',title:'WHO Releases Updated Essential Medicines List — 15 New Additions',summary:'The World Health Organization added 15 medicines to its Essential Medicines List, including novel oncology and antimicrobial agents.',source:'WHO',time:'6 hours ago',url:'https://www.who.int'},
      {icon:'🔬',title:'G20 Health Ministers Endorse Global AMR Action Framework',summary:'Health ministers from G20 nations pledged $1.2B toward new antibiotic development incentives through 2027.',source:'Reuters',time:'Yesterday',url:'https://www.reuters.com'},
      {icon:'📋',title:'ICH Publishes New Guideline on Pharmaceutical Quality Risk Management',summary:'The ICH released updated Q9(R1) guidance on quality risk management, affecting GMP compliance requirements globally.',source:'ICH',time:'Yesterday',url:'https://www.ich.org'},
    ],
    who:[
      {type:'Alert',typeColor:'#7c3aed',title:'H5N1 Avian Influenza — Enhanced Surveillance in Southeast Asia',summary:'WHO calls for heightened monitoring of H5N1 transmission in poultry workers across Vietnam, Thailand and Indonesia.',tags:['Vietnam','Thailand','Indonesia'],url:'https://www.who.int'},
      {type:'Update',typeColor:'#d97706',title:'MERS-CoV Sporadic Cases — Arabian Peninsula Advisory',summary:'Sporadic MERS-CoV cases continue to be reported in Saudi Arabia and UAE. WHO recommends standard infection prevention measures.',tags:['Saudi Arabia','UAE','Qatar'],url:'https://www.who.int'},
    ]
  };

  const fetchFeed = async (showLoader=false) => {
    if (showLoader) setFeedLoading(true);
    try {
      const token = localStorage.getItem('sfda_token')||'';
      const res = await fetch('/api/intelligence-feed/',{headers:{Authorization:`Token ${token}`}});
      if (!res.ok) throw new Error();
      const data = await res.json();
      if (data.feed&&data.who) {
        if (liveFeed?.feed) {
          const old = new Set(liveFeed.feed.map(i=>i.title));
          const nids = new Set(data.feed.map((x,i)=>old.has(x.title)?null:i).filter(i=>i!==null));
          setNewItemIds(nids); setTimeout(()=>setNewItemIds(new Set()),4000);
        }
        setLiveFeed(data); setFeedCountdown(300);
      }
    } catch {}
    finally { setFeedLoading(false); }
  };

  const setPage = p => setPageRaw(p);
  const handleLogin = ()=>setAuthScreen(null);
  const handleLogout = ()=>{clearAuth();setAuthScreen('login');};
  const t    = T[lang];
  const isAr = lang==='ar';
  const dir  = isAr?'rtl':'ltr';

  const showToast = (msg,color=C.success)=>{setToast({msg,color});setTimeout(()=>setToast(null),3500);};

  const loadData = async ()=>{
    try{const[rR,sR]=await Promise.all([getReports(),getStats()]);setReports(rR.data);setStats(sR.data);}
    catch(e){console.error(e);}finally{setLoading(false);}
  };

  useEffect(()=>{loadData();},[]);
  useEffect(()=>{
    if(!authScreen){fetchFeed(true);const iv=setInterval(()=>fetchFeed(false),FEED_MS);return()=>clearInterval(iv);}
  },[authScreen]);
  useEffect(()=>{
    if(authScreen||page==='new')return;
    const tk=setInterval(()=>{setFeedCountdown(s=>{if(s<=1){fetchFeed(false);return 300;}return s-1;});},1000);
    return()=>clearInterval(tk);
  },[authScreen,page]);
  useEffect(()=>{
    const len=(liveFeed?.feed||STATIC.feed).length;
    if(!len||page==='new')return;
    const r=setInterval(()=>setActiveNewsIdx(i=>(i+1)%len),6000);
    return()=>clearInterval(r);
  },[liveFeed?.feed?.length,page]);

  const handleNewReport = report=>{
    loadData();
    showToast(`✓ "${report.title||report.event_name}" — ${t.reportCreated}`);
    setPage('reports');
  };

  const handleDelete = async (id,e)=>{
    e?.stopPropagation();e?.preventDefault();
    if(!window.confirm(isAr?'هل تريد حذف هذا التقرير؟':'Delete this report?'))return;
    try{
      await apiDelete(id);
      setReports(p=>p.filter(r=>r.id!==id));
      setStats(p=>({...p,total:Math.max(0,(p.total||1)-1)}));
      if(selectedReport===id){setSelected(null);setPage('reports');}
      showToast(isAr?'تم حذف التقرير':'Report deleted');
    }catch(err){
      const s=err?.response?.status,m=err?.response?.data?.error||err?.message||'';
      if(s===401)showToast(isAr?'انتهت الجلسة':'Session expired',C.danger);
      else if(s===404){setReports(p=>p.filter(r=>r.id!==id));showToast(isAr?'تم حذف التقرير':'Report deleted');}
      else showToast(isAr?`فشل الحذف: ${m||s||'خطأ'}`:`Delete failed: ${m||s||'Error'}`,C.danger);
    }
  };

  const openDetail = id=>{setSelected(id);setPage('detail');};
  const upcoming   = reports.filter(r=>r.status==='ready');

  // Auth screens
  if(authScreen==='login')  return <LoginPage  onLogin={handleLogin} onGoSignup={l=>{saveLang(l);setLangState(l);setAuthScreen('signup');}} onGoForgot={l=>{saveLang(l);setLangState(l);setAuthScreen('forgot');}} initialLang={lang}/>;
  if(authScreen==='signup') return <SignupPage onSignup={handleLogin} onGoLogin={l=>{saveLang(l);setLangState(l);setAuthScreen('login');}} initialLang={lang}/>;
  if(authScreen==='forgot') return <ForgotPasswordPage onGoLogin={l=>{saveLang(l);setLangState(l);setAuthScreen('login');}} initialLang={lang}/>;

  const feed    = liveFeed?liveFeed.feed:STATIC.feed;
  const who     = liveFeed?liveFeed.who:STATIC.who;
  const isLive  = !!liveFeed;
  const mins    = Math.floor(feedCountdown/60);
  const secs    = feedCountdown%60;

  const pageTitles = {
    dashboard: isAr?'لوحة التحكم':'Dashboard',
    reports:   isAr?'التقارير':'Reports',
    detail:    isAr?'تفاصيل التقرير':'Report Detail',
    new:       isAr?'إنشاء تقرير':'New Report',
    ai:        isAr?'المساعد الذكي':'AI Assistant',
  };

  return (
    <div style={{ display:'flex', height:'100vh', fontFamily:FONT, background:C.bg, overflow:'hidden', direction:dir }}>
      <style>{GLOBAL_CSS}</style>
      <Toast toast={toast}/>
      <Sidebar page={page} setPage={p=>{setPage(p);setSelected(null);}} lang={lang} setLang={setLang}/>

      <div style={{ flex:1, display:'flex', flexDirection:'column', overflow:'hidden' }}>

        {/* AI fullscreen */}
        {page==='ai' && (
          <div style={{ flex:1, display:'flex', flexDirection:'column', overflow:'hidden' }}>
            <AIAssistant reports={reports}/>
          </div>
        )}

        {page!=='ai' && (
          <>
            {/* ── Topbar ── */}
            <div style={{ background:C.surface, borderBottom:`1px solid ${C.border}`, padding:'0 28px', height:60, display:'flex', justifyContent:'space-between', alignItems:'center', flexShrink:0, direction:dir, boxShadow:SHADOW }}>
              <div style={{ display:'flex', alignItems:'center', gap:14 }}>
                <span style={{ fontSize:15, fontWeight:700, color:C.ink, fontFamily:FONT }}>{pageTitles[page]}</span>
                {page==='reports'&&reports.length>0&&(
                  <>
                    <div style={{ width:1, height:16, background:C.border }}/>
                    <span style={{ fontSize:11.5, color:C.ink4, fontFamily:FONT }}>{reports.length} {isAr?'تقرير':'reports'}</span>
                  </>
                )}
              </div>
              <div style={{ display:'flex', alignItems:'center', gap:8 }}>
                {page!=='new' && (
                  <button onClick={()=>setPage('new')}
                    style={{ display:'flex', alignItems:'center', gap:7, padding:'8px 18px', background:C.teal, color:'white', border:'none', borderRadius:8, fontSize:13, fontWeight:700, cursor:'pointer', fontFamily:FONT, transition:'all 0.18s', boxShadow:`0 2px 12px rgba(10,102,85,0.3)`, whiteSpace:'nowrap' }}
                    onMouseEnter={e=>{e.currentTarget.style.background='#0b7a66';e.currentTarget.style.transform='translateY(-1px)';e.currentTarget.style.boxShadow='0 4px 20px rgba(10,102,85,0.4)';}}
                    onMouseLeave={e=>{e.currentTarget.style.background=C.teal;e.currentTarget.style.transform='none';e.currentTarget.style.boxShadow='0 2px 12px rgba(10,102,85,0.3)';}}>
                    <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round"><path d="M12 5v14M5 12h14"/></svg>
                    {isAr?'تقرير جديد':'New Report'}
                  </button>
                )}
                <button onClick={handleLogout}
                  style={{ display:'flex', alignItems:'center', gap:6, padding:'8px 14px', background:'transparent', color:C.ink3, border:`1px solid ${C.borderHi}`, borderRadius:8, fontSize:12.5, fontWeight:500, cursor:'pointer', fontFamily:FONT, transition:'all 0.15s' }}
                  onMouseEnter={e=>{e.currentTarget.style.background=C.coralBg;e.currentTarget.style.color=C.coral;e.currentTarget.style.borderColor='rgba(232,86,58,0.3)';}}
                  onMouseLeave={e=>{e.currentTarget.style.background='transparent';e.currentTarget.style.color=C.ink3;e.currentTarget.style.borderColor=C.borderHi;}}>
                  <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round"><path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/><polyline points="16 17 21 12 16 7"/><line x1="21" y1="12" x2="9" y2="12"/></svg>
                  {isAr?'خروج':'Logout'}
                </button>
              </div>
            </div>

            {/* ── Content ── */}
            <div style={{ flex:1, overflowY:'auto', padding:page==='new'?'28px 32px 50px':'24px 28px 40px' }}>

              {/* ══ DASHBOARD ════════════════════════════════════════ */}
              {page==='dashboard' && (
                <div style={{ animation:'fadeUp 0.4s ease both', direction:dir }}>

                  {/* Stat cards */}
                  <div style={{ display:'grid', gridTemplateColumns:'repeat(3,1fr)', gap:14, marginBottom:22 }}>
                    {[
                      {val:stats.total, label:isAr?'إجمالي التقارير':'Total Reports',  rgb:'10,102,85',  clr:C.teal,  bg:C.tealLight,
                       icon:<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/></svg>},
                      {val:stats.ready, label:isAr?'جاهزة للسفر':'Ready to Fly',     rgb:'34,134,58',  clr:C.green, bg:C.greenBg,
                       icon:<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round"><path d="M17.8 19.2L16 11l3.5-3.5C21 6 21 4 19.5 2.5S18 2 16.5 3.5L13 7l-8.2-1.8L3 7l7 4L3 17l1 2 6-2 4 7z"/></svg>},
                      {val:stats.draft, label:isAr?'قيد التحضير':'In Progress',       rgb:'212,149,42', clr:C.amber, bg:C.amberBg,
                       icon:<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>},
                    ].map((s,i)=>(
                      <div key={i} style={{ position:'relative', borderRadius:12, overflow:'hidden', background:C.surface, border:`1px solid ${C.border}`, padding:'22px 24px', cursor:'default', transition:'all 0.2s', boxShadow:SHADOW, animation:`fadeUp 0.4s ease ${i*0.07}s both` }}
                        onMouseEnter={e=>{e.currentTarget.style.transform='translateY(-3px)';e.currentTarget.style.boxShadow=SHADOW_MD;e.currentTarget.style.borderColor=`rgba(${s.rgb},0.25)`;}}
                        onMouseLeave={e=>{e.currentTarget.style.transform='none';e.currentTarget.style.boxShadow=SHADOW;e.currentTarget.style.borderColor=C.border;}}>
                        <div style={{ position:'absolute', top:0, left:0, right:0, height:3, background:`linear-gradient(90deg,${s.clr},rgba(${s.rgb},0.4))` }}/>
                        <div style={{ width:42, height:42, borderRadius:11, background:s.bg, display:'flex', alignItems:'center', justifyContent:'center', color:s.clr, marginBottom:14 }}>
                          {s.icon}
                        </div>
                        <div style={{ fontSize:44, fontWeight:300, color:s.clr, lineHeight:1, marginBottom:6, fontFamily:FONT }}>
                          {loading?'—':s.val}
                        </div>
                        <div style={{ fontSize:12, fontWeight:500, color:C.ink3 }}>{s.label}</div>
                      </div>
                    ))}
                  </div>

                  {/* Map */}
                  <Card style={{ marginBottom:20, overflow:'hidden' }}>
                    <div style={{ padding:'14px 20px', borderBottom:`1px solid ${C.border}`, display:'flex', justifyContent:'space-between', alignItems:'center', direction:dir }}>
                      <div style={{ display:'flex', alignItems:'center', gap:10 }}>
                        <div style={{ width:30, height:30, borderRadius:8, background:C.tealLight, display:'flex', alignItems:'center', justifyContent:'center', fontSize:14 }}>🌍</div>
                        <div>
                          <div style={{ fontWeight:700, fontSize:13.5, color:C.ink }}>{t.mapTitle}</div>
                          <div style={{ fontSize:10.5, color:C.ink4, marginTop:1 }}>{t.mapSubtitle}</div>
                        </div>
                      </div>
                      <div style={{ display:'flex', gap:16 }}>
                        {[[C.green,t.riskLow],[C.amber,t.riskMedium],[C.coral,t.riskHigh]].map(([c,l])=>(
                          <span key={l} style={{ display:'flex', alignItems:'center', gap:5, fontSize:10.5, color:C.ink3 }}>
                            <span style={{ width:7, height:7, borderRadius:'50%', background:c, display:'inline-block' }}/>{l}
                          </span>
                        ))}
                      </div>
                    </div>
                    <div style={{ maxHeight:220, overflow:'hidden' }}>
                      <WorldMap upcomingReports={upcoming}/>
                    </div>
                  </Card>

                  {/* Live feeds */}
                  <div style={{ display:'grid', gridTemplateColumns:'1fr 1fr', gap:16, marginBottom:24 }}>

                    {/* Intel feed */}
                    <Card>
                      <div style={{ padding:'13px 18px 11px', borderBottom:`1px solid ${C.border}`, display:'flex', alignItems:'center', justifyContent:'space-between' }}>
                        <div style={{ display:'flex', alignItems:'center', gap:9 }}>
                          <div style={{ width:30, height:30, borderRadius:8, background:'#eff6ff', display:'flex', alignItems:'center', justifyContent:'center', fontSize:13 }}>📰</div>
                          <div style={{ display:'flex', alignItems:'center', gap:7 }}>
                            <span style={{ fontWeight:700, fontSize:13.5, color:C.ink, fontFamily:FONT }}>{t.intelFeed}</span>
                            {isLive ? (
                              <span style={{ fontSize:9, color:C.green, fontWeight:700, background:C.greenBg, padding:'2px 7px', borderRadius:20, border:'1px solid rgba(34,134,58,0.2)', display:'inline-flex', alignItems:'center', gap:3 }}>
                                <span style={{ width:4, height:4, borderRadius:'50%', background:C.green, animation:'blink 2s infinite' }}/>LIVE
                              </span>
                            ) : <span style={{ fontSize:9, color:C.ink4, background:C.surface2, padding:'2px 7px', borderRadius:20 }}>{t.feedCurated}</span>}
                          </div>
                        </div>
                        <div style={{ display:'flex', alignItems:'center', gap:7 }}>
                          {isLive && <span style={{ fontSize:9.5, color:C.ink4, fontFamily:FONT }}>{mins}:{String(secs).padStart(2,'0')}</span>}
                          <button onClick={()=>{fetchFeed(true);setFeedCountdown(300);}} disabled={feedLoading}
                            style={{ width:28, height:28, borderRadius:7, background:C.surface2, border:`1px solid ${C.border}`, cursor:feedLoading?'wait':'pointer', display:'flex', alignItems:'center', justifyContent:'center', transition:'all 0.15s' }}
                            onMouseEnter={e=>{if(!feedLoading)e.currentTarget.style.borderColor=C.teal;}}
                            onMouseLeave={e=>{e.currentTarget.style.borderColor=C.border;}}>
                            <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke={feedLoading?C.ink4:C.teal} strokeWidth="2.5" strokeLinecap="round" style={{ animation:feedLoading?'spin 1s linear infinite':'none' }}>
                              <path d="M3 12a9 9 0 0 1 9-9 9.75 9.75 0 0 1 6.74 2.74L21 8"/><path d="M21 3v5h-5"/>
                              <path d="M21 12a9 9 0 0 1-9 9 9.75 9.75 0 0 1-6.74-2.74L3 16"/><path d="M8 16H3v5"/>
                            </svg>
                          </button>
                        </div>
                      </div>
                      <div style={{ maxHeight:300, overflowY:'auto' }}>
                        {feed.map((item,i)=>{
                          const active=i===activeNewsIdx, isNew=newItemIds.has(i);
                          return (
                            <div key={i} onClick={()=>item.url&&window.open(item.url,'_blank')}
                              style={{ display:'flex', gap:10, padding:'10px 16px', borderBottom:i<feed.length-1?`1px solid ${C.border}`:'none', alignItems:'flex-start', cursor:item.url?'pointer':'default', transition:'background 0.15s', background:isNew?'rgba(10,102,85,0.04)':active?'rgba(10,102,85,0.03)':'transparent', borderInlineStart:active?`2px solid ${C.teal}`:'2px solid transparent' }}>
                              <div style={{ width:30, height:30, borderRadius:8, background:active?C.tealLight:C.surface2, border:`1px solid ${active?C.tealMid:C.border}`, display:'flex', alignItems:'center', justifyContent:'center', fontSize:12, flexShrink:0 }}>
                                {isNew?'🆕':(item.icon||'📰')}
                              </div>
                              <div style={{ flex:1, minWidth:0 }}>
                                <div style={{ fontWeight:600, fontSize:12, color:active?C.teal:C.ink, marginBottom:3, lineHeight:1.45, fontFamily:FONT }}>{item.title}</div>
                                <div style={{ fontSize:10.5, color:C.ink3, marginBottom:4, lineHeight:1.5, fontFamily:FONT }}>{item.summary}</div>
                                <div style={{ display:'flex', alignItems:'center', gap:5, fontSize:9.5, color:C.ink4 }}>
                                  <span>{item.source}</span><span style={{ width:2, height:2, borderRadius:'50%', background:C.ink4 }}/><span>{item.time}</span>
                                  {item.url&&<span style={{ color:C.teal }}>↗</span>}
                                </div>
                              </div>
                              {item.impact&&<span style={{ background:C.greenBg, color:C.green, borderRadius:20, padding:'2px 8px', fontSize:8.5, fontWeight:700, whiteSpace:'nowrap', flexShrink:0, border:'1px solid rgba(34,134,58,0.2)' }}>{item.impact}</span>}
                            </div>
                          );
                        })}
                      </div>
                      {isLive&&feed.length>0&&(
                        <div style={{ padding:'8px 16px', borderTop:`1px solid ${C.border}`, display:'flex', gap:5 }}>
                          {feed.map((_,i)=>(
                            <button key={i} onClick={()=>setActiveNewsIdx(i)} style={{ width:i===activeNewsIdx?16:5, height:4, borderRadius:4, background:i===activeNewsIdx?C.teal:C.border, border:'none', padding:0, cursor:'pointer', transition:'all 0.3s' }}/>
                          ))}
                        </div>
                      )}
                    </Card>

                    {/* WHO */}
                    <Card>
                      <div style={{ padding:'13px 18px 11px', borderBottom:`1px solid ${C.border}`, display:'flex', alignItems:'center', justifyContent:'space-between' }}>
                        <div style={{ display:'flex', alignItems:'center', gap:9 }}>
                          <div style={{ width:30, height:30, borderRadius:8, background:'#fef2f2', display:'flex', alignItems:'center', justifyContent:'center', fontSize:13 }}>🏥</div>
                          <div style={{ display:'flex', alignItems:'center', gap:7 }}>
                            <span style={{ fontWeight:700, fontSize:13.5, color:C.ink, fontFamily:FONT }}>{t.whoAlerts}</span>
                            {isLive&&<span style={{ fontSize:9, color:C.coral, fontWeight:700, background:C.coralBg, padding:'2px 7px', borderRadius:20, border:'1px solid rgba(232,86,58,0.2)', display:'inline-flex', alignItems:'center', gap:3 }}><span style={{ width:4, height:4, borderRadius:'50%', background:C.coral, animation:'blink 2s infinite' }}/>LIVE</span>}
                          </div>
                        </div>
                        {isLive&&<span style={{ fontSize:9.5, color:C.ink4 }}>{mins}:{String(secs).padStart(2,'0')}</span>}
                      </div>
                      <div style={{ overflowY:'auto', maxHeight:300 }}>
                        {who.map((item,i)=>(
                          <div key={i} style={{ padding:'13px 16px', borderBottom:i<who.length-1?`1px solid ${C.border}`:'none' }}>
                            <div style={{ display:'flex', alignItems:'center', justifyContent:'space-between', marginBottom:7 }}>
                              <span style={{ background:item.typeColor||C.coral, color:'white', borderRadius:6, padding:'2px 10px', fontSize:10, fontWeight:700 }}>{item.type}</span>
                              {item.url&&<a href={item.url} target="_blank" rel="noopener noreferrer" style={{ fontSize:10.5, color:C.blue, fontWeight:600, textDecoration:'none' }}>{t.feedReadMore} ↗</a>}
                            </div>
                            <a href={item.url||'#'} target="_blank" rel="noopener noreferrer" style={{ fontWeight:600, fontSize:12.5, color:C.ink, display:'block', textDecoration:'none', lineHeight:1.4, marginBottom:6, fontFamily:FONT }}
                              onMouseEnter={e=>{if(item.url)e.currentTarget.style.color=C.teal;}}
                              onMouseLeave={e=>e.currentTarget.style.color=C.ink}>
                              {item.title}
                            </a>
                            <div style={{ fontSize:11, color:C.ink3, marginBottom:8, lineHeight:1.55, fontFamily:FONT }}>{item.summary}</div>
                            <div style={{ display:'flex', flexWrap:'wrap', gap:5 }}>
                              {(item.tags||[]).map(tag=><span key={tag} style={{ background:C.surface2, color:C.ink3, borderRadius:20, padding:'2px 9px', fontSize:10, border:`1px solid ${C.border}` }}>{tag}</span>)}
                            </div>
                          </div>
                        ))}
                      </div>
                    </Card>
                  </div>

                  {/* Recent reports */}
                  <SectionLabel dir={dir} onViewAll={()=>setPage('reports')}>
                    {isAr?'آخر التقارير':'Recent Reports'}
                  </SectionLabel>

                  {reports.length===0&&!loading ? (
                    <Card style={{ padding:'36px', textAlign:'center' }}>
                      <div style={{ fontSize:32, marginBottom:10 }}>✈️</div>
                      <div style={{ fontSize:16, fontWeight:700, color:C.ink, marginBottom:6, fontFamily:FONT }}>No reports yet</div>
                      <div style={{ fontSize:13, color:C.ink3, marginBottom:18 }}>Create your first travel intelligence briefing</div>
                      <button onClick={()=>setPage('new')} style={{ padding:'10px 22px', background:C.teal, color:'white', border:'none', borderRadius:9, cursor:'pointer', fontSize:13, fontWeight:700, fontFamily:FONT, boxShadow:`0 4px 16px rgba(10,102,85,0.3)` }}>
                        {t.createFirstBtn}
                      </button>
                    </Card>
                  ) : (
                    reports.slice(0,5).map((r,i)=>{
                      const ready=r.status==='ready';
                      return (
                        <div key={r.id} onClick={()=>openDetail(r.id)}
                          style={{ background:C.surface, borderRadius:11, padding:'13px 18px', display:'flex', alignItems:'center', gap:14, border:`1px solid ${C.border}`, cursor:'pointer', transition:'all 0.18s', marginBottom:8, direction:dir, boxShadow:SHADOW, animation:`fadeUp 0.35s ease ${i*0.06}s both` }}
                          onMouseEnter={e=>{e.currentTarget.style.borderColor=C.tealMid;e.currentTarget.style.boxShadow=SHADOW_MD;e.currentTarget.style.transform=`translateX(${isAr?'-':''}2px)`;}}
                          onMouseLeave={e=>{e.currentTarget.style.borderColor=C.border;e.currentTarget.style.boxShadow=SHADOW;e.currentTarget.style.transform='none';}}>
                          <div style={{ width:38, height:38, borderRadius:10, background:ready?C.greenBg:C.amberBg, border:`1px solid ${ready?'rgba(34,134,58,0.2)':'rgba(212,149,42,0.2)'}`, display:'flex', alignItems:'center', justifyContent:'center', fontSize:17, flexShrink:0 }}>
                            {ready?'✈️':'📝'}
                          </div>
                          <div style={{ flex:1, minWidth:0 }}>
                            <div style={{ fontWeight:600, fontSize:13.5, color:C.ink, marginBottom:3, fontFamily:FONT, overflow:'hidden', textOverflow:'ellipsis', whiteSpace:'nowrap' }}>{r.title||r.event_name}</div>
                            <div style={{ display:'flex', gap:12, fontSize:11.5, color:C.ink3, flexWrap:'wrap' }}>
                              <span style={{ display:'flex', alignItems:'center', gap:4 }}>
                                <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke={C.teal} strokeWidth="2.5" strokeLinecap="round"><path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"/><circle cx="12" cy="10" r="3"/></svg>
                                {r.city}, {translateCountry(r.country,lang)}
                              </span>
                              <span>{r.start_date}</span>
                              {r.ai_generated&&<span style={{ color:'#7c3aed', fontWeight:700, fontSize:10, background:'#f5f3ff', padding:'2px 6px', borderRadius:4, border:'1px solid rgba(124,58,237,0.2)' }}>✦ AI</span>}
                            </div>
                          </div>
                          <div style={{ display:'flex', alignItems:'center', gap:10, flexShrink:0 }}>
                            <StatusBadge status={r.status} t={t}/>
                            <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke={C.ink4} strokeWidth="2" strokeLinecap="round"><polyline points={isAr?"15 18 9 12 15 6":"9 18 15 12 9 6"}/></svg>
                          </div>
                        </div>
                      );
                    })
                  )}
                </div>
              )}

              {/* ══ REPORTS ═══════════════════════════════════════════ */}
              {page==='reports' && (
                <ReportsPage reports={reports} lang={lang} t={t} isAr={isAr} dir={dir} setPage={setPage} handleDelete={handleDelete} openDetail={openDetail}/>
              )}

              {/* ══ DETAIL ════════════════════════════════════════════ */}
              {page==='detail'&&selectedReport && (
                <ReportDetail lang={lang} reportId={selectedReport} onBack={()=>setPage('reports')}/>
              )}

              {/* ══ NEW ════════════════════════════════════════════════ */}
              {page==='new' && (
                <NewReportForm onSuccess={handleNewReport} onCancel={()=>setPage('dashboard')} lang={lang}/>
              )}

            </div>
          </>
        )}
      </div>
    </div>
  );
}
