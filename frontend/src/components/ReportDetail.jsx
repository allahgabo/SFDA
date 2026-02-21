import { useState, useEffect, useCallback } from 'react';
import { getReport } from '../services/api';
import { downloadPDF } from '../utils/downloadPDF';
import { T, translateCountry } from '../i18n';

const initials = n => (n||'').split(' ').slice(0,2).map(w=>w[0]||'').join('').toUpperCase()||'?';
const GRADS = [
  ['#1c3370','#3b5bdb'],['#0f766e','#14b8a6'],['#7e22ce','#a855f7'],
  ['#b45309','#f59e0b'],['#be123c','#fb7185'],['#0369a1','#38bdf8'],
];
const grad  = n => GRADS[(n?.charCodeAt(0)||0)%GRADS.length];
const wIcon = c => {
  const s=(c||'').toLowerCase();
  return s.includes('sun')||s.includes('clear')?'☀️':s.includes('cloud')?'⛅':s.includes('rain')?'🌧️':s.includes('storm')?'⛈️':s.includes('snow')?'❄️':'🌤️';
};

/* ── Dark navy section bar ── */
const SecBar = ({ icon, title }) => (
  <div style={{ background:'#1c3370', color:'white', padding:'11px 20px', borderRadius:10, marginBottom:16, display:'flex', alignItems:'center', gap:10, fontSize:14, fontWeight:800 }}>
    <span style={{ fontSize:17 }}>{icon}</span>{title}
  </div>
);

/* ── Dark blue full-bleed divider banner ── */
const Divider = ({ icon, title }) => (
  <div style={{ background:'linear-gradient(135deg,#0d1e3d 0%,#1c3370 60%,#1e4a9a 100%)', padding:'14px 20px', borderRadius:10, margin:'24px 0 0', display:'flex', alignItems:'center', gap:10 }}>
    <span style={{ fontSize:18 }}>{icon}</span>
    <span style={{ color:'white', fontWeight:800, fontSize:15 }}>{title}</span>
  </div>
);

/* ── Info chip — label on top, value below ── */
const Chip = ({ icon, label, value, sub }) => (
  <div style={{ background:'white', border:'1px solid #e8edf4', borderRadius:12, padding:'13px 16px', boxShadow:'0 1px 3px rgba(0,0,0,0.04)' }}>
    <div style={{ display:'flex', alignItems:'center', gap:5, fontSize:11, color:'#94a3b8', fontWeight:700, marginBottom:6 }}>
      {icon && <span>{icon}</span>}
      {label}
    </div>
    <div style={{ fontSize:13.5, fontWeight:800, color:'#0d1829', lineHeight:1.3 }}>{value||'—'}</div>
    {sub && <div style={{ fontSize:10.5, color:'#94a3b8', marginTop:3 }}>{sub}</div>}
  </div>
);

/* ── Blue-bordered overview text block ── */
const Overview = ({ text, isAr }) => (
  <div style={{ borderInlineStart:'4px solid #1c3370', background:'white', padding:'14px 18px', borderRadius:'0 10px 10px 0', fontSize:13.5, color:'#334155', lineHeight:1.85, marginBottom:20 }}>
    {text}
  </div>
);

const TblHead = ({ cols, bg='#1c3370' }) => (
  <thead><tr style={{ background:bg }}>
    {cols.map(h => <th key={h} style={{ padding:'10px 14px', color:'white', fontWeight:700, textAlign:'right', fontSize:12 }}>{h}</th>)}
  </tr></thead>
);
const rowStyle = i => ({ background: i%2===0 ? 'white' : '#f8fafc', borderBottom:'1px solid #f1f5f9' });

export default function ReportDetail({ reportId, onBack, onPDFOpen, lang='ar' }) {
  const [report,  setReport]  = useState(null);
  const [loading, setLoading] = useState(true);
  const t    = T[lang];
  const isAr = lang === 'ar';
  const dir  = isAr ? 'rtl' : 'ltr';
  const font = isAr ? "'Cairo','Segoe UI',sans-serif" : "'DM Sans',-apple-system,sans-serif";

  useEffect(() => {
    setLoading(true);
    getReport(reportId)
      .then(r => { setReport(r.data); setLoading(false); })
      .catch(() => setLoading(false));
  }, [reportId]);

  if (loading) return (
    <div style={{ display:'flex', alignItems:'center', justifyContent:'center', height:'60vh', flexDirection:'column', gap:14 }}>
      <div style={{ width:44, height:44, border:'4px solid #e2e8f0', borderTopColor:'#1c3370', borderRadius:'50%', animation:'spin 0.8s linear infinite' }}/>
      <div style={{ color:'#64748b', fontSize:14, fontFamily:font }}>{t.loadingReport}</div>
      <style>{`@keyframes spin{to{transform:rotate(360deg)}}`}</style>
    </div>
  );
  if (!report) return null;

  const isReady = report.status === 'ready';
  const ci = report.country_info || {};
  const cd = report.conference_data || {};
  const sess = report.sessions || {};
  const card = { background:'white', border:'1px solid #e8edf4', borderRadius:14, padding:'22px 24px', marginTop:16, boxShadow:'0 1px 4px rgba(0,0,0,0.05)' };

  return (
    <div style={{ background:'#f1f5f9', minHeight:'100vh', fontFamily:font, direction:dir }}>
      <style>{`@keyframes spin{to{transform:rotate(360deg)}}`}</style>

      {/* ══ WHITE STICKY HEADER ══════════════════════════════════════════════ */}
      <div style={{ background:'white', borderBottom:'1px solid #e8edf4', padding:'14px 28px', position:'sticky', top:0, zIndex:100, boxShadow:'0 2px 8px rgba(0,0,0,0.06)' }}>

        {/* Breadcrumb + action buttons row */}
        <div style={{ display:'flex', alignItems:'center', justifyContent:'space-between', marginBottom:12 }}>
          {/* Breadcrumb */}
          <div style={{ display:'flex', alignItems:'center', gap:8, fontSize:12.5, color:'#94a3b8', direction:dir }}>
            <button onClick={onBack}
              style={{ background:'none', border:'none', cursor:'pointer', color:'#64748b', fontWeight:600, fontSize:12.5, fontFamily:font, padding:0 }}>
              {t.breadcrumbDashboard}
            </button>
            <span style={{ color:'#d1d5db' }}>›</span>
            <button onClick={onBack}
              style={{ background:'none', border:'none', cursor:'pointer', color:'#64748b', fontWeight:600, fontSize:12.5, fontFamily:font, padding:0 }}>
              {t.breadcrumbReports}
            </button>
            <span style={{ color:'#d1d5db' }}>›</span>
            <span style={{ color:'#1c3370', fontWeight:700 }}>{report.event_name}</span>
          </div>

          {/* Action buttons */}
          <div style={{ display:'flex', gap:8 }}>
            <button
              onClick={async () => {
                try { await downloadPDF(reportId, `SFDA_${report.event_name}.pdf`); }
                catch(e) { alert('PDF export failed: ' + e.message); }
              }}
              style={{ display:'flex', alignItems:'center', gap:7, padding:'8px 18px', background:'#1c3370', color:'white', border:'none', borderRadius:9, fontSize:13, fontWeight:700, cursor:'pointer', fontFamily:font, boxShadow:'0 2px 8px rgba(28,51,112,0.3)' }}>
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>
              {t.exportPDF}
            </button>

          </div>
        </div>

        {/* Page title */}
        <h1 style={{ margin:0, fontSize:22, fontWeight:900, color:'#0d1829', letterSpacing: isAr?0:'-0.03em' }}>
          {report.event_name}
        </h1>
      </div>

      {/* ══ CONTENT ═════════════════════════════════════════════════════════ */}
      <div style={{ padding:'20px 28px 60px', maxWidth:1100, margin:'0 auto' }}>

        {/* ── Summary card ── */}
        <div style={{ ...card, marginTop:20 }}>
          <div style={{ display:'flex', alignItems:'flex-start', justifyContent:'space-between', marginBottom:16, gap:12, direction:dir }}>
            {/* Title + badge */}
            <div style={{ flex:1 }}>
              <div style={{ display:'flex', alignItems:'center', gap:10, flexWrap:'wrap' }}>
                <span style={{ fontWeight:800, fontSize:16, color:'#0d1829' }}>{report.event_name}</span>
                <span style={{ background: isReady?'#e8fdf2':'#fef9e7', color: isReady?'#1a9655':'#b45309', border:`1px solid ${isReady?'#a7f0c4':'#fde68a'}`, borderRadius:20, padding:'3px 12px', fontSize:11.5, fontWeight:700 }}>
                  {isReady ? t.statusReady : t.statusDraft}
                </span>
              </div>
            </div>
            {/* Export */}
            <button onClick={async () => {
                try { await downloadPDF(reportId, `SFDA_${report.event_name}.pdf`); }
                catch(e) { alert('PDF export failed: ' + e.message); }
              }}
              style={{ display:'flex', alignItems:'center', gap:6, padding:'7px 14px', background:'#1c3370', color:'white', border:'none', borderRadius:8, fontSize:12.5, fontWeight:700, cursor:'pointer', flexShrink:0, fontFamily:font }}>
              <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>
              {t.exportPDF}
            </button>
          </div>

          {/* Meta rows */}
          <div style={{ display:'flex', flexDirection:'column', gap:9, fontSize:13 }}>
            <div style={{ display:'flex', alignItems:'center', gap:8, color:'#4a7adb' }}>
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round"><path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"/><circle cx="12" cy="10" r="3"/></svg>
              <span style={{ fontWeight:500 }}>{report.city}{report.country ? `، ${translateCountry(report.country, lang)}` : ''}</span>
            </div>
            {report.start_date && (
              <div style={{ display:'flex', alignItems:'center', gap:8, color:'#64748b' }}>
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round"><rect x="3" y="4" width="18" height="18" rx="2"/><line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/></svg>
                <span style={{ fontFamily:"'DM Sans',sans-serif" }}>{report.start_date}{report.end_date && report.end_date!==report.start_date ? ` - ${report.end_date}` : ''}</span>
              </div>
            )}
            {report.event_website && (
              <div style={{ display:'flex', alignItems:'center', gap:8 }}>
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#4a7adb" strokeWidth="2" strokeLinecap="round"><circle cx="12" cy="12" r="9"/><line x1="2" y1="12" x2="22" y2="12"/><path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"/></svg>
                <a href={report.event_website} target="_blank" rel="noreferrer"
                  style={{ color:'#2563eb', fontSize:13, fontWeight:600, textDecoration:'none' }}>
                  {t.conferenceWebsite}
                  <svg style={{ marginInlineStart:4, display:'inline', verticalAlign:'middle' }} width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round"><path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"/><polyline points="15 3 21 3 21 9"/><line x1="10" y1="14" x2="21" y2="3"/></svg>
                </a>
              </div>
            )}
          </div>
        </div>

        {/* ── Rich Intelligence Sections ── */}
        {[
          { key:'conference_summary',         icon:'📄', title: t.conferenceSummaryTitle },
          { key:'conference_history',         icon:'🕐', title: t.conferenceHistoryTitle },
          { key:'ksa_participation_history',  icon:'👤', title: t.ksaParticipationHistoryTitle },
        ].map(({ key, icon, title }) => report[key] ? (
          <div key={key} style={{ marginTop:16 }}>
            <div style={{ background:'linear-gradient(135deg,#0d1e3d 0%,#1c3370 60%,#1e4a9a 100%)', padding:'12px 20px', borderRadius:10, display:'flex', alignItems:'center', justifyContent:'space-between', direction:dir }}>
              <span style={{ color:'white', fontWeight:900, fontSize:14 }}>{title}</span>
              <span style={{ fontSize:17 }}>{icon}</span>
            </div>
            <div style={{ background:'white', border:'1px solid #e8edf4', borderRadius:'0 0 14px 14px', padding:'18px 22px', fontSize:13.5, color:'#334155', lineHeight:1.9, boxShadow:'0 1px 4px rgba(0,0,0,0.05)', direction:dir }}>
              {report[key]}
            </div>
          </div>
        ) : null)}

        {/* 2-column: لمحة عن الدولة + تحليل صلة الهيئة */}
        {(report.country_info?.overview || report.sfda_relevance) && (
          <div style={{ display:'grid', gridTemplateColumns:'1fr 1fr', gap:16, marginTop:16 }}>
            {report.country_info?.overview && (
              <div style={{ background:'white', border:'1px solid #e8edf4', borderRadius:14, overflow:'hidden', boxShadow:'0 1px 4px rgba(0,0,0,0.05)' }}>
                <div style={{ background:'linear-gradient(135deg,#0d1e3d 0%,#1c3370 60%,#1e4a9a 100%)', padding:'12px 20px', display:'flex', alignItems:'center', justifyContent:'space-between', direction:dir }}>
                  <span style={{ color:'white', fontWeight:900, fontSize:14 }}>{t.countryBriefTitle}</span>
                  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="rgba(255,255,255,0.7)" strokeWidth="1.8" strokeLinecap="round"><circle cx="12" cy="12" r="10"/><line x1="2" y1="12" x2="22" y2="12"/><path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"/></svg>
                </div>
                <div style={{ padding:'18px 22px', fontSize:13.5, color:'#334155', lineHeight:1.9, direction:dir }}>{report.country_info.overview}</div>
              </div>
            )}
            {report.sfda_relevance && (
              <div style={{ background:'white', border:'1px solid #e8edf4', borderRadius:14, overflow:'hidden', boxShadow:'0 1px 4px rgba(0,0,0,0.05)' }}>
                <div style={{ background:'linear-gradient(135deg,#0d1e3d 0%,#1c3370 60%,#1e4a9a 100%)', padding:'12px 20px', display:'flex', alignItems:'center', justifyContent:'space-between', direction:dir }}>
                  <span style={{ color:'white', fontWeight:900, fontSize:14 }}>{t.sfdaRelevanceTitle}</span>
                  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="rgba(255,255,255,0.7)" strokeWidth="1.8" strokeLinecap="round"><circle cx="12" cy="12" r="10"/><polyline points="12 8 12 12 14 14"/></svg>
                </div>
                <div style={{ padding:'18px 22px', fontSize:13.5, color:'#334155', lineHeight:1.9, direction:dir }}>{report.sfda_relevance}</div>
              </div>
            )}
          </div>
        )}

        {/* 2-column: العلاقات الثنائية + الملخص الجيوسياسي */}
        {(report.bilateral_relations || report.geopolitical_summary) && (
          <div style={{ display:'grid', gridTemplateColumns:'1fr 1fr', gap:16, marginTop:16 }}>
            {report.bilateral_relations && (
              <div style={{ background:'white', border:'1px solid #e8edf4', borderRadius:14, overflow:'hidden', boxShadow:'0 1px 4px rgba(0,0,0,0.05)' }}>
                <div style={{ background:'linear-gradient(135deg,#0d1e3d 0%,#1c3370 60%,#1e4a9a 100%)', padding:'12px 20px', display:'flex', alignItems:'center', justifyContent:'space-between', direction:dir }}>
                  <span style={{ color:'white', fontWeight:900, fontSize:14 }}>{t.bilateralRelationsTitle}</span>
                  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="rgba(255,255,255,0.7)" strokeWidth="1.8" strokeLinecap="round"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/></svg>
                </div>
                <div style={{ padding:'18px 22px', fontSize:13.5, color:'#334155', lineHeight:1.9, direction:dir }}>{report.bilateral_relations}</div>
              </div>
            )}
            {report.geopolitical_summary && (
              <div style={{ background:'white', border:'1px solid #e8edf4', borderRadius:14, overflow:'hidden', boxShadow:'0 1px 4px rgba(0,0,0,0.05)' }}>
                <div style={{ background:'linear-gradient(135deg,#0d1e3d 0%,#1c3370 60%,#1e4a9a 100%)', padding:'12px 20px', display:'flex', alignItems:'center', justifyContent:'space-between', direction:dir }}>
                  <span style={{ color:'white', fontWeight:900, fontSize:14 }}>{t.geopoliticalSummaryTitle}</span>
                  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="rgba(255,255,255,0.7)" strokeWidth="1.8" strokeLinecap="round"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>
                </div>
                <div style={{ padding:'18px 22px', fontSize:13.5, color:'#334155', lineHeight:1.9, direction:dir }}>{report.geopolitical_summary}</div>
              </div>
            )}
          </div>
        )}

        {/* 2-column: متطلبات الدخول + موجز القيادة */}
        {(report.entry_requirements || report.leadership_brief) && (
          <div style={{ display:'grid', gridTemplateColumns:'1fr 1fr', gap:16, marginTop:16 }}>
            {report.entry_requirements && (
              <div style={{ background:'white', border:'1px solid #e8edf4', borderRadius:14, overflow:'hidden', boxShadow:'0 1px 4px rgba(0,0,0,0.05)' }}>
                <div style={{ background:'linear-gradient(135deg,#0d1e3d 0%,#1c3370 60%,#1e4a9a 100%)', padding:'12px 20px', display:'flex', alignItems:'center', justifyContent:'space-between', direction:dir }}>
                  <span style={{ color:'white', fontWeight:900, fontSize:14 }}>{t.entryRequirementsTitle}</span>
                  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="rgba(255,255,255,0.7)" strokeWidth="1.8" strokeLinecap="round"><rect x="2" y="5" width="20" height="14" rx="2"/><line x1="2" y1="10" x2="22" y2="10"/></svg>
                </div>
                <div style={{ padding:'18px 22px', fontSize:13.5, color:'#334155', lineHeight:1.9, direction:dir }}>{report.entry_requirements}</div>
              </div>
            )}
            {report.leadership_brief && (
              <div style={{ background:'white', border:'1px solid #e8edf4', borderRadius:14, overflow:'hidden', boxShadow:'0 1px 4px rgba(0,0,0,0.05)' }}>
                <div style={{ background:'linear-gradient(135deg,#0d1e3d 0%,#1c3370 60%,#1e4a9a 100%)', padding:'12px 20px', display:'flex', alignItems:'center', justifyContent:'space-between', direction:dir }}>
                  <span style={{ color:'white', fontWeight:900, fontSize:14 }}>{t.leadershipBriefTitle}</span>
                  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="rgba(255,255,255,0.7)" strokeWidth="1.8" strokeLinecap="round"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>
                </div>
                <div style={{ padding:'18px 22px', fontSize:13.5, color:'#334155', lineHeight:1.9, direction:dir }}>{report.leadership_brief}</div>
              </div>
            )}
          </div>
        )}

        {/* Trade Exchange - full width */}
        {report.trade_exchange && (
          <div style={{ marginTop:16 }}>
            <div style={{ background:'linear-gradient(135deg,#0d1e3d 0%,#1c3370 60%,#1e4a9a 100%)', padding:'12px 20px', borderRadius:10, display:'flex', alignItems:'center', justifyContent:'space-between', direction:dir }}>
              <span style={{ color:'white', fontWeight:900, fontSize:14 }}>{t.bilateralTradeTitle}</span>
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="rgba(255,255,255,0.7)" strokeWidth="1.8" strokeLinecap="round"><polyline points="22 7 13.5 15.5 8.5 10.5 2 17"/><polyline points="16 7 22 7 22 13"/></svg>
            </div>
            <div style={{ background:'white', border:'1px solid #e8edf4', borderRadius:'0 0 14px 14px', padding:'18px 22px', fontSize:13.5, color:'#334155', lineHeight:1.9, boxShadow:'0 1px 4px rgba(0,0,0,0.05)', direction:dir }}>
              {report.trade_exchange}
            </div>
          </div>
        )}

        {/* ── Conference Data ── */}
        <div style={{ marginTop:16 }}>
          <SecBar icon="📅" title={t.conferenceDataTitle} />

          {/* 3-column conference cards */}
          <div style={{ display:'grid', gridTemplateColumns:'1fr 1fr 1fr', gap:14 }}>
            {/* Organizer */}
            <div style={{ background:'#f4f6f9', border:'1px solid #e2e8f0', borderRadius:14, padding:'18px', display:'flex', flexDirection:'column', alignItems:'center' }}>
              <div style={{ fontSize:11, color:'#94a3b8', fontWeight:700, marginBottom:14, alignSelf:'flex-start' }}>
                {t.organizerLabel}
              </div>
              <div style={{ background:'white', borderRadius:12, padding:'20px', width:'100%', display:'flex', flexDirection:'column', alignItems:'center', justifyContent:'center', minHeight:100, marginBottom:12, border:'1px solid #e8edf4' }}>
                {cd.logo_url
                  ? <img src={cd.logo_url} alt="logo" style={{ maxWidth:120, maxHeight:60, objectFit:'contain' }}/>
                  : <div style={{ width:60, height:60, borderRadius:12, background:'#eff6ff', display:'flex', alignItems:'center', justifyContent:'center', fontSize:24 }}>🏛️</div>
                }
              </div>
              <div style={{ fontSize:13.5, fontWeight:700, color:'#0d1829', textAlign:'center' }}>{cd.organizer || '—'}</div>
            </div>

            {/* Event */}
            <div style={{ background:'#f4f6f9', border:'1px solid #e2e8f0', borderRadius:14, padding:'18px', display:'flex', flexDirection:'column' }}>
              <div style={{ fontSize:11, color:'#94a3b8', fontWeight:700, marginBottom:14 }}>
                {t.eventLabel}
              </div>
              <div style={{ flex:1, display:'flex', flexDirection:'column', justifyContent:'center', alignItems:'center', textAlign:'center', gap:10 }}>
                <div style={{ fontSize:16, fontWeight:900, color:'#1c3370', lineHeight:1.35 }}>{report.event_name}</div>
                {report.start_date && (
                  <div style={{ fontSize:12.5, color:'#64748b', fontFamily:"'DM Sans',sans-serif" }}>
                    {report.start_date}{report.end_date && report.end_date!==report.start_date ? ` - ${report.end_date}` : ''}
                  </div>
                )}
              </div>
            </div>

            {/* Event Leader */}
            <div style={{ background:'#1c3370', borderRadius:14, padding:'18px', display:'flex', flexDirection:'column' }}>
              <div style={{ fontSize:11, color:'rgba(255,255,255,0.5)', fontWeight:700, marginBottom:14 }}>
                {t.eventLeaderLabel}
              </div>
              <div style={{ flex:1, display:'flex', flexDirection:'column', justifyContent:'center', alignItems:'center', textAlign:'center', gap:8 }}>
                {cd.event_leader ? (
                  <>
                    <div style={{ width:48, height:48, borderRadius:'50%', background:'rgba(255,255,255,0.15)', display:'flex', alignItems:'center', justifyContent:'center', fontSize:22 }}>👤</div>
                    <div style={{ color:'white', fontWeight:800, fontSize:14 }}>{cd.event_leader}</div>
                  </>
                ) : (
                  <>
                    <div style={{ width:48, height:48, borderRadius:'50%', background:'rgba(255,255,255,0.1)', display:'flex', alignItems:'center', justifyContent:'center', fontSize:20 }}>👤</div>
                    <div style={{ color:'rgba(255,255,255,0.6)', fontSize:13, fontWeight:600 }}>{t.notSpecified}</div>
                  </>
                )}
              </div>
            </div>
          </div>

          {/* Overview text */}
          {cd.overview && (
            <div style={{ marginTop:16, ...card, padding:'16px 20px' }}>
              <div style={{ fontSize:12, fontWeight:800, color:'#1c3370', marginBottom:10, display:'flex', alignItems:'center', gap:7 }}>
                <div style={{ background:'#1c3370', color:'white', borderRadius:6, padding:'3px 10px', fontSize:11 }}>{t.overview}</div>
              </div>
              <Overview text={cd.overview} isAr={isAr}/>
            </div>
          )}
        </div>

        {/* ── Country Info ── */}
        <div style={{ marginTop:16 }}>
          <SecBar icon="🌐" title={t.generalInfoTitle} />

          {/* Head of state + Country flag cards */}
          <div style={{ display:'grid', gridTemplateColumns:'1fr 1fr', gap:14, marginBottom:16 }}>
            {/* Head of State */}
            <div style={{ background:'#1c3370', borderRadius:14, padding:'22px', display:'flex', flexDirection:'column', alignItems:'center', gap:12 }}>
              <div style={{ fontSize:11, color:'rgba(255,255,255,0.5)', fontWeight:700, alignSelf:'flex-start' }}>
                {t.headOfStateLabel}
              </div>
              <div style={{ width:56, height:56, borderRadius:'50%', background:'rgba(255,255,255,0.12)', display:'flex', alignItems:'center', justifyContent:'center', fontSize:24, border:'2px solid rgba(255,255,255,0.15)' }}>
                {ci.head_photo ? <img src={ci.head_photo} alt="" style={{ width:'100%', height:'100%', borderRadius:'50%', objectFit:'cover' }}/> : '📷'}
              </div>
              <div style={{ textAlign:'center' }}>
                <div style={{ color:'white', fontWeight:800, fontSize:14, lineHeight:1.3 }}>{ci.head_of_state || '—'}</div>
                {ci.head_of_state_title && (
                  <div style={{ color:'rgba(255,255,255,0.6)', fontSize:11.5, marginTop:5, lineHeight:1.4 }}>{ci.head_of_state_title}</div>
                )}
              </div>
            </div>

            {/* Country */}
            <div style={{ background:'#1c3370', borderRadius:14, padding:'22px', display:'flex', flexDirection:'column', alignItems:'center', justifyContent:'center', gap:12 }}>
              <div style={{ fontSize:11, color:'rgba(255,255,255,0.5)', fontWeight:700, alignSelf:'flex-start' }}>
                {t.countryLabel}
              </div>
              <div style={{ fontSize:52, lineHeight:1 }}>{ci.flag || '🌍'}</div>
              <div style={{ color:'white', fontWeight:900, fontSize:18 }}>{translateCountry(report.country, lang)}</div>
            </div>
          </div>

          {/* Overview */}
          {ci.overview && (
            <div style={{ ...card, padding:'16px 20px', marginTop:0 }}>
              <div style={{ marginBottom:10 }}>
                <div style={{ background:'#1c3370', color:'white', borderRadius:6, padding:'3px 10px', fontSize:11, fontWeight:800, display:'inline-block' }}>{t.overview}</div>
              </div>
              <Overview text={ci.overview} isAr={isAr}/>
            </div>
          )}

          {/* Info chips grid */}
          <div style={{ display:'grid', gridTemplateColumns:'repeat(3, 1fr)', gap:12, marginTop:14 }}>
            <Chip icon="🏛️" label={t.capitalLabel}          value={ci.capital}/>
            <Chip icon="👥" label={t.populationLabel}      value={ci.population}/>
            <Chip icon="💰" label={t.currencyLabel}            value={ci.currency} sub={ci.currency_rate}/>
            <Chip icon="🏛️" label={t.governmentLabel}         value={ci.government}/>
            <Chip icon="📐" label={t.areaLabel}               value={ci.area}/>
            <Chip icon="☪️" label={t.religionLabel}           value={ci.religion}/>
            <Chip icon="🔤" label={t.languageLabel} value={ci.official_language}/>
            {ci.timezone && <Chip icon="⏰" label={t.timezoneLabel} value={ci.timezone}/>}
            {ci.gdp      && <Chip icon="📊" label={t.gdpLabel}         value={ci.gdp}/>}
          </div>
        </div>

        {/* ── Visit Objectives ── */}
        {(report.visit_objectives||[]).length > 0 && (
          <div style={{ marginTop:16 }}>
            <SecBar icon="🎯" title={t.visitObjectivesTitle} />
            <div style={{ background:'white', borderRadius:14, border:'1px solid #e8edf4', padding:'18px 20px', boxShadow:'0 1px 4px rgba(0,0,0,0.05)' }}>
              {(report.visit_objectives||[]).map((o,i) => (
                <div key={i} style={{ display:'flex', alignItems:'flex-start', gap:12, padding:'10px 0', borderBottom: i < report.visit_objectives.length-1 ? '1px solid #f1f5f9' : 'none' }}>
                  <div style={{ width:22, height:22, borderRadius:'50%', background:'#eff6ff', border:'2px solid #3b82f6', display:'flex', alignItems:'center', justifyContent:'center', flexShrink:0, marginTop:2 }}>
                    <div style={{ width:7, height:7, borderRadius:'50%', background:'#3b82f6' }}/>
                  </div>
                  <span style={{ fontSize:13.5, color:'#334155', lineHeight:1.7, flex:1 }}>{o}</span>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* ── Delegation ── */}
        {(report.delegation||[]).length > 0 && (
          <div style={{ marginTop:16 }}>
            <SecBar icon="👥" title={t.delegationTitle2} />
            <div style={{ ...card, marginTop:0 }}>
              <table style={{ width:'100%', borderCollapse:'collapse', fontSize:13 }}>
                <TblHead cols={['#', isAr?'الاسم':'Name', isAr?'المسمى الوظيفي':'Title', isAr?'الجهة':'Department']}/>
                <tbody>
                  {(report.delegation||[]).map((m,i) => (
                    <tr key={i} style={rowStyle(i)}>
                      <td style={{ padding:'11px 14px', color:'#1c3370', fontWeight:800, width:40, textAlign:'center' }}>{i+1}</td>
                      <td style={{ padding:'11px 14px', fontWeight:700, color:'#0f172a' }}>{m.name}</td>
                      <td style={{ padding:'11px 14px', color:'#334155' }}>{m.title}</td>
                      <td style={{ padding:'11px 14px', color:'#64748b', fontSize:12 }}>{m.department}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* ── Agenda ── */}
        {(report.agenda||[]).length > 0 && (
          <div style={{ marginTop:16 }}>
            <SecBar icon="📅" title={t.agendaTitle2} />
            {(report.agenda||[]).map((day,di) => (
              <div key={di} style={{ marginBottom:14 }}>
                <div style={{ display:'flex', alignItems:'center', justifyContent:'space-between', background:'#1e3a6e', color:'white', padding:'10px 16px', borderRadius:'10px 10px 0 0' }}>
                  <span style={{ fontWeight:800, fontSize:13.5 }}>{day.day_label}</span>
                  {day.day_label_en && <span style={{ background:'#b8932a', padding:'2px 10px', borderRadius:10, fontSize:10.5, fontWeight:700 }}>{day.day_label_en}</span>}
                </div>
                <table style={{ width:'100%', borderCollapse:'collapse', fontSize:13, background:'white', borderRadius:'0 0 10px 10px', overflow:'hidden', border:'1px solid #e8edf4', borderTop:'none' }}>
                  <TblHead cols={[isAr?'الوقت':'Time', isAr?'النشاط':'Activity', isAr?'الموقع':'Location']} bg="#f0f4ff"/>
                  <tbody>
                    {(day.items||[]).map((item,ii) => (
                      <tr key={ii} style={rowStyle(ii)}>
                        <td style={{ padding:'10px 12px', fontWeight:800, color:'#1c3370', whiteSpace:'nowrap', fontSize:12, width:'12%' }}>{item.time}</td>
                        <td style={{ padding:'10px 12px', color:'#334155', lineHeight:1.5 }}>{item.activity}</td>
                        <td style={{ padding:'10px 12px', color:'#64748b', fontSize:12, width:'24%' }}>{item.location}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ))}
          </div>
        )}

        {/* ── Executive Summary ── */}
        {report.executive_summary && (
          <div style={{ marginTop:16 }}>
            <div style={{ background:'linear-gradient(135deg,#0d1e3d 0%,#1c3370 60%,#1e4a9a 100%)', padding:'11px 20px', borderRadius:'10px 10px 0 0', display:'flex', alignItems:'center', justifyContent:'space-between' }}>
              <span style={{ color:'white', fontWeight:800, fontSize:14 }}>{t.executiveSummaryTitle}</span>
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="rgba(255,255,255,0.7)" strokeWidth="2" strokeLinecap="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/></svg>
            </div>
            <div style={{ background:'white', border:'1px solid #e8edf4', borderTop:'none', borderRadius:'0 0 10px 10px', padding:'20px 22px', fontSize:13.5, color:'#334155', lineHeight:2, boxShadow:'0 1px 4px rgba(0,0,0,0.05)' }}>
              {report.executive_summary}
            </div>
          </div>
        )}

        {/* ── Conference Tracks ── */}
        {(report.conference_tracks||[]).length > 0 && (
          <div style={{ marginTop:16 }}>
            {/* Header bar with count badge */}
            <div style={{ background:'linear-gradient(135deg,#0d1e3d 0%,#1c3370 60%,#1e4a9a 100%)', padding:'11px 20px', borderRadius:10, display:'flex', alignItems:'center', justifyContent:'space-between' }}>
              <span style={{ color:'white', fontWeight:800, fontSize:14 }}>{t.conferenceTracksTitle}</span>
              <div style={{ display:'flex', alignItems:'center', gap:10 }}>
                <span style={{ background:'rgba(255,255,255,0.15)', color:'white', borderRadius:8, padding:'2px 10px', fontSize:12, fontWeight:700 }}>{report.conference_tracks.length}</span>
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="rgba(255,255,255,0.7)" strokeWidth="2"><rect x="3" y="3" width="7" height="7" rx="1"/><rect x="14" y="3" width="7" height="7" rx="1"/><rect x="3" y="14" width="7" height="7" rx="1"/><rect x="14" y="14" width="7" height="7" rx="1"/></svg>
              </div>
            </div>

            {/* 2-column grid — RTL: odd items right col, even left col */}
            <div style={{ background:'white', border:'1px solid #e8edf4', borderRadius:10, padding:'18px', marginTop:2, boxShadow:'0 1px 4px rgba(0,0,0,0.05)' }}>
              <div style={{ display:'grid', gridTemplateColumns:'1fr 1fr', gap:10 }}>
                {/* Right column: items 1,3,5,7... (index 0,2,4,6 = odd numbers) */}
                {[0,1].map(col => (
                  <div key={col} style={{ display:'flex', flexDirection:'column', gap:10 }}>
                    {report.conference_tracks
                      .map((track, i) => ({ track, i }))
                      .filter(({ i }) => isAr ? (i % 2 === col) : (i % 2 === col))
                      .map(({ track, i }) => (
                        <div key={i} style={{ display:'flex', alignItems:'flex-start', gap:12, background:'#f8fafc', border:'1px solid #e8edf4', borderRadius:10, padding:'11px 14px', direction:dir }}>
                          <div style={{ width:28, height:28, borderRadius:'50%', background:'#1c3370', color:'white', fontWeight:800, fontSize:12, textAlign:'center', lineHeight:'28px', flexShrink:0 }}>{i+1}</div>
                          <div style={{ flex:1 }}>
                            <div style={{ fontSize:13, color:'#334155', fontWeight:700, lineHeight:1.4 }}>
                              {typeof track === 'object' && track !== null ? (track.name || '—') : (track || '—')}
                            </div>
                            {typeof track === 'object' && track !== null && track.explanation && (
                              <div style={{ fontSize:11.5, color:'#64748b', marginTop:4, lineHeight:1.5 }}>{track.explanation}</div>
                            )}
                          </div>
                        </div>
                      ))
                    }
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* ── Ambassadors + Destination Map (side by side) ── */}
        <div style={{ display:'grid', gridTemplateColumns:'1fr 1fr', gap:16, marginTop:16 }}>

          {/* Key Ambassadors */}
          <div style={{ background:'white', border:'1px solid #e8edf4', borderRadius:14, overflow:'hidden', boxShadow:'0 1px 4px rgba(0,0,0,0.05)' }}>
            <div style={{ padding:'14px 18px', borderBottom:'1px solid #f1f5f9', display:'flex', alignItems:'center', justifyContent:'space-between', direction:dir }}>
              <span style={{ fontWeight:800, fontSize:14, color:'#0d1829' }}>{t.keyAmbassadorsTitle}</span>
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#94a3b8" strokeWidth="1.8" strokeLinecap="round"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/></svg>
            </div>
            <div style={{ padding:'18px' }}>
              {(report.key_ambassadors||[]).length > 0 ? (
                <div style={{ display:'flex', flexDirection:'column', gap:12 }}>
                  {(report.key_ambassadors||[]).map((amb, i) => (
                    <div key={i} style={{ display:'flex', alignItems:'flex-start', gap:12, padding:'12px', background:'#f8fafc', borderRadius:10, border:'1px solid #e8edf4', direction:dir }}>
                      <div style={{ width:40, height:40, borderRadius:'50%', background:'linear-gradient(135deg,#1c3370,#3b5bdb)', display:'flex', alignItems:'center', justifyContent:'center', color:'white', fontWeight:800, fontSize:15, flexShrink:0 }}>
                        {(amb.name||'?').charAt(0)}
                      </div>
                      <div style={{ flex:1, minWidth:0 }}>
                        <div style={{ fontWeight:800, fontSize:13.5, color:'#0d1829', marginBottom:2 }}>{amb.name}</div>
                        <div style={{ fontSize:12, color:'#64748b', marginBottom:4 }}>{amb.title}</div>
                        {amb.country && <span style={{ background:'#eff6ff', color:'#1c3370', borderRadius:6, padding:'2px 8px', fontSize:11, fontWeight:700 }}>🌍 {translateCountry(amb.country, lang)}</span>}
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div style={{ textAlign:'center', padding:'32px 20px', color:'#94a3b8' }}>
                  <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="#cbd5e1" strokeWidth="1.5" strokeLinecap="round" style={{ display:'block', margin:'0 auto 14px' }}>
                    <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/>
                    <path d="M23 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/>
                  </svg>
                  <div style={{ fontSize:13.5, fontWeight:700, color:'#64748b', marginBottom:6, fontFamily:font }}>
                    {t.noAmbassadors}
                  </div>
                  <div style={{ fontSize:12, color:'#94a3b8', lineHeight:1.6, fontFamily:font }}>
                    {isAr
                      ? 'استخدم استخراج الذكاء الاصطناعي من صفحة المتابعة لتحديد جهات الاتصال الرئيسية'
                      : 'Use AI extraction from the follow-up page to identify key contacts'}
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* Destination Map */}
          <div style={{ background:'white', border:'1px solid #e8edf4', borderRadius:14, overflow:'hidden', boxShadow:'0 1px 4px rgba(0,0,0,0.05)' }}>
            <div style={{ padding:'14px 18px', borderBottom:'1px solid #f1f5f9', display:'flex', alignItems:'center', justifyContent:'space-between', direction:dir }}>
              <div>
                <div style={{ display:'flex', alignItems:'center', gap:7, fontWeight:800, fontSize:14, color:'#0d1829' }}>
                  <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="#4a7adb" strokeWidth="2.2" strokeLinecap="round"><path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"/><circle cx="12" cy="10" r="3"/></svg>
                  {t.destinationMap}
                </div>
                <div style={{ fontSize:12, color:'#94a3b8', marginTop:3, fontFamily:"'DM Sans',sans-serif" }}>
                  {report.city}{report.country ? `، ${translateCountry(report.country, lang)}` : ''}
                </div>
              </div>
              <a href={`https://maps.google.com/?q=${encodeURIComponent((report.city||'')+', '+(report.country||''))}`}
                target="_blank" rel="noreferrer"
                style={{ display:'flex', alignItems:'center', gap:5, fontSize:12, color:'#2563eb', fontWeight:600, textDecoration:'none' }}>
                <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round"><path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"/><polyline points="15 3 21 3 21 9"/><line x1="10" y1="14" x2="21" y2="3"/></svg>
                {t.openGoogleMaps}
              </a>
            </div>
            <iframe
              title="destination-map"
              width="100%"
              height="260"
              style={{ border:'none', display:'block' }}
              loading="lazy"
              referrerPolicy="no-referrer-when-downgrade"
              src={`https://maps.google.com/maps?q=${encodeURIComponent((report.city||'')+', '+(report.country||''))}&output=embed&z=11`}
            />
          </div>
        </div>

        {/* ── Sessions ── */}
        {(['day1','day2','day3']).some(dk => sess[dk]?.length) && (
          <div style={{ marginTop:16 }}>
            <SecBar icon="📋" title={t.conferenceSessionsTitle} />
            {(['day1','day2','day3']).map((dk, di) => {
              const ds = sess[dk]; if (!ds?.length) return null;
              const lbl = (t.dayLabels || ['Day 1','Day 2','Day 3'])[di];
              return (
                <div key={dk} style={{ marginBottom:16 }}>
                  <div style={{ background:'#1e3a6e', color:'white', padding:'9px 16px', borderRadius:'10px 10px 0 0', fontWeight:800, fontSize:13.5 }}>{lbl}</div>
                  <div style={{ background:'white', border:'1px solid #e8edf4', borderTop:'none', borderRadius:'0 0 10px 10px', padding:'10px 14px' }}>
                    {ds.map((s,si) => (
                      <div key={si} style={{ borderInlineStart:'3px solid #1c3370', paddingInlineStart:14, paddingTop:10, paddingBottom:10, marginBottom:10, borderBottom: si<ds.length-1?'1px solid #f1f5f9':'none' }}>
                        <div style={{ fontSize:11, color:'#94a3b8', fontWeight:700, marginBottom:4 }}>🕐 {s.time}</div>
                        <div style={{ fontWeight:800, fontSize:13.5, color:'#1c3370', marginBottom:4, lineHeight:1.4 }}>{s.title}</div>
                        {s.speakers && <div style={{ fontSize:12, color:'#2563eb', marginBottom:4, fontWeight:600 }}>👤 {s.speakers}</div>}
                        {s.description && <div style={{ fontSize:12, color:'#64748b', lineHeight:1.55 }}>{s.description}</div>}
                      </div>
                    ))}
                  </div>
                </div>
              );
            })}
          </div>
        )}

        {/* ── Speakers ── */}
        {(report.speakers||[]).length > 0 && (
          <div style={{ marginTop:16 }}>
            {/* Header bar */}
            <div style={{ background:'linear-gradient(135deg,#0d1e3d 0%,#1c3370 60%,#1e4a9a 100%)', padding:'12px 20px', borderRadius:10, display:'flex', alignItems:'center', justifyContent:'space-between', direction:dir }}>
              <button style={{ display:'flex', alignItems:'center', gap:7, background:'rgba(255,255,255,0.12)', border:'1px solid rgba(255,255,255,0.2)', color:'white', borderRadius:8, padding:'6px 14px', fontSize:12.5, fontWeight:700, cursor:'pointer', fontFamily:font }}>
                <span style={{ fontSize:16 }}>+</span> {t.addSpeaker}
              </button>
              <div style={{ display:'flex', alignItems:'center', gap:10 }}>
                <span style={{ color:'white', fontWeight:900, fontSize:15 }}>{t.keySpeakersTitle}</span>
                <span style={{ background:'rgba(255,255,255,0.15)', color:'white', borderRadius:8, padding:'2px 10px', fontSize:12, fontWeight:700 }}>{report.speakers.length} {t.speakersSuffix}</span>
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="rgba(255,255,255,0.7)" strokeWidth="1.8" strokeLinecap="round"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/></svg>
              </div>
            </div>

            {/* 3-column photo cards */}
            <div style={{ display:'grid', gridTemplateColumns:'repeat(3,1fr)', gap:14, marginTop:14 }}>
              {(report.speakers||[]).map((s,i) => {
                const [g1,g2] = grad(s.name);
                const hasLinkedin = s.has_linkedin || s.linkedin_url;
                return (
                  <div key={i} style={{ background:'#f4f7fb', border:'1px solid #e8edf4', borderRadius:16, padding:'24px 20px 20px', textAlign:'center', position:'relative', boxShadow:'0 1px 4px rgba(0,0,0,0.05)', transition:'box-shadow 0.15s,transform 0.15s' }}
                    onMouseEnter={e => { e.currentTarget.style.boxShadow='0 6px 20px rgba(0,0,0,0.1)'; e.currentTarget.style.transform='translateY(-2px)'; }}
                    onMouseLeave={e => { e.currentTarget.style.boxShadow='0 1px 4px rgba(0,0,0,0.05)'; e.currentTarget.style.transform='none'; }}>

                    {/* LinkedIn badge */}
                    {hasLinkedin && (
                      <div style={{ position:'absolute', top:14, [isAr?'right':'left']:14, width:26, height:26, borderRadius:'50%', background:'#0a66c2', display:'flex', alignItems:'center', justifyContent:'center', boxShadow:'0 2px 6px rgba(10,102,194,0.4)' }}>
                        <svg width="13" height="13" viewBox="0 0 24 24" fill="white"><path d="M16 8a6 6 0 0 1 6 6v7h-4v-7a2 2 0 0 0-2-2 2 2 0 0 0-2 2v7h-4v-7a6 6 0 0 1 6-6z"/><rect x="2" y="9" width="4" height="12"/><circle cx="4" cy="4" r="2"/></svg>
                      </div>
                    )}

                    {/* Photo / Avatar */}
                    {s.photo_url ? (
                      <img src={s.photo_url} alt={s.name}
                        style={{ width:90, height:90, borderRadius:'50%', objectFit:'cover', border:'3px solid white', boxShadow:'0 2px 10px rgba(0,0,0,0.15)', marginBottom:14, display:'block', margin:'0 auto 14px' }}
                        onError={e => { e.target.style.display='none'; e.target.nextSibling.style.display='flex'; }}
                      />
                    ) : null}
                    <div style={{ width:90, height:90, borderRadius:'50%', background:`linear-gradient(135deg,${g1},${g2})`, display: s.photo_url ? 'none' : 'flex', alignItems:'center', justifyContent:'center', color:'white', fontWeight:900, fontSize:28, margin:'0 auto 14px', border:'3px solid white', boxShadow:'0 2px 10px rgba(0,0,0,0.15)' }}>
                      {initials(s.name)}
                    </div>

                    {/* Name */}
                    <div style={{ fontWeight:900, fontSize:15, color:'#0d1829', marginBottom:6, lineHeight:1.3, fontFamily:font }}>{s.name}</div>

                    {/* Title in blue */}
                    <div style={{ fontSize:12.5, color:'#2563eb', fontWeight:600, marginBottom: s.organization ? 4 : 0, lineHeight:1.4 }}>{s.title}</div>

                    {/* Organization */}
                    {s.organization && <div style={{ fontSize:12, color:'#94a3b8', fontWeight:500 }}>{s.organization}</div>}
                  </div>
                );
              })}
            </div>
          </div>
        )}

        {/* ── Participants (Expected) ── */}
        {(report.participants||[]).length > 0 && (
          <div style={{ marginTop:16 }}>
            {/* Header */}
            <div style={{ background:'linear-gradient(135deg,#0d1e3d 0%,#1c3370 60%,#1e4a9a 100%)', padding:'12px 20px', borderRadius:10, display:'flex', alignItems:'center', justifyContent:'space-between', direction:dir }}>
              <div style={{ display:'flex', alignItems:'center', gap:10 }}>
                <span style={{ color:'white', fontWeight:900, fontSize:15 }}>{t.expectedParticipantsTitle}</span>
                <span style={{ background:'rgba(255,255,255,0.15)', color:'white', borderRadius:8, padding:'2px 10px', fontSize:12, fontWeight:700 }}>{report.participants.length}</span>
              </div>
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="rgba(255,255,255,0.7)" strokeWidth="1.8" strokeLinecap="round"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/></svg>
            </div>

            {/* 5-column cards */}
            <div style={{ display:'grid', gridTemplateColumns:'repeat(5,1fr)', gap:12, marginTop:14 }}>
              {(report.participants||[]).map((p,i) => {
                const [g1,g2] = grad(p.name);
                return (
                  <div key={i} style={{ background:'white', border:'1px solid #e8edf4', borderRadius:14, padding:'18px 12px 14px', textAlign:'center', boxShadow:'0 1px 3px rgba(0,0,0,0.05)', transition:'box-shadow 0.15s,transform 0.15s' }}
                    onMouseEnter={e => { e.currentTarget.style.boxShadow='0 4px 16px rgba(0,0,0,0.09)'; e.currentTarget.style.transform='translateY(-2px)'; }}
                    onMouseLeave={e => { e.currentTarget.style.boxShadow='0 1px 3px rgba(0,0,0,0.05)'; e.currentTarget.style.transform='none'; }}>

                    {/* Avatar */}
                    {p.photo_url ? (
                      <img src={p.photo_url} alt={p.name}
                        style={{ width:64, height:64, borderRadius:'50%', objectFit:'cover', border:'2px solid #e8edf4', margin:'0 auto 10px', display:'block' }}
                        onError={e => { e.target.style.display='none'; e.target.nextSibling.style.display='flex'; }}
                      />
                    ) : null}
                    <div style={{ width:64, height:64, borderRadius:'50%', background:`linear-gradient(135deg,${g1},${g2})`, display: p.photo_url ? 'none' : 'flex', alignItems:'center', justifyContent:'center', color:'white', fontWeight:800, fontSize:20, margin:'0 auto 10px', border:'2px solid #e8edf4' }}>
                      {initials(p.name)}
                    </div>

                    <div style={{ fontWeight:800, fontSize:12.5, color:'#0d1829', marginBottom:4, lineHeight:1.3, fontFamily:font }}>{p.name}</div>
                    <div style={{ fontSize:11, color:'#2563eb', fontWeight:600, marginBottom:2, lineHeight:1.4 }}>{p.title}</div>
                    {p.organization && <div style={{ fontSize:10.5, color:'#94a3b8', marginBottom: p.country ? 8 : 0 }}>{p.organization}</div>}

                    {/* Country pill */}
                    {p.country && (
                      <div style={{ marginTop:8 }}>
                        <span style={{ background:'#f1f5f9', color:'#475569', borderRadius:20, padding:'3px 10px', fontSize:10.5, fontWeight:600 }}>{translateCountry(p.country, lang)}</span>
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          </div>
        )}

        {/* ── Bilateral Meetings ── */}
        {(report.bilateral_meetings||[]).length > 0 && (
          <div style={{ marginTop:16 }}>
            <SecBar icon="🤝" title={t.bilateralMeetingsTitle} />
            {(report.bilateral_meetings||[]).map((m,i) => (
              <div key={i} style={{ border:'1px solid #e2e8f0', borderRadius:14, overflow:'hidden', marginBottom:14 }}>
                <div style={{ background:'linear-gradient(135deg,#1c3370,#1e40af)', padding:'13px 20px' }}>
                  <div style={{ color:'rgba(255,255,255,0.55)', fontSize:11, fontWeight:700, marginBottom:4 }}>{t.officialMeetingLabel}</div>
                  <div style={{ color:'white', fontWeight:800, fontSize:15 }}>🤝 {m.entity}</div>
                </div>
                <div style={{ padding:'16px 20px', background:'white' }}>
                  <div style={{ display:'grid', gridTemplateColumns:'repeat(3,1fr)', gap:10, marginBottom:14 }}>
                    {[[t.officialLabel, m.counterpart],[t.jobTitleLabel2, m.counterpart_title],[t.dateTimeLabel, `${m.date||''} ${m.time||''}`]].map(([l,v]) => (
                      <div key={l} style={{ background:'#f8fafc', borderRadius:9, padding:'10px 12px', textAlign:'center', border:'1px solid #e8edf4' }}>
                        <div style={{ fontSize:10, color:'#94a3b8', fontWeight:700, marginBottom:4, textTransform:'uppercase' }}>{l}</div>
                        <div style={{ fontSize:12.5, fontWeight:700, color:'#1e293b', lineHeight:1.35 }}>{v||'—'}</div>
                      </div>
                    ))}
                  </div>
                  {(m.talking_points||[]).length > 0 && (
                    <>
                      <div style={{ fontWeight:700, fontSize:13, color:'#1c3370', marginBottom:10 }}>📌 {isAr?'نقاط النقاش':'Talking Points'}</div>
                      {(m.talking_points||[]).map((pt,pi) => (
                        <div key={pi} style={{ display:'flex', gap:10, marginBottom:8, alignItems:'flex-start' }}>
                          <div style={{ width:22, height:22, borderRadius:7, background:'#22c55e', color:'white', fontSize:10, fontWeight:800, textAlign:'center', lineHeight:'22px', flexShrink:0 }}>{pi+1}</div>
                          <span style={{ fontSize:12.5, color:'#334155', lineHeight:1.55, flex:1 }}>{pt}</span>
                        </div>
                      ))}
                    </>
                  )}
                  {m.location && <div style={{ marginTop:10, fontSize:12, color:'#64748b' }}>📍 {m.location}</div>}
                </div>
              </div>
            ))}
          </div>
        )}

        {/* ── Suggested Meetings ── */}
        {(report.suggested_meetings||[]).length > 0 && (
          <div style={{ marginTop:16 }}>
            {/* Header */}
            <div style={{ background:'linear-gradient(135deg,#0d1e3d 0%,#1c3370 60%,#1e4a9a 100%)', padding:'12px 20px', borderRadius:10, display:'flex', alignItems:'center', justifyContent:'space-between', direction:dir }}>
              <div style={{ display:'flex', alignItems:'center', gap:10 }}>
                <span style={{ color:'white', fontWeight:900, fontSize:15 }}>{t.suggestedMeetingsTitle}</span>
                <span style={{ background:'rgba(255,255,255,0.15)', color:'white', borderRadius:8, padding:'2px 10px', fontSize:12, fontWeight:700 }}>{report.suggested_meetings.length}</span>
              </div>
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="rgba(255,255,255,0.7)" strokeWidth="1.8" strokeLinecap="round"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>
            </div>

            {/* Colored border rows */}
            <div style={{ display:'flex', flexDirection:'column', gap:10, marginTop:12 }}>
              {(report.suggested_meetings||[]).map((m,i) => {
                const priority = (m.priority||'low').toLowerCase();
                const isHigh   = priority === 'high';
                const isMed    = priority === 'medium' || priority === 'متوسطة';
                const dotColor  = isHigh ? '#ef4444' : isMed ? '#f59e0b' : '#94a3b8';
                const bgColor   = isHigh ? '#fff5f5' : isMed ? '#fffbeb' : '#f8fafc';
                const borderClr = isHigh ? '#fecaca' : isMed ? '#fde68a' : '#e2e8f0';
                const badgeBg   = isHigh ? '#fee2e2' : isMed ? '#fef9c3' : '#f1f5f9';
                const badgeClr  = isHigh ? '#dc2626' : isMed ? '#b45309' : '#64748b';
                const badgeTxt  = isHigh ? t.priorityHigh : isMed ? t.priorityMedium : t.priorityLow;

                return (
                  <div key={i} style={{ background:bgColor, border:`1px solid ${borderClr}`, borderRadius:12, padding:'14px 18px', direction:dir }}>
                    {/* Top row: dot + entity name + priority badge */}
                    <div style={{ display:'flex', alignItems:'center', gap:10, marginBottom:6, justifyContent:'space-between' }}>
                      <div style={{ display:'flex', alignItems:'center', gap:8 }}>
                        <span style={{ width:9, height:9, borderRadius:'50%', background:dotColor, display:'inline-block', flexShrink:0 }}/>
                        <span style={{ fontWeight:800, fontSize:14, color:'#0d1829', fontFamily:font }}>{m.entity}</span>
                      </div>
                      <span style={{ background:badgeBg, color:badgeClr, border:`1px solid ${borderClr}`, borderRadius:20, padding:'3px 12px', fontSize:11.5, fontWeight:700, whiteSpace:'nowrap', fontFamily:font }}>
                        {badgeTxt}
                      </span>
                    </div>

                    {/* Country */}
                    {m.country && (
                      <div style={{ fontSize:12.5, color:'#2563eb', fontWeight:600, marginBottom:6, marginInlineStart:17 }}>
                        {translateCountry(m.country, lang)}
                      </div>
                    )}

                    {/* Description */}
                    {m.description && (
                      <div style={{ fontSize:13, color:'#475569', lineHeight:1.65, marginInlineStart:17, fontFamily:font }}>
                        {m.description}
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          </div>
        )}

        {/* ── Embassy + Weather side-by-side ── */}
        {(report.embassy?.name || (report.weather||[]).length > 0) && (
          <div style={{ display:'grid', gridTemplateColumns:'1fr 1fr', gap:16, marginTop:16 }}>

            {/* Embassy card */}
            <div style={{ background:'white', border:'1px solid #e8edf4', borderRadius:14, overflow:'hidden', boxShadow:'0 1px 4px rgba(0,0,0,0.05)' }}>
              <div style={{ background:'linear-gradient(135deg,#0d1e3d 0%,#1c3370 60%,#1e4a9a 100%)', padding:'12px 20px', display:'flex', alignItems:'center', justifyContent:'space-between', direction:dir }}>
                <span style={{ color:'white', fontWeight:900, fontSize:14 }}>{t.saudiEmbassyTitle}</span>
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="rgba(255,255,255,0.7)" strokeWidth="1.8" strokeLinecap="round"><rect x="2" y="7" width="20" height="14" rx="2"/><path d="M16 21V5a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v16"/></svg>
              </div>
              <div style={{ padding:'18px 20px' }}>
                {/* Embassy name */}
                {report.embassy?.name && <div style={{ fontWeight:800, fontSize:15, color:'#0d1829', marginBottom:14 }}>{report.embassy.name}</div>}

                {/* Mission box */}
                {report.embassy?.mission && (
                  <div style={{ background:'#f8fafc', border:'1px solid #e8edf4', borderRadius:10, padding:'10px 14px', marginBottom:14, direction:dir }}>
                    <div style={{ display:'flex', alignItems:'center', gap:6, fontSize:11, color:'#94a3b8', fontWeight:700, marginBottom:5 }}>
                      <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><rect x="2" y="7" width="20" height="14" rx="2"/><path d="M16 21V5a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v16"/></svg>
                      {t.embassyBuilding}
                    </div>
                    <div style={{ fontSize:12.5, color:'#475569', lineHeight:1.6 }}>{report.embassy.mission}</div>
                    {report.embassy?.ppt_note && (
                      <div style={{ marginTop:8, display:'flex', alignItems:'center', gap:5, fontSize:11, color:'#94a3b8' }}>
                        <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><rect x="2" y="3" width="20" height="14" rx="2"/><line x1="8" y1="21" x2="16" y2="21"/><line x1="12" y1="17" x2="12" y2="21"/></svg>
                        {report.embassy.ppt_note}
                      </div>
                    )}
                  </div>
                )}

                {/* Ambassador */}
                {report.embassy?.ambassador_name && (
                  <div style={{ display:'flex', alignItems:'center', gap:10, background:'#f8fafc', borderRadius:10, padding:'10px 14px', marginBottom:14, border:'1px solid #e8edf4' }}>
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#1c3370" strokeWidth="2" strokeLinecap="round"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>
                    <div>
                      <div style={{ fontWeight:800, fontSize:13.5, color:'#0d1829' }}>{report.embassy.ambassador_name}</div>
                      {report.embassy.ambassador_title && <div style={{ fontSize:11.5, color:'#64748b', marginTop:2 }}>{report.embassy.ambassador_title}</div>}
                    </div>
                  </div>
                )}

                {/* Contact rows */}
                {[
                  report.embassy?.address && { icon:'📍', val: report.embassy.address, isAddr:true },
                  report.embassy?.phone   && { icon:'📞', val: report.embassy.phone },
                  report.embassy?.fax     && { icon:'🖨️', val: report.embassy.fax },
                  report.embassy?.email   && { icon:'✉️', val: report.embassy.email },
                  report.embassy?.website && { icon:'🌐', val: report.embassy.website, isLink:true },
                ].filter(Boolean).map((row, i) => (
                  <div key={i} style={{ display:'flex', alignItems:'flex-start', gap:10, padding:'7px 0', borderTop: i===0 ? '1px solid #f1f5f9' : 'none' }}>
                    <span style={{ fontSize:14, flexShrink:0, marginTop:1 }}>{row.icon}</span>
                    {row.isLink
                      ? <a href={row.val} target="_blank" rel="noreferrer" style={{ fontSize:12.5, color:'#2563eb', wordBreak:'break-all', textDecoration:'none', fontFamily:"'DM Sans',sans-serif" }}>{row.val}</a>
                      : <span style={{ fontSize:12.5, color:'#475569', fontFamily:"'DM Sans',sans-serif", lineHeight:1.5 }}>{row.val}</span>
                    }
                  </div>
                ))}
              </div>
            </div>

            {/* Weather card */}
            {(report.weather||[]).length > 0 && (
              <div style={{ background:'white', border:'1px solid #e8edf4', borderRadius:14, overflow:'hidden', boxShadow:'0 1px 4px rgba(0,0,0,0.05)' }}>
                <div style={{ background:'linear-gradient(135deg,#0d1e3d 0%,#1c3370 60%,#1e4a9a 100%)', padding:'12px 20px', display:'flex', alignItems:'center', justifyContent:'space-between', direction:dir }}>
                  <span style={{ color:'white', fontWeight:900, fontSize:14 }}>{t.weatherForecastTitle}</span>
                  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="rgba(255,255,255,0.7)" strokeWidth="1.8" strokeLinecap="round"><path d="M23 19a9 9 0 1 1-17.95-1"/><polyline points="17.73 14.73 17 17 15 17"/><circle cx="17" cy="19" r="3" strokeWidth="1.5"/></svg>
                </div>
                <div style={{ padding:'18px 20px' }}>
                  {/* Weather summary text */}
                  {report.weather[0] && (
                    <div style={{ fontSize:13, color:'#475569', lineHeight:1.7, marginBottom:16 }}>
                      {isAr
                        ? `من المتوقع أن يكون الطقس في ${report.city} خلال الفترة من ${report.weather[0].date} إلى ${report.weather[report.weather.length-1]?.date} ${report.weather[0].condition} بشكل عام، وهو مثالي للأنشطة الخارجية والداخلية.`
                        : `Weather in ${report.city} is expected to be ${report.weather[0].condition} throughout the event period.`
                      }
                    </div>
                  )}

                  {/* Today's highlights */}
                  {report.weather[0] && (
                    <div style={{ display:'grid', gridTemplateColumns:'1fr 1fr', gap:10, marginBottom:14 }}>
                      <div style={{ background:'#f8fafc', borderRadius:10, padding:'12px 14px', border:'1px solid #e8edf4' }}>
                        <div style={{ display:'flex', alignItems:'center', gap:5, fontSize:11, color:'#94a3b8', fontWeight:700, marginBottom:6 }}>
                          <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><circle cx="12" cy="12" r="5"/><line x1="12" y1="1" x2="12" y2="3"/><line x1="12" y1="21" x2="12" y2="23"/><line x1="4.22" y1="4.22" x2="5.64" y2="5.64"/><line x1="18.36" y1="18.36" x2="19.78" y2="19.78"/><line x1="1" y1="12" x2="3" y2="12"/><line x1="21" y1="12" x2="23" y2="12"/></svg>
                          {t.temperature}
                        </div>
                        <div style={{ fontWeight:800, fontSize:15, color:'#0d1829' }}>{report.weather[0].high}°C / {report.weather[0].low}°C</div>
                      </div>
                      <div style={{ background:'#f8fafc', borderRadius:10, padding:'12px 14px', border:'1px solid #e8edf4' }}>
                        <div style={{ display:'flex', alignItems:'center', gap:5, fontSize:11, color:'#94a3b8', fontWeight:700, marginBottom:6 }}>
                          <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M12 2v6m0 14v-6m-7-7H2m20 0h-3M5.93 5.93l-1.41-1.41M19.07 5.93l1.41-1.41"/></svg>
                          {t.humidity2}
                        </div>
                        <div style={{ fontWeight:800, fontSize:15, color:'#0d1829' }}>{report.weather[0].humidity}</div>
                      </div>
                      <div style={{ background:'#f8fafc', borderRadius:10, padding:'12px 14px', border:'1px solid #e8edf4', display:'flex', alignItems:'flex-start', gap:5 }}>
                        <div style={{ fontSize:11, color:'#94a3b8', fontWeight:700, marginBottom:6 }}>{t.condition}</div>
                        <div style={{ fontWeight:700, fontSize:13.5, color:'#0d1829' }}>{wIcon(report.weather[0].condition)} {report.weather[0].condition}</div>
                      </div>
                      <div style={{ background:'#f8fafc', borderRadius:10, padding:'12px 14px', border:'1px solid #e8edf4' }}>
                        <div style={{ fontSize:11, color:'#94a3b8', fontWeight:700, marginBottom:6 }}>{t.wind2}</div>
                        <div style={{ fontWeight:700, fontSize:13, color:'#0d1829' }}>💨 {report.weather[0].wind}</div>
                      </div>
                    </div>
                  )}

                  {/* Recommendations */}
                  <div style={{ background:'#f8fafc', borderRadius:10, padding:'12px 14px', border:'1px solid #e8edf4' }}>
                    <div style={{ fontSize:11, color:'#94a3b8', fontWeight:700, marginBottom:8 }}>{t.weatherTipsTitle}</div>
                    {[
                      t.weatherTips[0],
                      t.weatherTips[1],
                      t.weatherTips[2],
                      t.weatherTips[3],
                    ].map((tip, i) => (
                      <div key={i} style={{ display:'flex', alignItems:'flex-start', gap:8, marginBottom:5 }}>
                        <span style={{ color:'#1c3370', fontWeight:800, fontSize:12, flexShrink:0, marginTop:2 }}>•</span>
                        <span style={{ fontSize:12.5, color:'#475569', lineHeight:1.55 }}>{tip}</span>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            )}
          </div>
        )}

        {/* ── Consulate info (below, full-width) ── */}
        {report.consulate?.name && (
          <div style={{ marginTop:16 }}>
            <div style={{ background:'linear-gradient(135deg,#0d1e3d 0%,#1c3370 60%,#1e4a9a 100%)', padding:'12px 20px', borderRadius:10, display:'flex', alignItems:'center', justifyContent:'space-between', direction:dir }}>
              <span style={{ color:'white', fontWeight:900, fontSize:14 }}>{t.consulateInfoTitle}</span>
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="rgba(255,255,255,0.7)" strokeWidth="1.8" strokeLinecap="round"><path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"/><circle cx="12" cy="10" r="3"/></svg>
            </div>
            <div style={{ background:'white', border:'1px solid #e8edf4', borderRadius:'0 0 14px 14px', padding:'18px 22px', boxShadow:'0 1px 4px rgba(0,0,0,0.05)' }}>
              {/* Consulate name */}
              <div style={{ fontWeight:800, fontSize:15, color:'#0d1829', marginBottom:14, direction:dir }}>{report.consulate.name}</div>

              {/* Consul officer */}
              {report.consulate.consul_name && (
                <div style={{ display:'flex', alignItems:'center', gap:10, background:'#f8fafc', borderRadius:10, padding:'10px 14px', marginBottom:14, border:'1px solid #e8edf4', direction:dir }}>
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#1c3370" strokeWidth="2" strokeLinecap="round"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>
                  <div>
                    <div style={{ fontWeight:800, fontSize:13.5, color:'#0d1829' }}>{t.honorificPrefix}{report.consulate.consul_name}</div>
                    {report.consulate.consul_title && <div style={{ fontSize:11.5, color:'#64748b', marginTop:2 }}>{report.consulate.consul_title}</div>}
                  </div>
                </div>
              )}

              {/* Contact grid */}
              <div style={{ display:'flex', flexDirection:'column', gap:8, direction:dir }}>
                {[
                  report.consulate.address        && { icon:'📍', val: report.consulate.address },
                  report.consulate.phone          && { icon:'📞', val: report.consulate.phone },
                  report.consulate.email          && { icon:'✉️', val: report.consulate.email },
                  report.consulate.working_hours  && { icon:'🕐', val: report.consulate.working_hours },
                  report.consulate.emergency_phone && { icon:'🚨', val: report.consulate.emergency_phone },
                ].filter(Boolean).map((row, i) => (
                  <div key={i} style={{ display:'flex', alignItems:'flex-start', gap:10, padding:'8px 0', borderTop: i > 0 ? '1px solid #f1f5f9' : 'none' }}>
                    <span style={{ fontSize:14, flexShrink:0, marginTop:1 }}>{row.icon}</span>
                    <span style={{ fontSize:12.5, color:'#475569', fontFamily:"'DM Sans',sans-serif", lineHeight:1.5 }}>{row.val}</span>
                  </div>
                ))}
                {report.consulate.website && (
                  <div style={{ display:'flex', alignItems:'flex-start', gap:10, padding:'8px 0', borderTop:'1px solid #f1f5f9' }}>
                    <span style={{ fontSize:14, flexShrink:0 }}>🌐</span>
                    <a href={report.consulate.website} target="_blank" rel="noreferrer"
                      style={{ fontSize:12.5, color:'#2563eb', wordBreak:'break-all', textDecoration:'none', fontFamily:"'DM Sans',sans-serif" }}>
                      {report.consulate.website}
                    </a>
                  </div>
                )}
              </div>
            </div>
          </div>
        )}

        {/* ── SFDA Talking Points (AI-generated) ── */}
        {(report.sfda_talking_points||[]).length > 0 && (
          <div style={{ marginTop:16 }}>
            <div style={{ background:'linear-gradient(135deg,#0d1e3d 0%,#1c3370 60%,#1e4a9a 100%)', padding:'12px 20px', borderRadius:10, display:'flex', alignItems:'center', justifyContent:'space-between', direction:dir }}>
              <span style={{ color:'white', fontWeight:900, fontSize:14 }}>{t.talkingPointsAITitle}</span>
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="rgba(255,255,255,0.7)" strokeWidth="1.8" strokeLinecap="round"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/></svg>
            </div>
            <div style={{ background:'white', border:'1px solid #e8edf4', borderRadius:'0 0 14px 14px', padding:'18px 22px', boxShadow:'0 1px 4px rgba(0,0,0,0.05)' }}>
              <ol style={{ margin:0, padding:0, listStyle:'none' }}>
                {(report.sfda_talking_points||[]).map((pt, i) => (
                  <li key={i} style={{ display:'flex', alignItems:'flex-start', gap:14, padding:'9px 0', borderBottom: i < report.sfda_talking_points.length-1 ? '1px solid #f1f5f9' : 'none', direction:dir }}>
                    <span style={{ fontWeight:800, fontSize:14, color:'#1c3370', flexShrink:0, minWidth:20, marginTop:1 }}>{i+1}.</span>
                    <span style={{ fontSize:13.5, color:'#334155', lineHeight:1.7 }}>{pt}</span>
                  </li>
                ))}
              </ol>
            </div>
          </div>
        )}

        {/* ── Today's Prayer Times summary ── */}
        {(report.prayer_times||[]).length > 0 && (() => {
          const today = report.prayer_times[0];
          return (
            <div style={{ marginTop:16 }}>
              <div style={{ background:'linear-gradient(135deg,#0d1e3d 0%,#1c3370 60%,#1e4a9a 100%)', padding:'12px 20px', borderRadius:10, display:'flex', alignItems:'center', justifyContent:'space-between', direction:dir }}>
                <span style={{ color:'white', fontWeight:900, fontSize:14 }}>{t.prayerTimesTitle2} ({report.city})</span>
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="rgba(255,255,255,0.7)" strokeWidth="1.8" strokeLinecap="round"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>
              </div>
              <div style={{ background:'white', border:'1px solid #e8edf4', borderRadius:'0 0 14px 14px', padding:'18px 22px', boxShadow:'0 1px 4px rgba(0,0,0,0.05)' }}>
                <div style={{ display:'grid', gridTemplateColumns:'repeat(3,1fr)', gap:10, direction:dir }}>
                  {[
                    ['الفجر', 'Fajr',    today.fajr],
                    ['الظهر', 'Dhuhr',   today.dhuhr],
                    ['العصر', 'Asr',     today.asr],
                    ['المغرب','Maghrib',  today.maghrib],
                    ['العشاء','Isha',    today.isha],
                  ].map(([ar, en, val]) => val && (
                    <div key={ar} style={{ display:'flex', alignItems:'center', justifyContent:'space-between', padding:'10px 14px', background:'#f8fafc', borderRadius:10, border:'1px solid #e8edf4', direction:dir }}>
                      <span style={{ fontSize:13.5, color:'#334155', fontWeight:700 }}>{isAr ? ar : en}</span>
                      <span style={{ fontSize:14, fontWeight:900, color:'#1c3370', fontFamily:"'DM Sans',sans-serif" }}>{val}</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          );
        })()}

        {/* ── Daily Prayer Times table ── */}
        {(report.prayer_times||[]).length > 0 && (
          <div style={{ marginTop:16 }}>
            <div style={{ background:'linear-gradient(135deg,#0d1e3d 0%,#1c3370 60%,#1e4a9a 100%)', padding:'12px 20px', borderRadius:10, display:'flex', alignItems:'center', justifyContent:'space-between', direction:dir }}>
              <div>
                <div style={{ color:'white', fontWeight:900, fontSize:14 }}>{t.prayerDailySchedule}</div>
                <div style={{ color:'rgba(255,255,255,0.6)', fontSize:11.5, marginTop:2 }}>{report.city}</div>
              </div>
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="rgba(255,255,255,0.7)" strokeWidth="1.8" strokeLinecap="round"><path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/></svg>
            </div>
            <div style={{ background:'white', border:'1px solid #e8edf4', borderRadius:'0 0 14px 14px', overflow:'hidden', boxShadow:'0 1px 4px rgba(0,0,0,0.05)' }}>
              <table style={{ width:'100%', borderCollapse:'collapse', fontSize:13, direction:dir }}>
                <thead>
                  <tr style={{ background:'#f8fafc' }}>
                    {['Date','الفجر','الشروق','الظهر','العصر','المغرب','العشاء'].map(h => (
                      <th key={h} style={{ padding:'11px 14px', fontWeight:700, color: h==='Date'?'#2563eb':'#334155', fontSize:12.5, textAlign:'center', borderBottom:'2px solid #e8edf4' }}>{h}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {(report.prayer_times||[]).map((pt, i) => (
                    <tr key={i} style={{ background: i%2===0?'white':'#f8fafc', borderBottom:'1px solid #f1f5f9' }}>
                      <td style={{ padding:'10px 14px', fontWeight:700, color:'#1c3370', textAlign:'center', fontFamily:"'DM Sans',sans-serif" }}>{pt.date}</td>
                      <td style={{ padding:'10px 14px', fontWeight:600, color:'#334155', textAlign:'center', fontFamily:"'DM Sans',sans-serif" }}>{pt.fajr}</td>
                      <td style={{ padding:'10px 14px', fontWeight:600, color:'#334155', textAlign:'center', fontFamily:"'DM Sans',sans-serif" }}>{pt.shuruq || pt.sunrise || '—'}</td>
                      <td style={{ padding:'10px 14px', fontWeight:600, color:'#334155', textAlign:'center', fontFamily:"'DM Sans',sans-serif" }}>{pt.dhuhr}</td>
                      <td style={{ padding:'10px 14px', fontWeight:600, color:'#334155', textAlign:'center', fontFamily:"'DM Sans',sans-serif" }}>{pt.asr}</td>
                      <td style={{ padding:'10px 14px', fontWeight:600, color:'#334155', textAlign:'center', fontFamily:"'DM Sans',sans-serif" }}>{pt.maghrib}</td>
                      <td style={{ padding:'10px 14px', fontWeight:600, color:'#334155', textAlign:'center', fontFamily:"'DM Sans',sans-serif" }}>{pt.isha}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* ── Previous Outcomes ── */}
        {(report.previous_outcomes||[]).length > 0 && (
          <div style={{ marginTop:16 }}>
            <SecBar icon="📈" title={t.previousOutcomesTitle} />
            {(report.previous_outcomes||[]).map((o,i) => (
              <div key={i} style={{ borderInlineStart:'4px solid #1c3370', background:'white', borderRadius:'0 12px 12px 0', padding:'14px 18px', marginBottom:12, border:'1px solid #e8edf4', boxShadow:'0 1px 3px rgba(0,0,0,0.04)' }}>
                <div style={{ fontWeight:800, fontSize:14, color:'#1c3370', marginBottom:6 }}>{isAr?'دورة':'Edition'} {o.year}</div>
                <div style={{ fontSize:13, color:'#475569', lineHeight:1.7 }}>{o.summary}</div>
              </div>
            ))}
          </div>
        )}

        {/* Footer */}
        <div style={{ marginTop:32, textAlign:'center', padding:'16px', background:'white', borderRadius:12, border:'1px solid #e8edf4' }}>
          <div style={{ fontSize:11.5, color:'#94a3b8' }}>{t.footer}</div>
          <div style={{ fontSize:10.5, color:'#cbd5e1', marginTop:4 }}>SFDA · {new Date().getFullYear()}</div>
        </div>

      </div>
    </div>
  );
}
