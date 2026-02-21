import { useState, useRef } from 'react';
import { createReport, generateAI, getPDFUrl, getPreviewUrl } from '../services/api';

const COUNTRIES = [
  { en:'United States',   ar:'الولايات المتحدة الأمريكية' },
  { en:'United Kingdom',  ar:'المملكة المتحدة' },
  { en:'Germany',         ar:'ألمانيا' },
  { en:'France',          ar:'فرنسا' },
  { en:'Italy',           ar:'إيطاليا' },
  { en:'Spain',           ar:'إسبانيا' },
  { en:'Japan',           ar:'اليابان' },
  { en:'China',           ar:'الصين' },
  { en:'South Korea',     ar:'كوريا الجنوبية' },
  { en:'India',           ar:'الهند' },
  { en:'Singapore',       ar:'سنغافورة' },
  { en:'Australia',       ar:'أستراليا' },
  { en:'Canada',          ar:'كندا' },
  { en:'Brazil',          ar:'البرازيل' },
  { en:'Mexico',          ar:'المكسيك' },
  { en:'Netherlands',     ar:'هولندا' },
  { en:'Switzerland',     ar:'سويسرا' },
  { en:'Sweden',          ar:'السويد' },
  { en:'Norway',          ar:'النرويج' },
  { en:'Denmark',         ar:'الدنمارك' },
  { en:'Belgium',         ar:'بلجيكا' },
  { en:'Austria',         ar:'النمسا' },
  { en:'Finland',         ar:'فنلندا' },
  { en:'Portugal',        ar:'البرتغال' },
  { en:'Greece',          ar:'اليونان' },
  { en:'Poland',          ar:'بولندا' },
  { en:'Turkey',          ar:'تركيا' },
  { en:'Russia',          ar:'روسيا' },
  { en:'Ukraine',         ar:'أوكرانيا' },
  { en:'Egypt',           ar:'مصر' },
  { en:'Saudi Arabia',    ar:'المملكة العربية السعودية' },
  { en:'UAE',             ar:'الإمارات العربية المتحدة' },
  { en:'Kuwait',          ar:'الكويت' },
  { en:'Qatar',           ar:'قطر' },
  { en:'Bahrain',         ar:'البحرين' },
  { en:'Oman',            ar:'عُمان' },
  { en:'Jordan',          ar:'الأردن' },
  { en:'Lebanon',         ar:'لبنان' },
  { en:'Iraq',            ar:'العراق' },
  { en:'Morocco',         ar:'المغرب' },
  { en:'Tunisia',         ar:'تونس' },
  { en:'Algeria',         ar:'الجزائر' },
  { en:'South Africa',    ar:'جنوب أفريقيا' },
  { en:'Nigeria',         ar:'نيجيريا' },
  { en:'Kenya',           ar:'كينيا' },
  { en:'Ethiopia',        ar:'إثيوبيا' },
  { en:'Pakistan',        ar:'باكستان' },
  { en:'Malaysia',        ar:'ماليزيا' },
  { en:'Thailand',        ar:'تايلاند' },
  { en:'Indonesia',       ar:'إندونيسيا' },
  { en:'Vietnam',         ar:'فيتنام' },
  { en:'Philippines',     ar:'الفلبين' },
  { en:'Taiwan',          ar:'تايوان' },
  { en:'Hong Kong',       ar:'هونغ كونغ' },
  { en:'New Zealand',     ar:'نيوزيلندا' },
  { en:'Argentina',       ar:'الأرجنتين' },
  { en:'Colombia',        ar:'كولومبيا' },
  { en:'Chile',           ar:'تشيلي' },
];

const EVENT_TYPES_EN = ['Conference','Summit','Exhibition','Forum','Workshop','Bilateral Meeting','Scientific Congress','Trade Show'];
const EVENT_TYPES_AR = ['مؤتمر','قمة','معرض','منتدى','ورشة عمل','اجتماع ثنائي','مؤتمر علمي','معرض تجاري'];

const L = {
  en: {
    pageTitle:'Create New Report', pageSubtitle:'AI will generate a complete travel intelligence briefing',
    eventDetails:'Event Details', eventName:'Event Name', eventNamePH:'e.g., Milken Institute Global Conference 2026',
    reportTitle:'Report Title', reportTitlePH:'e.g., Global Conference 2026 Briefing',
    eventType:'Event Type', reportLang:'Report Language', langEn:'English', langAr:'Arabic',
    eventWebsite:'Event Website', websitePH:'https://event-website.com',
    location:'Location', city:'City', cityPH:'e.g., Los Angeles',
    country:'Country', countryPH:'Select country',
    venue:'Venue', venuePH:'e.g., Beverly Hilton',
    dates:'Event Dates', startDate:'Start Date', endDate:'End Date',
    traveler:'Traveler Details', travelerName:'Traveler Name', travelerTitle:'Title',
    context:'Additional Context', contextBadge:'OPTIONAL', contextPH:'Add any context, objectives, or requirements...',
    cancel:'Cancel', generate:'Generate AI Report', generating:'Creating...',
    genTitle:'Generating Your Report', genSubtitle:'AI is compiling a complete intelligence briefing...',
    doneTitle:'Report Generated!', viewPDF:'📄 View PDF', previewHTML:'👁️ Preview HTML', backDash:'← Back to Dashboard',
    sectionsGen:'Sections Generated:',
    required:'Please fill in: Event Name, City, Country, and Start Date.',
    genSteps:['Analyzing destination risk profile...','Collecting geopolitical intelligence...','Reviewing WHO health advisories...','Generating conference details...','Building delegation and agenda...','Compiling speakers and bilateral meetings...','Adding consulate, weather & prayer times...','Finalizing report structure...'],
    sections:[['🎯','Visit Objectives'],['📅','Agenda Days'],['👥','Delegation Members'],['🎤','Key Speakers'],['🤝','Bilateral Meetings'],['🔷','Conference Tracks'],['📋','Sessions Total'],['🌤️','Weather Days'],['🕌','Prayer Time Entries']],
    speakersSuffix:'speakers', meetingsSuffix:'meetings',
  },
  ar: {
    pageTitle:'إنشاء تقرير جديد', pageSubtitle:'سيقوم الذكاء الاصطناعي بإنشاء تقرير إحاطة استخباراتي متكامل',
    eventDetails:'تفاصيل الفعالية', eventName:'اسم الفعالية', eventNamePH:'مثال: مؤتمر ميلكن العالمي 2026',
    reportTitle:'عنوان التقرير', reportTitlePH:'مثال: إحاطة المؤتمر العالمي 2026',
    eventType:'نوع الفعالية', reportLang:'لغة التقرير', langEn:'English', langAr:'عربي',
    eventWebsite:'الموقع الإلكتروني للفعالية', websitePH:'https://event-website.com',
    location:'الموقع الجغرافي', city:'المدينة', cityPH:'مثال: لوس أنجلوس',
    country:'الدولة', countryPH:'اختر الدولة',
    venue:'المقر', venuePH:'مثال: فندق بيفرلي هيلتون',
    dates:'تواريخ الفعالية', startDate:'تاريخ البدء', endDate:'تاريخ الانتهاء',
    traveler:'بيانات المسافر', travelerName:'اسم المسافر', travelerTitle:'المسمى الوظيفي',
    context:'سياق إضافي', contextBadge:'اختياري', contextPH:'أضف أي سياق أو أهداف أو متطلبات...',
    cancel:'إلغاء', generate:'إنشاء التقرير بالذكاء الاصطناعي', generating:'جاري الإنشاء...',
    genTitle:'جاري إنشاء التقرير', genSubtitle:'يقوم الذكاء الاصطناعي بإعداد إحاطة استخباراتية متكاملة...',
    doneTitle:'تم إنشاء التقرير!', viewPDF:'📄 عرض PDF', previewHTML:'👁️ معاينة HTML', backDash:'→ العودة للوحة التحكم',
    sectionsGen:'الأقسام المُنشأة:',
    required:'يرجى تعبئة: اسم الفعالية، المدينة، الدولة، وتاريخ البدء.',
    genSteps:['تحليل ملف مخاطر الوجهة...','جمع المعلومات الاستخباراتية الجيوسياسية...','مراجعة التنبيهات الصحية لمنظمة الصحة العالمية...','إنشاء تفاصيل المؤتمر...','بناء الوفد وجدول الأعمال...','تجميع المتحدثين والاجتماعات الثنائية...','إضافة القنصلية والطقس وأوقات الصلاة...','اكتمال هيكل التقرير...'],
    sections:[['🎯','أهداف الزيارة'],['📅','أيام جدول الأعمال'],['👥','أعضاء الوفد'],['🎤','المتحدثون الرئيسيون'],['🤝','الاجتماعات الثنائية'],['🔷','مسارات المؤتمر'],['📋','إجمالي الجلسات'],['🌤️','أيام الطقس'],['🕌','مواقيت الصلاة']],
    speakersSuffix:'متحدث', meetingsSuffix:'اجتماع',
  },
};

export default function NewReportForm({ onSuccess, onCancel, lang = 'ar' }) {
  const l    = L[lang] || L.ar;
  const isAr = lang === 'ar';
  const dir  = isAr ? 'rtl' : 'ltr';
  const font = isAr ? "'Cairo',sans-serif" : "'Cairo',sans-serif";
  const eventTypes = isAr ? EVENT_TYPES_AR : EVENT_TYPES_EN;

  const [form, setForm] = useState({
    title:'', event_name:'', event_type: eventTypes[0],
    language: isAr ? 'Arabic' : 'English',
    event_website:'', city:'', country:'', venue:'',
    start_date:'', end_date:'', context:'',
    traveler_name:'Dr. Hisham Al Jadhey',
    traveler_title:'الرئيس التنفيذي للهيئة العامة للغذاء والدواء',
  });
  const [phase,       setPhase]       = useState('form');
  const [genStep,     setGenStep]     = useState('');
  const [report,      setReport]      = useState(null);
  const [error,       setError]       = useState('');
  const [previewMode, setPreviewMode] = useState(null);
  const submittingRef    = useRef(false);
  const [isSubmitting,   setIsSubmitting] = useState(false);
  const createdReportRef = useRef(null);

  const set = k => e => setForm(p => ({...p, [k]: e.target.value}));

  const handleGenerate = async () => {
    if (submittingRef.current) return;
    if (!form.event_name || !form.city || !form.country || !form.start_date) {
      setError(l.required); return;
    }
    submittingRef.current = true;
    setIsSubmitting(true);
    setError('');
    setPhase('generating');
    let stepIdx = 0;
    const stepInterval = setInterval(() => {
      setGenStep(l.genSteps[stepIdx % l.genSteps.length]);
      stepIdx++;
    }, 700);
    try {
      const payload = {...form, title: form.title || form.event_name};
      let newReport;
      if (createdReportRef.current) {
        newReport = createdReportRef.current;
      } else {
        const createRes = await createReport(payload);
        newReport = createRes.data;
        createdReportRef.current = newReport;
      }
      setGenStep(isAr ? 'استدعاء الذكاء الاصطناعي لإنشاء المحتوى...' : 'Calling AI to generate full report content...');
      const genRes = await generateAI(newReport.id);
      const fullReport = genRes.data.report;
      clearInterval(stepInterval);
      setReport(fullReport);
      setPhase('done');
      onSuccess(fullReport);
    } catch (e) {
      clearInterval(stepInterval);
      // Log full response for debugging
      console.error('[NewReportForm] Request failed:', e.response?.status, JSON.stringify(e.response?.data));

      // DRF returns validation errors as {field: [msg]} — extract all messages
      const data = e.response?.data;
      let raw;
      if (data && typeof data === 'object' && !data.error && !data.detail) {
        const msgs = Object.entries(data)
          .map(([field, errs]) => {
            const errList = Array.isArray(errs) ? errs.join(', ') : String(errs);
            return `${field}: ${errList}`;
          })
          .join(' | ');
        raw = msgs || e.message || 'Validation failed.';
      } else {
        raw = data?.error || data?.detail || data?.message || e.message || 'Generation failed.';
      }

      const friendly = raw.includes('API_KEY') || raw.includes('Authentication')
        ? '⚠️ API key missing. Set ANTHROPIC_API_KEY in backend/.env'
        : raw.includes('quota') || raw.includes('billing')
        ? '⚠️ API quota exceeded.'
        : e.response?.status === 400
        ? `⚠️ Validation error — ${raw}`
        : `⚠️ ${raw}`;
      setError(friendly);
      setPhase('form');
    } finally {
      submittingRef.current = false;
      setIsSubmitting(false);
    }
  };

  // ── Shared input style ──────────────────────────────────────
  const inp = {
    width:'100%', padding:'10px 12px', border:'1px solid #E8EAF0',
    borderRadius:8, fontSize:13, color:'#111827', background:'#FFFFFF',
    outline:'none', fontFamily:font, boxSizing:'border-box', direction:dir,
  };
  // Native select — force OS-native rendering so it always works
  const sel = {
    width:'100%', padding:'10px 12px', border:'1px solid #E8EAF0',
    borderRadius:8, fontSize:13, color:'#111827', background:'#FFFFFF',
    fontFamily:font, boxSizing:'border-box',
    // Force native OS select popup — renders above ALL browser content
    WebkitAppearance:'menulist',
    MozAppearance:'menulist',
    appearance:'menulist',
    cursor:'pointer',
  };
  const lbl = {
    fontSize:10.5, fontWeight:700, color:'rgba(180,196,225,0.45)', letterSpacing:'0.06em',
    textTransform:'uppercase', marginBottom:6, display:'block', fontFamily:font,
  };
  const onFocus = e => { e.target.style.borderColor='#3b82f6'; };
  const onBlur  = e => { e.target.style.borderColor='#e2e8f0'; };

  const Block = ({icon, title, badge, children}) => (
    <div style={{background:'#FFFFFF', borderRadius:12, padding:'20px 22px', border:'1px solid #EFF6FF', marginBottom:14, boxShadow:'0 4px 20px rgba(0,0,0,0.2)'}}>
      <div style={{display:'flex', alignItems:'center', gap:10, marginBottom:18, direction:dir}}>
        <div style={{width:28, height:28, borderRadius:7, background:'#EFF6FF', display:'flex', alignItems:'center', justifyContent:'center', fontSize:14, flexShrink:0}}>{icon}</div>
        <span style={{fontWeight:700, fontSize:15, color:'#111827', fontFamily:font}}>{title}</span>
        {badge && <span style={{fontSize:10, fontWeight:600, color:'rgba(212,175,55,0.6)', background:'rgba(212,175,55,0.08)', padding:'2px 7px', borderRadius:4}}>{badge}</span>}
      </div>
      {children}
    </div>
  );

  // ── Preview overlay ─────────────────────────────────────────
  if (previewMode && report) {
    const url = previewMode === 'pdf' ? getPDFUrl(report.id) : getPreviewUrl(report.id);
    return (
      <div style={{position:'fixed', inset:0, zIndex:2000, background:'rgba(0,0,0,0.75)', display:'flex', flexDirection:'column'}}>
        <div style={{background:'rgba(8,12,24,0.99)', padding:'12px 20px', display:'flex', alignItems:'center', justifyContent:'space-between', flexShrink:0}}>
          <span style={{color:'white', fontSize:14, fontWeight:700, fontFamily:font}}>{previewMode==='pdf'?'📄 PDF':'👁️ HTML'} — {report.title||report.event_name}</span>
          <div style={{display:'flex', gap:8}}>
            <a href={getPDFUrl(report.id)} download style={{padding:'7px 16px', background:'#3b82f6', color:'white', borderRadius:7, fontSize:12, fontWeight:600, textDecoration:'none', fontFamily:font}}>⬇ {isAr?'تحميل':'Download'}</a>
            <button onClick={()=>setPreviewMode(null)} style={{padding:'7px 16px', background:'rgba(255,255,255,0.15)', color:'white', border:'none', borderRadius:7, fontSize:12, fontWeight:600, cursor:'pointer', fontFamily:font}}>✕ {isAr?'إغلاق':'Close'}</button>
          </div>
        </div>
        <iframe src={url} title="Preview" style={{flex:1, border:'none', background:'white'}}/>
      </div>
    );
  }

  // ── Generating phase ────────────────────────────────────────
  if (phase === 'generating') {
    return (
      <div style={{display:'flex', flexDirection:'column', alignItems:'center', justifyContent:'center', height:'60vh', gap:20, direction:dir}}>
        <div style={{width:64, height:64, borderRadius:16, background:'linear-gradient(135deg,#0d9488,#9a7a1e)', display:'flex', alignItems:'center', justifyContent:'center', fontSize:28, boxShadow:'0 4px 20px rgba(59,130,246,0.4)'}}>✦</div>
        <h2 style={{fontSize:22, fontWeight:700, color:'#111827', margin:0, fontFamily:font}}>{l.genTitle}</h2>
        <p style={{color:'rgba(180,196,225,0.45)', fontSize:13, textAlign:'center', maxWidth:400, fontFamily:font}}>{l.genSubtitle}</p>
        <div style={{background:'rgba(12,16,32,0.98)', borderRadius:12, padding:'16px 24px', border:'1px solid #E8EAF0', minWidth:340, textAlign:'center'}}>
          <div style={{display:'flex', alignItems:'center', gap:10, justifyContent:'center'}}>
            <span style={{display:'inline-block', animation:'spin 1s linear infinite', fontSize:18}}>⏳</span>
            <span style={{fontSize:13, color:'#374151', fontWeight:500, fontFamily:font}}>{genStep}</span>
          </div>
          <div style={{marginTop:14, background:'#E8EAF0', borderRadius:8, height:6, overflow:'hidden'}}>
            <div style={{height:'100%', background:'linear-gradient(90deg,#0d9488,#b8932e)', animation:'progress 30s linear forwards', borderRadius:8}}/>
          </div>
        </div>
        <style>{`@keyframes spin{to{transform:rotate(360deg)}}@keyframes progress{from{width:0}to{width:95%}}`}</style>
      </div>
    );
  }

  // ── Done phase ──────────────────────────────────────────────
  if (phase === 'done' && report) {
    const counts = [
      report.visit_objectives?.length, report.agenda?.length, report.delegation?.length,
      report.speakers?.length, report.bilateral_meetings?.length, report.conference_tracks?.length,
      (report.sessions?.day1?.length||0)+(report.sessions?.day2?.length||0)+(report.sessions?.day3?.length||0),
      report.weather?.length, report.prayer_times?.length,
    ];
    return (
      <div style={{display:'flex', flexDirection:'column', alignItems:'center', gap:20, padding:'40px 20px', direction:dir}}>
        <div style={{width:64, height:64, borderRadius:'50%', background:'#ECFDF5', display:'flex', alignItems:'center', justifyContent:'center', fontSize:28}}>✅</div>
        <h2 style={{fontSize:22, fontWeight:700, color:'#111827', margin:0, fontFamily:font}}>{l.doneTitle}</h2>
        <p style={{color:'rgba(180,196,225,0.45)', fontSize:13, textAlign:'center', maxWidth:440, fontFamily:font}}>
          <strong>{report.event_name}</strong> · {report.city}, {report.country} · {report.speakers?.length||0} {l.speakersSuffix} · {report.bilateral_meetings?.length||0} {l.meetingsSuffix}
        </p>
        <div style={{display:'flex', gap:12, flexWrap:'wrap', justifyContent:'center'}}>
          <button onClick={()=>setPreviewMode('pdf')} style={{padding:'12px 24px', background:'linear-gradient(135deg,#0d9488,#b8932e)', color:'#f7f8fa', border:'none', borderRadius:10, fontSize:13, fontWeight:700, cursor:'pointer', boxShadow:'0 4px 14px rgba(212,175,55,0.25)', fontFamily:font}}>{l.viewPDF}</button>
          <button onClick={()=>setPreviewMode('html')} style={{padding:'12px 24px', background:'transparent', color:'#2563EB', border:'1px solid rgba(212,175,55,0.4)', borderRadius:10, fontSize:13, fontWeight:700, cursor:'pointer', fontFamily:font}}>{l.previewHTML}</button>
          <button onClick={onCancel} style={{padding:'12px 24px', background:'rgba(255,255,255,0.05)', color:'rgba(180,196,225,0.6)', border:'none', borderRadius:10, fontSize:13, fontWeight:600, cursor:'pointer', fontFamily:font}}>{l.backDash}</button>
        </div>
        <div style={{background:'rgba(12,16,32,0.97)', borderRadius:14, border:'1px solid rgba(212,175,55,0.12)', padding:'18px 22px', maxWidth:560, width:'100%'}}>
          <div style={{fontWeight:700, fontSize:14, color:'#111827', marginBottom:12, fontFamily:font}}>{l.sectionsGen}</div>
          {l.sections.map(([icon, label], i) => (
            <div key={i} style={{display:'flex', justifyContent:'space-between', padding:'5px 0', borderBottom:'1px solid #f8fafc', fontSize:13, fontFamily:font}}>
              <span style={{color:'#374151'}}>{icon} {label}</span>
              <span style={{background:'#EFF6FF', color:'#2563EB', borderRadius:12, padding:'1px 10px', fontSize:11, fontWeight:700}}>{counts[i]||0}</span>
            </div>
          ))}
        </div>
      </div>
    );
  }

  // ── Form ────────────────────────────────────────────────────
  return (
    <div style={{maxWidth:720, margin:'0 auto', paddingBottom:50, direction:dir, fontFamily:font}}>

      {/* Header */}
      <div style={{textAlign:'center', marginBottom:28}}>
        <div style={{width:54, height:54, borderRadius:16, background:'linear-gradient(135deg,#1d4ed8,#3b82f6)', display:'flex', alignItems:'center', justifyContent:'center', fontSize:22, margin:'0 auto 14px', boxShadow:'0 4px 16px rgba(212,175,55,0.25)'}}>✦</div>
        <h2 style={{margin:0, fontSize:24, fontWeight:700, color:'#111827', fontFamily:font}}>{l.pageTitle}</h2>
        <p style={{margin:'6px 0 0', fontSize:13, color:'#94a3b8', fontFamily:font}}>{l.pageSubtitle}</p>
      </div>

      {error && (
        <div style={{background:'#FEF2F2', border:'1px solid rgba(244,63,94,0.25)', borderRadius:10, padding:'12px 16px', marginBottom:16, color:'#f87171', fontSize:13, fontFamily:font}}>
          {error}
        </div>
      )}

      {/* ── Event Details ── */}
      <Block icon="📄" title={l.eventDetails}>
        <div style={{marginBottom:14}}>
          <label style={lbl}>{l.eventName} <span style={{color:'#ef4444'}}>*</span></label>
          <input style={inp} placeholder={l.eventNamePH} value={form.event_name} onChange={set('event_name')} onFocus={onFocus} onBlur={onBlur}/>
        </div>
        <div style={{marginBottom:14}}>
          <label style={lbl}>{l.reportTitle}</label>
          <input style={inp} placeholder={l.reportTitlePH} value={form.title} onChange={set('title')} onFocus={onFocus} onBlur={onBlur}/>
        </div>
        <div style={{display:'grid', gridTemplateColumns:'1fr 1fr', gap:12, marginBottom:14}}>
          <div>
            <label style={lbl}>{l.eventType}</label>
            <select style={sel} value={form.event_type} onChange={set('event_type')}>
              {eventTypes.map(t => <option key={t} value={t}>{t}</option>)}
            </select>
          </div>
          <div>
            <label style={lbl}>{l.reportLang}</label>
            <select style={sel} value={form.language} onChange={set('language')}>
              <option value="Arabic">{l.langAr}</option>
              <option value="English">{l.langEn}</option>
            </select>
          </div>
        </div>
        <div>
          <label style={lbl}>{l.eventWebsite}</label>
          <input style={inp} placeholder={l.websitePH} value={form.event_website} onChange={set('event_website')} onFocus={onFocus} onBlur={onBlur}/>
        </div>
      </Block>

      {/* ── Location ── */}
      <Block icon="📍" title={l.location}>
        <div style={{display:'grid', gridTemplateColumns:'1fr 1fr 1fr', gap:12}}>
          <div>
            <label style={lbl}>{l.city} <span style={{color:'#ef4444'}}>*</span></label>
            <input style={inp} placeholder={l.cityPH} value={form.city} onChange={set('city')} onFocus={onFocus} onBlur={onBlur}/>
          </div>
          <div>
            <label style={lbl}>{l.country} <span style={{color:'#ef4444'}}>*</span></label>
            <select style={sel} value={form.country} onChange={set('country')}>
              <option value="">{l.countryPH}</option>
              {COUNTRIES.map(c => {
                const v = isAr ? c.ar : c.en;
                return <option key={c.en} value={v}>{v}</option>;
              })}
            </select>
          </div>
          <div>
            <label style={lbl}>{l.venue}</label>
            <input style={inp} placeholder={l.venuePH} value={form.venue} onChange={set('venue')} onFocus={onFocus} onBlur={onBlur}/>
          </div>
        </div>
      </Block>

      {/* ── Dates ── */}
      <Block icon="📅" title={l.dates}>
        <div style={{display:'grid', gridTemplateColumns:'1fr 1fr', gap:12}}>
          <div>
            <label style={lbl}>{l.startDate} <span style={{color:'#ef4444'}}>*</span></label>
            <input type="date" style={inp} value={form.start_date} onChange={set('start_date')}/>
          </div>
          <div>
            <label style={lbl}>{l.endDate}</label>
            <input type="date" style={inp} value={form.end_date} onChange={set('end_date')}/>
          </div>
        </div>
      </Block>

      {/* ── Traveler ── */}
      <Block icon="👤" title={l.traveler}>
        <div style={{display:'grid', gridTemplateColumns:'1fr 1fr', gap:12}}>
          <div><label style={lbl}>{l.travelerName}</label><input style={inp} value={form.traveler_name} onChange={set('traveler_name')} onFocus={onFocus} onBlur={onBlur}/></div>
          <div><label style={lbl}>{l.travelerTitle}</label><input style={inp} value={form.traveler_title} onChange={set('traveler_title')} onFocus={onFocus} onBlur={onBlur}/></div>
        </div>
      </Block>

      {/* ── Context ── */}
      <Block icon="💬" title={l.context} badge={l.contextBadge}>
        <textarea style={{...inp, resize:'vertical', minHeight:90, lineHeight:1.65}} placeholder={l.contextPH} value={form.context} onChange={set('context')} onFocus={onFocus} onBlur={onBlur}/>
      </Block>

      {/* ── Actions ── */}
      <div style={{display:'flex', justifyContent:'center', gap:12, paddingTop:4}}>
        <button onClick={onCancel} style={{padding:'11px 26px', background:'transparent', border:'1px solid rgba(212,175,55,0.2)', borderRadius:9, fontSize:13, fontWeight:600, cursor:'pointer', color:'#6B7280', fontFamily:font}}>
          {l.cancel}
        </button>
        <button onClick={handleGenerate} disabled={isSubmitting}
          style={{padding:'11px 28px', background:isSubmitting?'rgba(212,175,55,0.4)':'linear-gradient(135deg,#0d9488,#b8932e)', border:'none', borderRadius:9, color:'#f7f8fa', fontSize:13, fontWeight:700, cursor:isSubmitting?'not-allowed':'pointer', display:'flex', alignItems:'center', gap:9, boxShadow:'0 4px 16px rgba(59,130,246,0.38)', minWidth:200, justifyContent:'center', opacity:isSubmitting?0.7:1, fontFamily:font}}>
          <span>✦</span> {isSubmitting ? l.generating : l.generate}
        </button>
      </div>
    </div>
  );
}
