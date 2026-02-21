import { useState, useEffect, useRef } from 'react';
import { chatAssistant } from '../services/api';

const RISK_COLORS = { low:'#22c55e', medium:'#f59e0b', high:'#ef4444' };

export default function AIAssistant({ reports }) {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const bottomRef = useRef(null);
  const inputRef = useRef(null);

  useEffect(() => {
    const reportList = reports.map(r => `• ${r.title} (${r.city}, ${r.country})`).join('\n');
    setMessages([{
      id:1, role:'assistant', timestamp:new Date(),
      content:`Hello! I'm your Travel AI Assistant. I have access to **${reports.length} report${reports.length!==1?'s':''}**:\n${reportList}\n\nI can help you with:\n**Executive summaries and conference briefings**\n**Key speakers and expected participants**\n**Suggested bilateral meetings and talking points**\n**Weather conditions and local recommendations**\n**Embassy & Consulate contact information**\n**Entry requirements and visa information**\n**Prayer times for the destination**\n\nHow can I assist you today?`,
    }]);
  }, [reports]);

  useEffect(() => { bottomRef.current?.scrollIntoView({ behavior:'smooth' }); }, [messages]);

  const buildSystem = () => {
    const details = reports.map(r => [
      `Report: "${r.title}"`,
      `Event: ${r.event_name}`,
      `Location: ${r.city}, ${r.country}`,
      `Dates: ${r.start_date} – ${r.end_date||r.start_date}`,
      `Status: ${r.status}`,
      `Risk: ${r.risk_level}`,
      `Speakers: ${r.speakers?.length||0}`,
      `Bilateral meetings: ${r.bilateral_meetings?.length||0}`,
    ].join(' | ')).join('\n');

    return `You are the Travel AI Assistant for SFDA (Saudi Food and Drug Authority). You have access to the following travel reports:\n\n${details}\n\nAssist with: executive summaries, key speakers, bilateral meeting talking points, weather, embassy/consulate contacts, visa requirements, prayer times, geopolitical risk. Be concise, professional, and use bullet points. Reference actual report data when answering.`;
  };

  const sendMsg = async (text) => {
    const txt = (text||input).trim();
    if (!txt||loading) return;
    const userMsg = { id:Date.now(), role:'user', content:txt, timestamp:new Date() };
    setMessages(p=>[...p,userMsg]);
    setInput('');
    setLoading(true);

    const history = messages.map(m=>({ role:m.role, content:m.content.replace(/<[^>]+>/g,'') }));

    try {
      const res = await chatAssistant([...history, { role:'user', content:txt }], buildSystem());
      setMessages(p=>[...p,{ id:Date.now()+1, role:'assistant', content:res.data.content, timestamp:new Date() }]);
    } catch {
      setMessages(p=>[...p,{ id:Date.now()+1, role:'assistant', content:'Connection error. Please try again.', timestamp:new Date() }]);
    }
    setLoading(false);
  };

  const fmt = content => content
    .replace(/\*\*(.*?)\*\*/g,'<strong>$1</strong>')
    .replace(/\*(.*?)\*/g,'<em>$1</em>')
    .split('\n').map(line => {
      if (line.startsWith('• ')||line.startsWith('- ')) return `<div style="display:flex;gap:7px;margin:3px 0"><span style="color:#3b82f6;font-size:9px;margin-top:5px">●</span><span>${line.slice(2)}</span></div>`;
      if (line.trim()==='') return '<div style="margin:4px 0"></div>';
      return `<span>${line}</span><br/>`;
    }).join('');

  const suggested = reports.length>0 ? [
    `Summarize the ${reports[0]?.title||'latest'} report`,
    'Who are the key speakers I should meet?',
    'What bilateral meetings are suggested?',
    `Weather and embassy info for ${reports[0]?.city||'destination'}`,
  ] : ['What can you help me with?','How do I create a report?','What is geopolitical risk?','Tell me about SFDA travel intelligence'];

  const fmtTime = d => new Date(d).toLocaleTimeString('en-US',{hour:'2-digit',minute:'2-digit'});

  return (
    <div style={{ display:'flex', flexDirection:'column', height:'100%', background:'#f8fafc' }}>
      <div style={{ background:'white', borderBottom:'1px solid #e9eef5', padding:'16px 28px 14px', display:'flex', alignItems:'center', gap:12, flexShrink:0 }}>
        <div style={{ width:38, height:38, borderRadius:10, background:'linear-gradient(135deg,#1d4ed8,#3b82f6)', display:'flex', alignItems:'center', justifyContent:'center', fontSize:18, boxShadow:'0 3px 10px rgba(59,130,246,0.3)' }}>🤖</div>
        <div>
          <div style={{ fontWeight:700, fontSize:17, color:'#0d1829' }}>Travel AI Assistant</div>
          <div style={{ fontSize:12, color:'#94a3b8', marginTop:1 }}>Your intelligent companion for travel planning</div>
        </div>
        <div style={{ marginLeft:'auto', display:'flex', alignItems:'center', gap:6 }}>
          <span style={{ width:8, height:8, borderRadius:'50%', background:'#22c55e', display:'inline-block' }}/>
          <span style={{ fontSize:12, color:'#64748b', fontWeight:500 }}>Online · {reports.length} report{reports.length!==1?'s':''} loaded</span>
        </div>
      </div>

      <div style={{ flex:1, overflowY:'auto', padding:'28px 0', display:'flex', flexDirection:'column' }}>
        <div style={{ width:'100%', maxWidth:760, margin:'0 auto', padding:'0 24px', display:'flex', flexDirection:'column', gap:16 }}>
          {messages.map(msg => (
            <div key={msg.id} style={{ display:'flex', gap:12, alignItems:'flex-start', justifyContent:msg.role==='user'?'flex-end':'flex-start', animation:'fadeUp 0.25s ease' }}>
              {msg.role==='assistant' && (
                <div style={{ width:34, height:34, borderRadius:10, background:'linear-gradient(135deg,#1d4ed8,#3b82f6)', display:'flex', alignItems:'center', justifyContent:'center', fontSize:16, flexShrink:0, marginTop:2 }}>🤖</div>
              )}
              <div style={{ maxWidth:'80%', background:msg.role==='user'?'linear-gradient(135deg,#1d4ed8,#3b82f6)':'white', color:msg.role==='user'?'white':'#1e293b', borderRadius:msg.role==='user'?'18px 18px 4px 18px':'4px 18px 18px 18px', padding:'13px 16px', fontSize:13.5, lineHeight:1.65, boxShadow:msg.role==='user'?'0 3px 12px rgba(59,130,246,0.3)':'0 2px 8px rgba(0,0,0,0.07)', border:msg.role==='assistant'?'1px solid #edf2f7':'none' }}>
                {msg.role==='assistant'
                  ? <div dangerouslySetInnerHTML={{ __html:fmt(msg.content) }}/>
                  : <span>{msg.content}</span>}
                <div style={{ fontSize:10, color:msg.role==='user'?'rgba(255,255,255,0.6)':'#94a3b8', marginTop:6, textAlign:'right' }}>{fmtTime(msg.timestamp)}</div>
              </div>
              {msg.role==='user' && (
                <div style={{ width:34, height:34, borderRadius:'50%', background:'linear-gradient(135deg,#3b82f6,#2563eb)', display:'flex', alignItems:'center', justifyContent:'center', fontSize:12, fontWeight:800, color:'white', flexShrink:0, marginTop:2 }}>US</div>
              )}
            </div>
          ))}
          {loading && (
            <div style={{ display:'flex', gap:12, alignItems:'flex-start' }}>
              <div style={{ width:34, height:34, borderRadius:10, background:'linear-gradient(135deg,#1d4ed8,#3b82f6)', display:'flex', alignItems:'center', justifyContent:'center', fontSize:16, flexShrink:0 }}>🤖</div>
              <div style={{ background:'white', borderRadius:'4px 18px 18px 18px', padding:'16px 18px', boxShadow:'0 2px 8px rgba(0,0,0,0.07)', border:'1px solid #edf2f7' }}>
                <div style={{ display:'flex', gap:5, alignItems:'center' }}>
                  {[0,1,2].map(i => <span key={i} style={{ width:7, height:7, borderRadius:'50%', background:'#94a3b8', display:'inline-block', animation:`bounce 1.2s ease infinite`, animationDelay:`${i*0.15}s` }}/>)}
                </div>
              </div>
            </div>
          )}
          <div ref={bottomRef}/>
        </div>
      </div>

      {messages.length<=1 && !loading && (
        <div style={{ padding:'0 0 12px', flexShrink:0 }}>
          <div style={{ maxWidth:760, margin:'0 auto', padding:'0 24px' }}>
            <div style={{ display:'flex', alignItems:'center', gap:6, marginBottom:10 }}>
              <span style={{ fontSize:14 }}>✦</span>
              <span style={{ fontSize:12, color:'#64748b', fontWeight:600 }}>Suggested questions</span>
            </div>
            <div style={{ display:'grid', gridTemplateColumns:'1fr 1fr', gap:8 }}>
              {suggested.map((q,i) => (
                <button key={i} onClick={()=>sendMsg(q)}
                  style={{ background:'white', border:'1.5px solid #e2e8f0', borderRadius:10, padding:'10px 14px', fontSize:12.5, color:'#374151', cursor:'pointer', textAlign:'left', fontFamily:'inherit', lineHeight:1.4, transition:'all 0.15s' }}
                  onMouseEnter={e=>{ e.currentTarget.style.borderColor='#3b82f6'; e.currentTarget.style.background='#eff6ff'; e.currentTarget.style.color='#1d4ed8'; }}
                  onMouseLeave={e=>{ e.currentTarget.style.borderColor='#e2e8f0'; e.currentTarget.style.background='white'; e.currentTarget.style.color='#374151'; }}>
                  {q}
                </button>
              ))}
            </div>
          </div>
        </div>
      )}

      <div style={{ background:'white', borderTop:'1px solid #e9eef5', padding:'14px 24px', flexShrink:0 }}>
        <div style={{ maxWidth:760, margin:'0 auto', display:'flex', gap:10, alignItems:'center' }}>
          <div style={{ flex:1, background:'#f8fafc', border:'1.5px solid #e2e8f0', borderRadius:12, padding:'10px 14px', display:'flex', alignItems:'center', cursor:'text', transition:'border-color 0.15s' }}
            onClick={()=>inputRef.current?.focus()}>
            <input ref={inputRef} value={input} onChange={e=>setInput(e.target.value)}
              onKeyDown={e=>{ if(e.key==='Enter'&&!e.shiftKey){e.preventDefault();sendMsg();} }}
              placeholder="Ask me anything about your travel reports..."
              disabled={loading}
              style={{ flex:1, background:'none', border:'none', outline:'none', fontSize:13.5, color:'#0d1829', fontFamily:'inherit' }}
              onFocus={e=>e.currentTarget.parentElement.style.borderColor='#3b82f6'}
              onBlur={e=>e.currentTarget.parentElement.style.borderColor='#e2e8f0'}
            />
          </div>
          <button onClick={()=>sendMsg()} disabled={loading||!input.trim()}
            style={{ width:44, height:44, borderRadius:12, background:loading||!input.trim()?'#e2e8f0':'linear-gradient(135deg,#1d4ed8,#3b82f6)', border:'none', cursor:loading||!input.trim()?'not-allowed':'pointer', display:'flex', alignItems:'center', justifyContent:'center', flexShrink:0, boxShadow:!loading&&input.trim()?'0 3px 10px rgba(59,130,246,0.35)':'none', transition:'all 0.2s' }}
            onMouseEnter={e=>{ if(!loading&&input.trim()) e.currentTarget.style.transform='scale(1.06)'; }}
            onMouseLeave={e=>{ e.currentTarget.style.transform='none'; }}>
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none">
              <path d="M22 2L11 13M22 2L15 22L11 13M22 2L2 9L11 13" stroke={loading||!input.trim()?'#94a3b8':'white'} strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
            </svg>
          </button>
        </div>
      </div>
      <style>{`@keyframes fadeUp{from{opacity:0;transform:translateY(6px)}to{opacity:1;transform:none}}@keyframes bounce{0%,60%,100%{transform:translateY(0)}30%{transform:translateY(-6px)}}`}</style>
    </div>
  );
}
