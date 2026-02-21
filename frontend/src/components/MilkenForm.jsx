import React, { useState } from 'react';
import axios from 'axios';
import './MilkenForm.css';

const API_BASE = process.env.REACT_APP_API_URL || 'http://localhost:8000/api';

// Default data matching the original PDF exactly
const defaultData = {
  // Cover
  report_title: 'مشاركة معالي الرئيس التنفيذي في مؤتمر معهد ميلكن العالمي 4-6 مايو 2025م',
  report_subtitle: 'لوس انجلوس-الولايات المتحدة الامريكية',
  // Visit Info
  meeting_date: '4 – 6 مايو 2025',
  city: 'لوس أنجلوس- الولايات المتحدة الامريكية',
  visit_objectives: [
    'عرض التجربة التنظيمية السعودية في قطاع التقنية الحيوية بما يشمل الأطر التشريعية الحديثة وتسريع إجراءات التسجيل باستخدام الذكاء الاصطناعي.',
    'تعزيز حضور المملكة في المحافل الصحية والاستثمارية الدولية وبناء شراكات استراتيجية مع جهات تنظيمية ومؤسسات بحثية وشركات عالمية.',
    'الاستفادة من تجارب الاستثمار في الصناعات الصحية ودورها في دعم الابتكار وتعزيز جودة وسلامة المنتجات الحيوية.',
  ],
  // Delegation
  delegation: [
    { name: 'معالي الرئيس التنفيذي الدكتور/ هشام بن سعد الجضعي', title: 'الرئيس التنفيذي', department: 'الرئيس التنفيذي' },
    { name: 'سعادة الأستاذة/ الآء بنت فؤاد سندي', title: 'مساعد الرئيس لقطاع الشؤون التنفيذية', department: 'الشؤون التنفيذية' },
    { name: 'الاستاذة/ ابرار الصبيحي', title: 'رئيس قسم المراسم', department: 'الرئيس التنفيذي' },
  ],
  // Agenda
  agenda_days: [
    {
      day_label: 'اليوم الأول', date: '3 مايو 2025م',
      items: [
        { time: '6:00 ص', activity: 'المغادرة من مطار الملك خالد الدولي', location: 'الرياض' },
        { time: '16:05 م', activity: 'الوصول الى مطار لوس انجلوس الدولي', location: 'لوس انجلوس' },
        { time: '19:00م', activity: 'جلسة اجتياز', location: 'مقر الإقامة الفندقية للوفد' },
      ]
    },
    {
      day_label: 'اليوم الثاني', date: '4 مايو 2025م',
      items: [
        { time: '8:00ص-20:00م', activity: 'افتتاح الجلسة الحوارية', location: 'فندق بيفرلي هيلتون – لوس أنجلوس' },
        { time: '12:30-14:30م', activity: 'Leaders in Health', location: 'فندق بيفرلي هيلتون' },
        { time: '15:00م-17:00م', activity: 'ورشة عمل البيت السعودي', location: 'لم يحدد' },
      ]
    },
    {
      day_label: 'اليوم الثالث', date: '5 مايو 2025م',
      items: [{ time: '9:30ص-16:00م', activity: 'افتتاح الجلسة الحوارية', location: 'فندق بيفرلي هيلتون' }]
    },
    {
      day_label: 'اليوم الرابع', date: '6 مايو 2025م',
      items: [
        { time: '10:00-11:00ص', activity: 'The Roadmap to Longevity', location: 'فندق بيفرلي هيلتون' },
        { time: '11:30ص-12:30م', activity: 'Driving Investment into Health Innovations Investment (Invite Only)', location: 'فندق بيفرلي هيلتون' },
        { time: '16:40م', activity: 'المغادرة من مطار لوس انجلوس الدولي', location: 'لوس انجلوس' },
      ]
    },
  ],
  // Conference
  conference_responsible: 'السيد/ ريتشارد ديتيزيو',
  conference_responsible_title: 'الرئيس التنفيذي لمعهد ميلكن.',
  conference_overview: 'يُعد مؤتمر معهد ميلكن العالمي أحد أبرز المنصات الفكرية والاقتصادية في العالم ويُعقد سنويًا في مدينة لوس أنجلوس بالولايات المتحدة الأمريكية. ويعد هذا المؤتمر المنبثق من أعمال وفعاليات معهد ميلكن العالمي الذي يعتبر بمثابة "دافوس مصغر" حيث يجتمع فيه قادة العالم على المستوى الاقتصادي والسياسي والاستثماري والصحي.',
  conference_slogan: '"نحو مستقبل مزدهر – Toward a Flourishing Future"',
  conference_dates: 'خلال الفترة من 4 إلى 7 مايو 2025.',
  conference_participants: 'أكثر من 4,000 مشارك من مختلف أنحاء العالم.',
  conference_speakers_count: 'ما يزيد عن 900 متحدث وقرابة 200 جلسة متخصصة.',
  conference_tracks: [
    'الوصول -الفرص -والتنقل الاقتصادي', 'الأعمال والصناعة', 'الطاقة والبيئة', 'الأسواق المالية',
    'الصحة والبحوث الطبية', 'رأس المال البشري- تطوير القوى العاملة- التعليم',
    'العلاقات الدولية والجيواقتصادية', 'العمل الخيري والأثر الاجتماعي', 'السياسات والتنظيمات',
    'الأمن والمخاطر', 'المجتمع والثقافة', 'التقنية والابتكار',
  ],
  prev_2023_outcomes: [
    'الذكاء الاصطناعي في الرعاية الصحية: تم التركيز على إمكانات الذكاء الاصطناعي في تحسين نظم الرعاية الصحية بما في ذلك التنبؤ بالتهديدات البيولوجية وتطوير اللقاحات.',
    'الصحة العامة والوقاية: نوقشت استراتيجيات تعزيز الصحة العامة من خلال التركيز على الوقاية من الأمراض غير المعدية مثل أمراض القلب والسكرى.',
  ],
  prev_2024_outcomes: [
    'مبادرات صحية جديدة: أستعرض المعهد عدة مبادرات تهدف إلى تشكيل مستقبل الصحة من خلال الشراكات والتعاون مع التركيز على الوقاية والبحوث الطبية المجتمعية.',
    'التغير المناخي والاستدامة: تمت مناقشة المساهمات المالية لتحقيق أهداف الحد من الانبعاثات والحفاظ على البيئة.',
  ],
  ksa_participation_2023: [
    'شارك معالي وزير الاقتصاد والتخطيط فيصل الإبراهيم في جلسة حوارية بعنوان "العولمة : نماذج جديدة في الابتكار والتكامل" في 1 مايو 2023.',
    'شارك معالي وزير الاستثمار خالد الفالح في جلسة بعنوان "السعودية : من الرؤية إلى الواقع" في 2 مايو 2023.',
  ],
  ksa_participation_2024: [
    'شارك معالي رئيس مجلس هيئة السوق المالية محمد القويز في جلسة بعنوان "أسواق رأس المال في السعودية: استراتيجيات للتقدم" في مايو 2024.',
    'شاركت السيدة سارة السحيمي رئيسة مجلس إدارة مجموعة تداول السعودية كمتحدثة في المؤتمر ذاته.',
  ],
  key_speakers: [
    { name: 'كريستالينا غورغييفا', role: 'المدير العام لصندوق النقد الدولي (IMF)', linkedin_url: 'https://www.linkedin.com/in/kristalina-georgieva/' },
    { name: 'أجاى بانغا', role: 'رئيس البنك الدولي', linkedin_url: 'Ajay Banga Selected 14th President of the World Bank' },
    { name: 'جين فريزر', role: 'الرئيس التنفيذي لشركة Citigroup', linkedin_url: 'https://www.linkedin.com/in/jane-fraser-3292068/' },
    { name: 'فرناندو حداد', role: 'وزير المالية في البرازيل', linkedin_url: 'https://www.linkedin.com/today/author/fernandohaddad23/' },
    { name: 'خالد الفالح', role: 'وزير الاستثمار، المملكة العربية السعودية', linkedin_url: '' },
    { name: 'عبدالله بن عامر العيسى', role: 'وزير الاتصالات وتقنية المعلومات، المملكة العربية السعودية', linkedin_url: '' },
    { name: 'توني بلير', role: 'الرئيس التنفيذي لمعهد توني بلير للتغيير العالمي؛ رئيس الوزراء البريطاني السابق', linkedin_url: '' },
    { name: 'إيلون ماسك', role: 'المؤسس والرئيس التنفيذي لشركة Tesla', linkedin_url: '' },
  ],
  bilateral_meetings: [
    {
      entity: '',
      counterpart: '',
      date: 'مايو 2025م',
      time: '',
      location: '',
      talking_points: ["Opening Remark from the", "Opening Remark from the SFDA", "SFDA's Experience", "Q&A and discussion"]
    }
  ],
  // Consulate
  consulate_phone: '0013104796000',
  consulate_email: 'uscacon@mofa.gov.sa',
  consulate_hours: 'من 9 صباحاً – حتى 4 مساءً',
  consulate_holidays: 'السبت الجمعة',
  consulate_address: 'The Royal Consulate General Of Saudi Arabia In Los Angeles California. 12400 Wilshire Blvd Suite 700 Los Angeles ,CA 90025',
  consul_general_name: 'الأستاذ/ بندر بن فهد الزيد',
  consul_general_title: 'القنصل العام للمملكة العربية السعودية في لوس أنجلوس',
  consul_appointment_since: 'منذ 2023 حتى الآن',
  // Prayer times
  prayer_times: [
    { date: '4 مايو 2025م', day: 'الاحد', fajr: '4:45 AM', shurooq: '6:01 AM', dhuhr: '12:50 PM', asr: '4:33 PM', maghrib: '7:39 PM', isha: '8:56 PM' },
    { date: '5 مايو 2025م', day: 'الاثنين', fajr: '4:43 AM', shurooq: '6:00 AM', dhuhr: '12:50 PM', asr: '4:33 PM', maghrib: '7:40 PM', isha: '8:57 PM' },
    { date: '6 مايو 2025م', day: 'الخلافاء', fajr: '4:42 AM', shurooq: '5:59 AM', dhuhr: '12:50 PM', asr: '4:33 PM', maghrib: '7:41 PM', isha: '8:58 PM' },
    { date: '7 مايو 2025م', day: 'الاربعاء', fajr: '4:41 AM', shurooq: '5:58 AM', dhuhr: '12:50 PM', asr: '4:33 PM', maghrib: '7:42 PM', isha: '8:59 PM' },
  ],
  weather_days: [
    { day: '4', high: '19°', low: '12°' },
    { day: '5', high: '19°', low: '12°' },
    { day: '6', high: '20°', low: '12°' },
    { day: '7', high: '20°', low: '11°' },
  ],
};

// ----- Small reusable sub-components -----
const SectionCard = ({ title, children }) => (
  <div className="section-card">
    <div className="section-card-title">{title}</div>
    <div className="section-card-body">{children}</div>
  </div>
);

const Field = ({ label, value, onChange, type = 'text', rows = 1 }) => (
  <div className="field">
    <label className="field-label">{label}</label>
    {rows > 1 ? (
      <textarea className="field-input" rows={rows} value={value} onChange={e => onChange(e.target.value)} />
    ) : (
      <input className="field-input" type={type} value={value} onChange={e => onChange(e.target.value)} />
    )}
  </div>
);

const ListField = ({ label, items, onChange }) => {
  const add = () => onChange([...items, '']);
  const remove = (i) => onChange(items.filter((_, idx) => idx !== i));
  const update = (i, v) => { const arr = [...items]; arr[i] = v; onChange(arr); };
  return (
    <div className="field">
      <label className="field-label">{label}</label>
      {items.map((item, i) => (
        <div key={i} className="list-item-row">
          <textarea className="field-input" rows={2} value={item} onChange={e => update(i, e.target.value)} />
          <button className="btn-remove" onClick={() => remove(i)}>✕</button>
        </div>
      ))}
      <button className="btn-add" onClick={add}>+ إضافة</button>
    </div>
  );
};

// -----  Main Form -----
function MilkenForm() {
  const [formData, setFormData] = useState(defaultData);
  const [loading, setLoading] = useState(false);
  const [previewLoading, setPreviewLoading] = useState(false);
  const [error, setError] = useState('');
  const [activeTab, setActiveTab] = useState('cover');

  const set = (key) => (val) => setFormData(prev => ({ ...prev, [key]: val }));
  const setNested = (key, index, field) => (val) => {
    setFormData(prev => {
      const arr = [...prev[key]];
      arr[index] = { ...arr[index], [field]: val };
      return { ...prev, [key]: arr };
    });
  };

  const handleGeneratePDF = async () => {
    setLoading(true);
    setError('');
    try {
      const response = await axios.post(`${API_BASE}/generate-pdf/`, formData, {
        responseType: 'blob',
        headers: { 'Content-Type': 'application/json' },
      });
      const url = window.URL.createObjectURL(new Blob([response.data], { type: 'application/pdf' }));
      const link = document.createElement('a');
      link.href = url;
      const today = new Date().toISOString().split('T')[0];
      link.setAttribute('download', `Milken_Report_${today}.pdf`);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
    } catch (err) {
      setError('خطأ في توليد PDF: ' + (err.response?.data?.error || err.message));
    } finally {
      setLoading(false);
    }
  };

  const handlePreviewHTML = async () => {
    setPreviewLoading(true);
    setError('');
    try {
      const response = await axios.post(`${API_BASE}/preview-html/`, formData, {
        headers: { 'Content-Type': 'application/json' },
      });
      const win = window.open('', '_blank');
      win.document.write(response.data);
      win.document.close();
    } catch (err) {
      setError('خطأ في المعاينة: ' + (err.message));
    } finally {
      setPreviewLoading(false);
    }
  };

  const tabs = [
    { id: 'cover', label: 'الغلاف' },
    { id: 'visit', label: 'معلومات الزيارة' },
    { id: 'delegation', label: 'الوفد' },
    { id: 'agenda', label: 'جدول الأعمال' },
    { id: 'conference', label: 'بيانات المؤتمر' },
    { id: 'sessions', label: 'الجلسات' },
    { id: 'speakers', label: 'المتحدثون' },
    { id: 'bilateral', label: 'اللقاءات الثنائية' },
    { id: 'consulate', label: 'القنصلية' },
    { id: 'prayer', label: 'الطقس والصلاة' },
  ];

  return (
    <div className="milken-form">
      {/* Tabs */}
      <div className="tabs">
        {tabs.map(t => (
          <button
            key={t.id}
            className={`tab-btn ${activeTab === t.id ? 'active' : ''}`}
            onClick={() => setActiveTab(t.id)}
          >{t.label}</button>
        ))}
      </div>

      <div className="form-body">
        {/* ── COVER TAB ── */}
        {activeTab === 'cover' && (
          <SectionCard title="بيانات صفحة الغلاف">
            <Field label="عنوان التقرير (الغلاف)" value={formData.report_title} onChange={set('report_title')} rows={2} />
            <Field label="العنوان الفرعي (الغلاف)" value={formData.report_subtitle} onChange={set('report_subtitle')} />
          </SectionCard>
        )}

        {/* ── VISIT TAB ── */}
        {activeTab === 'visit' && (
          <SectionCard title="المعلومات الأساسية للزيارة">
            <Field label="تاريخ الاجتماع" value={formData.meeting_date} onChange={set('meeting_date')} />
            <Field label="المدينة" value={formData.city} onChange={set('city')} />
            <ListField label="أهداف الزيارة" items={formData.visit_objectives} onChange={set('visit_objectives')} />
          </SectionCard>
        )}

        {/* ── DELEGATION TAB ── */}
        {activeTab === 'delegation' && (
          <SectionCard title="قائمة الوفد المشارك بالزيارة">
            {formData.delegation.map((m, i) => (
              <div key={i} className="repeat-block">
                <div className="repeat-header">
                  <span>عضو {i + 1}</span>
                  <button className="btn-remove" onClick={() =>
                    setFormData(prev => ({ ...prev, delegation: prev.delegation.filter((_, idx) => idx !== i) }))
                  }>✕ حذف</button>
                </div>
                <Field label="الاسم" value={m.name} onChange={setNested('delegation', i, 'name')} />
                <Field label="المنصب" value={m.title} onChange={setNested('delegation', i, 'title')} />
                <Field label="القطاع / الإدارة" value={m.department} onChange={setNested('delegation', i, 'department')} />
              </div>
            ))}
            <button className="btn-add" onClick={() =>
              setFormData(prev => ({ ...prev, delegation: [...prev.delegation, { name: '', title: '', department: '' }] }))
            }>+ إضافة عضو</button>
          </SectionCard>
        )}

        {/* ── AGENDA TAB ── */}
        {activeTab === 'agenda' && (
          <SectionCard title="موجز جدول الأعمال">
            {formData.agenda_days.map((day, di) => (
              <div key={di} className="repeat-block">
                <div className="repeat-header">
                  <span style={{ fontWeight: 700 }}>{day.day_label} — {day.date}</span>
                </div>
                <div style={{ display: 'flex', gap: 10 }}>
                  <Field label="اليوم" value={day.day_label}
                    onChange={(v) => { const arr = [...formData.agenda_days]; arr[di].day_label = v; setFormData(p => ({ ...p, agenda_days: arr })); }} />
                  <Field label="التاريخ" value={day.date}
                    onChange={(v) => { const arr = [...formData.agenda_days]; arr[di].date = v; setFormData(p => ({ ...p, agenda_days: arr })); }} />
                </div>
                {day.items.map((item, ii) => (
                  <div key={ii} className="repeat-block" style={{ background: '#f8faff', marginBottom: 6 }}>
                    <div style={{ display: 'grid', gridTemplateColumns: '1fr 2fr 1fr', gap: 8 }}>
                      <Field label="الوقت" value={item.time}
                        onChange={(v) => { const arr = [...formData.agenda_days]; arr[di].items[ii].time = v; setFormData(p => ({ ...p, agenda_days: arr })); }} />
                      <Field label="النشاط" value={item.activity}
                        onChange={(v) => { const arr = [...formData.agenda_days]; arr[di].items[ii].activity = v; setFormData(p => ({ ...p, agenda_days: arr })); }} />
                      <Field label="الموقع" value={item.location}
                        onChange={(v) => { const arr = [...formData.agenda_days]; arr[di].items[ii].location = v; setFormData(p => ({ ...p, agenda_days: arr })); }} />
                    </div>
                    <button className="btn-remove" style={{ marginTop: 4 }} onClick={() => {
                      const arr = [...formData.agenda_days];
                      arr[di].items = arr[di].items.filter((_, idx) => idx !== ii);
                      setFormData(p => ({ ...p, agenda_days: arr }));
                    }}>✕ حذف النشاط</button>
                  </div>
                ))}
                <button className="btn-add" onClick={() => {
                  const arr = [...formData.agenda_days];
                  arr[di].items.push({ time: '', activity: '', location: '' });
                  setFormData(p => ({ ...p, agenda_days: arr }));
                }}>+ إضافة نشاط</button>
              </div>
            ))}
            <button className="btn-add" onClick={() =>
              setFormData(prev => ({ ...prev, agenda_days: [...prev.agenda_days, { day_label: 'يوم جديد', date: '', items: [] }] }))
            }>+ إضافة يوم</button>
          </SectionCard>
        )}

        {/* ── CONFERENCE TAB ── */}
        {activeTab === 'conference' && (
          <SectionCard title="بيانات المؤتمر">
            <Field label="المسؤول (الاسم)" value={formData.conference_responsible} onChange={set('conference_responsible')} />
            <Field label="المسؤول (المنصب)" value={formData.conference_responsible_title} onChange={set('conference_responsible_title')} />
            <Field label="نظرة عامة عن المؤتمر" value={formData.conference_overview} onChange={set('conference_overview')} rows={5} />
            <Field label="الشعار" value={formData.conference_slogan} onChange={set('conference_slogan')} />
            <Field label="تواريخ المؤتمر" value={formData.conference_dates} onChange={set('conference_dates')} />
            <Field label="عدد المشاركين" value={formData.conference_participants} onChange={set('conference_participants')} />
            <Field label="عدد المتحدثين والجلسات" value={formData.conference_speakers_count} onChange={set('conference_speakers_count')} />
            <ListField label="المحاور الرئيسية (12 محور)" items={formData.conference_tracks} onChange={set('conference_tracks')} />
            <ListField label="مخرجات 2023" items={formData.prev_2023_outcomes} onChange={set('prev_2023_outcomes')} />
            <ListField label="مخرجات 2024" items={formData.prev_2024_outcomes} onChange={set('prev_2024_outcomes')} />
            <ListField label="مشاركات المملكة 2023" items={formData.ksa_participation_2023} onChange={set('ksa_participation_2023')} />
            <ListField label="مشاركات المملكة 2024" items={formData.ksa_participation_2024} onChange={set('ksa_participation_2024')} />
          </SectionCard>
        )}

        {/* ── SESSIONS TAB ── */}
        {activeTab === 'sessions' && (
          <SectionCard title="جدول جلسات معالي الرئيس التنفيذي">
            <div className="info-note">
              ملاحظة: الجلسات الثابتة في PDF محددة سلفاً. يمكنك تعديل بياناتها هنا.
            </div>
            <Field label="وقت جلسة Leaders in Health" value="12:30-14:30" onChange={() => {}} />
            <Field label="موقع الجلسات" value="The Beverly Hilton Hotel" onChange={() => {}} />
          </SectionCard>
        )}

        {/* ── SPEAKERS TAB ── */}
        {activeTab === 'speakers' && (
          <SectionCard title="أبرز المتحدثين">
            {formData.key_speakers.map((sp, i) => (
              <div key={i} className="repeat-block">
                <div className="repeat-header">
                  <span>متحدث {i + 1}</span>
                  <button className="btn-remove" onClick={() =>
                    setFormData(prev => ({ ...prev, key_speakers: prev.key_speakers.filter((_, idx) => idx !== i) }))
                  }>✕ حذف</button>
                </div>
                <Field label="الاسم" value={sp.name} onChange={setNested('key_speakers', i, 'name')} />
                <Field label="المنصب" value={sp.role} onChange={setNested('key_speakers', i, 'role')} />
                <Field label="رابط LinkedIn" value={sp.linkedin_url} onChange={setNested('key_speakers', i, 'linkedin_url')} />
              </div>
            ))}
            <button className="btn-add" onClick={() =>
              setFormData(prev => ({ ...prev, key_speakers: [...prev.key_speakers, { name: '', role: '', linkedin_url: '' }] }))
            }>+ إضافة متحدث</button>
          </SectionCard>
        )}

        {/* ── BILATERAL TAB ── */}
        {activeTab === 'bilateral' && (
          <SectionCard title="اللقاءات الثنائية">
            {formData.bilateral_meetings.map((m, i) => (
              <div key={i} className="repeat-block">
                <div className="repeat-header">
                  <span>لقاء {i + 1}</span>
                  <button className="btn-remove" onClick={() =>
                    setFormData(prev => ({ ...prev, bilateral_meetings: prev.bilateral_meetings.filter((_, idx) => idx !== i) }))
                  }>✕ حذف</button>
                </div>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10 }}>
                  <Field label="الجهة" value={m.entity} onChange={setNested('bilateral_meetings', i, 'entity')} />
                  <Field label="الطرف النظير" value={m.counterpart} onChange={setNested('bilateral_meetings', i, 'counterpart')} />
                  <Field label="التاريخ" value={m.date} onChange={setNested('bilateral_meetings', i, 'date')} />
                  <Field label="الوقت" value={m.time} onChange={setNested('bilateral_meetings', i, 'time')} />
                  <Field label="الموقع" value={m.location} onChange={setNested('bilateral_meetings', i, 'location')} />
                </div>
                <ListField
                  label="نقاط الحديث"
                  items={m.talking_points || []}
                  onChange={(val) => setNested('bilateral_meetings', i, 'talking_points')(val)}
                />
              </div>
            ))}
            <button className="btn-add" onClick={() =>
              setFormData(prev => ({
                ...prev,
                bilateral_meetings: [...prev.bilateral_meetings, { entity: '', counterpart: '', date: '', time: '', location: '', talking_points: [] }]
              }))
            }>+ إضافة لقاء</button>
          </SectionCard>
        )}

        {/* ── CONSULATE TAB ── */}
        {activeTab === 'consulate' && (
          <SectionCard title="القنصلية السعودية — لوس أنجلوس">
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10 }}>
              <Field label="رقم الهاتف" value={formData.consulate_phone} onChange={set('consulate_phone')} />
              <Field label="البريد الإلكتروني" value={formData.consulate_email} onChange={set('consulate_email')} />
              <Field label="ساعات العمل" value={formData.consulate_hours} onChange={set('consulate_hours')} />
              <Field label="أيام العطلة" value={formData.consulate_holidays} onChange={set('consulate_holidays')} />
            </div>
            <Field label="العنوان" value={formData.consulate_address} onChange={set('consulate_address')} rows={2} />
            <Field label="اسم القنصل العام" value={formData.consul_general_name} onChange={set('consul_general_name')} />
            <Field label="منصب القنصل العام" value={formData.consul_general_title} onChange={set('consul_general_title')} />
            <Field label="تاريخ التعيين" value={formData.consul_appointment_since} onChange={set('consul_appointment_since')} />
          </SectionCard>
        )}

        {/* ── PRAYER TIMES TAB ── */}
        {activeTab === 'prayer' && (
          <SectionCard title="الطقس ومواقيت الصلاة">
            <div style={{ fontWeight: 700, marginBottom: 10, color: '#1c3370' }}>الطقس:</div>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 10, marginBottom: 16 }}>
              {formData.weather_days.map((w, i) => (
                <div key={i} className="repeat-block" style={{ padding: 8 }}>
                  <Field label="اليوم" value={w.day} onChange={(v) => {
                    const arr = [...formData.weather_days]; arr[i].day = v;
                    setFormData(p => ({ ...p, weather_days: arr }));
                  }} />
                  <Field label="أعلى درجة" value={w.high} onChange={(v) => {
                    const arr = [...formData.weather_days]; arr[i].high = v;
                    setFormData(p => ({ ...p, weather_days: arr }));
                  }} />
                  <Field label="أدنى درجة" value={w.low} onChange={(v) => {
                    const arr = [...formData.weather_days]; arr[i].low = v;
                    setFormData(p => ({ ...p, weather_days: arr }));
                  }} />
                </div>
              ))}
            </div>
            <div style={{ fontWeight: 700, marginBottom: 10, color: '#1c3370' }}>مواقيت الصلاة:</div>
            {formData.prayer_times.map((pt, i) => (
              <div key={i} className="repeat-block" style={{ marginBottom: 10 }}>
                <div style={{ fontWeight: 700, marginBottom: 6, color: '#555' }}>{pt.date} — {pt.day}</div>
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 8 }}>
                  {['date', 'day', 'fajr', 'shurooq', 'dhuhr', 'asr', 'maghrib', 'isha'].map(field => (
                    <Field key={field}
                      label={{ date: 'التاريخ', day: 'اليوم', fajr: 'الفجر', shurooq: 'الشروق', dhuhr: 'الظهر', asr: 'العصر', maghrib: 'المغرب', isha: 'العشاء' }[field]}
                      value={pt[field]}
                      onChange={(v) => {
                        const arr = [...formData.prayer_times]; arr[i][field] = v;
                        setFormData(p => ({ ...p, prayer_times: arr }));
                      }}
                    />
                  ))}
                </div>
              </div>
            ))}
          </SectionCard>
        )}
      </div>

      {/* Action Buttons */}
      <div className="action-bar">
        {error && <div className="error-msg">{error}</div>}
        <div className="action-buttons">
          <button className="btn-preview" onClick={handlePreviewHTML} disabled={previewLoading}>
            {previewLoading ? '⏳ جارٍ المعاينة...' : '🔍 معاينة HTML'}
          </button>
          <button className="btn-generate" onClick={handleGeneratePDF} disabled={loading}>
            {loading ? '⏳ جارٍ توليد PDF...' : '📄 توليد PDF وتنزيله'}
          </button>
        </div>
        <div className="filename-note">
          📋 اسم الملف: Milken_Report_{new Date().toISOString().split('T')[0]}.pdf
        </div>
      </div>
    </div>
  );
}

export default MilkenForm;
