"""
ai_generator.py — SFDA Executive Brief Generator  v3.0
=======================================================
PIPELINE:
  Phase 0   → translate Arabic inputs
  Phase 1A  → Claude Sonnet + web_search — deep research (speakers/sessions/facts)
  Phase 1B  → OpenAI gpt-4o-search  — parallel research
  Phase 1C  → Website scraping — if event_website provided (best speaker/session source)
  Phase 2   → OpenAI gpt-4o / Claude Sonnet — generate JSON from structured research

KEY IMPROVEMENTS vs v2:
  - Research tokens: 3000 → 8000 (per call)
  - Research truncation: 4500 → 14000 chars fed to generator
  - Research turns: 2 → 6 continuation turns
  - Website scraping phase added
  - conference_tracks returns {name, explanation} objects
  - Structured research handoff: prose → labelled sections
  - All new blueprint fields fully specified in prompt
  - Bilateral meetings use research-verified institutions
"""

import re, time, json
from django.conf import settings


# ─── Helpers ──────────────────────────────────────────────────────────────────

def _clean_json(raw: str) -> str:
    raw = raw.strip()
    raw = re.sub(r'^```(?:json)?\s*', '', raw)
    raw = re.sub(r'\s*```$', '', raw)
    return raw.strip()

def _safe_json_load(raw: str) -> dict:
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        m = re.search(r'\{.*\}', raw, re.DOTALL)
        if m:
            try:
                return json.loads(m.group())
            except Exception:
                pass
    return {}

def _has_arabic(text: str) -> bool:
    return bool(re.search(r'[\u0600-\u06FF]', text or ''))

def _extract_claude_text(response) -> str:
    return '\n'.join(b.text for b in response.content if hasattr(b, 'text'))

def _truncate(text: str, max_chars: int = 14000) -> str:
    if len(text) <= max_chars:
        return text
    # Keep beginning (speakers/sessions) and end (embassy/consul)
    keep = max_chars // 2
    return text[:keep] + '\n...[middle truncated]...\n' + text[-keep:]

def _call_claude(claude, max_retries=3, **kwargs):
    for attempt in range(max_retries):
        try:
            return claude.messages.create(**kwargs)
        except Exception as e:
            if '429' in str(e) or 'rate_limit' in str(e):
                wait = 60 * (attempt + 1)
                print(f"[AI] Rate limit — waiting {wait}s (attempt {attempt+1}/{max_retries})")
                time.sleep(wait)
                if attempt == max_retries - 1:
                    raise
            else:
                raise
    raise RuntimeError("Max retries exceeded")


# ─── Phase 1C: Website scraping ───────────────────────────────────────────────

def _scrape_event_website(claude, oai, use_claude, use_openai, event_website, event_name):
    """Scrape the official conference website for speakers and sessions."""
    if not event_website or not event_website.startswith('http'):
        return ""

    prompt = f"""Visit the conference website and extract ALL available information.
URL: {event_website}

Extract and list:
1. SPEAKERS: Every confirmed speaker — exact full name, exact title, exact organization
2. SESSIONS/AGENDA: Every session title with time and date
3. CONFERENCE TRACKS or THEMES: Official track names and descriptions
4. CONFERENCE FACTS: Edition number, expected attendance, founding year
5. KEY QUOTES or THEMES from the event description

This is the official source — prioritize this data above all other sources.
If the speakers page is at a sub-URL (e.g. /speakers), also visit that page.
List every single name you find — even partial lists are valuable."""

    if use_claude:
        try:
            resp = _call_claude(
                claude,
                model="claude-sonnet-4-20250514",
                max_tokens=4000,
                system="Web scraper. Extract every speaker name, session title, and track exactly as written. Never summarize — list everything.",
                tools=[{"type": "web_search_20250305", "name": "web_search"}],
                messages=[{"role": "user", "content": prompt}],
            )
            text = _extract_claude_text(resp)
            # One continuation turn to follow sub-pages
            if resp.stop_reason == "tool_use":
                tool_results = [
                    {"type": "tool_result", "tool_use_id": b.id, "content": "Continue extracting all speaker and session data."}
                    for b in resp.content if hasattr(b, 'type') and b.type == 'tool_use'
                ]
                if tool_results:
                    resp2 = _call_claude(
                        claude,
                        model="claude-sonnet-4-20250514",
                        max_tokens=3000,
                        system="Web scraper. List all speakers and sessions.",
                        tools=[{"type": "web_search_20250305", "name": "web_search"}],
                        messages=[
                            {"role": "user", "content": prompt},
                            {"role": "assistant", "content": resp.content},
                            {"role": "user", "content": tool_results},
                        ],
                    )
                    text += '\n' + _extract_claude_text(resp2)
            if text.strip():
                return f"=== OFFICIAL WEBSITE DATA ({event_website}) ===\n{text.strip()}"
        except Exception as e:
            print(f"[AI] Website scrape error: {e}")

    if use_openai:
        try:
            r = oai.chat.completions.create(
                model="gpt-4o-search-preview",
                messages=[
                    {"role": "system", "content": "Extract all speaker names, sessions, and tracks from the conference website. List every name found."},
                    {"role": "user", "content": prompt},
                ],
                max_tokens=3000,
            )
            text = r.choices[0].message.content.strip()
            if text:
                return f"=== OFFICIAL WEBSITE DATA ({event_website}) ===\n{text}"
        except Exception as e:
            print(f"[AI] OpenAI website scrape error: {e}")

    return ""


# ─── Phase 1A: Claude deep research ───────────────────────────────────────────

def _research_claude(claude, event_name, city, country_en, start_date, end_date, venue, event_website):
    year = start_date[:4]
    month_year = start_date[:7]

    prompt = f"""You are a research analyst preparing a Saudi government official travel briefing.
Search the web thoroughly for VERIFIED facts for each section below.
RULE: If you cannot find a fact with certainty, write "NOT FOUND" — NEVER invent names, titles, or addresses.

EVENT: {event_name}
LOCATION: {city}, {country_en}
DATES: {start_date} to {end_date or start_date}
VENUE: {venue or 'TBD'}
YEAR: {year}

Search for each section (use web_search for EACH one):

A) SPEAKERS & SESSIONS — Most important section:
   Search: "{event_name} {year} speakers confirmed"
   Search: "{event_name} {year} agenda program schedule"
   List every speaker: EXACT full name + exact title + exact organization
   List every session: exact title + time + location

B) CONSULATE & EMBASSY:
   Search: "Saudi Arabia consulate {city} official address"
   Search: "Saudi Arabia embassy {country_en} ambassador 2025"
   Find: complete address, phone number, email, consul/ambassador EXACT name

C) CURRENT LEADER:
   Search: "current president prime minister {country_en} {year}"
   Find: EXACT full official name and title (verify it is current as of {start_date})

D) VERIFIED COUNTRY STATISTICS:
   Search: "{country_en} GDP 2024 World Bank IMF"
   Search: "{country_en} population 2024 official"
   Find: GDP (with year + source), population, capital, currency, timezone

E) BILATERAL TRADE DATA:
   Search: "Saudi Arabia {country_en} bilateral trade 2024 2025"
   Search: "Saudi Arabia {country_en} strategic agreements cooperation"
   Find: verified trade volume figures, key existing agreements, cooperation areas

F) REGULATORY BODIES:
   Search: "{country_en} FDA equivalent food drug regulatory authority"
   Search: "{country_en} health ministry pharmaceutical regulator"
   Find: exact official name of FDA equivalent, health ministry, and standards body

G) VISA/ENTRY:
   Search: "Saudi Arabia official passport {country_en} visa requirements 2025"
   Find: exact visa policy for Saudi official/diplomatic passport

H) WEATHER:
   Search: "{city} average temperature {month_year}"
   Find: realistic daily high/low °C for each of {start_date} to {end_date or start_date}

I) PRAYER TIMES:
   Calculate prayer times for {city} coordinates on {start_date}
   Format: Fajr, Dhuhr, Asr, Maghrib, Isha in HH:MM

J) CONFERENCE HISTORY:
   Search: "{event_name} {int(year)-1} outcomes highlights"
   Search: "{event_name} {int(year)-2} major announcements"
   Find: actual themes, outcomes, notable moments from past 3 editions

Report all findings with source URLs where possible."""

    messages = [{"role": "user", "content": prompt}]
    resp = _call_claude(
        claude,
        model="claude-sonnet-4-20250514",
        max_tokens=8000,
        system="Research analyst. Use web_search for EACH labeled section. Write NOT FOUND if you cannot verify. Include source URLs. Be specific and thorough.",
        tools=[{"type": "web_search_20250305", "name": "web_search"}],
        messages=messages,
    )
    parts = [_extract_claude_text(resp)]

    # Up to 6 continuation turns for comprehensive research
    for turn in range(6):
        if resp.stop_reason != "tool_use":
            break
        tool_results = [
            {"type": "tool_result", "tool_use_id": b.id, "content": "Continue the research — please complete all remaining sections."}
            for b in resp.content if hasattr(b, 'type') and b.type == 'tool_use'
        ]
        if not tool_results:
            break
        time.sleep(2)
        messages = messages + [
            {"role": "assistant", "content": resp.content},
            {"role": "user", "content": tool_results},
        ]
        resp = _call_claude(
            claude,
            model="claude-sonnet-4-20250514",
            max_tokens=6000,
            system="Research analyst. Complete all remaining sections. Include specific names, numbers, and source URLs.",
            tools=[{"type": "web_search_20250305", "name": "web_search"}],
            messages=messages,
        )
        parts.append(_extract_claude_text(resp))
        # Stop if we have enough content
        total = sum(len(p) for p in parts)
        if total > 20000:
            break

    return '\n\n'.join(p for p in parts if p.strip())


# ─── Phase 1B: OpenAI search ──────────────────────────────────────────────────

def _research_openai(oai, event_name, city, country_en, start_date, end_date, venue, event_website):
    year = start_date[:4]
    month_year = start_date[:7]

    prompt = f"""Saudi government travel briefing research. Find VERIFIED facts only.
RULE: Write "NOT FOUND" for anything unverifiable. NEVER invent names or data.

EVENT: {event_name} | {city}, {country_en} | {start_date}–{end_date or start_date}

A) CONFIRMED SPEAKERS: Search "{event_name} {year} speakers" — list EVERY name with exact title and organization
B) AGENDA/SESSIONS: Search "{event_name} {year} agenda" — list every session title, time, location
C) CONFERENCE TRACKS: Search "{event_name} {year} tracks themes" — official track names with descriptions
D) SAUDI CONSULATE in {city}: exact address, phone, email, consul general name (full official name)
E) SAUDI AMBASSADOR to {country_en}: EXACT full name as of {year} — search "Saudi Arabia ambassador {country_en} 2025"
F) CURRENT LEADER of {country_en}: exact full official name and title verified as of {start_date}
G) COUNTRY STATS: World Bank/IMF GDP (year), population (year), capital, currency, area, timezone
H) BILATERAL TRADE: Saudi-{country_en} trade volume 2023-2024 (verified figures with sources)
I) KEY REGULATORY BODY in {country_en}: exact official name of FDA/drug regulatory equivalent
J) VISA POLICY: Saudi official passport requirements for {country_en} entry
K) WEATHER: {city} {month_year} average temperatures (realistic daily high/low °C)
L) PRAYER TIMES: {city} on {start_date} — Fajr, Dhuhr, Asr, Maghrib, Isha in HH:MM
M) PAST EDITIONS: {event_name} outcomes from {int(year)-1}, {int(year)-2} — themes, agreements, attendance

Label each section A-M. Include source URLs."""

    try:
        r = oai.chat.completions.create(
            model="gpt-4o-search-preview",
            messages=[
                {"role": "system", "content": "Research specialist. Search the web for each labeled section. NEVER invent names, addresses, or statistics. Write NOT FOUND if uncertain."},
                {"role": "user", "content": prompt},
            ],
            max_tokens=5000,
        )
        return r.choices[0].message.content.strip()
    except Exception as e:
        print(f"[AI] OpenAI research error: {e}")
        return ""


# ─── Phase 2: Generate JSON ────────────────────────────────────────────────────

def _generate_json(research, event_name, city, country, country_en,
                   start_date, end_date, venue, event_type, context,
                   oai, claude, use_openai, use_claude):

    from datetime import datetime, timedelta

    try:
        d0 = datetime.strptime(start_date, "%Y-%m-%d")
        d1 = datetime.strptime(end_date, "%Y-%m-%d") if end_date and end_date != start_date else d0
        num_days = max(1, (d1 - d0).days + 1)
        dates = [(d0 + timedelta(days=i)).strftime("%Y-%m-%d") for i in range(num_days)]
    except Exception:
        num_days = 3
        dates = [start_date] * 3

    day_ar = ["اليوم الأول","اليوم الثاني","اليوم الثالث","اليوم الرابع","اليوم الخامس"]
    day_en = ["Day 1","Day 2","Day 3","Day 4","Day 5"]
    venue_str = venue or city
    year = start_date[:4]

    # Leader overrides (training data may be stale)
    overrides = {
        "united states": "Donald J. Trump",
        "usa":           "Donald J. Trump",
        "united kingdom":"Keir Starmer",
        "uk":            "Keir Starmer",
        "germany":       "Friedrich Merz",
        "france":        "Emmanuel Macron",
        "canada":        "Mark Carney",
        "italy":         "Giorgia Meloni",
        "japan":         "Shigeru Ishiba",
        "australia":     "Anthony Albanese",
    }
    leader_note = ""
    for k, v in overrides.items():
        if k in country_en.lower():
            leader_note = f"OVERRIDE: current head of state of {country_en} = {v} (use EXACTLY this name)\n"
            break

    agenda_spec = "\n".join(
        f'  Day {i+1}: date="{dates[i]}", label_ar="{day_ar[i]}", label_en="{day_en[i]}"'
        for i in range(num_days)
    )

    import json as _json
    weather_skeleton = _json.dumps([
        {"day": day_en[i], "date": dates[i],
         "condition": "<Sunny/Cloudy/Rainy/Partly Cloudy>",
         "high": "<int °C from research H>",
         "low": "<int °C>",
         "humidity": "<n>%", "wind": "<n> km/h"}
        for i in range(num_days)
    ], ensure_ascii=False)

    prayer_skeleton = _json.dumps([
        {"date": dates[i], "day": f"{day_en[i]} — {day_ar[i]}",
         "fajr": "<HH:MM>", "dhuhr": "<HH:MM>",
         "asr": "<HH:MM>", "maghrib": "<HH:MM>", "isha": "<HH:MM>"}
        for i in range(num_days)
    ], ensure_ascii=False)

    # Build agenda day template strings
    extra_days = ""
    for i in range(1, num_days):
        extra_days += f""",
    {{"day_label":"{day_ar[i]}","day_label_en":"{day_en[i]}","date":"{dates[i]}","items":[
      {{"time":"09:00","activity":"<REAL session title from research A — Arabic>","location":"<room from research>","type":"session","strategic_relevance":"<Arabic phrase>"}},
      {{"time":"10:30","activity":"<REAL session from research — Arabic>","location":"<room>","type":"session","strategic_relevance":"<Arabic>"}},
      {{"time":"12:00","activity":"استراحة الغداء والتواصل","location":"<dining venue>","type":"networking","strategic_relevance":"بناء الشبكات الاستراتيجية"}},
      {{"time":"14:00","activity":"<Real session or bilateral — Arabic>","location":"<room>","type":"bilateral","strategic_relevance":"<Arabic>"}},
      {{"time":"16:00","activity":"<Real session — Arabic>","location":"<room>","type":"session","strategic_relevance":"<Arabic>"}},
      {{"time":"18:30","activity":"<Evening reception or networking>","location":"<venue>","type":"networking","strategic_relevance":"—"}}
    ]}}"""

    # Build sessions day template strings
    extra_sessions = ""
    for i in range(1, num_days):
        extra_sessions += f""",
    "day{i+1}":[
      {{"time":"09:00","title":"<REAL session from research A — Arabic>","description":"<2-3 sentences Arabic>","speakers":"<exact names from research>","policy_implications":"<Arabic>","investment_implications":"<Arabic>","regulatory_impact":"<Arabic>","strategic_score":"عالي"}},
      {{"time":"11:00","title":"<REAL session — Arabic>","description":"<Arabic>","speakers":"<names>","policy_implications":"<Arabic>","investment_implications":"<Arabic>","regulatory_impact":"<Arabic>","strategic_score":"متوسط"}},
      {{"time":"14:30","title":"<REAL session — Arabic>","description":"<Arabic>","speakers":"<names>","policy_implications":"<Arabic>","investment_implications":"<Arabic>","regulatory_impact":"<Arabic>","strategic_score":"عالي"}}
    ]"""

    research_for_prompt = _truncate(research, 14000)

    prompt = f"""Generate a COMPLETE Milken-style executive intelligence briefing JSON for a Saudi government delegation.
This is a CLASSIFIED STRATEGIC INTELLIGENCE DOCUMENT — every field must reflect geopolitical weight, national interest, and executive-level analysis.

{leader_note}
EVENT: {event_name}
CITY: {city} | COUNTRY: {country} | VENUE: {venue_str}
DATES: {start_date} to {end_date or start_date} ({num_days} days)
CONTEXT: {context or 'SFDA official participation — Hisham Al Jadhey, CEO'}
{agenda_spec}

═══════════════════════════════════════════════════════════
RESEARCH DATA (HIGHEST PRIORITY — use all verified facts):
═══════════════════════════════════════════════════════════
{research_for_prompt}
═══════════════════════════════════════════════════════════

INSTRUCTIONS:
- All text fields MUST be in formal Arabic (except names, titles, organizations)
- Use REAL names, statistics, and institutions from the research above
- For any field marked NOT FOUND in research, use "يُحدَّد لاحقاً" or "—"
- NEVER write placeholder text like "<Real speaker>", "John Smith", "يُعبأ لاحقاً"
- Replace every <angle bracket placeholder> with real Arabic strategic content
- Bilateral meetings: counterpart = always "يُحدَّد لاحقاً" (we don't know the specific individual)
- conference_tracks MUST be objects with "name" AND "explanation" keys — not plain strings
- All intel_* fields MUST be arrays of Arabic bullet strings (2-4 bullets each)
- All ns_* fields MUST be complete Arabic paragraphs (2-3 sentences)
- weather: exactly {num_days} objects with integer temperatures in °C
- prayer_times: exactly {num_days} objects with HH:MM times

Return ONLY valid JSON — no markdown, no comments, no trailing commas.

{{
  "report_subtitle": "<Arabic subtitle — official conference theme or strategic tagline>",

  "visit_objectives": [
    "<Specific objective 1 — named strategic goal tied to this event's actual agenda>",
    "<Objective 2 — regulatory cooperation opportunity from research>",
    "<Objective 3 — specific bilateral relationship to advance>",
    "<Objective 4 — institutional gain: named international body or partnership>",
    "<Objective 5 — Vision 2030 alignment: specific program or target>"
  ],

  "executive_summary": "<7-9 sentences Arabic. Must cover: (1) why {event_name} matters globally with specific figures/participants, (2) Saudi Arabia's strategic interests served by attending, (3) SFDA's specific institutional agenda at this conference, (4) bilateral opportunities with {country_en}, (5) expected outcomes. Tone: classified ministerial intelligence brief. NO generic language.>",

  "geopolitical_summary": "<6-8 sentences Arabic. Analytical assessment of: conference's role in global policy architecture, which world powers attend and why, economic/investment significance (cite figures from research), regulatory implications for pharma/health sector, Saudi Arabia's geopolitical positioning opportunity. Must read like an intelligence assessment, not a press release.>",

  "intel_global_significance": [
    "<Arabic bullet: specific evidence of conference's global influence — named participants, decisions made, capital allocated>",
    "<Arabic bullet: economic/investment significance — verified figures>",
    "<Arabic bullet: Saudi Arabia's strategic role and positioning at this forum>"
  ],

  "intel_regulatory_impact": [
    "<Arabic bullet: specific regulatory/policy decisions expected this edition — named frameworks or legislation>",
    "<Arabic bullet: pharmaceutical/health regulatory impact directly relevant to SFDA's mandate>",
    "<Arabic bullet: harmonization or compliance opportunity for Saudi Arabia>"
  ],

  "intel_long_term_value": [
    "<Arabic bullet: 3-5 year strategic value — specific partnerships or influence this participation enables>",
    "<Arabic bullet: institutional positioning — named international bodies SFDA can advance its standing in>",
    "<Arabic bullet: measurable outcome target — what success looks like after this visit>"
  ],

  "conference_summary": "<5-7 sentences Arabic. Cover: organizing body full name, founding year, global ranking, this edition's theme, expected number and level of participants (use research figures), what makes this edition unique. Be specific.>",

  "conference_history": "<5-7 sentences Arabic. Year-by-year highlights from past 3 editions: actual themes from research, notable policy announcements, participation growth, agreements reached. Use specific years and real milestones from research J.>",

  "ksa_participation_history": "<5-7 sentences Arabic. Saudi Vision 2030 linkage: which specific 2030 targets this conference advances, SFDA regulatory modernization program relevance, health sector transformation investment targets, Saudi Arabia's international regulatory leadership positioning.>",

  "ns_vision_alignment": "<2-3 sentences Arabic. Specific Vision 2030 programs or targets this visit serves — name the actual initiative (e.g. Health Sector Transformation Program, NTP). Must be concrete.>",

  "ns_regulatory_relevance": "<2-3 sentences Arabic. Specific SFDA regulatory reform programs advanced by this conference — name actual SFDA strategic initiatives or ICH/GCC/WHO harmonization tracks.>",

  "ns_investment_implications": "<2-3 sentences Arabic. Specific investment opportunity or target — pharmaceutical sector FDI figures, named investment programs or zones relevant to this conference's topics.>",

  "ns_institutional_positioning": "<2-3 sentences Arabic. Specific international body or leadership role SFDA is advancing — ICH, WHO, IAEA, regional regulatory networks. Concrete and measurable.>",

  "sfda_relevance": "<5-6 sentences Arabic. SFDA-specific strategic value: regulatory harmonization goals advanced, international recognition opportunities, partnership pipeline with named counterpart bodies.>",

  "bilateral_relations": "<8-10 sentences Arabic. Use verified figures from research E: actual trade volume with year, top cooperation sectors, named strategic agreements (e.g. specific MoUs), investment flows both directions, visa policy from research G, diplomatic alignment, future roadmap. This section MUST contain verified statistics.>",

  "bilateral_fields": {{
    "trade_volume": "<Verified figure from research E — e.g. '$X billion (2023, source)' — NOT FOUND if unverified>",
    "cooperation_areas": "<Arabic — 3-5 specific sectors with named cooperation frameworks>",
    "strategic_agreements": "<Arabic — list actual named bilateral agreements from research E>",
    "health_regulatory": "<Arabic — specific health/pharma cooperation frameworks between Saudi Arabia and {country_en}>"
  }},

  "entry_requirements": "<4-5 sentences Arabic. From research G: exact visa policy for Saudi official passport, entry conditions, any health requirements, processing times.>",

  "leadership_brief": "<5-7 sentences Arabic. From research C: EXACT verified name + title of head of state, political system, governing coalition, economic policy orientation, foreign policy stance toward Saudi Arabia, key priorities relevant to this visit.>",

  "political_economic_orientation": "<Arabic 1-2 sentences: this country's economic policy model and current priorities.>",

  "political_strategic_priorities": "<Arabic 1-2 sentences: top foreign/economic policy priorities most relevant to Saudi Arabia's interests.>",

  "trade_exchange": "<4-6 sentences Arabic. Detailed bilateral trade: verified volume, key sectors, Saudi investment in {country_en}, reciprocal investment, major joint economic projects.>",

  "sfda_talking_points": [
    "<Specific Arabic talking point 1 — regulatory cooperation framework to propose, citing specific regulations or standards>",
    "<Point 2 — data sharing or pharmacovigilance harmonization — specific data systems or databases>",
    "<Point 3 — market access for Saudi pharmaceutical exports — specific products or categories>",
    "<Point 4 — halal pharmaceuticals/food safety standards — specific harmonization opportunity>",
    "<Point 5 — AI/digital health regulation — named initiative or framework to discuss>",
    "<Point 6 — joint clinical trial framework — specific regulatory pathway>",
    "<Point 7 — AMR or pandemic preparedness — specific mechanism or agreement>",
    "<Point 8 — SFDA international recognition — specific accreditation or listing target>"
  ],

  "country_info": {{
    "capital": "<capital city from research D>",
    "head_of_state_title": "<Arabic official title from research C>",
    "head_of_state": "<EXACT full name from research C or leader override — use override if provided>",
    "population": "<from research D — X million (year, source)>",
    "area": "<km² from research D>",
    "gdp": "<from research D — $X trillion (year, source)>",
    "gdp_per_capita": "<from research D — $X,XXX (year, source)>",
    "currency": "<full name (CODE) from research D>",
    "official_language": "<language>",
    "religion": "<predominant religion>",
    "timezone": "UTC<±n>",
    "government": "<Arabic — political system type>",
    "key_sectors": "<Arabic — 3-5 key sectors most relevant to Saudi cooperation>",
    "overview": "<Arabic — 4-5 sentences strategic assessment: economic standing, geopolitical role, regulatory environment, relevance to Saudi Arabia. Use verified figures.>"
  }},

  "embassy": {{
    "name": "<full official Arabic name of Saudi embassy in {country_en}>",
    "mission": "<Arabic — mission statement 1-2 sentences>",
    "ambassador_name": "<EXACT name from research K — write 'يُحدَّد لاحقاً' if NOT FOUND>",
    "ambassador_title": "سفير خادم الحرمين الشريفين لدى {country_en}",
    "address": "<full verified street address from research — NOT FOUND if unverified>",
    "phone": "<verified phone from research — NOT FOUND if unverified>",
    "fax": "—",
    "email": "<verified email — NOT FOUND if unverified>",
    "website": "<verified URL>"
  }},

  "delegation": [
    {{"name":"د. هشام بن سعد الجضعي","title":"الرئيس التنفيذي للهيئة العامة للغذاء والدواء","department":"الرئاسة التنفيذية","strategic_role":"رئاسة الوفد الرسمي وتمثيل المملكة على أعلى مستوى تنفيذي"}},
    {{"name":"د. محمد بن عبدالعزيز الفراج","title":"مساعد الرئيس التنفيذي للشؤون الدولية","department":"الشؤون الدولية","strategic_role":"إدارة الاجتماعات الثنائية وتنسيق اتفاقيات التعاون الدولي"}},
    {{"name":"م. سارة بنت عبدالله العمري","title":"مدير إدارة الشؤون التنظيمية الدولية","department":"الشؤون التنظيمية","strategic_role":"متابعة ملفات التناسق التنظيمي ومفاوضات اتفاقيات الاعتراف المتبادل"}},
    {{"name":"د. خالد بن سعد المطيري","title":"مستشار الرئيس التنفيذي للسياسات الدوائية","department":"السياسات الدوائية","strategic_role":"تقديم المشورة التقنية وتمثيل الهيئة في الجلسات العلمية والتقنية المتخصصة"}}
  ],

  "agenda": [
    {{"day_label":"{day_ar[0]}","day_label_en":"{day_en[0]}","date":"{dates[0]}","items":[
      {{"time":"08:00","activity":"وصول الوفد والتسجيل الرسمي","location":"{venue_str}","type":"logistics","strategic_relevance":"—"}},
      {{"time":"09:00","activity":"<REAL opening session title from research A — Arabic>","location":"<hall name from research>","type":"ceremony","strategic_relevance":"<Arabic — strategic significance of opening>"}},
      {{"time":"10:30","activity":"<REAL session from research A — Arabic title>","location":"<room>","type":"session","strategic_relevance":"<Arabic — specific relevance to SFDA agenda>"}},
      {{"time":"12:00","activity":"استراحة الغداء والتواصل مع كبار المسؤولين","location":"<dining venue>","type":"networking","strategic_relevance":"بناء الشبكات الاستراتيجية مع صانعي القرار"}},
      {{"time":"14:00","activity":"<Real afternoon session or bilateral from research — Arabic>","location":"<room>","type":"bilateral","strategic_relevance":"<Arabic>"}},
      {{"time":"16:00","activity":"<Real session from research — Arabic>","location":"<room>","type":"session","strategic_relevance":"<Arabic>"}},
      {{"time":"19:00","activity":"حفل الاستقبال الرسمي للمؤتمر","location":"<ballroom>","type":"ceremony","strategic_relevance":"التواصل البروتوكولي مع الوفود الحكومية"}}
    ]}}
    {extra_days}
  ],

  "conference_data": {{
    "organizer": "<REAL organizing body name from research — NOT SFDA>",
    "overview": "<Arabic — what the conference is, its global standing, policy influence>",
    "slogan": "<official conference theme or tagline this edition — from research or official website>",
    "dates": "{start_date} to {end_date or start_date}",
    "location": "{venue_str}, {country}",
    "founded": "<year conference was established>",
    "edition": "<this edition number>",
    "expected_participants": "<verified number and type from research>",
    "participant_profile": "<Arabic — level and type of attendees: CEOs, ministers, etc>",
    "core_themes": "<Arabic — the 3-5 main themes of this edition from research>",
    "ksa_participation": "<Arabic — Saudi Arabia's participation history and expected role>"
  }},

  "conference_tracks": [
    {{"name": "<REAL official track name from research — Arabic>", "explanation": "<2-sentence Arabic explanation of this track's strategic content and its specific relevance to SFDA and Saudi health/pharma sector>"}},
    {{"name": "<REAL track 2>", "explanation": "<Arabic explanation>"}},
    {{"name": "<REAL track 3>", "explanation": "<Arabic explanation>"}},
    {{"name": "<REAL track 4>", "explanation": "<Arabic explanation>"}},
    {{"name": "<REAL track 5>", "explanation": "<Arabic explanation>"}}
  ],

  "previous_outcomes": [
    {{"year":"{int(year)-1}","theme":"<Arabic — actual theme from research J>","summary":"<Arabic — SPECIFIC outcomes: policy announcements, agreements, named participants. Use research J data. NOT generic.>","relevance":"<Arabic — why this outcome specifically matters to Saudi Arabia and SFDA>"}},
    {{"year":"{int(year)-2}","theme":"<Arabic>","summary":"<Arabic — specific outcomes from research J>","relevance":"<Arabic>"}},
    {{"year":"{int(year)-3}","theme":"<Arabic>","summary":"<Arabic>","relevance":"<Arabic>"}}
  ],

  "sessions": {{
    "day1":[
      {{"time":"09:00","title":"<REAL session title from research A — Arabic>","description":"<2-3 sentences Arabic — what this session covers, specific policy or investment implications>","speakers":"<EXACT names from research — 'يُحدَّد لاحقاً' if not in research>","policy_implications":"<Arabic — specific policy impact>","investment_implications":"<Arabic — specific capital/investment dimension>","regulatory_impact":"<Arabic — specific regulatory significance for SFDA>","strategic_score":"عالي"}},
      {{"time":"11:00","title":"<REAL session — Arabic>","description":"<Arabic>","speakers":"<exact names>","policy_implications":"<Arabic>","investment_implications":"<Arabic>","regulatory_impact":"<Arabic>","strategic_score":"متوسط"}},
      {{"time":"14:30","title":"<REAL session — Arabic>","description":"<Arabic>","speakers":"<exact names>","policy_implications":"<Arabic>","investment_implications":"<Arabic>","regulatory_impact":"<Arabic>","strategic_score":"عالي"}}
    ]
    {extra_sessions}
  }},

  "speakers": [
    {{"name":"<REAL speaker from research A — exact full name>","title":"<exact official title from research>","organization":"<exact organization name>","country":"<country>","influence_profile":"<Arabic 2 sentences — their specific global role, policy influence, regulatory or investment decisions they control>","relevance":"<Arabic — concrete relevance to SFDA's agenda: specific regulatory issue, investment decision, or partnership opportunity they represent>"}},
    {{"name":"<REAL speaker 2>","title":"<exact title>","organization":"<exact org>","country":"<country>","influence_profile":"<Arabic>","relevance":"<Arabic>"}},
    {{"name":"<REAL speaker 3>","title":"<exact title>","organization":"<exact org>","country":"<country>","influence_profile":"<Arabic>","relevance":"<Arabic>"}},
    {{"name":"<REAL speaker 4>","title":"<exact title>","organization":"<exact org>","country":"<country>","influence_profile":"<Arabic>","relevance":"<Arabic>"}},
    {{"name":"<REAL speaker 5>","title":"<exact title>","organization":"<exact org>","country":"<country>","influence_profile":"<Arabic>","relevance":"<Arabic>"}},
    {{"name":"<REAL speaker 6>","title":"<exact title>","organization":"<exact org>","country":"<country>","influence_profile":"<Arabic>","relevance":"<Arabic>"}}
  ],

  "bilateral_meetings": [
    {{
      "entity": "<REAL official institution name from research F — FDA/Health Ministry/Standards Body equivalent in {country_en}>",
      "counterpart": "يُحدَّد لاحقاً",
      "counterpart_title": "<Arabic official title of the typical head of this institution>",
      "date": "{dates[0]}",
      "time": "14:00",
      "location": "{venue_str}",
      "talking_points": [
        "<Arabic — specific regulatory harmonization agenda item: named regulation, standard, or process>",
        "<Arabic — specific data sharing or pharmacovigilance system to propose>",
        "<Arabic — specific MoU or agreement to negotiate: named scope and mechanism>",
        "<Arabic — specific market access or mutual recognition opportunity with named products/categories>"
      ],
      "strategic_objective": "<Arabic — one specific, measurable goal this meeting serves for SFDA (e.g. 'التوقيع على إطار الاعتراف المتبادل بتصاريح الأدوية')>",
      "expected_outcome": "<Arabic — one concrete deliverable expected from this meeting (e.g. 'الاتفاق على مسار التفاوض لاتفاقية الاعتراف المتبادل')>"
    }},
    {{
      "entity": "<REAL second institution from research F — different from first>",
      "counterpart": "يُحدَّد لاحقاً",
      "counterpart_title": "<Arabic title>",
      "date": "{dates[min(1, num_days-1)]}",
      "time": "10:30",
      "location": "{venue_str}",
      "talking_points": [
        "<Arabic — specific talking point 1>",
        "<Arabic — specific talking point 2>",
        "<Arabic — specific talking point 3>"
      ],
      "strategic_objective": "<Arabic — specific measurable goal>",
      "expected_outcome": "<Arabic — concrete deliverable>"
    }},
    {{
      "entity": "<REAL third institution — pharmaceutical association or health tech body>",
      "counterpart": "يُحدَّد لاحقاً",
      "counterpart_title": "<Arabic title>",
      "date": "{dates[min(2, num_days-1)]}",
      "time": "16:00",
      "location": "{venue_str}",
      "talking_points": [
        "<Arabic — specific investment or commercial cooperation point>",
        "<Arabic — specific technology transfer or R&D opportunity>",
        "<Arabic — specific market development initiative>"
      ],
      "strategic_objective": "<Arabic>",
      "expected_outcome": "<Arabic>"
    }}
  ],

  "consulate": {{
    "name": "<full official Arabic name of Saudi consulate in {city}>",
    "address": "<full verified street address from research D/C — write NOT FOUND if unverified>",
    "phone": "<verified phone number from research — NOT FOUND if unverified>",
    "email": "<verified email — NOT FOUND if unverified>",
    "emergency_phone": "<24-hour emergency line — NOT FOUND if unverified>",
    "working_hours": "من الاثنين إلى الجمعة، 9:00–17:00",
    "consul_name": "<EXACT name from research C — write '—' if NOT FOUND>",
    "consul_title": "القنصل العام للمملكة العربية السعودية",
    "consul_bio": "<Arabic 2-3 sentences about consular services and mission support available to Saudi official delegations>"
  }},

  "weather": {weather_skeleton},
  "prayer_times": {prayer_skeleton},

  "key_ambassadors": [{{
    "name": "<EXACT ambassador name from research K — write 'يُحدَّد لاحقاً' if NOT FOUND>",
    "title": "سفير خادم الحرمين الشريفين لدى {country_en}",
    "country": "{country_en}",
    "relevance": "<Arabic 2-3 sentences — ambassador's specific role in facilitating this delegation, current bilateral initiatives they're managing, how to engage through the embassy>"
  }}],

  "participants": [],

  "suggested_meetings": [
    {{"entity":"<REAL regulatory authority from research F>","country":"{country_en}","priority":"high","description":"<Arabic — specific regulatory mandate of this body>","rationale":"<Arabic — specific harmonization or recognition opportunity with SFDA>"}},
    {{"entity":"<REAL health ministry from research>","country":"{country_en}","priority":"high","description":"<Arabic>","rationale":"<Arabic — specific Vision 2030 health cooperation angle>"}},
    {{"entity":"<REAL food/standards body from research F>","country":"{country_en}","priority":"medium","description":"<Arabic>","rationale":"<Arabic — halal standards or food safety harmonization>"}},
    {{"entity":"<REAL pharma industry body>","country":"{country_en}","priority":"medium","description":"<Arabic>","rationale":"<Arabic — pharma market access, clinical trials, investment>"}},
    {{"entity":"<REAL health research institution>","country":"{country_en}","priority":"low","description":"<Arabic>","rationale":"<Arabic — research collaboration, capacity building>"}}
  ],

  "attachments": [
    "{event_name} — البرنامج الرسمي {year}.pdf",
    "الموجز الاقتصادي لدولة {country_en} {year}.pdf",
    "رؤية المملكة العربية السعودية 2030 — برنامج تحويل القطاع الصحي.pdf",
    "الخطة الاستراتيجية للهيئة العامة للغذاء والدواء 2025–2030.pdf",
    "السيرة الذاتية لأعضاء الوفد الرسمي.pdf",
    "الموجز الثنائي السعودي–{country_en} — التعاون في القطاع الصحي والدوائي.pdf",
    "ملفات المتحدثين الرئيسيين — {event_name} {year}.pdf",
    "متطلبات الدخول إلى {country_en} للجوازات الدبلوماسية والرسمية.pdf"
  ]

}}

FINAL QUALITY CHECKS — before returning JSON verify:
1. Every speaker name is REAL (from research A or website data) — not a placeholder
2. Every session title is REAL (from research A) — not a placeholder  
3. ambassador_name: EXACT from research K — 'يُحدَّد لاحقاً' if NOT FOUND
4. consul_name: EXACT from research C — '—' if NOT FOUND
5. trade_volume: from research E with year — '—' if NOT FOUND
6. head_of_state: use leader override if provided, otherwise from research C
7. conference_tracks: each item MUST be {{"name": "...", "explanation": "..."}} — not a string
8. All intel_* fields: non-empty arrays of Arabic bullet strings
9. All ns_* fields: non-empty Arabic paragraphs
10. weather: {num_days} objects with integer temperatures for {city} in {start_date[:7]}"""

    system_msg = (
        "Saudi government strategic briefing specialist. "
        "Output ONLY valid JSON — no markdown fences, no comments, no trailing commas. "
        "ANTI-HALLUCINATION PROTOCOL:\n"
        "- Use ONLY names/addresses/statistics that appear in the research data above\n"
        "- For ambassador: copy EXACTLY from research K or write 'يُحدَّد لاحقاً'\n"
        "- For consul: copy EXACTLY from research C or write '—'\n"
        "- For speakers: use ONLY names that appear in research A or website data\n"
        "- For session titles: use ONLY titles from research A or website data\n"
        "- NEVER invent official names, addresses, phone numbers, or statistics\n"
        "- conference_tracks MUST be objects {name, explanation} — never plain strings\n"
        f"- weather array must have exactly {num_days} items with int temperatures\n"
        "- Replace ALL <angle bracket> placeholders with real Arabic strategic content"
    )

    if use_openai:
        try:
            r = oai.chat.completions.create(
                model="gpt-4o",
                temperature=0.15,
                max_tokens=12000,
                response_format={"type": "json_object"},
                messages=[
                    {"role": "system", "content": system_msg},
                    {"role": "user", "content": prompt},
                ],
            )
            return _safe_json_load(_clean_json(r.choices[0].message.content.strip()))
        except Exception as e:
            print(f"[AI] OpenAI JSON gen failed: {e}. Falling back to Claude...")

    if use_claude:
        resp = _call_claude(
            claude,
            model="claude-sonnet-4-20250514",
            max_tokens=10000,
            system=system_msg,
            messages=[{"role": "user", "content": prompt}],
        )
        return _safe_json_load(_clean_json(_extract_claude_text(resp)))

    raise RuntimeError("No AI available for JSON generation")


# ─── Public Entry Point ────────────────────────────────────────────────────────

def generate_report_content(event_name, city, country, start_date, end_date,
                             venue, event_type, context, language='Arabic',
                             event_website=''):
    """
    PIPELINE v3.0
    Phase 0   → translate Arabic inputs to English
    Phase 1A  → Claude Sonnet + web_search (deep research, 8 turns)
    Phase 1B  → OpenAI gpt-4o-search (parallel research)
    Phase 1C  → Website scraping (if event_website provided)
    Phase 2   → OpenAI gpt-4o / Claude Sonnet — JSON generation (12k tokens)
    """
    anthropic_key = getattr(settings, 'ANTHROPIC_API_KEY', '')
    openai_key    = getattr(settings, 'OPENAI_API_KEY', '')

    use_claude = bool(anthropic_key and 'YOUR' not in anthropic_key)
    use_openai = bool(openai_key    and 'YOUR' not in openai_key)

    if not use_claude and not use_openai:
        raise ValueError(
            "No API key configured. Add to backend/.env:\n"
            "  ANTHROPIC_API_KEY=sk-ant-...\n"
            "  OPENAI_API_KEY=sk-proj-..."
        )

    claude = None
    oai    = None

    if use_claude:
        import anthropic as _ant
        claude = _ant.Anthropic(api_key=anthropic_key)

    if use_openai:
        try:
            from openai import OpenAI as _OAI
            oai = _OAI(api_key=openai_key)
        except Exception:
            use_openai = False

    # ── Phase 0: Translate ─────────────────────────────────────────────────────
    def _translate(text):
        if not text or not _has_arabic(text):
            return text
        if use_claude:
            r = claude.messages.create(
                model="claude-haiku-4-5-20251001",
                max_tokens=100,
                messages=[{"role": "user", "content": f"Translate to English only, nothing else: {text}"}]
            )
            return _extract_claude_text(r).strip()
        r = oai.chat.completions.create(
            model="gpt-4o-mini", max_tokens=80,
            messages=[{"role": "user", "content": f"Translate to English only: {text}"}],
        )
        return r.choices[0].message.content.strip()

    country_en = _translate(country)
    city_en    = _translate(city)

    # ── Known-conference fallback knowledge base ───────────────────────────────
    # When APIs are overloaded, inject verified facts for well-known conferences
    # so the generator never produces empty reports for identifiable events.
    KNOWN_CONFERENCES = {
        "milken": {
            "full_name": "Milken Institute Global Conference",
            "organizer": "Milken Institute",
            "organizer_type": "Nonprofit, nonpartisan think tank founded 1991, headquartered in Santa Monica, California",
            "ceo": "Richard Ditizio (CEO, Milken Institute)",
            "founder": "Michael Milken (Chairman)",
            "website": "https://www.globalconference.org",
            "2025": {
                "edition": "28th Annual",
                "theme": "Toward a Flourishing Future",
                "dates": "May 4–7, 2025",
                "venue": "The Beverly Hilton and The Waldorf Astoria Beverly Hills, Los Angeles",
                "attendees": "5,000 attendees from 80+ countries",
                "speakers_count": "1,000 speakers",
                "sessions_count": "170 public sessions",
                "confirmed_speakers": [
                    "Jane Fraser — CEO, Citi",
                    "Vis Raghavan — Head of Banking and Executive Vice Chair, Citi",
                    "Richard Ditizio — CEO, Milken Institute",
                ],
                "topics": "Greater access to capital, state of public health, evolving geopolitical tensions, climate change, artificial intelligence, impact investing",
                "media": "CNBC, Bloomberg, Yahoo Finance, Fox Business broadcasting live",
            },
            "history": {
                "2024": {"theme": "Shaping a Healthier, More Equitable and Prosperous Future", "attendance": "4,500+"},
                "2023": {"theme": "Towards a New World Order", "attendance": "4,000+"},
                "2022": {"theme": "Drivers of Change", "attendance": "3,500+"},
            }
        },
        "wef": {
            "full_name": "World Economic Forum Annual Meeting",
            "organizer": "World Economic Forum",
            "venue_city": "Davos, Switzerland",
        },
        "wha": {
            "full_name": "World Health Assembly",
            "organizer": "World Health Organization",
            "venue_city": "Geneva, Switzerland",
        },
    }

    def _get_conference_knowledge(event_name_lower):
        for key, data in KNOWN_CONFERENCES.items():
            if key in event_name_lower or data.get("full_name", "").lower() in event_name_lower:
                return data
            # Also check if all words of the key appear in the name
            if all(word in event_name_lower for word in key.split()):
                return data
        return None

    # ── Phase 1: Research with retry logic ────────────────────────────────────
    research_parts = []
    event_name_lower = event_name.lower()

    def _try_research_with_retry(fn, label, max_attempts=2, retry_wait=45):
        """Run a research function with retry on overload errors."""
        for attempt in range(max_attempts):
            try:
                result = fn()
                if result and result.strip():
                    return result
            except Exception as e:
                err = str(e)
                if '529' in err or 'overload' in err.lower():
                    if attempt < max_attempts - 1:
                        print(f"[AI] {label} overloaded — waiting {retry_wait}s before retry...")
                        time.sleep(retry_wait)
                    else:
                        print(f"[AI] {label} still overloaded after {max_attempts} attempts — skipping")
                elif 'timeout' in err.lower() or 'timed out' in err.lower():
                    if attempt < max_attempts - 1:
                        print(f"[AI] {label} timed out — retrying in 20s...")
                        time.sleep(20)
                    else:
                        print(f"[AI] {label} timed out after {max_attempts} attempts — skipping")
                else:
                    print(f"[AI] {label} error: {e}")
                    break
        return ""

    # 1A: Claude deep research
    if use_claude:
        print("[AI] Phase 1A: Claude Sonnet deep research...")
        r = _try_research_with_retry(
            lambda: _research_claude(claude, event_name, city_en, country_en, start_date, end_date, venue, event_website),
            "Claude research",
            max_attempts=2, retry_wait=45
        )
        if r:
            research_parts.append("=== CLAUDE RESEARCH ===\n" + r)
            print(f"[AI] Claude research: {len(r)} chars")

    if use_claude and use_openai:
        time.sleep(3)

    # 1B: OpenAI parallel research
    if use_openai:
        print("[AI] Phase 1B: OpenAI search research...")
        r = _try_research_with_retry(
            lambda: _research_openai(oai, event_name, city_en, country_en, start_date, end_date, venue, event_website),
            "OpenAI research",
            max_attempts=2, retry_wait=30
        )
        if r:
            research_parts.append("=== OPENAI RESEARCH ===\n" + r)
            print(f"[AI] OpenAI research: {len(r)} chars")

    # 1C: Website scraping
    if event_website and event_website.startswith('http'):
        print(f"[AI] Phase 1C: Scraping official website {event_website}...")
        ws = _try_research_with_retry(
            lambda: _scrape_event_website(claude, oai, use_claude, use_openai, event_website, event_name),
            "Website scrape",
            max_attempts=2, retry_wait=30
        )
        if ws:
            research_parts.insert(0, ws)
            print(f"[AI] Website data: {len(ws)} chars")

    # 1D: Known-conference fallback — always inject if conference is identifiable
    conf_knowledge = _get_conference_knowledge(event_name_lower)
    if conf_knowledge:
        year = start_date[:4]
        year_data = conf_knowledge.get(year, {})
        kb_lines = [
            f"=== VERIFIED CONFERENCE KNOWLEDGE BASE ===",
            f"Conference: {conf_knowledge.get('full_name', event_name)}",
            f"Organizer: {conf_knowledge.get('organizer', '')} — {conf_knowledge.get('organizer_type', '')}",
            f"CEO/Leader: {conf_knowledge.get('ceo', '')}",
            f"Founder: {conf_knowledge.get('founder', '')}",
        ]
        if year_data:
            kb_lines += [
                f"\n{year} EDITION:",
                f"  Edition number: {year_data.get('edition', '')}",
                f"  Official theme: {year_data.get('theme', '')}",
                f"  Dates: {year_data.get('dates', '')}",
                f"  Venue: {year_data.get('venue', '')}",
                f"  Attendance: {year_data.get('attendees', '')}",
                f"  Speakers: {year_data.get('speakers_count', '')}",
                f"  Sessions: {year_data.get('sessions_count', '')}",
                f"  Topics: {year_data.get('topics', '')}",
                f"  Media coverage: {year_data.get('media', '')}",
                f"\nCONFIRMED SPEAKERS ({year}):",
            ]
            for sp in year_data.get('confirmed_speakers', []):
                kb_lines.append(f"  - {sp}")
        hist = conf_knowledge.get('history', {})
        if hist:
            kb_lines.append("\nPAST EDITIONS:")
            for yr, hdata in sorted(hist.items(), reverse=True):
                kb_lines.append(f"  {yr}: Theme='{hdata.get('theme','')}', Attendance={hdata.get('attendance','')}")
        kb_lines += [
            "\nUSA — VERIFIED FACTS (as of 2025):",
            "  Saudi Ambassador to USA: HRH Princess Reema bint Bandar (since Feb 2019, first female Saudi ambassador)",
            "  Embassy: 601 New Hampshire Ave NW, Washington DC 20037 | Tel: (202) 342-3800 | info@saudiembassy.net",
            "  Saudi Consulate LA: 12400 Wilshire Blvd Suite 700, Los Angeles CA 90025 | Tel: (310) 479-6000 | uscacon@mofa.gov.sa",
            "  Consul General LA: Mr. Fawaz Alshubaili",
            "  US President (2025): Donald J. Trump (47th President, since Jan 20 2025)",
            "  US GDP (2025, IMF): $30.62 trillion",
            "  US Population (2025): ~347 million",
            "  US GDP per capita (2025): ~$88,000",
            "  US-Saudi bilateral trade (2024, USTR): $39.5 billion total (goods + services)",
            "  US goods exports to Saudi: $13.1 billion (2024)",
            "  US goods imports from Saudi: $12.9 billion (2024)",
            "  US FDA equivalent: U.S. Food and Drug Administration (FDA), Commissioner: Robert Califf (2022–)",
            "  US Health Ministry equivalent: Department of Health and Human Services (HHS)",
            "  Prayer times LA (May 2025): Fajr ~05:18, Dhuhr ~12:15, Asr ~15:45, Maghrib ~19:46, Isha ~21:11",
            "  Weather LA (May 2025): Highs 26-29°C, Lows 15-17°C, Mostly sunny, low humidity",
        ]
        kb_text = "\n".join(kb_lines)
        # Always insert knowledge base — even if research succeeded (it adds verified facts)
        research_parts.append(kb_text)
        print(f"[AI] Knowledge base injected: {len(kb_text)} chars")

    research = (
        "COMBINED RESEARCH:\n\n" + "\n\n".join(research_parts)
        if research_parts else
        f"No research available for {event_name} in {city_en}. Generate best-effort content for {country_en}."
    )
    total_research = len(research)
    print(f"[AI] Total research: {total_research} chars")

    # ── Phase 2: Generate JSON ─────────────────────────────────────────────────
    # Only need cooldown if Claude was used for research
    if use_claude and research_parts:
        wait = 65
        print(f"[AI] Cooling down {wait}s before JSON gen...")
        time.sleep(wait)

    print("[AI] Phase 2: Generating JSON...")
    data = _generate_json(
        research, event_name, city, country, country_en,
        start_date, end_date, venue, event_type, context,
        oai, claude, use_openai, use_claude,
    )

    # ── Post-processing ────────────────────────────────────────────────────────

    # Fix CEO name spelling
    for member in data.get('delegation', []):
        name = member.get('name', '')
        if 'الجاضي' in name or 'الجاضعي' in name:
            member['name'] = name.replace('الجاضي', 'الجضعي').replace('الجاضعي', 'الجضعي')

    # Sanitize placeholder leakage
    FAKES = {'John Smith', 'Jane Doe', 'Samandal', 'سمندل', 'جون سميث',
             'جين دو', 'يُعبأ لاحقاً', 'placeholder', 'name here'}
    def _is_placeholder(v):
        return (not v or v in FAKES or
                (isinstance(v, str) and ('<' in v or '>' in v or v.startswith('placeholder'))))

    if _is_placeholder(data.get('embassy', {}).get('ambassador_name', '')):
        data.setdefault('embassy', {})['ambassador_name'] = 'يُحدَّد لاحقاً'
    if _is_placeholder(data.get('consulate', {}).get('consul_name', '')):
        data.setdefault('consulate', {})['consul_name'] = '—'
    for m in data.get('bilateral_meetings', []):
        if _is_placeholder(m.get('counterpart', '')):
            m['counterpart'] = 'يُحدَّد لاحقاً'
    for amb in data.get('key_ambassadors', []):
        if _is_placeholder(amb.get('name', '')):
            amb['name'] = 'يُحدَّد لاحقاً'

    # Normalize conference_tracks — ensure objects with name+explanation
    tracks = data.get('conference_tracks', [])
    normalized_tracks = []
    for t in tracks:
        if isinstance(t, dict) and t.get('name'):
            normalized_tracks.append({
                'name': t.get('name', ''),
                'explanation': t.get('explanation', t.get('description', ''))
            })
        elif isinstance(t, str) and t.strip():
            normalized_tracks.append({
                'name': t.strip(),
                'explanation': 'محور استراتيجي ذو صلة مباشرة بمهام الهيئة وأهداف رؤية 2030 في قطاع الصحة والدواء والغذاء.'
            })
    data['conference_tracks'] = normalized_tracks

    # Normalize sessions speakers list → string
    for dk in ('day1', 'day2', 'day3', 'day4'):
        for s in data.get('sessions', {}).get(dk, []):
            sp = s.get('speakers', '')
            if isinstance(sp, list):
                s['speakers'] = '، '.join(str(x) for x in sp if x)

    # Normalize weather temperatures → int
    for d in data.get('weather', []):
        for k in ('high', 'low'):
            v = str(d.get(k, '')).replace('°C', '').replace('°', '').strip()
            try:
                d[k] = int(float(v))
            except Exception:
                pass

    # Remove placeholder speakers
    real_speakers = [
        sp for sp in data.get('speakers', [])
        if sp.get('name') and not _is_placeholder(sp.get('name', ''))
    ]
    data['speakers'] = real_speakers

    print(f"[AI] Done. Fields: {list(data.keys())}")
    print(f"[AI] Speakers: {len(data.get('speakers', []))}, "
          f"Sessions day1: {len(data.get('sessions', {}).get('day1', []))}, "
          f"Tracks: {len(data.get('conference_tracks', []))}")

    return data
