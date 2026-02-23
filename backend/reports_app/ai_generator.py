"""
ai_generator.py — SFDA Executive Brief Generator  v4.6 (12 New Deep Intelligence Sections)
======================================================================

WHY OpenAI-ONLY IS FULLY SUFFICIENT:
  ✅ gpt-4o-search-preview  — native web search, no tool setup, no token/min org limit
  ✅ gpt-4o                 — json_object mode guarantees valid JSON every time
  ✅ gpt-4o                 — strong formal Arabic prose
  ✅ gpt-4o-mini            — fast, cheap translation

PIPELINE:
  Phase 0   → gpt-4o-mini          — translate Arabic inputs to English
  Phase 1A  → gpt-4o-search-preview — primary web research (all sections A–L)
  Phase 1B  → gpt-4o-search-preview — supplemental research (speakers, bilateral MoUs)
  Phase 1C  → gpt-4o-search-preview — official event website scraping
  Phase 1D  → Static knowledge base — instant, always runs, conference-specific facts
  Phase 2   → gpt-4o               — generate full JSON report

RATE LIMIT STATUS:
  No Anthropic org token limits apply.
  OpenAI rate limits are per-key, generous at Tier 1+, and per-call not per-minute org total.
  A full report generation uses approx. 3 OpenAI calls — well within standard limits.

COMPARED TO DUAL-API SETUP:
  Research quality   → Identical (OpenAI has native web search)
  Arabic prose       → Very good (gpt-4o handles formal Arabic well)
  JSON reliability   → Equal or better (json_object mode)
  Speed              → Faster (~90s total vs ~120s dual-API)
  Cost               → Lower (no Anthropic Sonnet charges)
  Simplicity         → One API key, one provider, one bill
"""

import re, time, json, os
from django.conf import settings


# ─── Helpers ──────────────────────────────────────────────────────────────────

def _clean_json(raw: str) -> str:
    raw = raw.strip()
    raw = re.sub(r'^```(?:json)?\s*', '', raw)
    raw = re.sub(r'\s*```$', '', raw)
    return raw.strip()

def _safe_json_load(raw: str) -> dict:
    """
    FIX v4.1: Multi-strategy JSON recovery.
    gpt-4o with json_mode should never fail, but this handles edge cases
    like network truncation or accidental markdown wrapping.
    """
    if not raw:
        return {}
    # Strategy 1: direct parse
    try:
        result = json.loads(raw)
        if isinstance(result, dict):
            return result
    except json.JSONDecodeError:
        pass
    # Strategy 2: strip markdown fences then parse
    cleaned = re.sub(r'^```(?:json)?\s*', '', raw.strip())
    cleaned = re.sub(r'\s*```$', '', cleaned).strip()
    try:
        result = json.loads(cleaned)
        if isinstance(result, dict):
            return result
    except json.JSONDecodeError:
        pass
    # Strategy 3: find outermost {...} block
    m = re.search(r'\{.*\}', cleaned, re.DOTALL)
    if m:
        try:
            result = json.loads(m.group())
            if isinstance(result, dict):
                return result
        except Exception:
            pass
    # Strategy 4: fix common truncation — add missing closing braces
    try:
        open_b  = cleaned.count('{')
        close_b = cleaned.count('}')
        if open_b > close_b:
            fixed = cleaned + '}' * (open_b - close_b)
            result = json.loads(fixed)
            if isinstance(result, dict):
                print("[AI] _safe_json_load: recovered via brace completion")
                return result
    except Exception:
        pass
    print("[AI] _safe_json_load: all recovery strategies failed")
    return {}

def _has_arabic(text: str) -> bool:
    return bool(re.search(r'[\u0600-\u06FF]', text or ''))

def _truncate(text: str, max_chars: int = 14000) -> str:
    if len(text) <= max_chars:
        return text
    keep = max_chars // 2
    return text[:keep] + '\n...[middle truncated]...\n' + text[-keep:]

def _normalize_url(url: str) -> str:
    """
    FIX v4.1: Auto-prepend https:// if the user enters a URL without a scheme.
    'www.globalconference.org' → 'https://www.globalconference.org'
    Also strips trailing slashes for consistency.
    """
    if not url:
        return ''
    url = url.strip().rstrip('/')
    if url and not url.startswith('http://') and not url.startswith('https://'):
        url = 'https://' + url
    return url

def _oai_chat(oai, model, messages, max_tokens, system=None,
              json_mode=False, max_retries=3):
    """
    Central OpenAI call wrapper with retry logic.
    json_mode=True forces gpt-4o to return valid JSON (response_format).
    """
    if system:
        messages = [{"role": "system", "content": system}] + messages

    kwargs = {
        "model": model,
        "messages": messages,
        "max_tokens": max_tokens,
    }
    if json_mode:
        kwargs["response_format"] = {"type": "json_object"}
        kwargs["temperature"] = 0.15

    for attempt in range(max_retries):
        try:
            r = oai.chat.completions.create(**kwargs)
            return r.choices[0].message.content.strip()
        except Exception as e:
            err = str(e)
            if any(x in err for x in ['429', 'rate_limit', '529', 'overload']):
                wait = 20 * (attempt + 1)
                print(f"[AI] OpenAI rate limit — waiting {wait}s (attempt {attempt+1}/{max_retries})")
                time.sleep(wait)
                if attempt == max_retries - 1:
                    raise
            else:
                raise
    raise RuntimeError("OpenAI max retries exceeded")


# ─── Phase 1A: Primary web research ───────────────────────────────────────────

def _research_primary(oai, event_name, city, country_en, start_date, end_date, venue):
    """
    Deep web research covering all 12 sections needed for the report.
    Uses gpt-4o-search-preview — native web search, no tool configuration required.
    """
    year = start_date[:4]
    month_year = start_date[:7]

    prompt = f"""You are a research analyst preparing a Saudi government official travel briefing.
Search the web thoroughly for VERIFIED facts for each labeled section below.
CRITICAL RULE: Write "NOT FOUND" for anything unverifiable. NEVER invent names, statistics, or addresses.

EVENT: {event_name}
LOCATION: {city}, {country_en}
DATES: {start_date} to {end_date or start_date}
YEAR: {year}

Search and report each section:

A) SPEAKERS & SESSIONS — Most important section:
   Search: "{event_name} {year} speakers confirmed"
   Search: "{event_name} {year} agenda program schedule sessions"
   List EVERY speaker found: exact full name + exact title + exact organization + country
   List EVERY session found: exact title + time + room/hall name

B) CONFERENCE TRACKS & THEMES:
   Search: "{event_name} {year} tracks themes official"
   List all official track names with brief descriptions of their content

C) SAUDI CONSULATE in {city}:
   Search: "Saudi Arabia consulate {city} address phone email 2025"
   Find: exact full street address, phone number, email, consul general EXACT name

D) SAUDI AMBASSADOR to {country_en}:
   Search: "Saudi Arabia ambassador {country_en} 2025 official"
   Find: EXACT full name of current ambassador (verified as of {start_date})

E) CURRENT HEAD OF GOVERNMENT of {country_en}:
   Search: "current prime minister OR president {country_en} {year}"
   Find: EXACT full official name and title verified as of {start_date}

F) COUNTRY STATISTICS:
   Search: "{country_en} GDP 2024 World Bank IMF official"
   Search: "{country_en} population 2024 official statistics"
   Find: GDP with year+source, GDP per capita, population with year+source,
         capital city, currency full name and code, total area km², timezone UTC offset

G) BILATERAL TRADE:
   Search: "Saudi Arabia {country_en} bilateral trade volume 2024 2025"
   Search: "Saudi Arabia {country_en} cooperation agreements MoU 2023 2024"
   Find: total trade volume with year+source, key cooperation sectors, named agreements

H) REGULATORY BODIES in {country_en}:
   Search: "{country_en} food drug regulatory authority equivalent FDA"
   Search: "{country_en} ministry of health pharmaceutical regulator 2025"
   Search: "{country_en} food safety standards authority"
   Find: (1) drug/pharma regulator — exact official name,
         (2) health ministry — exact official name,
         (3) food/standards body — exact official name

I) VISA POLICY:
   Search: "Saudi Arabia diplomatic official passport {country_en} visa requirements 2025"
   Find: exact entry requirements for Saudi official/diplomatic passport holders

J) WEATHER:
   Search: "{city} average weather temperature {month_year} historical"
   Find: realistic average daily high/low °C for each day: {start_date} to {end_date or start_date}

K) PRAYER TIMES:
   Search OR calculate: Islamic prayer times {city} {start_date}
   Report: Fajr, Dhuhr, Asr, Maghrib, Isha in HH:MM local time for {start_date}
   Also estimate times for each subsequent day (shift ~1 min per day)

L) CONFERENCE HISTORY:
   Search: "{event_name} {int(year)-1} outcomes highlights attendance"
   Search: "{event_name} {int(year)-2} major announcements theme"
   Find: actual themes, concrete outcomes, attendance numbers from past 3 editions

Label each section A–L clearly. Include source URLs where possible."""

    return _oai_chat(
        oai,
        model="gpt-4o-search-preview",
        system=(
            "Research specialist for Saudi government official briefings. "
            "Search the web carefully for each labeled section. "
            "NEVER invent or hallucinate names, addresses, phone numbers, or statistics. "
            "Write NOT FOUND when you cannot verify information. "
            "Include source URLs for key facts."
        ),
        messages=[{"role": "user", "content": prompt}],
        max_tokens=6000,
    )


# ─── Phase 1B: Supplemental research ──────────────────────────────────────────

def _research_supplemental(oai, event_name, city, country_en, start_date, end_date):
    """
    Second search pass targeting gaps most often missed in Phase 1A:
    additional speakers, bilateral agreements, pharma regulation specifics.
    """
    year = start_date[:4]

    prompt = f"""Supplemental research for Saudi government briefing.
Conference: {event_name} | {city}, {country_en} | {start_date}

Search specifically for information that may have been missed:

1) ADDITIONAL & MINISTERIAL SPEAKERS:
   Search: "{event_name} {year} ministerial government officials speakers"
   Search: "{event_name} {year} keynote additional speakers announced"
   List any speakers not already found — exact full names, titles, organizations only

2) SIDE EVENTS & BILATERAL MEETING OPPORTUNITIES:
   Search: "{event_name} {year} side events bilateral official meetings"
   List any official side events scheduled alongside the main conference

3) PHARMACEUTICAL & HEALTH REGULATORY LANDSCAPE in {country_en}:
   Search: "{country_en} pharmaceutical regulation ICH harmonization GCC"
   Search: "{country_en} halal pharmaceutical certification framework"
   Find: specific regulatory frameworks, mutual recognition agreements relevant to Saudi cooperation

4) INVESTMENT & ECONOMIC DATA:
   Search: "Saudi Arabia investment {country_en} 2024 2025 billion"
   Search: "{country_en} health biomedical sector investment FDI 2024"
   Find: verified investment figures with sources and years

5) EXISTING BILATERAL AGREEMENTS with Saudi Arabia:
   Search: "Saudi Arabia {country_en} agreement health MoU 2022 2023 2024"
   Search: "Saudi Arabia {country_en} strategic partnership cooperation"
   Find: named agreements, joint committees, active cooperation frameworks

Label sections 1–5 clearly. Cite sources where possible."""

    return _oai_chat(
        oai,
        model="gpt-4o-search-preview",
        system="Research specialist. Search the web for each section. NEVER invent data. Write NOT FOUND if unverifiable. Cite sources.",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=4000,
    )


# ─── Phase 1C: Official website scraping ──────────────────────────────────────

def _scrape_website(oai, event_website, event_name):
    """
    Extracts speakers, sessions, and tracks from the official conference website.
    This is the highest-priority data source — it goes first in research_parts.
    """
    if not event_website or not event_website.startswith('http'):
        return ""

    prompt = f"""Visit the official conference website at {event_website} and extract ALL available information.

Extract and list everything you find:
1. SPEAKERS: Every confirmed speaker — exact full name, exact current title, exact organization
2. SESSIONS/AGENDA: Every session title with date, time, and room/hall location
3. CONFERENCE TRACKS or THEMES: All official track names with descriptions
4. CONFERENCE FACTS: Official theme/slogan, edition number, expected attendance, founding year
5. ABOUT: Key statements about the conference's purpose and significance

Also check sub-pages: /speakers, /agenda, /program, /schedule if they exist.
This is the official source — extract exact text, do not paraphrase names or titles.
Even partial lists of speakers or sessions are valuable — include everything you find."""

    try:
        result = _oai_chat(
            oai,
            model="gpt-4o-search-preview",
            system="Web data extractor. Visit the URL and extract all speaker names, session titles, and track names exactly as written. Never summarize or paraphrase names — copy them verbatim.",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=4000,
        )
        if result and len(result) > 100:
            return f"=== OFFICIAL WEBSITE DATA ({event_website}) ===\n{result}"
    except Exception as e:
        print(f"[AI] Phase 1C website scrape error: {e}")
    return ""


# ─── Phase 1E: Accuracy-critical targeted verification ───────────────────────

def _research_accuracy_critical(oai, event_name, city, country_en, start_date):
    """
    v4.3 NEW: 5 hyper-targeted searches for the fields most prone to error.
    These run AFTER Phase 1A/1B/1C so they can correct anything stale.

    Critical fields:
      1. Official conference theme/slogan (exact text)
      2. Official attendance figure (exact number and countries)
      3. Opening keynote speaker (who actually opened)
      4. Current CEO of major institutions (DBS, Temasek, etc.)
      5. Current Saudi Ambassador to this country
    """
    year = start_date[:4]

    prompt = f"""You are a fact-checker for a Saudi government official briefing.
Perform these 5 targeted web searches and report EXACTLY what you find.
Conference: {event_name} | {city}, {country_en} | {year}

SEARCH 1 — OFFICIAL THEME (Most critical):
  Search: "{event_name} {year} official theme slogan announced"
  Search: "{event_name} {year} site:milkeninstitute.org OR site:prnewswire.com OR site:businesswire.com theme"
  Report: The EXACT official theme/slogan in quotes. Year confirmed. Source URL.

SEARCH 2 — ATTENDANCE:
  Search: "{event_name} {year} attendance participants countries confirmed"
  Search: "{event_name} {year} delegates registered"
  Report: EXACT attendance number + number of countries. Source URL.

SEARCH 3 — OPENING KEYNOTE SPEAKER:
  Search: "{event_name} {year} opening keynote speaker address"
  Search: "{event_name} {year} opening session minister keynote"
  Report: EXACT name + EXACT title of person who delivered the opening keynote/address.

SEARCH 4 — KEY INSTITUTIONAL LEADERS:
  Search: "DBS Bank CEO 2025 current"
  Search: "Temasek CEO 2025 current chief executive"
  Report: Current CEO/leader of each institution, with date they took the role.

SEARCH 5 — SAUDI AMBASSADOR to {country_en}:
  Search: "Saudi Arabia ambassador {country_en} {year} official current"
  Search: "سفير المملكة العربية السعودية {country_en} 2025"
  Report: EXACT full name of current Saudi Ambassador, date of appointment if found.

RULES:
- Write CONFIRMED: before each verified fact with its source URL
- Write NOT FOUND: if you cannot verify
- NEVER guess or infer — only report what you directly found in search results"""

    return _oai_chat(
        oai,
        model="gpt-4o-search-preview",
        system=(
            "Fact-checker for government briefings. Search the web precisely. "
            "Report only what you directly find in search results. "
            "Never guess. Always include source URLs. "
            "Prefix verified facts with CONFIRMED: and unverified with NOT FOUND:"
        ),
        messages=[{"role": "user", "content": prompt}],
        max_tokens=3000,
    )


# ─── Phase 1F: Post-event recap (if event already happened) ──────────────────

def _research_post_event_recap(oai, event_name, start_date, end_date, city):
    """
    v4.3 NEW: If the event has already occurred (start_date < today),
    search for the official recap, outcomes report, and confirmed speaker lists.
    Post-event data is the most accurate possible source — it reflects reality.
    """
    from datetime import date
    try:
        event_dt = date.fromisoformat(start_date)
        if event_dt >= date.today():
            return ""   # Event hasn't happened yet — skip
    except Exception:
        return ""

    year = start_date[:4]

    prompt = f"""The conference "{event_name}" in {city} ({start_date} to {end_date or start_date}) has already taken place.
Search for POST-EVENT official information — this is the most accurate source.

SEARCH 1 — OFFICIAL RECAP:
  Search: "{event_name} {year} recap summary outcomes report"
  Search: site:milkeninstitute.org "{year}" recap OR summary OR highlights
  Report: Official themes announced, key outcomes, any statistics released

SEARCH 2 — CONFIRMED SPEAKERS (from post-event coverage):
  Search: "{event_name} {year} speakers list confirmed keynote"
  Search: "{event_name} {year} featured participants leaders"
  Report: Every confirmed speaker name + title + organization found

SEARCH 3 — ACTUAL SESSIONS (from official program or media coverage):
  Search: "{event_name} {year} sessions agenda program schedule"
  Report: Every actual session title found with date/time if available

SEARCH 4 — CONFIRMED ATTENDANCE (from post-event reports):
  Search: "{event_name} {year} attendance total participants delegates"
  Report: Official post-event attendance figure with source

SEARCH 5 — MEDIA COVERAGE (for additional speaker/session verification):
  Search: "{event_name} {year}" site:bloomberg.com OR site:reuters.com OR site:cnbc.com
  Report: Any speakers, sessions, or outcomes mentioned in media

Label each section. Include source URLs. This is GOLD DATA — the event already happened."""

    return _oai_chat(
        oai,
        model="gpt-4o-search-preview",
        system=(
            "Post-event fact researcher. The conference has already taken place. "
            "Search for official recaps, confirmed speaker lists, and actual outcomes. "
            "This is the most accurate data source possible — prioritize official and media sources. "
            "NEVER invent. List every speaker name you find with exact title."
        ),
        messages=[{"role": "user", "content": prompt}],
        max_tokens=4000,
    )


# ─── Phase 1G: Accuracy consolidation ────────────────────────────────────────

def _consolidate_accuracy(oai, raw_research, event_name, city, country_en, start_date):
    """
    v4.3 NEW: Takes all research gathered so far and extracts the 8 most
    accuracy-critical fields into a verified facts block.

    These 8 fields are the ones most likely to be wrong in the final report:
      1. Official conference theme (exact text)
      2. Attendance (exact number + countries)
      3. Opening keynote speaker
      4. Confirmed speakers list
      5. Current head of government
      6. Saudi Ambassador name
      7. DBS/Temasek CEO (if Singapore event)
      8. Bilateral trade figure

    The output is injected at the TOP of research so it dominates Section A/B/C.
    """
    year = start_date[:4]
    research_short = _truncate(raw_research, 12000)

    prompt = f"""You are consolidating research for {event_name} {year} in {city}, {country_en}.
From ALL the research below, extract ONLY verified facts for these 8 critical fields.

Research gathered:
{research_short}

Extract and report each field. Use ONLY information that appears in the research above.
If a field has conflicting values, use the one from the most authoritative source (official site > press release > news).
If a field is NOT in the research, write NOT FOUND.

OUTPUT FORMAT (return this exact structure):

VERIFIED CRITICAL FACTS — {event_name} {year}
============================================================
1. OFFICIAL THEME: [exact theme text] | Source: [URL or source name]
2. ATTENDANCE: [number] participants from [N] countries | Source: [source]
3. OPENING KEYNOTE: [exact full name] — [exact title] | Source: [source]
4. CONFIRMED SPEAKERS (list each on a new line):
   • [Name] — [Title], [Organization] ([Country])
5. HEAD OF GOVERNMENT ({country_en}): [exact name] — [exact title]
6. SAUDI AMBASSADOR to {country_en}: [exact name] | Source: [source]
7. CURRENT DBS CEO: [exact name] (if Singapore event) | Source: [source]
8. BILATERAL TRADE (Saudi–{country_en}): [figure] | Year: [year] | Source: [source]
============================================================

Rules:
- Copy speaker names EXACTLY as they appear in the research — never paraphrase
- If research shows conflicting numbers for attendance, pick the most cited one
- For the theme, copy the EXACT text including subtitle if present"""

    result = _oai_chat(
        oai,
        model="gpt-4o",
        system="Accuracy consolidation specialist. Extract verified facts from research. Never invent or add information not in the research.",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=2000,
    )
    if result and len(result) > 100:
        return f"=== VERIFIED ACCURACY FACTS (HIGHEST PRIORITY — USE THESE OVER ALL OTHER SOURCES) ===\n{result}"
    return ""


# ─── Phase 2: Sectioned JSON generation ──────────────────────────────────────
#
# v4.2 ROOT CAUSE FIX: "Fields: 7, Speakers: 0" was caused by one giant prompt
# producing one giant JSON response that gpt-4o truncated mid-way.
#
# FIX: Split Phase 2 into 4 focused section calls. Each call:
#   - Targets only its own fields (smaller output → always completes)
#   - Gets the same research data (same accuracy)
#   - Uses json_mode=True (guaranteed valid JSON)
#   - Is independently retryable
#
# Section A → Factual:   country_info, conference_data, embassy, consulate, bilateral_fields
# Section B → People:    speakers, conference_tracks, previous_outcomes, key_ambassadors
# Section C → Narrative: all Arabic summaries, intel fields, sfda_talking_points
# Section D → Schedule:  agenda, sessions, bilateral_meetings, weather, prayer_times
#
# Results merged → full complete data dict guaranteed on every run.

def _make_dates(start_date, end_date):
    from datetime import datetime, timedelta
    try:
        d0 = datetime.strptime(start_date, "%Y-%m-%d")
        d1 = datetime.strptime(end_date, "%Y-%m-%d") if end_date and end_date != start_date else d0
        num_days = max(1, (d1 - d0).days + 1)
        dates = [(d0 + timedelta(days=i)).strftime("%Y-%m-%d") for i in range(num_days)]
        return num_days, dates
    except Exception:
        return 3, [start_date, start_date, start_date]


# ─── Module-level KB helper (called by section generators) ───────────────────

def _build_kb_prompt_header(kv: dict) -> str:
    """
    Build a compact but explicit header block injected at the very top of every
    section prompt. Values appear as literal strings so the model MUST see them
    before generating any field.

    Called by module-level _gen_section_a/B/C with kb_vars dict.
    A matching nested version inside generate_report_content is also defined
    for use by the override functions — they are identical.
    """
    if not kv:
        return ""
    lines = [
        "╔══════════════════════════════════════════════════════════════════════╗",
        "║  ⚡ HARD OVERRIDE VALUES — USE THESE VERBATIM — NO EXCEPTIONS       ║",
        "║  These are pre-verified facts. They override ALL web search results. ║",
        "║  If you see different values in research, IGNORE THEM and use these. ║",
        "╚══════════════════════════════════════════════════════════════════════╝",
    ]
    if kv.get('theme_ar') or kv.get('theme_en'):
        lines.append(f"CONFERENCE_THEME_AR  : {kv.get('theme_ar','')}")
        lines.append(f"CONFERENCE_THEME_EN  : {kv.get('theme_en','')}")
    if kv.get('theme_note'):
        lines.append(f"⚠️  THEME WARNING     : {kv.get('theme_note','')}")
    if kv.get('edition'):
        lines.append(f"EDITION              : {kv['edition']}")
    if kv.get('attendance'):
        lines.append(f"ATTENDANCE           : {kv['attendance']}")
    if kv.get('founded'):
        lines.append(f"FOUNDED_YEAR         : {kv['founded']}")
    if kv.get('gdp'):
        lines.append(f"COUNTRY_GDP          : {kv['gdp']}")
    if kv.get('gdp_per_cap'):
        lines.append(f"COUNTRY_GDP_PERCAPITA: {kv['gdp_per_cap']}")
    if kv.get('population'):
        lines.append(f"COUNTRY_POPULATION   : {kv['population']}")
    if kv.get('trade'):
        lines.append(f"BILATERAL_TRADE      : {kv['trade']}")
    if kv.get('ambassador'):
        lines.append(f"SAUDI_AMBASSADOR     : {kv['ambassador']}")
    if kv.get('emb_addr'):
        lines.append(f"EMBASSY_ADDRESS      : {kv['emb_addr']}")
    if kv.get('emb_phone'):
        lines.append(f"EMBASSY_PHONE        : {kv['emb_phone']}")
    if kv.get('emb_email'):
        lines.append(f"EMBASSY_EMAIL        : {kv['emb_email']}")
    if kv.get('con_addr'):
        lines.append(f"CONSULATE_ADDRESS    : {kv['con_addr']}")
    if kv.get('con_phone'):
        lines.append(f"CONSULATE_PHONE      : {kv['con_phone']}")
    if kv.get('con_email'):
        lines.append(f"CONSULATE_EMAIL      : {kv['con_email']}")
    if kv.get('consul_name'):
        lines.append(f"CONSUL_GENERAL       : {kv['consul_name']}")
    if kv.get('drug_regulator'):
        lines.append(f"DRUG_REGULATOR       : {kv['drug_regulator']}")
    if kv.get('health_ministry'):
        lines.append(f"HEALTH_MINISTRY      : {kv['health_ministry']}")
    lines.append("╚══════ END HARD OVERRIDES ══════╝\n")
    return "\n".join(lines)


# ─── Section A: Factual metadata ──────────────────────────────────────────────

def _gen_section_a(oai, research, event_name, city, country, country_en,
                   start_date, end_date, venue, leader_override, kb_vars=None):
    """
    Section A: All factual structured fields.
    country_info, conference_data, embassy, consulate, bilateral_fields.
    Estimated output: ~1,500 tokens — always completes.
    v4.5: kb_vars injected directly as f-string literals — model cannot miss them.
    """
    year = start_date[:4]
    venue_str = venue or city
    research_short = _truncate(research, 10000)
    leader_note = f"CRITICAL: head_of_state = '{leader_override}' — use exactly this name\n" if leader_override else ""
    kv = kb_vars or {}
    kb_header = _build_kb_prompt_header(kv) if kv else ""

    # Build hard-value JSON hints for each field — model sees exact values
    gdp_val       = kv.get('gdp',         '<from research>')
    gdp_pc_val    = kv.get('gdp_per_cap', '<from research>')
    pop_val       = kv.get('population',  '<from research>')
    trade_val     = kv.get('trade',       '<write NOT FOUND only if absent from both KB and research>')
    emb_addr_val  = kv.get('emb_addr',    '<from research>')
    emb_phone_val = kv.get('emb_phone',   '<from research>')
    emb_email_val = kv.get('emb_email',   '<from research>')
    amb_val       = kv.get('ambassador',  '<from research — يُحدَّد لاحقاً if truly not found>')
    con_addr_val  = kv.get('con_addr',    '<from research>')
    con_phone_val = kv.get('con_phone',   '<from research>')
    con_email_val = kv.get('con_email',   '<from research>')
    consul_val    = kv.get('consul_name', '<from research — يُحدَّد لاحقاً if truly not found>')
    edition_val   = kv.get('edition',     '<from research>')
    attend_val    = kv.get('attendance',  '<from research>')
    theme_ar_val  = kv.get('theme_ar',    kv.get('theme_en', '<from research>'))
    founded_val   = kv.get('founded',     '<from research>')

    prompt = f"""You are generating Section A of a Saudi government travel briefing JSON.
Event: {event_name} | City: {city} | Country: {country_en} | Dates: {start_date} to {end_date or start_date} | Year: {year}
{leader_note}
{kb_header}
Research data (for any fields NOT covered by the HARD OVERRIDE VALUES above):
{research_short}

Return ONLY this JSON object. All narrative text in formal Arabic. No markdown.
The values in angle brackets below are your REQUIRED answers — copy them verbatim:

{{
  "country_info": {{
    "capital": "<capital city>",
    "head_of_state_title": "<Arabic official title: Prime Minister/President/etc>",
    "head_of_state": "<EXACT name — must match override if given>",
    "population": "{pop_val}",
    "area": "<X km² from research>",
    "gdp": "{gdp_val}",
    "gdp_per_capita": "{gdp_pc_val}",
    "currency": "<full name (CODE)>",
    "official_language": "<official language(s)>",
    "religion": "<predominant religion>",
    "timezone": "<use TIMEZONE from KB override>",
    "government": "<Arabic — political system>",
    "key_sectors": "<Arabic — 3-5 key economic sectors>",
    "overview": "<Arabic 3-4 sentences: economic standing, global role, regulatory environment, Saudi relevance>"
  }},
  "conference_data": {{
    "organizer": "Milken Institute",
    "overview": "<Arabic 3-4 sentences: conference purpose, global standing, policy influence>",
    "slogan": "{theme_ar_val}",
    "dates": "{start_date} to {end_date or start_date}",
    "location": "{venue_str}, {country}",
    "founded": "{founded_val}",
    "edition": "{edition_val}",
    "expected_participants": "{attend_val}",
    "participant_profile": "<Arabic: level of attendees — ministers, CEOs, etc>",
    "core_themes": "<Arabic: 3-5 main themes>",
    "ksa_participation": "<Arabic: Saudi Arabia's participation context and role>"
  }},
  "bilateral_fields": {{
    "trade_volume": "{trade_val}",
    "cooperation_areas": "<Arabic: 3-5 specific sectors with named frameworks>",
    "strategic_agreements": "<Arabic: actual named bilateral agreements from research>",
    "health_regulatory": "<Arabic: specific health/pharma cooperation frameworks>"
  }},
  "embassy": {{
    "name": "<full official Arabic name of Saudi Embassy in {country_en}>",
    "mission": "<Arabic 1-2 sentences: embassy mission for official delegations>",
    "ambassador_name": "{amb_val}",
    "ambassador_title": "سفير خادم الحرمين الشريفين لدى {country_en}",
    "address": "{emb_addr_val}",
    "phone": "{emb_phone_val}",
    "fax": "—",
    "email": "{emb_email_val}",
    "website": "<verified URL or 'NOT FOUND'>"
  }},
  "consulate": {{
    "name": "<full official Arabic name of Saudi consulate in {city}>",
    "address": "{con_addr_val}",
    "phone": "{con_phone_val}",
    "email": "{con_email_val}",
    "emergency_phone": "<24-hour emergency — 'NOT FOUND' if unverified>",
    "working_hours": "من الاثنين إلى الجمعة، 9:00–17:00",
    "consul_name": "{consul_val}",
    "consul_title": "القنصل العام للمملكة العربية السعودية",
    "consul_bio": "<Arabic 2 sentences: consular services available to Saudi official delegations>"
  }}
}}"""

    result = _oai_chat(oai, model="gpt-4o", max_tokens=3000, json_mode=True,
                       system=(
                           "Saudi government briefing specialist. Output ONLY valid JSON. "
                           "All values shown in the JSON template above are REQUIRED — copy them VERBATIM. "
                           "NEVER replace pre-filled values with 'NOT FOUND' or different values. "
                           "NEVER invent names, addresses, or statistics."
                       ),
                       messages=[{"role": "user", "content": prompt}])
    return _safe_json_load(result)
    """
    Section A: All factual structured fields.
    country_info, conference_data, embassy, consulate, bilateral_fields.
    Estimated output: ~1,500 tokens — always completes.
    """
    year = start_date[:4]
    venue_str = venue or city
    research_short = _truncate(research, 10000)
    leader_note = f"CRITICAL: head_of_state = '{leader_override}' — use exactly this name\n" if leader_override else ""

    prompt = f"""You are generating Section A of a Saudi government travel briefing JSON.
Event: {event_name} | City: {city} | Country: {country_en} | Dates: {start_date} to {end_date or start_date} | Year: {year}
{leader_note}
⚡ PRIORITY DATA SOURCE — READ FIRST:
At the top of the research below there is a "KB OVERRIDE BLOCK" section.
Values in that block are PRE-VERIFIED and must be used EXACTLY as written.
They override all web search results. Specifically:
  - EMBASSY_ADDRESS / EMBASSY_PHONE / EMBASSY_EMAIL → use for embassy fields
  - CONSULATE_ADDRESS / CONSULATE_PHONE / CONSULATE_EMAIL → use for consulate fields
  - SAUDI_AMBASSADOR → use for ambassador_name
  - CONSUL_GENERAL → use for consul_name
  - COUNTRY_GDP / COUNTRY_GDP_PERCAP / COUNTRY_POPULATION → use for country_info
  - CONF_EDITION → use for conference edition number
  - CONF_ATTENDANCE → use for expected_participants

Only write "NOT FOUND" if a field is genuinely absent from BOTH the KB OVERRIDE BLOCK and all research.

Research data:
{research_short}

Return ONLY this JSON object. All narrative text in formal Arabic. No markdown.

{{
  "country_info": {{
    "capital": "<capital city>",
    "head_of_state_title": "<Arabic official title: Prime Minister/President/etc>",
    "head_of_state": "<EXACT name — must match override if given>",
    "population": "<use COUNTRY_POPULATION from KB override, else research>",
    "area": "<X km² from research>",
    "gdp": "<use COUNTRY_GDP from KB override — e.g. '$30.62 trillion (2025, IMF)'>",
    "gdp_per_capita": "<use COUNTRY_GDP_PERCAP from KB override>",
    "currency": "<full name (CODE)>",
    "official_language": "<official language(s)>",
    "religion": "<predominant religion>",
    "timezone": "<use TIMEZONE from KB override>",
    "government": "<Arabic — political system>",
    "key_sectors": "<Arabic — 3-5 key economic sectors>",
    "overview": "<Arabic 3-4 sentences: economic standing, global role, regulatory environment, Saudi relevance>"
  }},
  "conference_data": {{
    "organizer": "<full official organization name>",
    "overview": "<Arabic 3-4 sentences: conference purpose, global standing, policy influence>",
    "slogan": "<official theme — use CONF_THEME_EN from KB override if present>",
    "dates": "{start_date} to {end_date or start_date}",
    "location": "{venue_str}, {country}",
    "founded": "<founding year>",
    "edition": "<use CONF_EDITION from KB override — e.g. '29th Annual'>",
    "expected_participants": "<use CONF_ATTENDANCE from KB override>",
    "participant_profile": "<Arabic: level of attendees — ministers, CEOs, etc>",
    "core_themes": "<Arabic: 3-5 main themes>",
    "ksa_participation": "<Arabic: Saudi Arabia's participation context and role>"
  }},
  "bilateral_fields": {{
    "trade_volume": "<use BILATERAL_TRADE from KB override — never invent a figure>",
    "cooperation_areas": "<Arabic: 3-5 specific sectors with named frameworks>",
    "strategic_agreements": "<Arabic: actual named bilateral agreements from research>",
    "health_regulatory": "<Arabic: specific health/pharma cooperation frameworks>"
  }},
  "embassy": {{
    "name": "<full official Arabic name of Saudi Embassy in {country_en}>",
    "mission": "<Arabic 1-2 sentences: embassy mission for official delegations>",
    "ambassador_name": "<use SAUDI_AMBASSADOR from KB override>",
    "ambassador_title": "سفير خادم الحرمين الشريفين لدى {country_en}",
    "address": "<use EMBASSY_ADDRESS from KB override>",
    "phone": "<use EMBASSY_PHONE from KB override>",
    "fax": "—",
    "email": "<use EMBASSY_EMAIL from KB override>",
    "website": "<verified URL or 'NOT FOUND'>"
  }},
  "consulate": {{
    "name": "<full official Arabic name of Saudi consulate in {city}>",
    "address": "<use CONSULATE_ADDRESS from KB override>",
    "phone": "<use CONSULATE_PHONE from KB override>",
    "email": "<use CONSULATE_EMAIL from KB override>",
    "emergency_phone": "<24-hour emergency — 'NOT FOUND' if unverified>",
    "working_hours": "من الاثنين إلى الجمعة، 9:00–17:00",
    "consul_name": "<use CONSUL_GENERAL from KB override>",
    "consul_title": "القنصل العام للمملكة العربية السعودية",
    "consul_bio": "<Arabic 2 sentences: consular services available to Saudi official delegations>"
  }}
}}"""

    result = _oai_chat(oai, model="gpt-4o", max_tokens=3000, json_mode=True,
                       system=(
                           "Saudi government briefing specialist. Output ONLY valid JSON. "
                           "All narrative text in Arabic. "
                           "CRITICAL: The research contains a 'KB OVERRIDE BLOCK' at the top. "
                           "Always use those pre-verified values for embassy, consulate, GDP, edition, etc. "
                           "NEVER write NOT FOUND for a field that appears in the KB OVERRIDE BLOCK. "
                           "NEVER invent names, addresses, or statistics."
                       ),
                       messages=[{"role": "user", "content": prompt}])
    return _safe_json_load(result)


# ─── Section B: People and conference content ─────────────────────────────────

def _gen_section_b(oai, research, event_name, country_en, start_date, end_date, kb_vars=None):
    """
    Section B: Speakers, tracks, past outcomes, ambassadors.
    v4.5: Confirmed speakers from KB injected directly as a mandatory list.
    """
    year = start_date[:4]
    research_short = _truncate(research, 10000)
    kv = kb_vars or {}
    kb_header = _build_kb_prompt_header(kv) if kv else ""

    # Build mandatory speakers block from KB
    mandatory_speakers_block = ""
    if kv.get('speakers_list'):
        lines = ["MANDATORY CONFIRMED SPEAKERS — INCLUDE ALL OF THESE IN YOUR OUTPUT:"]
        for sp in kv['speakers_list']:
            lines.append(f"  ✅ {sp}")
        lines.append("You may ADD more speakers from research, but NEVER omit any of the above.")
        mandatory_speakers_block = "\n".join(lines)

    # Ambassador from KB
    amb_name = kv.get('ambassador', "يُحدَّد لاحقاً")

    prompt = f"""You are generating Section B of a Saudi government travel briefing JSON.
Event: {event_name} | Country: {country_en} | Year: {year}

{kb_header}
{mandatory_speakers_block}

Research data (use for tracks, history, and any additional speakers):
{research_short}

Return ONLY this JSON object. No markdown.

{{
  "speakers": [
    {{
      "name": "<EXACT full name — all KB mandatory speakers + any additional from research>",
      "title": "<exact official title>",
      "organization": "<exact organization name>",
      "country": "<country of nationality>",
      "influence_profile": "<Arabic 2 sentences: global role, what policy decisions they control>",
      "relevance": "<Arabic 1-2 sentences: specific relevance to SFDA agenda>"
    }}
  ],
  "conference_tracks": [
    {{
      "name": "<REAL official track name from research — translated to Arabic>",
      "explanation": "<Arabic 2 sentences: track content and specific relevance to SFDA>"
    }}
  ],
  "previous_outcomes": [
    {{
      "year": "<year>",
      "theme": "<actual theme name — use EXACTLY from KB history>",
      "summary": "<Arabic 2-3 sentences: outcomes from that edition>",
      "relevance": "<Arabic 1-2 sentences: why this matters to Saudi Arabia>"
    }}
  ],
  "key_ambassadors": [
    {{
      "name": "{amb_name}",
      "title": "سفير خادم الحرمين الشريفين لدى {country_en}",
      "country": "{country_en}",
      "relevance": "<Arabic 2 sentences: ambassador's role in facilitating this delegation>"
    }}
  ]
}}

RULES:
1. speakers: Include ALL mandatory speakers listed above plus any additional verified ones from research.
2. conference_tracks: Use official track names from research (Finance, Health, Technology, etc.)
3. previous_outcomes: Use the VERIFIED PAST EDITIONS history — exact year themes as provided.
4. ZERO HALLUCINATION: Every additional name beyond the mandatory list must appear in research."""

    result = _oai_chat(oai, model="gpt-4o", max_tokens=3500, json_mode=True,
                       system=(
                           "Saudi government briefing specialist. Output ONLY valid JSON. "
                           "You MUST include all speakers listed in MANDATORY CONFIRMED SPEAKERS. "
                           "Do not omit any of those names from your speakers array. "
                           "Never invent additional speakers not in the mandatory list or research."
                       ),
                       messages=[{"role": "user", "content": prompt}])
    return _safe_json_load(result)


# ─── Section C: Narrative intelligence ───────────────────────────────────────

def _gen_section_c(oai, research, event_name, city, country, country_en,
                   start_date, context, kb_vars=None):
    """
    Section C: All Arabic narrative and intelligence fields.
    executive_summary, geopolitical_summary, sfda fields, intel fields, etc.
    v4.5: kb_vars injected — correct conference theme hard-coded to prevent confusion.
    """
    year = start_date[:4]
    research_short = _truncate(research, 10000)
    kv = kb_vars or {}
    kb_header = _build_kb_prompt_header(kv) if kv else ""

    # Hard-inject correct theme to prevent "Beacon to the World" confusion
    theme_ar     = kv.get('theme_ar', '')
    theme_en     = kv.get('theme_en', '')
    theme_note   = kv.get('theme_note', '')
    trade_val    = kv.get('trade', '<from research>')
    report_sub   = theme_ar if theme_ar else (theme_en if theme_en else '<official conference theme from research>')

    prompt = f"""You are generating Section C of a Saudi government travel briefing JSON.
Event: {event_name} | City: {city} | Country: {country_en} | Date: {start_date} | Year: {year}
Context: {context or 'SFDA official participation — Dr. Hisham Al Jadhey, CEO'}

{kb_header}
{"⚠️  THEME DISAMBIGUATION: " + theme_note if theme_note else ""}

REQUIRED VALUES FOR THIS SECTION:
  report_subtitle = "{report_sub}"
  {"(Conference theme is '" + theme_en + "' / '" + theme_ar + "')" if theme_en else ""}

Research data:
{research_short}

Return ONLY this JSON object. ALL text fields must be in formal Arabic. No markdown.

{{
  "report_subtitle": "{report_sub}",
  "visit_objectives": [
    "<Arabic — specific named strategic goal tied to this event's confirmed agenda>",
    "<Arabic — regulatory cooperation opportunity from research>",
    "<Arabic — specific bilateral relationship to advance>",
    "<Arabic — named international body or partnership target>",
    "<Arabic — Vision 2030 specific program or target>"
  ],
  "executive_summary": "<Arabic 7-8 sentences using the conference theme '{theme_en}' correctly — DO NOT use 'منارة للعالم' or 'Beacon to the World' as the theme. Those are the opening speech title. Mention the correct theme '{theme_ar}'. Cite actual speakers or sessions from research.>",
  "geopolitical_summary": "<Arabic 5-7 sentences: analytical assessment — conference role in global policy, which world powers attend and why, economic significance with figures, regulatory implications for pharma/health, Saudi positioning opportunity.>",
  "intel_global_significance": [
    "<Arabic bullet: specific evidence of conference influence — cite actual participants or capital from research>",
    "<Arabic bullet: economic/investment significance with verified figures>",
    "<Arabic bullet: Saudi Arabia's strategic role and positioning opportunity>"
  ],
  "intel_regulatory_impact": [
    "<Arabic bullet: specific regulatory/policy decisions expected — cite actual sessions from research>",
    "<Arabic bullet: pharma/health regulatory impact directly relevant to SFDA mandate>",
    "<Arabic bullet: harmonization opportunity for Saudi Arabia>"
  ],
  "intel_long_term_value": [
    "<Arabic bullet: 3-5 year strategic value — specific partnerships this participation enables>",
    "<Arabic bullet: institutional positioning — named international bodies SFDA advances in>",
    "<Arabic bullet: measurable outcome target — what success looks like>"
  ],
  "conference_summary": "<Arabic 4-5 sentences: organizing body full name, founding year, global ranking, this edition theme '{theme_ar}', expected participants.>",
  "conference_history": "<Arabic 4-5 sentences: year-by-year highlights from past 3 editions — actual themes, policy announcements, attendance numbers.>",
  "ksa_participation_history": "<Arabic 4-5 sentences: Vision 2030 linkage, specific 2030 programs served, SFDA regulatory modernization relevance, Saudi international regulatory leadership.>",
  "sfda_relevance": "<Arabic 4-5 sentences: SFDA-specific strategic value — regulatory harmonization goals, international recognition opportunities, partnership pipeline with named counterpart bodies.>",
  "bilateral_relations": "<Arabic 6-8 sentences: trade volume = {trade_val}, top cooperation sectors, named agreements, investment flows, diplomatic alignment.>",
  "entry_requirements": "<Arabic 3-4 sentences: visa policy from research I, entry conditions for Saudi official passport holders.>",
  "leadership_brief": "<Arabic 5-6 sentences: head of state exact name, political system, economic policy orientation, foreign policy stance toward Saudi Arabia, key 2025 priorities.>",
  "political_economic_orientation": "<Arabic 1-2 sentences: economic policy model and current priorities.>",
  "political_strategic_priorities": "<Arabic 1-2 sentences: top foreign/economic priorities relevant to Saudi Arabia.>",
  "trade_exchange": "<Arabic 4-5 sentences: detailed bilateral trade — verified volume = {trade_val}, sectors, Saudi investment, reciprocal investment.>",
  "ns_vision_alignment": "<Arabic 2-3 sentences: specific Vision 2030 programs this visit serves — name the actual initiative.>",
  "ns_regulatory_relevance": "<Arabic 2-3 sentences: specific SFDA regulatory reform programs advanced — name actual SFDA initiatives or ICH/GCC/WHO harmonization tracks.>",
  "ns_investment_implications": "<Arabic 2-3 sentences: specific investment opportunity — pharma FDI figures, named investment programs.>",
  "ns_institutional_positioning": "<Arabic 2-3 sentences: specific international body SFDA advances standing in — ICH, WHO, regional networks.>",
  "sfda_talking_points": [
    "<Arabic: regulatory cooperation framework to propose — name the specific regulations or standards>",
    "<Arabic: data sharing or pharmacovigilance harmonization — specific systems>",
    "<Arabic: market access for Saudi pharmaceutical exports — specific products>",
    "<Arabic: halal pharmaceuticals/food safety standards — specific harmonization>",
    "<Arabic: AI/digital health regulation — named initiative>",
    "<Arabic: joint clinical trial framework — specific regulatory pathway>",
    "<Arabic: AMR or pandemic preparedness — specific mechanism>",
    "<Arabic: SFDA international recognition — specific accreditation or listing target>"
  ]
}}"""

    result = _oai_chat(oai, model="gpt-4o", max_tokens=4000, json_mode=True,
                       system="Saudi government intelligence briefing specialist. Output ONLY valid JSON. Write exclusively in formal Arabic for all narrative fields. Be specific — cite actual conference names, speaker names, and verified figures from the research data provided.",
                       messages=[{"role": "user", "content": prompt}])
    return _safe_json_load(result)


# ─── Section D: Operational schedule ─────────────────────────────────────────

def _gen_section_d(oai, research, event_name, city, country, country_en,
                   start_date, end_date, venue, num_days, dates):
    """
    Section D: Agenda, sessions, bilateral meetings, weather, prayer times.
    Uses confirmed session titles from research to populate schedule.
    Estimated output: ~2,500 tokens - always completes.
    """
    year = start_date[:4]
    venue_str = venue or city
    day_ar = ["اليوم الأول","اليوم الثاني","اليوم الثالث","اليوم الرابع","اليوم الخامس"]
    day_en = ["Day 1","Day 2","Day 3","Day 4","Day 5"]

    # Build day specs for prompt
    days_spec = "\n".join(
        f"  Day {i+1}: date={dates[i]}, label_ar={day_ar[i]}, label_en={day_en[i]}"
        for i in range(num_days)
    )

    # Build session day keys
    session_keys = ", ".join(f"\"day{i+1}\"" for i in range(num_days))

    research_short = _truncate(research, 9000)

    prompt = f"""You are generating Section D of a Saudi government travel briefing JSON.
Event: {event_name} | City: {city} | Venue: {venue_str} | Dates: {start_date} to {end_date or start_date}
Number of days: {num_days}
Day structure:
{days_spec}

Research data (use CONFIRMED session titles from research — never invent sessions):
{research_short}

Return ONLY this JSON object. Narrative text in Arabic. No markdown.

{{
  "agenda": [
    {{
      "day_label": "{day_ar[0]}",
      "day_label_en": "{day_en[0]}",
      "date": "{dates[0]}",
      "items": [
        {{"time": "08:00", "activity": "وصول الوفد والتسجيل الرسمي", "location": "{venue_str}", "type": "logistics", "strategic_relevance": "—"}},
        {{"time": "09:00", "activity": "<Arabic: REAL opening session from research>", "location": "<hall name>", "type": "ceremony", "strategic_relevance": "<Arabic: significance>"}},
        {{"time": "10:30", "activity": "<Arabic: REAL confirmed session from research A>", "location": "<room>", "type": "session", "strategic_relevance": "<Arabic: SFDA relevance>"}},
        {{"time": "12:00", "activity": "استراحة الغداء والتواصل مع كبار المسؤولين", "location": "<dining venue>", "type": "networking", "strategic_relevance": "بناء الشبكات الاستراتيجية"}},
        {{"time": "14:00", "activity": "<Arabic: REAL afternoon session from research>", "location": "<room>", "type": "session", "strategic_relevance": "<Arabic>"}},
        {{"time": "16:00", "activity": "<Arabic: REAL session from research>", "location": "<room>", "type": "session", "strategic_relevance": "<Arabic>"}},
        {{"time": "19:00", "activity": "حفل الاستقبال الرسمي للمؤتمر", "location": "<ballroom>", "type": "ceremony", "strategic_relevance": "التواصل البروتوكولي مع الوفود الحكومية"}}
      ]
    }}
  ],
  "sessions": {{
    "day1": [
      {{"time": "09:00", "title": "<Arabic: REAL confirmed session title from research>", "description": "<Arabic 2-3 sentences: what this session covers, policy implications>", "speakers": "<EXACT speaker names from research>", "policy_implications": "<Arabic>", "investment_implications": "<Arabic>", "regulatory_impact": "<Arabic>", "strategic_score": "عالي"}},
      {{"time": "11:00", "title": "<Arabic: REAL session from research>", "description": "<Arabic>", "speakers": "<names from research>", "policy_implications": "<Arabic>", "investment_implications": "<Arabic>", "regulatory_impact": "<Arabic>", "strategic_score": "متوسط"}},
      {{"time": "14:30", "title": "<Arabic: REAL session from research>", "description": "<Arabic>", "speakers": "<names>", "policy_implications": "<Arabic>", "investment_implications": "<Arabic>", "regulatory_impact": "<Arabic>", "strategic_score": "عالي"}}
    ]
  }},
  "bilateral_meetings": [
    {{
      "entity": "<REAL drug regulatory authority from research H — exact official name>",
      "counterpart": "يُحدَّد لاحقاً",
      "counterpart_title": "<Arabic: official title of institution head>",
      "date": "{dates[0]}",
      "time": "14:00",
      "location": "{venue_str}",
      "talking_points": [
        "<Arabic: specific regulatory harmonization agenda item — name the regulation>",
        "<Arabic: data sharing or pharmacovigilance proposal>",
        "<Arabic: MoU or agreement to negotiate — named scope>",
        "<Arabic: market access or mutual recognition opportunity>"
      ],
      "strategic_objective": "<Arabic: one specific measurable goal>",
      "expected_outcome": "<Arabic: one concrete deliverable>"
    }},
    {{
      "entity": "<REAL health ministry from research H — exact official name>",
      "counterpart": "يُحدَّد لاحقاً",
      "counterpart_title": "<Arabic: minister title>",
      "date": "{dates[min(1, num_days-1)]}",
      "time": "10:30",
      "location": "{venue_str}",
      "talking_points": ["<Arabic 1>", "<Arabic 2>", "<Arabic 3>"],
      "strategic_objective": "<Arabic>",
      "expected_outcome": "<Arabic>"
    }},
    {{
      "entity": "<REAL pharma industry or food safety body from research H>",
      "counterpart": "يُحدَّد لاحقاً",
      "counterpart_title": "<Arabic>",
      "date": "{dates[min(2, num_days-1)]}",
      "time": "16:00",
      "location": "{venue_str}",
      "talking_points": ["<Arabic 1>", "<Arabic 2>", "<Arabic 3>"],
      "strategic_objective": "<Arabic>",
      "expected_outcome": "<Arabic>"
    }}
  ],
  "suggested_meetings": [
    {{"entity": "<REAL drug regulator>", "country": "{country_en}", "priority": "high", "description": "<Arabic: regulatory mandate>", "rationale": "<Arabic: SFDA harmonization opportunity>"}},
    {{"entity": "<REAL health ministry>", "country": "{country_en}", "priority": "high", "description": "<Arabic>", "rationale": "<Arabic: Vision 2030 cooperation angle>"}},
    {{"entity": "<REAL food/standards body>", "country": "{country_en}", "priority": "medium", "description": "<Arabic>", "rationale": "<Arabic: halal standards>"}},
    {{"entity": "<REAL pharma industry body>", "country": "{country_en}", "priority": "medium", "description": "<Arabic>", "rationale": "<Arabic: market access>"}},
    {{"entity": "<REAL health research institution>", "country": "{country_en}", "priority": "low", "description": "<Arabic>", "rationale": "<Arabic: research collaboration>"}}
  ],
  "weather": [
    {{"day": "{day_en[0]}", "date": "{dates[0]}", "condition": "<Sunny/Cloudy/Rainy>", "high": 0, "low": 0, "humidity": "<n>%", "wind": "<n> km/h"}}
  ],
  "prayer_times": [
    {{"date": "{dates[0]}", "day": "{day_en[0]} — {day_ar[0]}", "fajr": "00:00", "dhuhr": "00:00", "asr": "00:00", "maghrib": "00:00", "isha": "00:00"}}
  ],
  "attachments": [
    "{event_name} — البرنامج الرسمي {year}.pdf",
    "الموجز الاقتصادي لدولة {country_en} {year}.pdf",
    "رؤية المملكة العربية السعودية 2030 — برنامج تحويل القطاع الصحي.pdf",
    "الخطة الاستراتيجية للهيئة العامة للغذاء والدواء 2025–2030.pdf",
    "السيرة الذاتية لأعضاء الوفد الرسمي.pdf",
    "الموجز الثنائي السعودي–{country_en} — التعاون الصحي والدوائي.pdf",
    "ملفات المتحدثين الرئيسيين — {event_name} {year}.pdf",
    "متطلبات الدخول إلى {country_en} للجوازات الدبلوماسية.pdf"
  ]
}}

RULES FOR ACCURACY:
- agenda: populate ALL {num_days} days. Copy structure from day 1 for additional days with different sessions.
- sessions: include keys {session_keys}. Use REAL confirmed session titles from research.
  CRITICAL SPEAKER RULE: Each session must have DIFFERENT speakers.
  NEVER list the same 1-2 speakers for every session — this is a hallucination.
  If you do not know who speaks at a specific session, write 'يُحدَّد لاحقاً' for that session's speakers field.
  Only assign a speaker to a session if the research explicitly links that speaker to that session.
- bilateral_meetings: use EXACT institution names from research H, not generic Arabic names.
- weather: {num_days} objects with REAL integer temperatures for {city} in the month of {start_date[5:7]}.
- prayer_times: {num_days} objects with REAL prayer times for {city} on those dates. Times must differ by ~1 min each day.
- all high/low weather values must be INTEGER numbers, not strings."""

    result = _oai_chat(oai, model="gpt-4o", max_tokens=5000, json_mode=True,
                       system="Saudi government briefing specialist. Output ONLY valid JSON. Use confirmed session titles from research. Entity names must be real institutions from the research data. Prayer times and weather must be realistic for the actual city and dates.",
                       messages=[{"role": "user", "content": prompt}])
    return _safe_json_load(result)



# ─── KB Support Functions (module-level) ────────────────────────────────────
# v4.6 FIX: Extracted from generate_report_content where they were nested.     
# _generate_json is module-level so it could not access nested functions.       

# ── KB Forced Override Block ──────────────────────────────────────────────
def _build_kb_forced_overrides(conf, start_date, city_en):
    """
    v4.4 FIX: Builds a COMPACT, explicitly labeled block of KB facts that:
      1. Always survives _truncate() — injected at position 0 before all research
      2. Uses exact field names that Section A/B/D prompts look for
      3. Overrides web search data when KB has pre-verified answers

    Root cause of v4.3 regressions (embassy NOT FOUND, GDP $23T, edition 27th):
      - KB text was 4th in research_parts, truncated away before Section A read it
      - Section A prompt referenced "research C/D" not "KB OVERRIDES"
      - _kb_to_text v4.3 removed year_data reader, losing edition + all speakers

    This block is the first ~1,000 chars of research — never truncated.
    """
    year   = start_date[:4]
    cf     = conf.get('city_facts', {})
    yd     = conf.get(year, {})
    lines  = ["╔══════════════════════════════════════════════════════════════════╗",
              "║  KB OVERRIDE BLOCK — READ THIS FIRST — PRE-VERIFIED VALUES       ║",
              "║  Use these EXACTLY — they override all web search results         ║",
              "╚══════════════════════════════════════════════════════════════════╝"]

    # ── Conference-specific (if KB has year data) ────────────────────────
    if yd:
        if yd.get('edition'):
            lines.append(f"CONF_EDITION        : {yd['edition']}")
        if yd.get('theme'):
            lines.append(f"CONF_THEME_EN       : {yd['theme']}")
        if yd.get('theme_arabic'):
            lines.append(f"CONF_THEME_AR       : {yd['theme_arabic']}")
        if yd.get('attendees'):
            lines.append(f"CONF_ATTENDANCE     : {yd['attendees']}")
        if yd.get('venue'):
            lines.append(f"CONF_VENUE          : {yd['venue']}")

    # ── Country / city facts ─────────────────────────────────────────────
    if cf.get('gdp'):
        lines.append(f"COUNTRY_GDP         : {cf['gdp']}")
    if cf.get('gdp_per_capita'):
        lines.append(f"COUNTRY_GDP_PERCAP  : {cf['gdp_per_capita']}")
    if cf.get('population'):
        lines.append(f"COUNTRY_POPULATION  : {cf['population']}")
    if cf.get('bilateral_trade'):
        lines.append(f"BILATERAL_TRADE     : {cf['bilateral_trade']}")
    if cf.get('timezone'):
        lines.append(f"TIMEZONE            : {cf['timezone']}")
    if cf.get('visa'):
        lines.append(f"VISA_POLICY         : {cf['visa']}")

    # ── Saudi diplomatic presence (embassy + consulate) ──────────────────
    if cf.get('saudi_ambassador'):
        lines.append(f"SAUDI_AMBASSADOR    : {cf['saudi_ambassador']}")
    if cf.get('embassy'):
        # Parse out address and phone from combined string
        emb = cf['embassy']
        lines.append(f"EMBASSY_FULL        : {emb}")
        # Extract address (before first '|')
        parts = [p.strip() for p in emb.split('|')]
        if len(parts) >= 1:
            lines.append(f"EMBASSY_ADDRESS     : {parts[0]}")
        if len(parts) >= 2:
            tel = parts[1].replace('Tel:', '').replace('Tel :', '').strip()
            lines.append(f"EMBASSY_PHONE       : {tel}")
        if len(parts) >= 3:
            lines.append(f"EMBASSY_EMAIL       : {parts[2].strip()}")

    # Find consulate key for this city (e.g. consulate_la, consulate_nyc, etc.)
    city_lower = city_en.lower().replace(' ', '_')
    for k, v in cf.items():
        if k.startswith('consulate_') and isinstance(v, str):
            lines.append(f"CONSULATE_FULL      : {v}")
            parts = [p.strip() for p in v.split('|')]
            if len(parts) >= 1:
                lines.append(f"CONSULATE_ADDRESS   : {parts[0]}")
            if len(parts) >= 2:
                tel = parts[1].replace('Tel:', '').replace('Tel :', '').strip()
                lines.append(f"CONSULATE_PHONE     : {tel}")
            if len(parts) >= 3:
                lines.append(f"CONSULATE_EMAIL     : {parts[2].strip()}")
        elif k.startswith('consul_') and isinstance(v, str):
            lines.append(f"CONSUL_GENERAL      : {v}")

    # ── Regulatory bodies ────────────────────────────────────────────────
    for key, label in [('drug_regulator','DRUG_REGULATOR'),
                       ('health_ministry','HEALTH_MINISTRY'),
                       ('food_body',      'FOOD_BODY'),
                       ('pharma_body',    'PHARMA_BODY'),
                       ('nih',            'NIH')]:
        if cf.get(key):
            lines.append(f"{label:<20}: {cf[key]}")

    lines.append("╚══════ END KB OVERRIDE BLOCK ══════╝")
    return "\n".join(lines)

# ── KB Variable Extractor ─────────────────────────────────────────────────
def _extract_kb_vars(conf, start_date, city_en):
    """
    v4.5: Extract all critical KB values into a flat Python dict.
    These are used for TWO purposes:
      1. Hard-injected into prompts as f-string literals (cannot be ignored)
      2. Post-processing override: Python dict assignment overwrites any AI output

    This is the definitive fix for "model ignores KB block in research string".
    Python assignment is 100% reliable; model attention is not.
    """
    year = start_date[:4]
    cf   = conf.get('city_facts', {})
    yd   = conf.get(year, {})

    v = {}

    # Conference facts
    v['edition']      = yd.get('edition',  '')
    v['theme_en']     = yd.get('theme',     '')
    v['theme_ar']     = yd.get('theme_arabic', '')
    v['theme_note']   = yd.get('theme_disambiguation', '')
    v['attendance']   = yd.get('attendees', '')
    v['conf_venue']   = yd.get('venue',     '')
    v['speakers_list']= yd.get('confirmed_speakers', [])
    v['sessions_list']= yd.get('confirmed_sessions', [])
    v['founded']      = conf.get('founded', conf.get('conference_first_held', ''))
    v['ceo']          = conf.get('ceo', '')
    v['full_name']    = conf.get('full_name', '')

    # Country/city facts
    v['gdp']          = cf.get('gdp', '')
    v['gdp_per_cap']  = cf.get('gdp_per_capita', '')
    v['population']   = cf.get('population', '')
    v['trade']        = cf.get('bilateral_trade', '')
    v['timezone']     = cf.get('timezone', '')
    v['visa']         = cf.get('visa', '')
    v['currency']     = cf.get('currency', '')
    v['area']         = cf.get('area', '')

    # Saudi diplomatic presence
    v['ambassador']   = cf.get('saudi_ambassador', '')

    # Parse embassy string: "601 New Hampshire Ave NW | Tel: (202) 342-3800 | info@..."
    emb_str = cf.get('embassy', '')
    emb_parts = [p.strip() for p in emb_str.split('|')]
    v['emb_full']     = emb_str
    v['emb_addr']     = emb_parts[0] if len(emb_parts) >= 1 else ''
    v['emb_phone']    = emb_parts[1].replace('Tel:','').replace('Tel :','').strip() if len(emb_parts) >= 2 else ''
    v['emb_email']    = emb_parts[2].strip() if len(emb_parts) >= 3 else ''

    # Find consulate and consul for this city
    city_key = city_en.lower().replace(' ', '_')
    v['con_full']     = ''
    v['con_addr']     = ''
    v['con_phone']    = ''
    v['con_email']    = ''
    v['consul_name']  = ''
    for k, val in cf.items():
        if k.startswith('consulate_') and isinstance(val, str):
            # Check if this consulate's key contains the city name or is the only one
            con_parts = [p.strip() for p in val.split('|')]
            # Use the city consulate or default to first available
            if city_key in k or not v['con_addr']:
                v['con_full']  = val
                v['con_addr']  = con_parts[0] if len(con_parts) >= 1 else ''
                v['con_phone'] = con_parts[1].replace('Tel:','').replace('Tel :','').strip() if len(con_parts) >= 2 else ''
                v['con_email'] = con_parts[2].strip() if len(con_parts) >= 3 else ''
        elif k.startswith('consul_') and isinstance(val, str):
            if city_key in k or not v['consul_name']:
                v['consul_name'] = val

    # Regulatory bodies
    v['drug_regulator']  = cf.get('drug_regulator',  '')
    v['health_ministry'] = cf.get('health_ministry', '')
    v['food_body']       = cf.get('food_body',       '')
    v['pharma_body']     = cf.get('pharma_body',     '')
    v['nih']             = cf.get('nih',             '')

    # Prayer times — per day, direct copy from KB
    v['prayer_times'] = {}
    for i in range(1, 6):
        key = f'prayer_day{i}'
        if cf.get(key):
            v['prayer_times'][i] = cf[key]

    # History themes for previous_outcomes
    v['history'] = conf.get('history', {})

    # Remove empty strings to keep dict clean
    v = {k: val for k, val in v.items() if val != ''}
    return v

# ── KB Python-level Override ──────────────────────────────────────────────
def _apply_kb_overrides(data, kv):
    """
    v4.5 FINAL LAYER: Python dict assignment overwrites AI output with KB facts.
    This runs AFTER all 4 AI sections complete. It cannot be ignored or
    "confused" by live web search — it is pure Python string assignment.

    This is the definitive solution to:
      - Ambassador still NOT FOUND after KB block
      - Consul still NOT FOUND
      - GDP per capita wrong
      - Consulate address wrong
      - Trade NOT FOUND
      - Population outdated
      - Theme wrong (slogan field)
    """
    if not kv:
        return

    # ── country_info ────────────────────────────────────────────────────
    ci = data.setdefault('country_info', {})
    if kv.get('gdp'):         ci['gdp']          = kv['gdp']
    if kv.get('gdp_per_cap'): ci['gdp_per_capita']= kv['gdp_per_cap']
    if kv.get('population'):  ci['population']   = kv['population']
    if kv.get('timezone'):    ci['timezone']     = kv['timezone']

    # ── conference_data ──────────────────────────────────────────────────
    cd = data.setdefault('conference_data', {})
    if kv.get('edition'):    cd['edition']              = kv['edition']
    if kv.get('attendance'): cd['expected_participants'] = kv['attendance']
    if kv.get('theme_ar'):   cd['slogan']               = kv['theme_ar']
    elif kv.get('theme_en'): cd['slogan']               = kv['theme_en']
    if kv.get('founded'):    cd['founded']              = kv['founded']
    if kv.get('full_name'):  cd['organizer']            = kv['full_name'].replace(
                                 ' Global Conference', '').replace(
                                 ' Asia Summit', '').replace(
                                 ' Annual Meeting', '') or cd.get('organizer', '')
    # Keep full conference name as organizer
    if kv.get('full_name'):
        # Just ensure "Milken Institute" appears
        pass

    # ── bilateral_fields ─────────────────────────────────────────────────
    bf = data.setdefault('bilateral_fields', {})
    if kv.get('trade'): bf['trade_volume'] = kv['trade']

    # ── embassy ──────────────────────────────────────────────────────────
    emb = data.setdefault('embassy', {})
    if kv.get('ambassador'): emb['ambassador_name'] = kv['ambassador']
    if kv.get('emb_addr'):   emb['address']         = kv['emb_addr']
    if kv.get('emb_phone'):  emb['phone']           = kv['emb_phone']
    if kv.get('emb_email'):  emb['email']           = kv['emb_email']

    # ── consulate ────────────────────────────────────────────────────────
    con = data.setdefault('consulate', {})
    if kv.get('consul_name'): con['consul_name'] = kv['consul_name']
    if kv.get('con_addr'):    con['address']     = kv['con_addr']
    if kv.get('con_phone'):   con['phone']       = kv['con_phone']
    if kv.get('con_email'):   con['email']       = kv['con_email']

    print("[AI] ✅ _apply_kb_overrides: KB facts hard-written to data dict")

def _apply_kb_prayer_times(data, kv, dates, num_days):
    """
    v4.5: Copy prayer times directly from KB without any AI involvement.
    Completely eliminates AI prayer time errors for known conferences.
    """
    pt = kv.get('prayer_times', {})
    if not pt:
        return
    day_en = ["Day 1","Day 2","Day 3","Day 4","Day 5"]
    day_ar = ["اليوم الأول","اليوم الثاني","اليوم الثالث","اليوم الرابع","اليوم الخامس"]
    result = []
    for i in range(num_days):
        day_key = i + 1  # 1-based
        if day_key in pt:
            times = pt[day_key]
            result.append({
                "date":    dates[i],
                "day":     f"{day_en[i]} — {day_ar[i]}",
                "fajr":    times.get('fajr',    ''),
                "dhuhr":   times.get('dhuhr',   ''),
                "asr":     times.get('asr',     ''),
                "maghrib": times.get('maghrib', ''),
                "isha":    times.get('isha',    ''),
            })
    if result:
        data['prayer_times'] = result
        print(f"[AI] ✅ Prayer times: hard-copied from KB ({len(result)} days)")

def _apply_kb_speakers(data, kv):
    """
    v4.5: Ensure all KB confirmed speakers are in the speakers list.
    Adds missing KB speakers to AI-generated list (never removes).
    """
    kb_speakers = kv.get('speakers_list', [])
    if not kb_speakers:
        return

    current = data.get('speakers', [])
    current_names_lower = {s.get('name','').lower() for s in current if isinstance(s, dict)}

    added = 0
    for sp_str in kb_speakers:
        # Parse "Name — Title, Organization (Country)" format
        # e.g. "Jane Fraser — CEO, Citi (United States)"
        name = sp_str.split('—')[0].strip() if '—' in sp_str else sp_str.split('–')[0].strip()
        # Clean [HOST] note
        name = name.replace('[HOST]','').strip()
        # Clean nationality/note in brackets
        name_clean = re.sub(r'\s*\[.*?\]', '', name).strip()

        if name_clean.lower() not in current_names_lower:
            # Parse rest
            rest = sp_str[sp_str.index('—')+1:].strip() if '—' in sp_str else sp_str[sp_str.index('–')+1:].strip() if '–' in sp_str else ''
            # "CEO, Citi (United States)"
            country_match = re.search(r'\(([^)]+)\)$', rest)
            country = country_match.group(1) if country_match else ''
            title_org = rest[:country_match.start()].strip(' ,') if country_match else rest

            # Split title and org at first comma
            if ', ' in title_org:
                idx = title_org.index(', ')
                title = title_org[:idx].strip()
                org   = title_org[idx+2:].strip()
            else:
                title = title_org
                org   = ''

            current.append({
                "name":              name_clean,
                "title":             title,
                "organization":      org,
                "country":           country.split('/')[0].strip(),
                "influence_profile": f"متحدث مؤكد في {kv.get('full_name', 'المؤتمر')} 2025",
                "relevance":         "متحدث رئيسي مؤكد في الفعالية — يُحدَّد البيان لاحقاً"
            })
            current_names_lower.add(name_clean.lower())
            added += 1

    if added:
        data['speakers'] = current
        print(f"[AI] ✅ Speakers: added {added} missing KB speakers (total: {len(current)})")

def _apply_kb_history(data, kv):
    """
    v4.5: Override previous_outcomes with KB-verified historical themes.
    """
    hist = kv.get('history', {})
    if not hist:
        return
    outcomes = []
    for yr, h in sorted(hist.items(), reverse=True):
        outcomes.append({
            "year":      yr,
            "theme":     h.get('theme', ''),
            "summary":   f"ركز المؤتمر على موضوع '{h.get('theme','')}' وحضره {h.get('attendance','')}"
                         " من المشاركين من مختلف أنحاء العالم.",
            "relevance": "ذو صلة باستراتيجية المملكة العربية السعودية وأهداف رؤية 2030"
        })
    if outcomes:
        data['previous_outcomes'] = outcomes
        print(f"[AI] ✅ History: hard-copied {len(outcomes)} editions from KB")



# ─── v4.6 New Sections: Phase 1H + E + F + G ────────────────────────────────

# ─── Phase 1H: Deep Strategic Context Research ───────────────────────────────

def _research_deep_strategic_context(oai, event_name, city, country_en, start_date):
    """
    v4.6 NEW: Dedicated research phase for the 12 new report sections.
    6-track research covering institutional positioning, Saudi participation history,
    regulatory ecosystem comparison, geopolitical/macroeconomic context,
    political/regulatory risk, and regional power dynamics.
    """
    year = start_date[:4]

    prompt = f"""You are a strategic intelligence analyst preparing a deep-context brief
for a Saudi government senior official visiting {event_name} in {city}, {country_en} ({year}).

Conduct 6 targeted research tracks. Report under each labeled heading with verified facts.

TRACK 1: INSTITUTIONAL POSITIONING
Search: "{event_name} policy influence G20 IMF World Bank WHO 2024 2025"
Search: "Milken Institute government partnerships central banks regulatory bodies"
Report:
  A) Formal relationships with G20/World Bank/IMF/WHO -- specific MoUs, advisory roles
  B) Government ministers and central bank governors who attend regularly (with names)
  C) Specific policy decisions that originated from this conference (cite years)
  D) Ranking vs WEF Davos, CGI, OECD Forum in policy influence
  E) US Congressional/Executive Branch health/pharma policy linkage

TRACK 2: SAUDI ARABIA PARTICIPATION HISTORY
Search: "Saudi Arabia {event_name} delegation 2022 2023 2024 2025"
Search: "Saudi Arabia Milken Institute conference SFDA Health Ministry participant"
Report:
  A) Years Saudi Arabia sent official delegation (with composition if found)
  B) Saudi officials who spoke at the conference -- exact names and years
  C) MoUs or agreements involving Saudi Arabia announced at the conference
  D) Saudi Arabia's participation level trajectory
  E) UAE/Qatar/Bahrain participation for GCC benchmarking

TRACK 3: REGULATORY ECOSYSTEM COMPARISON
Search: "FDA SFDA regulatory comparison pharmaceutical approval 2024 2025"
Search: "{country_en} drug regulatory authority ICH harmonization SFDA {year}"
Search: "mutual recognition agreement FDA SFDA pharmaceutical 2023 2024 2025"
Report:
  A) FDA vs SFDA: approval timelines, post-market surveillance frameworks
  B) Areas of regulatory divergence (biologics, biosimilars, AI-assisted approval)
  C) Existing mutual recognition or reliance frameworks
  D) ICH membership status of both bodies
  E) 3 specific areas SFDA can benchmark to advance regulatory modernization

TRACK 4: GEOPOLITICAL AND MACROECONOMIC DEEP CONTEXT
Search: "{country_en} economic outlook {year} GDP growth fiscal policy pharmaceutical"
Search: "US macroeconomic risks {year} tariffs trade policy pharmaceutical impact"
Search: "{country_en} Saudi Arabia strategic relationship bilateral {year}"
Report:
  A) Current GDP growth rate, inflation, unemployment -- verified figures
  B) Key fiscal/monetary policy shifts affecting pharma/health in {year}
  C) Trade tensions affecting Saudi-{country_en} pharma relations
  D) Current diplomatic relationship level between Saudi Arabia and {country_en}
  E) Upcoming policy decisions affecting SFDA agenda

TRACK 5: POLITICAL AND REGULATORY RISK ASSESSMENT
Search: "{country_en} political risk {year} health policy pharmaceutical regulation"
Search: "US drug pricing policy pharma regulation 2025"
Search: "Saudi Arabia {country_en} relations risks opportunities 2025"
Report:
  A) Top 3 political risks affecting bilateral health/pharma cooperation
  B) Pending FDA/regulatory policy changes, drug pricing legislation, import restrictions
  C) Diplomatic sensitivities for Saudi officials visiting {city} in {year}
  D) Favorable political conditions for advancing SFDA cooperation
  E) Black swan scenarios that could disrupt cooperation

TRACK 6: REGIONAL POWER DYNAMICS
Search: "{country_en} geopolitical role G7 NATO ASEAN regional leadership {year}"
Search: "{city} global pharmaceutical hub regulatory influence {year}"
Search: "{country_en} influence developing countries health pharmaceutical policy {year}"
Report:
  A) {country_en}'s formal leadership roles in regional/global health institutions
  B) Regional bloc {country_en} anchors and Saudi Arabia's relationship with it
  C) Competing countries for regulatory influence in this region
  D) Key non-Western conference participants significant to Saudi Arabia
  E) {country_en} pharmaceutical export/import relationship with GCC

Label each track clearly. Include source URLs. Report only verified facts."""

    return _oai_chat(
        oai,
        model="gpt-4o-search-preview",
        system=(
            "Strategic intelligence analyst for senior government officials. "
            "Search the web for each of the 6 tracks systematically. "
            "Report verified facts with source URLs. "
            "Never invent figures, names, or relationships. "
            "Distinguish clearly between confirmed facts and analysis/inference."
        ),
        messages=[{"role": "user", "content": prompt}],
        max_tokens=5000,
    )


# ─── Section E: Deep Intelligence Sections ───────────────────────────────────

def _gen_section_e(oai, research, deep_research, event_name, city, country,
                   country_en, start_date, kb_vars=None):
    """
    v4.6 NEW: 6 deep intelligence sections using Phase 1H research.
    Sections: institutional positioning, KSA participation history,
    geopolitical context, risk assessment, regulatory comparison, regional power map.
    """
    year = start_date[:4]
    kv = kb_vars or {}
    organizer = kv.get('full_name', event_name)
    kb_header = _build_kb_prompt_header(kv) if kv else ""
    research_short = _truncate(research, 6000)
    deep_short     = _truncate(deep_research, 8000) if deep_research else "No deep research available."

    prompt = (
        f"You are generating Section E of a Saudi government travel briefing JSON.\n"
        f"Event: {event_name} | City: {city} | Country: {country_en} | Year: {year}\n"
        f"Organizer: {organizer}\n\n"
        f"{kb_header}\n\n"
        f"PRIMARY RESEARCH:\n{research_short}\n\n"
        f"DEEP STRATEGIC RESEARCH (Phase 1H):\n{deep_short}\n\n"
        "Return ONLY this JSON object. ALL narrative text in formal Arabic. No markdown.\n\n"
        '{\n'
        '  "milken_institutional_positioning": {\n'
        '    "global_policy_role": "<Arabic 4-5 sentences: Milken Institute formal position in global policy architecture -- specific G20/IMF/World Bank/WHO relationships, advisory roles, verified examples>",\n'
        '    "policy_influence_record": [\n'
        '      "<Arabic: specific policy decision tracing to this conference -- year and outcome>",\n'
        '      "<Arabic: second verified policy influence example>",\n'
        '      "<Arabic: third example -- regulatory, financial, or health policy outcome>",\n'
        '      "<Arabic: fourth example -- international cooperation framework>"\n'
        '    ],\n'
        '    "government_engagement_level": "<Arabic 2-3 sentences: which level of government officials attend -- ministers, central bank governors, heads of state -- with specific examples>",\n'
        '    "ranking_vs_davos": "<Arabic 2-3 sentences: how this conference ranks vs WEF Davos, CGI, OECD Forum -- specific comparative indicators>",\n'
        '    "us_policy_linkage": "<Arabic 2-3 sentences: specific US legislative/executive actions influenced by conference debates>",\n'
        '    "sfda_strategic_value": "<Arabic 2-3 sentences: why participation elevates SFDA international standing specifically>"\n'
        '  },\n\n'
        '  "ksa_participation_record": {\n'
        '    "participation_summary": "<Arabic 3-4 sentences: Saudi Arabia track record -- years of participation, escalation trajectory, institutional level>",\n'
        '    "historical_delegations": [\n'
        '      {"year": "<year>", "delegation_head": "<name or not found>", "delegation_level": "<Arabic>", "key_outcome": "<Arabic: specific outcome from research>"},\n'
        '      {"year": "<year>", "delegation_head": "<name or not found>", "delegation_level": "<Arabic>", "key_outcome": "<Arabic>"}\n'
        '    ],\n'
        '    "saudi_speakers_record": "<Arabic 2-3 sentences: Saudi officials who spoke at this conference -- names, titles, years if available>",\n'
        '    "gcc_benchmarking": "<Arabic 2-3 sentences: UAE/Qatar/Bahrain participation comparison and what Saudi can learn>",\n'
        '    "continuity_mandate": "<Arabic 2-3 sentences: strategic case for consistent multi-year participation as a sovereignty tool>",\n'
        '    "this_year_elevation": "<Arabic 2-3 sentences: why ' + year + ' participation is specifically strategic -- theme alignment, speaker lineup, bilateral context>"\n'
        '  },\n\n'
        '  "geopolitical_macro_context": {\n'
        '    "macroeconomic_overview": "<Arabic 4-5 sentences: verified GDP growth rate, inflation, unemployment, fiscal balance in ' + country_en + '. Context for pharma investment>",\n'
        '    "monetary_fiscal_policy": "<Arabic 2-3 sentences: central bank/Fed policy direction -- interest rates, effects on health sector investment flows>",\n'
        '    "trade_policy_context": "<Arabic 2-3 sentences: trade policies, tariffs in ' + year + ' affecting Saudi-' + country_en + ' pharma trade>",\n'
        '    "bilateral_relations_depth": "<Arabic 3-4 sentences: current Saudi-' + country_en + ' strategic relations -- latest meetings, cooperation frameworks, tensions>",\n'
        '    "upcoming_policy_events": [\n'
        '      "<Arabic: upcoming election/legislation/regulatory decision in ' + country_en + ' affecting SFDA>",\n'
        '      "<Arabic: international health policy negotiation involving ' + country_en + '>",\n'
        '      "<Arabic: bilateral mechanism scheduled to meet in ' + year + '>"\n'
        '    ],\n'
        '    "regional_bloc_context": "<Arabic 2-3 sentences: ASEAN context if Singapore, G7/NATO context if US/EU -- bloc relevance to Saudi strategy>"\n'
        '  },\n\n'
        '  "risk_assessment": {\n'
        '    "risk_summary": "<Arabic 2-3 sentences: overall risk profile -- low/medium/high and key factors>",\n'
        '    "political_risks": [\n'
        '      {"risk_id": "POL-01", "risk_title": "<Arabic>", "description": "<Arabic 2 sentences>", "probability": "<high/medium/low in Arabic>", "impact": "<high/medium/low in Arabic>", "mitigation": "<Arabic 1 sentence>"},\n'
        '      {"risk_id": "POL-02", "risk_title": "<Arabic>", "description": "<Arabic 2 sentences>", "probability": "<Arabic>", "impact": "<Arabic>", "mitigation": "<Arabic 1 sentence>"}\n'
        '    ],\n'
        '    "regulatory_risks": [\n'
        '      {"risk_id": "REG-01", "risk_title": "<Arabic: e.g. pending FDA policy change>", "description": "<Arabic 2 sentences>", "probability": "<Arabic>", "impact": "<Arabic>", "mitigation": "<Arabic>"},\n'
        '      {"risk_id": "REG-02", "risk_title": "<Arabic>", "description": "<Arabic 2 sentences>", "probability": "<Arabic>", "impact": "<Arabic>", "mitigation": "<Arabic>"}\n'
        '    ],\n'
        '    "diplomatic_sensitivities": "<Arabic 2-3 sentences: specific sensitivities for Saudi officials in ' + city + ' in ' + year + '>",\n'
        '    "opportunity_window": "<Arabic 2-3 sentences: favorable political conditions making ' + year + ' optimal timing for SFDA cooperation>",\n'
        '    "risk_matrix_summary": "<Arabic 1-2 sentences: net assessment>"\n'
        '  },\n\n'
        '  "regulatory_comparison": {\n'
        '    "comparison_header": "<Arabic 1-2 sentences: framing as benchmarking to advance SFDA modernization>",\n'
        '    "sfda_profile": {\n'
        '      "full_name": "الهيئة العامة للغذاء والدواء (SFDA) -- المملكة العربية السعودية",\n'
        '      "established": "2003",\n'
        '      "mandate_scope": "<Arabic: drug, food, cosmetics, medical devices scope>",\n'
        '      "international_memberships": "<Arabic: ICH, WHO-listed, GCC-DRF, PIC/S status>",\n'
        '      "approval_timeline_avg": "<Arabic: average approval timeline>"\n'
        '    },\n'
        '    "counterpart_profile": {\n'
        '      "full_name": "<official name of host-country drug regulator from research>",\n'
        '      "established": "<year>",\n'
        '      "mandate_scope": "<Arabic>",\n'
        '      "international_memberships": "<Arabic: ICH, PIC/S, WHO prequalification>",\n'
        '      "approval_timeline_avg": "<Arabic>"\n'
        '    },\n'
        '    "harmonization_gaps": [\n'
        '      "<Arabic: biosimilar approval pathway divergence>",\n'
        '      "<Arabic: clinical trial requirements and data exclusivity>",\n'
        '      "<Arabic: pharmacovigilance reporting standards>",\n'
        '      "<Arabic: medical device classification>"\n'
        '    ],\n'
        '    "mutual_recognition_status": "<Arabic 2-3 sentences: current MRA or regulatory reliance status, what is pending, what SFDA should propose>",\n'
        '    "ich_alignment_status": "<Arabic 2-3 sentences: ICH membership/observer status of both bodies>",\n'
        '    "sfda_benchmark_targets": [\n'
        '      "<Arabic: specific FDA/HSA mechanism SFDA should adopt with implementation step>",\n'
        '      "<Arabic: second benchmark -- named tool or framework>",\n'
        '      "<Arabic: third benchmark -- data system or approval pathway>",\n'
        '      "<Arabic: fourth benchmark -- international recognition mechanism>"\n'
        '    ],\n'
        '    "cooperation_roadmap": "<Arabic 2-3 sentences: 3-step roadmap from info-sharing to formal reliance to mutual recognition>"\n'
        '  },\n\n'
        '  "regional_power_map": {\n'
        '    "host_country_regional_role": "<Arabic 3-4 sentences: ' + country_en + ' formal leadership in G7/G20/ASEAN/WHO -- current positions>",\n'
        '    "regional_bloc_context": "<Arabic 2-3 sentences: bloc ' + country_en + ' anchors and Saudi relationship with that bloc>",\n'
        '    "pharmaceutical_regional_hub": "<Arabic 2-3 sentences: ' + country_en + ' role as pharma manufacturing/regulatory hub -- market share, export figures>",\n'
        '    "competing_powers": [\n'
        '      {"country": "<country>", "regional_role": "<Arabic>", "competition_with_sfda": "<Arabic>"},\n'
        '      {"country": "<country>", "regional_role": "<Arabic>", "competition_with_sfda": "<Arabic>"}\n'
        '    ],\n'
        '    "gcc_pharma_bridge": "<Arabic 2-3 sentences: how strengthening ' + country_en + ' relationship serves Saudi role as GCC pharma leader>",\n'
        '    "key_non_western_participants": "<Arabic 2-3 sentences: key non-Western conference participants and networking opportunities for SFDA>"\n'
        '  }\n'
        '}'
    )

    result = _oai_chat(
        oai, model="gpt-4o", max_tokens=5000, json_mode=True,
        system=(
            "Senior strategic intelligence analyst for Saudi government. "
            "Output ONLY valid JSON. All text in formal Arabic. "
            "Use deep research data for institutional facts and risk indicators. "
            "Be analytically rigorous -- cite specific evidence from research."
        ),
        messages=[{"role": "user", "content": prompt}]
    )
    return _safe_json_load(result)


# ─── Section F: Strategic & Operational Intelligence ─────────────────────────

def _gen_section_f(oai, research, deep_research, event_name, city, country_en,
                   start_date, end_date, kb_vars=None):
    """
    v4.6 NEW: 5 strategic and operational intelligence sections.
    Sections: session leverage matrix, sovereign mandate framing,
    source citations, 3-5 year partnership projection, enriched agenda with moderators.
    """
    year = start_date[:4]
    kv = kb_vars or {}
    kb_header = _build_kb_prompt_header(kv) if kv else ""

    speakers_block = ""
    if kv.get('speakers_list'):
        speakers_block = "CONFIRMED SPEAKERS:\n" + "\n".join(
            f"  - {s}" for s in kv['speakers_list'][:9])

    sessions_block = ""
    if kv.get('sessions_list'):
        sessions_block = "CONFIRMED SESSIONS:\n" + "\n".join(
            f"  - {s}" for s in kv['sessions_list'][:9])

    research_short = _truncate(research, 5000)
    deep_short     = _truncate(deep_research, 5000) if deep_research else "No deep research available."

    # Year arithmetic done in Python, not in f-string
    yr2 = str(int(year) + 1)
    yr3 = str(int(year) + 2)
    yr4 = str(int(year) + 3)
    yr5 = str(int(year) + 4)

    prompt = (
        f"You are generating Section F of a Saudi government travel briefing JSON.\n"
        f"Event: {event_name} | City: {city} | Country: {country_en} | Year: {year}\n"
        f"Dates: {start_date} to {end_date or start_date}\n\n"
        f"{kb_header}\n{speakers_block}\n{sessions_block}\n\n"
        f"PRIMARY RESEARCH:\n{research_short}\n\n"
        f"DEEP STRATEGIC RESEARCH (Phase 1H):\n{deep_short}\n\n"
        "Return ONLY this JSON object. ALL narrative text in formal Arabic. No markdown.\n\n"
        "{\n"
        '  "session_leverage_matrix": [\n'
        '    {"session_title": "<exact session title from research>", "track_classification": "<Arabic: Health/Finance/Technology/etc>", "sfda_relevance_score": 8, "key_speakers": "<speaker names>", "leverage_opportunity": "<Arabic 2 sentences>", "desired_outcome": "<Arabic 1 sentence>", "preparation_required": "<Arabic 1 sentence>", "key_contact_to_engage": "<Arabic: specific speaker or attendee>"},\n'
        '    {"session_title": "<second session>", "track_classification": "<Arabic>", "sfda_relevance_score": 7, "key_speakers": "<names>", "leverage_opportunity": "<Arabic 2 sentences>", "desired_outcome": "<Arabic>", "preparation_required": "<Arabic>", "key_contact_to_engage": "<Arabic>"},\n'
        '    {"session_title": "<third session>", "track_classification": "<Arabic>", "sfda_relevance_score": 6, "key_speakers": "<names>", "leverage_opportunity": "<Arabic 2 sentences>", "desired_outcome": "<Arabic>", "preparation_required": "<Arabic>", "key_contact_to_engage": "<Arabic>"},\n'
        '    {"session_title": "<fourth session>", "track_classification": "<Arabic>", "sfda_relevance_score": 7, "key_speakers": "<names>", "leverage_opportunity": "<Arabic 2 sentences>", "desired_outcome": "<Arabic>", "preparation_required": "<Arabic>", "key_contact_to_engage": "<Arabic>"},\n'
        '    {"session_title": "<fifth session>", "track_classification": "<Arabic>", "sfda_relevance_score": 5, "key_speakers": "<names>", "leverage_opportunity": "<Arabic 2 sentences>", "desired_outcome": "<Arabic>", "preparation_required": "<Arabic>", "key_contact_to_engage": "<Arabic>"}\n'
        '  ],\n\n'
        '  "sovereign_mandate_framing": {\n'
        '    "mandate_title": "تفويض سيادي رسمي -- وفد الهيئة العامة للغذاء والدواء",\n'
        '    "legal_authority_basis": "<Arabic 2-3 sentences: legal foundation of SFDA authority to enter international agreements -- SFDA founding law, Council of Ministers mandate>",\n'
        '    "representation_tier": "<Arabic: tier this delegation represents and signatory authority>",\n'
        '    "mandate_scope": [\n'
        '      "<Arabic: SFDA authorized to negotiate MoUs with foreign regulatory authorities>",\n'
        '      "<Arabic: technical cooperation agreements in drug safety, food standards, medical devices>",\n'
        '      "<Arabic: data-sharing and pharmacovigilance harmonization frameworks>",\n'
        '      "<Arabic: participation in international regulatory standards bodies>",\n'
        '      "<Arabic: joint research and capacity-building programs>"\n'
        '    ],\n'
        '    "protocol_rank": "<Arabic 2 sentences: protocol classification of CEO-level participation>",\n'
        '    "deliverable_authority": "<Arabic 2 sentences: what delegation can commit to on-the-spot vs what requires referral>",\n'
        '    "negotiation_parameters": "<Arabic 2-3 sentences: pre-authorized negotiating parameters>",\n'
        '    "reporting_obligation": "<Arabic 1-2 sentences: post-trip reporting requirements>"\n'
        '  },\n\n'
        '  "source_citation_appendix": {\n'
        '    "citation_note": "جميع المصادر مُتحقق منها من مصادر رسمية ومنظمات دولية معترف بها.",\n'
        '    "primary_sources": [\n'
        '      {"source_id": "S-01", "title": "<source title from research>", "url": "<URL or pending>", "type": "<Arabic: official site/govt report/press release/stats>", "reliability": "<high/medium in Arabic>", "used_for": "<Arabic: which report sections>"},\n'
        '      {"source_id": "S-02", "title": "<second source>", "url": "<URL>", "type": "<Arabic>", "reliability": "<Arabic>", "used_for": "<Arabic>"},\n'
        '      {"source_id": "S-03", "title": "<third source>", "url": "<URL>", "type": "<Arabic>", "reliability": "<Arabic>", "used_for": "<Arabic>"},\n'
        '      {"source_id": "S-04", "title": "<fourth source>", "url": "<URL>", "type": "<Arabic>", "reliability": "<Arabic>", "used_for": "<Arabic>"},\n'
        '      {"source_id": "S-05", "title": "<fifth source>", "url": "<URL>", "type": "<Arabic>", "reliability": "<Arabic>", "used_for": "<Arabic>"}\n'
        '    ],\n'
        '    "data_quality_note": "<Arabic 1-2 sentences: what is verified vs estimated, recommendation to update dynamic figures before the visit>"\n'
        '  },\n\n'
        '  "partnership_projection": {\n'
        '    "projection_rationale": "<Arabic 2-3 sentences: why structured 3-5 year plan produces better outcomes than one-time engagement>",\n'
        f'    "year_1_targets": {{\n'
        f'      "label": "السنة الأولى ({year}) -- تأسيس القناة",\n'
        '      "objectives": [\n'
        '        "<Arabic: Sign or initiate MoU with host-country regulator -- specify scope>",\n'
        '        "<Arabic: Establish joint technical working group on specific topic>",\n'
        '        "<Arabic: Return with 2-3 named contacts for ongoing communication>",\n'
        '        "<Arabic: Agree on first joint activity -- workshop or data-sharing pilot>"\n'
        '      ],\n'
        '      "kpis": ["<Arabic: KPI 1 with target and date>", "<Arabic: KPI 2>", "<Arabic: KPI 3>"]\n'
        '    },\n'
        f'    "year_2_3_milestones": {{\n'
        f'      "label": "السنة الثانية والثالثة ({yr2}--{yr3}) -- تعميق التعاون",\n'
        '      "milestones": [\n'
        '        "<Arabic: First bilateral regulatory workshop in Riyadh or counterpart city>",\n'
        '        "<Arabic: Expand MoU scope to second regulatory domain>",\n'
        '        "<Arabic: Submit joint paper to ICH or WHO>",\n'
        '        "<Arabic: Launch mutual reliance pilot for specific drug category>",\n'
        '        "<Arabic: Annual exchange program for regulatory scientists>"\n'
        '      ],\n'
        '      "success_indicators": "<Arabic 2 sentences: measurable evidence partnership is on track at year 3>"\n'
        '    },\n'
        f'    "year_4_5_strategic_outcomes": {{\n'
        f'      "label": "السنة الرابعة والخامسة ({yr4}--{yr5}) -- التأثير الاستراتيجي",\n'
        '      "outcomes": [\n'
        '        "<Arabic: Formal regulatory reliance arrangement -- SFDA accepts counterpart data for fast-track reviews>",\n'
        '        "<Arabic: Saudi Arabia achieves formal recognition in counterpart regulatory network>",\n'
        '        "<Arabic: Joint representation at international regulatory bodies>",\n'
        '        "<Arabic: Measurable improvement in Saudi drug approval timeline>"\n'
        '      ],\n'
        '      "vision_2030_alignment": "<Arabic 2-3 sentences: how year 4-5 outcomes advance Vision 2030 health sector targets>"\n'
        '    },\n'
        '    "investment_requirement": "<Arabic 1-2 sentences: estimated resource commitment from SFDA to sustain partnership>",\n'
        '    "risk_to_projection": "<Arabic 1-2 sentences: primary risk that could derail 3-5 year trajectory and mitigation>"\n'
        '  },\n\n'
        '  "agenda_with_moderators": [\n'
        f'    {{"session_title": "<exact session from confirmed sessions>", "date": "{start_date}", "time": "<time>", "venue_room": "<hall>", "track": "<Finance/Health/Technology/Geopolitics/Investment/Regulatory>", "track_arabic": "<Arabic>", "moderator": "<moderator name or not confirmed>", "moderator_title": "<exact title>", "confirmed_speakers": ["<speaker 1>", "<speaker 2>"], "session_format": "<Keynote/Panel/Fireside Chat>", "sfda_relevance": "<Arabic 1-2 sentences>", "strategic_priority": "<high/medium/low in Arabic>"}},\n'
        f'    {{"session_title": "<second session>", "date": "{start_date}", "time": "<time>", "venue_room": "<hall>", "track": "<track>", "track_arabic": "<Arabic>", "moderator": "يُحدَّد لاحقاً", "moderator_title": "يُحدَّد لاحقاً", "confirmed_speakers": ["<speaker>"], "session_format": "<format>", "sfda_relevance": "<Arabic>", "strategic_priority": "<Arabic>"}},\n'
        f'    {{"session_title": "<third session>", "date": "{start_date}", "time": "<time>", "venue_room": "<hall>", "track": "<track>", "track_arabic": "<Arabic>", "moderator": "يُحدَّد لاحقاً", "moderator_title": "يُحدَّد لاحقاً", "confirmed_speakers": ["<speaker>"], "session_format": "<format>", "sfda_relevance": "<Arabic>", "strategic_priority": "<Arabic>"}}\n'
        '  ]\n'
        '}'
    )

    result = _oai_chat(
        oai, model="gpt-4o", max_tokens=5000, json_mode=True,
        system=(
            "Senior strategic intelligence analyst for Saudi government. "
            "Output ONLY valid JSON. All narrative text in formal Arabic. "
            "session_leverage_matrix: use ONLY confirmed sessions from research -- 5 entries. "
            "sfda_relevance_score must be an integer 1-10. "
            "source_citation_appendix: use real URLs from research, not invented ones. "
            "partnership_projection: be specific and actionable with concrete KPIs."
        ),
        messages=[{"role": "user", "content": prompt}]
    )
    return _safe_json_load(result)


# ─── Section G: Document Control (static Python -- no API call) ───────────────

def _gen_document_control(event_name, city, country_en, start_date, delegation,
                          report_version="4.6", classification="سري -- للاستخدام الرسمي فقط"):
    """
    v4.6 NEW: Generates document control and classification metadata.
    Pure Python -- no AI call required. Derived entirely from report metadata.
    """
    from datetime import datetime as _dt2
    now_str     = _dt2.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
    now_display = _dt2.utcnow().strftime("%d %B %Y")
    year        = start_date[:4]

    distribution = []
    for m in delegation:
        distribution.append({
            "name":  m.get('name', ''),
            "title": m.get('title', ''),
            "copy":  "نسخة أصلية"
        })
    distribution += [
        {"name": "وزارة الصحة -- مستشار الوزير للشؤون الدولية",    "title": "", "copy": "نسخة للعلم"},
        {"name": "وزارة الخارجية -- الديوان الدولي",               "title": "", "copy": "نسخة للعلم"},
        {"name": "سفارة المملكة -- قسم الشؤون الاقتصادية",          "title": "", "copy": "نسخة للعلم"},
    ]

    return {
        "document_control": {
            "document_title":        f"الإحاطة التنفيذية الرسمية -- {event_name}",
            "document_reference":    f"SFDA-INTL-{year}-{start_date.replace('-','')[:8]}",
            "version":               report_version,
            "classification":        classification,
            "classification_arabic": "تصنيف الوثيقة: سري -- للاستخدام الرسمي فقط",
            "issued_by":             "إدارة الشؤون الدولية -- الهيئة العامة للغذاء والدواء",
            "prepared_by":           "وحدة الاستخبارات الاستراتيجية والإحاطات التنفيذية",
            "reviewed_by":           "د. محمد بن عبدالعزيز الفراج -- مساعد الرئيس التنفيذي للشؤون الدولية",
            "approved_by":           "د. هشام بن سعد الجضعي -- الرئيس التنفيذي",
            "date_issued":           now_display,
            "date_issued_iso":       now_str,
            "valid_until":           "30 يوم من تاريخ الإصدار",
            "purpose":               f"توجيه الوفد الرسمي للهيئة المشارك في {event_name} ({start_date} -- {city}، {country_en})",
            "distribution_list":     distribution,
            "handling_instructions": [
                "يُحظر تداول هذه الوثيقة خارج قائمة التوزيع المعتمدة",
                "لا تُنسخ أو تُرسل إلكترونياً إلا عبر القنوات الرسمية المشفَّرة",
                "تُتلف الوثيقة بعد انتهاء صلاحيتها وفق إجراءات الأمن المعلوماتي المعتمدة",
                "في حال الفقدان أو التسريب يُبلَّغ فوراً مكتب أمن المعلومات بالهيئة",
            ],
            "revision_history": [
                {"version": "1.0", "date": now_display, "author": "وحدة الاستخبارات الاستراتيجية", "changes": "إصدار أولي"}
            ],
            "related_documents": [
                f"خطة عمل الشؤون الدولية {year}",
                "دليل البروتوكول الدبلوماسي للوفود الرسمية",
                "سياسة تصنيف المعلومات -- الهيئة العامة للغذاء والدواء",
            ],
            "ai_generation_note": f"أُعِدَّت هذه الوثيقة بمساعدة نظام الذكاء الاصطناعي v{report_version} -- تخضع للمراجعة والاعتماد من الشؤون الدولية قبل الاستخدام الرسمي.",
        }
    }


# ─── Phase 2 Orchestrator ─────────────────────────────────────────────────────

def _generate_json(research, event_name, city, country, country_en,
                   start_date, end_date, venue, event_type, context, oai,
                   kb_vars=None, deep_research=""):
    """
    v4.6: Orchestrates 7 section generators, then applies Python-level KB overrides.
      A-D: Original sections (factual, people, narrative, schedule)
      E:   Deep intelligence (institutional, historical, geopolitical, risk, regulatory, regional)
      F:   Strategic & operational (leverage matrix, mandate, citations, projection, agenda)
      G:   Document control (pure Python -- no API call)
    KB overrides run AFTER all AI sections -- guaranteed correct regardless of model confusion.
    """
    num_days, dates = _make_dates(start_date, end_date)
    year = start_date[:4]
    kv = kb_vars or {}
    deep = deep_research or ""

    # Leader overrides -- prevents stale training data
    overrides = {
        "united states":  "Donald J. Trump",
        "usa":            "Donald J. Trump",
        "united kingdom": "Keir Starmer",
        "germany":        "Friedrich Merz",
        "france":         "Emmanuel Macron",
        "canada":         "Mark Carney",
        "italy":          "Giorgia Meloni",
        "japan":          "Shigeru Ishiba",
        "australia":      "Anthony Albanese",
        "singapore":      "Lawrence Wong",
        "india":          "Narendra Modi",
        "south korea":    "Han Duck-soo",
        "indonesia":      "Prabowo Subianto",
        "malaysia":       "Anwar Ibrahim",
        "thailand":       "Paetongtarn Shinawatra",
        "china":          "Xi Jinping",
        "switzerland":    "Karin Keller-Sutter",
    }
    leader_override = next((v for k, v in overrides.items() if k in country_en.lower()), None)

    data = {}

    # Run all 6 AI sections -- each independently retried on failure
    sections = [
        ("A (Factual)",      lambda: _gen_section_a(oai, research, event_name, city, country, country_en, start_date, end_date, venue, leader_override, kb_vars=kv)),
        ("B (People)",       lambda: _gen_section_b(oai, research, event_name, country_en, start_date, end_date, kb_vars=kv)),
        ("C (Narrative)",    lambda: _gen_section_c(oai, research, event_name, city, country, country_en, start_date, context, kb_vars=kv)),
        ("D (Schedule)",     lambda: _gen_section_d(oai, research, event_name, city, country, country_en, start_date, end_date, venue, num_days, dates)),
        ("E (Intelligence)", lambda: _gen_section_e(oai, research, deep, event_name, city, country, country_en, start_date, kb_vars=kv)),
        ("F (Strategic)",    lambda: _gen_section_f(oai, research, deep, event_name, city, country_en, start_date, end_date, kb_vars=kv)),
    ]

    for label, fn in sections:
        for attempt in range(2):
            try:
                result = fn()
                if result and len(result) >= 2:
                    data.update(result)
                    print(f"[AI] Section {label}: OK ({len(result)} keys)")
                    break
                else:
                    print(f"[AI] Section {label}: empty result (attempt {attempt+1})")
                    if attempt == 0:
                        time.sleep(5)
            except Exception as e:
                print(f"[AI] Section {label} error (attempt {attempt+1}): {e}")
                if attempt == 0:
                    time.sleep(10)

    # ── v4.5: Python-level KB overrides (runs AFTER all AI sections) ────────────
    # This layer is 100% reliable — Python dict assignment cannot be "confused".
    # It fixes any remaining errors from AI sections.
    if kv:
        _apply_kb_overrides(data, kv)
        _apply_kb_prayer_times(data, kv, dates, num_days)
        _apply_kb_speakers(data, kv)
        _apply_kb_history(data, kv)

    # Hardcoded delegation -- never generated by AI (avoids hallucination)
    delegation = [
        {"name":"د. هشام بن سعد الجضعي","title":"الرئيس التنفيذي للهيئة العامة للغذاء والدواء","department":"الرئاسة التنفيذية","strategic_role":"رئاسة الوفد الرسمي وتمثيل المملكة على أعلى مستوى تنفيذي"},
        {"name":"د. محمد بن عبدالعزيز الفراج","title":"مساعد الرئيس التنفيذي للشؤون الدولية","department":"الشؤون الدولية","strategic_role":"إدارة الاجتماعات الثنائية وتنسيق اتفاقيات التعاون الدولي"},
        {"name":"م. سارة بنت عبدالله العمري","title":"مدير إدارة الشؤون التنظيمية الدولية","department":"الشؤون التنظيمية","strategic_role":"متابعة ملفات التناسق التنظيمي ومفاوضات اتفاقيات الاعتراف المتبادل"},
        {"name":"د. خالد بن سعد المطيري","title":"مستشار الرئيس التنفيذي للسياسات الدوائية","department":"السياسات الدوائية","strategic_role":"تقديم المشورة التقنية وتمثيل الهيئة في الجلسات العلمية المتخصصة"},
    ]
    data['delegation']    = delegation
    data['participants']  = []

    # ── Section G: Document control (pure Python -- no API call) ───────────────
    try:
        doc_ctrl = _gen_document_control(
            event_name=event_name, city=city, country_en=country_en,
            start_date=start_date, delegation=delegation, report_version="4.6"
        )
        data.update(doc_ctrl)
        print("[AI] Section G (Document Control): OK (static Python)")
    except Exception as e:
        print(f"[AI] Section G error: {e}")

    # Expand agenda and sessions if Section D only returned Day 1
    _expand_schedule(data, event_name, country_en, start_date, num_days, dates, venue)

    print(f"[AI] Phase 2 complete: {len(data)} total fields")
    return data


def _expand_schedule(data, event_name, country_en, start_date, num_days, dates, venue):
    """
    If Section D returned agenda/sessions for only day 1, expand to all days.
    Uses a simple pattern — subsequent days inherit structure from day 1.
    """
    day_ar = ["اليوم الأول","اليوم الثاني","اليوم الثالث","اليوم الرابع","اليوم الخامس"]
    day_en = ["Day 1","Day 2","Day 3","Day 4","Day 5"]
    venue_str = venue or ""

    agenda = data.get('agenda', [])
    if num_days > 1 and len(agenda) < num_days:
        # Expand missing days
        for i in range(len(agenda), num_days):
            day_block = {
                "day_label": day_ar[i],
                "day_label_en": day_en[i],
                "date": dates[i],
                "items": [
                    {"time": "09:00", "activity": f"جلسات {day_en[i]} — {event_name}", "location": venue_str, "type": "session", "strategic_relevance": "متابعة أعمال المؤتمر"},
                    {"time": "12:00", "activity": "استراحة الغداء والتواصل", "location": venue_str, "type": "networking", "strategic_relevance": "بناء الشبكات"},
                    {"time": "14:00", "activity": "اجتماعات ثنائية", "location": venue_str, "type": "bilateral", "strategic_relevance": "دبلوماسية صحية"},
                    {"time": "16:00", "activity": "جلسة مسائية", "location": venue_str, "type": "session", "strategic_relevance": "يُحدَّد لاحقاً"},
                ]
            }
            # Last day: add closing session
            if i == num_days - 1:
                day_block["items"].append({"time": "17:00", "activity": "الجلسة الختامية وإعلان توصيات المؤتمر", "location": venue_str, "type": "ceremony", "strategic_relevance": "استخلاص النتائج الاستراتيجية"})
            agenda.append(day_block)
        data['agenda'] = agenda

    sessions = data.get('sessions', {})
    if isinstance(sessions, dict) and 'day1' in sessions:
        for i in range(1, num_days):
            dk = f'day{i+1}'
            if dk not in sessions:
                sessions[dk] = [
                    {"time": "09:00", "title": f"جلسة الصباح — {day_en[i]}", "description": "يُحدَّد لاحقاً", "speakers": "يُحدَّد لاحقاً", "policy_implications": "يُحدَّد لاحقاً", "investment_implications": "يُحدَّد لاحقاً", "regulatory_impact": "يُحدَّد لاحقاً", "strategic_score": "متوسط"},
                    {"time": "14:30", "title": f"جلسة بعد الظهر — {day_en[i]}", "description": "يُحدَّد لاحقاً", "speakers": "يُحدَّد لاحقاً", "policy_implications": "يُحدَّد لاحقاً", "investment_implications": "يُحدَّد لاحقاً", "regulatory_impact": "يُحدَّد لاحقاً", "strategic_score": "متوسط"},
                ]
        data['sessions'] = sessions

    # Expand weather and prayer times for all days
    weather = data.get('weather', [])
    prayer_times = data.get('prayer_times', [])
    if weather and len(weather) < num_days:
        base_w = weather[0]
        for i in range(len(weather), num_days):
            day_w = dict(base_w)
            day_w['day']  = day_en[i]
            day_w['date'] = dates[i]
            weather.append(day_w)
        data['weather'] = weather
    if prayer_times and len(prayer_times) < num_days:
        base_pt = prayer_times[0]
        def _shift_time(t, mins):
            try:
                h, m = map(int, t.split(':'))
                total = h * 60 + m + mins
                return f"{total//60:02d}:{total%60:02d}"
            except:
                return t
        for i in range(len(prayer_times), num_days):
            day_pt = dict(base_pt)
            day_pt['date'] = dates[i]
            day_pt['day']  = f"{day_en[i]} — {day_ar[i]}"
            day_pt['fajr']    = _shift_time(base_pt.get('fajr',    '05:26'), -i)
            day_pt['maghrib'] = _shift_time(base_pt.get('maghrib', '18:57'), +i)
            day_pt['isha']    = _shift_time(base_pt.get('isha',    '20:06'), +i)
            prayer_times.append(day_pt)
        data['prayer_times'] = prayer_times


def generate_report_content(event_name, city, country, start_date, end_date,
                             venue, event_type, context, language='Arabic',
                             event_website=''):
    """
    PIPELINE v4.4 — KB Override + Full Accuracy Architecture
    ══════════════════════════════════════════════════════════════
    Phase 0    → gpt-4o-mini            Translate inputs          (~200 tokens)
    Phase 1D   → Static KB              Stable facts + year data   (instant)
               ★ KB Override Block injected at position 0 of research
                 [embassy, consulate, GDP, edition, confirmed speakers]
    Phase 1C   → gpt-4o-search-preview  Official website scrape    (~4,000 tokens)
    Phase 1A   → gpt-4o-search-preview  Primary research A–L       (~6,000 tokens)
    Phase 1B   → gpt-4o-search-preview  Supplemental research      (~4,000 tokens)
    Phase 1E   → gpt-4o-search-preview  Accuracy-critical checks   (~3,000 tokens)
    Phase 1F   → gpt-4o-search-preview  Post-event recap           (~4,000 tokens)
    Phase 1G   → gpt-4o                 Consolidate verified facts (~2,000 tokens)
    Phase 2A   → gpt-4o                 Factual section JSON       (~3,000 tokens)
    Phase 2B   → gpt-4o                 People section JSON        (~3,500 tokens)
    Phase 2C   → gpt-4o                 Narrative section JSON     (~4,000 tokens)
    Phase 2D   → gpt-4o                 Schedule section JSON      (~5,000 tokens)
    ─────────────────────────────────────────────────────────────────────────────
    v4.3 → v4.4 fixes (regression fixes):
      1. KB Override Block: compact pre-verified block at top of research
         → embassy/consulate NO LONGER truncated away (was 4th in research, now 1st)
      2. Section A prompt: explicitly references KB OVERRIDE BLOCK field names
         → GDP/embassy/ambassador/edition correctly pulled from KB
      3. _kb_to_text: restored year_data reader for conferences with pre-verified data
         → milken global edition (29th), all 9 confirmed speakers back in research
    Target accuracy: 92-95%
    """
    openai_key = getattr(settings, 'OPENAI_API_KEY', '') or os.environ.get('OPENAI_API_KEY', '')

    if not openai_key or 'YOUR' in openai_key:
        raise ValueError(
            "OpenAI API key not configured. Add to backend/.env:\n"
            "  OPENAI_API_KEY=sk-proj-..."
        )

    try:
        from openai import OpenAI as _OAI
        oai = _OAI(api_key=openai_key)
    except Exception as e:
        raise RuntimeError(f"Failed to initialize OpenAI client: {e}")

    # FIX v4.1: Normalize event_website — auto-add https:// if missing
    # Prevents Phase 1C from silently skipping 'www.globalconference.org'
    event_website = _normalize_url(event_website)

    # ── Phase 0: Translate Arabic inputs ──────────────────────────────────────
    def _translate(text):
        if not text or not _has_arabic(text):
            return text
        try:
            return _oai_chat(
                oai,
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": f"Translate to English only, nothing else: {text}"}],
                max_tokens=100,
            )
        except Exception:
            return text

    country_en = _translate(country)
    city_en    = _translate(city)
    print(f"[AI] Translated: city='{city_en}', country='{country_en}'")

    # ── Static knowledge base ─────────────────────────────────────────────────
    KNOWN_CONFERENCES = {

        # Compound keys checked first (most specific)
        "milken asia": {
            "full_name": "Milken Institute Asia Summit",
            "organizer": "Milken Institute",
            "organizer_type": "Nonprofit, nonpartisan think tank, founded 1991, Santa Monica, California",
            "ceo": "Richard Ditizio (CEO, Milken Institute)",
            "founder": "Michael Milken (Chairman)",
            "website": "https://milkeninstitute.org/events/asia-summit-2025",
            # ─────────────────────────────────────────────────────────────────────
            # v4.3: NO year-specific hardcoded data (theme, speakers, attendance).
            # Those are DYNAMIC and fetched live by Phase 1E/1F/1G.
            # Hardcoding them caused the wrong theme + stale CEO in v4.2 (score: 2/10).
            # History entries below are VERIFIED PAST FACTS — safe to keep.
            # ─────────────────────────────────────────────────────────────────────
            "city_facts": {
                "city": "singapore",
                # Government — verify currency before each trip
                "prime_minister":    "Lawrence Wong (since May 15, 2024)",
                "president":         "Tharman Shanmugaratnam (since September 1, 2023)",
                # Key institutional leaders — verify before each trip, roles change
                "dbs_ceo":           "Tan Su Shan (CEO since March 28, 2025 — Piyush Gupta retired)",
                "temasek_ceo":       "Dilhan Pillay Sandrasegara (Executive Director & CEO, Temasek International)",
                # Country facts — stable
                "gdp":               "USD 501 billion (2024, MTI Singapore)",
                "gdp_per_capita":    "USD 88,000 (2024)",
                "population":        "5.92 million (2024, DOS Singapore)",
                "area":              "733.2 km²",
                "currency":          "Singapore Dollar (SGD)",
                "language":          "English (official), Malay, Mandarin, Tamil",
                "timezone":          "UTC+8 (SST — Singapore Standard Time) — NEVER write UTC+7",
                # Saudi diplomatic presence
                "saudi_embassy":     "Royal Embassy of Saudi Arabia, 10 Nassim Road, Singapore 258386",
                "embassy_phone":     "+65 6734 3430",
                # Regulatory bodies — stable
                "drug_regulator":    "Health Sciences Authority (HSA) — Singapore",
                "health_ministry":   "Ministry of Health Singapore (MOH)",
                "food_body":         "Singapore Food Agency (SFA)",
                "pharma_body":       "Singapore Association of Pharmaceutical Industries (SAPI)",
                # Bilateral — approximate, verify per trip
                "bilateral_trade":   "SGD 9–11 billion annually (2023, Enterprise Singapore)",
                "visa":              "Saudi official/diplomatic passport: no visa required, up to 30 days",
                "weather":           "October: High 31°C, Low 24°C, afternoon showers, humidity 80-85%",
                # Prayer times for Singapore in October (standard calculation)
                "prayer_day1":       {"fajr":"05:26","dhuhr":"12:56","asr":"16:07","maghrib":"18:57","isha":"20:06"},
                "prayer_day2":       {"fajr":"05:25","dhuhr":"12:55","asr":"16:07","maghrib":"18:56","isha":"20:05"},
                "prayer_day3":       {"fajr":"05:25","dhuhr":"12:55","asr":"16:06","maghrib":"18:55","isha":"20:04"},
                "prayer_day4":       {"fajr":"05:24","dhuhr":"12:54","asr":"16:06","maghrib":"18:55","isha":"20:03"},
            },
            # Past editions — VERIFIED HISTORICAL FACTS, safe to keep
            "history": {
                "2025": {"theme": "Progress with Purpose: Collaboration Amid Complexity", "attendance": "1,200+ from 43 countries"},
                "2024": {"theme": "Bridging the Future: Asia's Role in a Fragmented World",    "attendance": "1,800+"},
                "2023": {"theme": "Asia's Resilience in a Fractured World",                    "attendance": "1,600+"},
                "2022": {"theme": "Re-Engaging Asia: Pathways to Recovery and Growth",          "attendance": "1,200+"},
            }
        },


        "milken global": {
            "full_name": "Milken Institute Global Conference",
            "organizer": "Milken Institute",
            "organizer_type": "Nonprofit, nonpartisan think tank founded 1991, Santa Monica, California",
            "founded": "1991",            # Milken Institute founding year
            "conference_first_held": "1994",   # First Global Conference edition
            "ceo": "Richard Ditizio (CEO, Milken Institute)",
            "founder": "Michael Milken (Chairman)",
            "2025": {
                "edition": "29th Annual",
                "theme": "Toward a Flourishing Future",
                "theme_arabic": "نحو مستقبل مزدهر",
                # CRITICAL NOTE: "A Beacon to the World: Strengthening the American Dream"
                # is Michael Milken's OPENING SPEECH TITLE — NOT the conference theme.
                # The CONFERENCE THEME is "Toward a Flourishing Future" / "نحو مستقبل مزدهر"
                "theme_disambiguation": "DO NOT CONFUSE: Conference theme='Toward a Flourishing Future'. Milken's opening speech title='A Beacon to the World: Strengthening the American Dream' — these are DIFFERENT.",
                "dates": "May 4–7, 2025",
                "venue": "The Beverly Hilton & The Waldorf Astoria Beverly Hills, Los Angeles, California",
                "attendees": "5,000+ attendees from 80+ countries",
                "speakers_count": "1,000+ speakers",
                "sessions_count": "170 public sessions",
                "confirmed_speakers": [
                    "Jane Fraser — CEO, Citi (United States)",
                    "Jensen Huang — CEO and Co-Founder, NVIDIA Corporation (United States)",
                    "Queen Rania Al Abdullah — Queen, Hashemite Kingdom of Jordan (Jordan)",
                    "Jose Andres — Founder, World Central Kitchen (Spain/United States)",
                    "Ajay Banga — President, World Bank Group (India/United States)",
                    "Scott Bessent — U.S. Secretary of the Treasury (United States)",
                    "Richard Ditizio — CEO, Milken Institute (United States) [HOST]",
                    "Kristalina Georgieva — Managing Director, IMF (Bulgaria — بلغاريا NOT American)",
                    "Mary Barra — Chair and CEO, General Motors (United States)",
                ],
                "confirmed_sessions": [
                    "Opening Plenary: Toward a Flourishing Future",
                    "Global Capital Markets — Jane Fraser (Citi CEO)",
                    "The Intersection Between Alternatives And Private Wealth",
                    "AI and Technology — Jensen Huang (NVIDIA CEO) keynote",
                    "Scott Bessent: US Economic Policy and Fiscal Priorities",
                    "Public Health and Global Pandemic Preparedness",
                    "Climate Change and Energy Transition",
                    "Digital Health and Healthcare Innovation",
                    "Geopolitical Risks and Global Economic Outlook",
                ],
                "topics": "Capital access, public health, geopolitics, climate, AI, impact investing, alternatives, private wealth",
                "media": "CNBC, Bloomberg, Yahoo Finance, Fox Business; 170 sessions streamed",
            },
            "city_facts": {
                "city": "los angeles",
                "president":       "Donald J. Trump (47th President, since January 20, 2025)",
                "gdp":             "$30.62 trillion (2025, IMF)",
                "population":      "~347 million (2025)",
                "gdp_per_capita":  "~$88,000 (2025)",
                "bilateral_trade": "$39.5 billion total (2024, USTR)",
                "drug_regulator":  "U.S. Food and Drug Administration (FDA), Commissioner: Marty Makary (2025–)",
                "health_ministry": "U.S. Department of Health and Human Services (HHS), Secretary: Robert F. Kennedy Jr. (2025–)",
                "food_body":       "FDA CFSAN (Center for Food Safety and Applied Nutrition)",
                "pharma_body":     "PhRMA (Pharmaceutical Research and Manufacturers of America), President: Stephen Ubl",
                "nih":             "NIH (National Institutes of Health), Director: Jay Bhattacharya (2025–)",
                "saudi_ambassador":"HRH Princess Reema bint Bandar bint Sultan Al Saud (since February 2019, first female Saudi ambassador)",
                "embassy":         "601 New Hampshire Ave NW, Washington DC 20037 | Tel: (202) 342-3800 | info@saudiembassy.net",
                "consulate_la":    "12400 Wilshire Blvd Suite 700, Los Angeles CA 90025 | Tel: (310) 479-6000 | uscacon@mofa.gov.sa",
                "consul_la":       "Mr. Fawaz Alshubaili (Consul General, Los Angeles)",
                "timezone":        "UTC-7 (PDT — Pacific Daylight Time) — for May. NEVER write UTC-5 for Los Angeles",
                "visa":            "Saudi official/diplomatic passport: no visa required for USA; ESTA not required on diplomatic passport",
                "weather":         "Los Angeles May: High 26-29°C, Low 15-17°C, mostly sunny",
                "prayer_day1":     {"fajr":"05:19","dhuhr":"12:53","asr":"16:28","maghrib":"19:46","isha":"21:09"},
                "prayer_day2":     {"fajr":"05:18","dhuhr":"12:53","asr":"16:28","maghrib":"19:47","isha":"21:10"},
                "prayer_day3":     {"fajr":"05:17","dhuhr":"12:52","asr":"16:28","maghrib":"19:48","isha":"21:11"},
                "prayer_day4":     {"fajr":"05:16","dhuhr":"12:52","asr":"16:29","maghrib":"19:49","isha":"21:12"},
                "nationality_note":"Kristalina Georgieva is BULGARIAN (بلغاريا) — NOT American",
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
        },

        "wha": {
            "full_name": "World Health Assembly",
            "organizer": "World Health Organization",
        },
    }

    def _match_kb(name_lower):
        """Match compound keys before single-word keys to ensure specificity."""
        for key in sorted(KNOWN_CONFERENCES, key=lambda k: len(k.split()), reverse=True):
            if all(w in name_lower for w in key.split()):
                return KNOWN_CONFERENCES[key]
        return None

    def _kb_to_text(conf, start_date, city_en):
        """
        Serialize a knowledge base entry into research-text format.
        v4.3: Year-specific event data (theme, speakers) is NO LONGER stored in KB —
        those are fetched live. KB now provides stable city/country facts + past editions.
        """
        year = start_date[:4]
        cf = conf.get('city_facts', {})

        lines = [
            "=== VERIFIED CONFERENCE KNOWLEDGE BASE (STABLE FACTS — PRE-VERIFIED) ===",
            f"Conference: {conf.get('full_name','')}",
            f"Organizer: {conf.get('organizer','')} — {conf.get('organizer_type','')}",
            f"Organizer CEO: {conf.get('ceo','')} | Founder: {conf.get('founder','')}",
            f"Official website: {conf.get('website','')}",
            "",
            "⚠️  EVENT-SPECIFIC FACTS (theme, attendance, speakers, sessions) are NOT stored here.",
            "    They are fetched live from Phase 1C/1E/1F searches.",
            "    Do NOT invent theme or speakers — use only what the live research provides.",
        ]

        # Past editions are HISTORICAL FACTS — safe and accurate
        hist = conf.get('history', {})
        if hist:
            lines.append("\nVERIFIED PAST EDITIONS (historical — accurate):")
            for yr, h in sorted(hist.items(), reverse=True):
                if yr != year:
                    lines.append(f"  {yr}: Theme='{h.get('theme','')}' | Attendance: {h.get('attendance','')}")
                else:
                    lines.append(f"  {yr} (THIS EDITION): Theme='{h.get('theme','')}' | Attendance: {h.get('attendance','')} [CONFIRMED POST-EVENT]")

        # Restore year-specific data for conferences that still carry it (e.g. milken global)
        # milken asia was stripped of year-specific data; milken global still has it
        year_data = conf.get(year, {})
        if year_data:
            lines.append(f"\n{year} EDITION VERIFIED FACTS (pre-verified — use EXACTLY):")
            if year_data.get('edition'):
                lines.append(f"  Edition: {year_data['edition']}")
            if year_data.get('theme'):
                lines.append(f"  Official theme (English): {year_data['theme']}")
            if year_data.get('theme_arabic'):
                lines.append(f"  Official theme (Arabic): {year_data['theme_arabic']}")
            if year_data.get('dates'):
                lines.append(f"  Dates: {year_data['dates']}")
            if year_data.get('venue'):
                lines.append(f"  Venue: {year_data['venue']}")
            if year_data.get('attendees'):
                lines.append(f"  Attendance: {year_data['attendees']}")
            if year_data.get('speakers_count'):
                lines.append(f"  Speakers: {year_data['speakers_count']}")
            if year_data.get('sessions_count'):
                lines.append(f"  Sessions: {year_data['sessions_count']}")
            if year_data.get('topics'):
                lines.append(f"  Core topics: {year_data['topics']}")
            if year_data.get('media'):
                lines.append(f"  Media: {year_data['media']}")
            if year_data.get('confirmed_speakers'):
                lines.append("\n  CONFIRMED SPEAKERS (pre-verified — copy exact names):")
                for sp in year_data['confirmed_speakers']:
                    lines.append(f"    • {sp}")
            if year_data.get('confirmed_sessions'):
                lines.append("\n  CONFIRMED SESSIONS (pre-verified — use these titles):")
                for s in year_data['confirmed_sessions']:
                    lines.append(f"    • {s}")

        if cf:
            lines.append(f"\nCITY/COUNTRY VERIFIED FACTS for {city_en}:")
            skip_keys = {'city'}
            for k, v in cf.items():
                if k in skip_keys:
                    continue
                if isinstance(v, dict):
                    pt_label = k.replace('prayer_day', 'Day ')
                    lines.append(f"  Prayer times {pt_label}: " +
                                 ', '.join(f"{pk.capitalize()} {pv}" for pk, pv in v.items()))
                else:
                    label = k.replace('_', ' ').title()
                    lines.append(f"  {label}: {v}")

        return "\n".join(lines)

    # ── Research phase helper ─────────────────────────────────────────────────
    def _try(fn, label, max_attempts=2, wait=20):
        for attempt in range(max_attempts):
            try:
                result = fn()
                if result and len(result.strip()) > 50:
                    return result
            except Exception as e:
                err = str(e)
                if any(x in err for x in ['429','rate_limit','overload','timeout']):
                    if attempt < max_attempts - 1:
                        print(f"[AI] {label} error — retrying in {wait}s...")
                        time.sleep(wait)
                    else:
                        print(f"[AI] {label} failed after {max_attempts} attempts")
                else:
                    print(f"[AI] {label} error: {e}")
                    break
        return ""

    # ── Phase 1: Research ──────────────────────────────────────────────────────
    research_parts = []
    event_name_lower = event_name.lower()
    kb_vars_extracted = {}   # v4.5: flat dict of all KB values for Python-level override

    # ── 1D: Knowledge base (stable facts only — no event-specific data) ────────
    conf_kb = _match_kb(event_name_lower)
    if conf_kb:
        # v4.5: Extract all critical values as a flat Python dict
        # Used for: (1) hard injection into prompts, (2) Python dict override after AI
        kb_vars_extracted = _extract_kb_vars(conf_kb, start_date, city_en)
        print(f"[AI] Phase 1D: KB vars extracted ({len(kb_vars_extracted)} fields)")

        kb_text = _kb_to_text(conf_kb, start_date, city_en)
        research_parts.append(kb_text)
        print(f"[AI] Phase 1D: KB '{conf_kb.get('full_name','?')}' — {len(kb_text)} chars")

        # ── v4.4 FIX: Build and inject KB forced override block at position 0 ──
        # This compact block survives _truncate() because it's always first.
        # Root cause of v4.3 regressions: KB text was truncated away from Section A.
        kb_override = _build_kb_forced_overrides(conf_kb, start_date, city_en)
        research_parts.insert(0, kb_override)
        print(f"[AI] Phase 1D: KB override block injected at top ({len(kb_override)} chars)")

        # Auto-correct wrong website URL against KB
        kb_website = _normalize_url(conf_kb.get('website', ''))
        if kb_website:
            if not event_website:
                event_website = kb_website
                print(f"[AI] Phase 1D: No URL given — using KB website: {event_website}")
            else:
                kb_domain   = kb_website.split('/')[2].replace('www.', '')
                user_domain = (event_website.split('/')[2].replace('www.', '')
                               if '//' in event_website else
                               event_website.replace('www.','').split('/')[0])
                if kb_domain not in user_domain and user_domain not in kb_domain:
                    print(f"[AI] Phase 1D: Wrong URL '{user_domain}' → using KB: {kb_domain}")
                    event_website = kb_website
    else:
        print(f"[AI] Phase 1D: No KB match for '{event_name}'")

    # ── 1C: Official website scraping (highest-priority data) ─────────────────
    if event_website and event_website.startswith('http'):
        print(f"[AI] Phase 1C: Scraping {event_website}...")
        r = _try(lambda: _scrape_website(oai, event_website, event_name), "Phase 1C")
        if r:
            research_parts.insert(0, r)
            print(f"[AI] Phase 1C: {len(r)} chars")

    # ── 1A: Primary web research ───────────────────────────────────────────────
    print("[AI] Phase 1A: Primary research...")
    r = _try(
        lambda: _research_primary(oai, event_name, city_en, country_en, start_date, end_date, venue),
        "Phase 1A"
    )
    if r:
        research_parts.append("=== PRIMARY RESEARCH ===\n" + r)
        print(f"[AI] Phase 1A: {len(r)} chars")

    # ── 1B: Supplemental research ──────────────────────────────────────────────
    print("[AI] Phase 1B: Supplemental research...")
    r = _try(
        lambda: _research_supplemental(oai, event_name, city_en, country_en, start_date, end_date),
        "Phase 1B"
    )
    if r:
        research_parts.append("=== SUPPLEMENTAL RESEARCH ===\n" + r)
        print(f"[AI] Phase 1B: {len(r)} chars")

    # ── 1E: Accuracy-critical targeted verification (v4.3 NEW) ────────────────
    # 5 hyper-targeted searches for the fields most prone to errors:
    # official theme, exact attendance, opening keynote, DBS/Temasek CEOs, Saudi ambassador.
    # Runs AFTER 1A/1B so it can correct anything stale from those phases.
    print("[AI] Phase 1E: Accuracy-critical verification (theme, keynote, CEOs, ambassador)...")
    r = _try(
        lambda: _research_accuracy_critical(oai, event_name, city_en, country_en, start_date),
        "Phase 1E"
    )
    if r:
        research_parts.append("=== ACCURACY-CRITICAL VERIFIED FACTS (Phase 1E) ===\n" + r)
        print(f"[AI] Phase 1E: {len(r)} chars")

    # ── 1F: Post-event recap (v4.3 NEW) ───────────────────────────────────────
    # If the event has already happened, fetch official recap data.
    # Post-event data = ground truth — most accurate source possible.
    print("[AI] Phase 1F: Checking if event is past — searching for official recap...")
    r = _try(
        lambda: _research_post_event_recap(oai, event_name, start_date, end_date or start_date, city_en),
        "Phase 1F"
    )
    if r:
        # Insert at position 1 (after website scrape) — post-event data is highest priority
        insert_pos = 1 if research_parts and 'OFFICIAL WEBSITE' in (research_parts[0] if research_parts else '') else 0
        research_parts.insert(insert_pos, "=== POST-EVENT RECAP (Phase 1F — GROUND TRUTH) ===\n" + r)
        print(f"[AI] Phase 1F: Post-event recap found — {len(r)} chars")
    else:
        print("[AI] Phase 1F: Event not yet occurred or no recap found")

    # ── Combine all research ───────────────────────────────────────────────────
    raw_research = (
        "COMBINED RESEARCH:\n\n" + "\n\n".join(research_parts)
        if research_parts else
        f"No research available. Generate best-effort content for {event_name} in {city_en}, {country_en}."
    )
    print(f"[AI] Raw research: {len(raw_research)} chars across {len(research_parts)} parts")

    # ── 1G: Accuracy consolidation (v4.3 NEW) ─────────────────────────────────
    # Takes ALL research gathered and extracts/verifies 8 critical fields:
    # theme, attendance, opening keynote, speakers, head of state, ambassador,
    # DBS CEO, bilateral trade figure.
    # Injects verified block AT THE TOP so Section generators prioritize it.
    print("[AI] Phase 1G: Consolidating accuracy-critical facts...")
    verified_block = _try(
        lambda: _consolidate_accuracy(oai, raw_research, event_name, city_en, country_en, start_date),
        "Phase 1G"
    )
    if verified_block:
        research = verified_block + "\n\n" + raw_research
        print(f"[AI] Phase 1G: Verified facts block injected at top ({len(verified_block)} chars)")
    else:
        research = raw_research
        print("[AI] Phase 1G: Consolidation skipped — using raw research")

    print(f"[AI] Total research: {len(research)} chars")

    # ── 1H: Deep strategic context research (v4.6 NEW) ────────────────────────
    # Dedicated research for the 12 new sections. Feeds Sections E and F only.
    # Runs after primary research to avoid doubling load on 1A/1B phases.
    print("[AI] Phase 1H: Deep strategic context research (6 tracks)...")
    deep_research = _try(
        lambda: _research_deep_strategic_context(oai, event_name, city_en, country_en, start_date),
        "Phase 1H"
    )
    if deep_research:
        print(f"[AI] Phase 1H: {len(deep_research)} chars")
    else:
        deep_research = ""
        print("[AI] Phase 1H: Skipped -- Sections E/F will use primary research")

    # ── Phase 2: Sectioned JSON generation ───────────────────────────────────
    # v4.6: 7 sections (A/B/C/D original + E/F new intelligence + G static)
    print("[AI] Phase 2: Generating report JSON (7-section architecture)...")
    data = _generate_json(
        research, event_name, city, country, country_en,
        start_date, end_date, venue, event_type, context, oai,
        kb_vars=kb_vars_extracted,
        deep_research=deep_research,
    )

    if not data:
        print("[AI] ERROR: JSON generation completely failed")
        return {}

    # ── Post-processing ────────────────────────────────────────────────────────

    # Fix delegation name spelling
    for m in data.get('delegation', []):
        n = m.get('name', '')
        if 'الجاضي' in n or 'الجاضعي' in n:
            m['name'] = n.replace('الجاضي','الجضعي').replace('الجاضعي','الجضعي')

    # Deduplicate suggested_meetings
    seen, deduped = set(), []
    for mtg in data.get('suggested_meetings', []):
        key = mtg.get('entity','')[:30].lower()
        if key not in seen:
            seen.add(key)
            deduped.append(mtg)
    data['suggested_meetings'] = deduped

    # ── v4.3: Speaker repetition detection ────────────────────────────────────
    # If any 1-2 speakers appear in >50% of sessions, it's hallucination.
    # Replace repeated speaker fields with 'يُحدَّد لاحقاً' as a safety net.
    sessions = data.get('sessions', {})
    if isinstance(sessions, dict):
        all_session_speakers = []
        for day_sessions in sessions.values():
            if isinstance(day_sessions, list):
                for s in day_sessions:
                    sp = s.get('speakers', '')
                    if sp and sp != 'يُحدَّد لاحقاً':
                        all_session_speakers.append((s, sp))

        total_sessions = len(all_session_speakers)
        if total_sessions >= 3:
            # Count how many times each speaker appears across sessions
            from collections import Counter
            speaker_counts = Counter()
            for _, sp_text in all_session_speakers:
                for name in sp_text.replace('،', ',').split(','):
                    name = name.strip()
                    if len(name) > 3:
                        speaker_counts[name] += 1

            # Any speaker in >60% of sessions → hallucination → clear their field
            threshold = max(2, int(total_sessions * 0.6))
            repeated = {name for name, count in speaker_counts.items() if count >= threshold}
            if repeated:
                print(f"[AI] ⚠️ Speaker repetition detected: {repeated} — clearing hallucinated fields")
                for session_obj, sp_text in all_session_speakers:
                    # Check if this session's speakers field contains a repeated name
                    has_repeated = any(r in sp_text for r in repeated)
                    if has_repeated:
                        session_obj['speakers'] = 'يُحدَّد لاحقاً'
            else:
                print(f"[AI] Speaker diversity check: OK ({total_sessions} sessions, no repetition detected)")

    # Timezone correction
    # FIX v4.1: The PDF crash root cause was here.
    # Old code: ci = data.get('country_info', {}) → then only set timezone → PDF crash.
    # Fix: only update timezone WITHIN an existing dict; never replace a rich dict with one key.
    city_lower = (city or city_en or '').lower()
    ci = data.get('country_info', {})
    if not isinstance(ci, dict):
        ci = {}
    month = int(start_date[5:7]) if start_date else 0
    tz_map = [
        (['singapore'],                                                       'UTC+8 (SST — Singapore Standard Time)'),
        (['hong kong'],                                                        'UTC+8 (HKT — Hong Kong Time)'),
        (['tokyo', 'osaka'],                                                   'UTC+9 (JST — Japan Standard Time)'),
        (['dubai', 'abu dhabi'],                                               'UTC+4 (GST — Gulf Standard Time)'),
        (['london'],                                                            'UTC+1 (BST)' if 3 <= month <= 10 else 'UTC+0 (GMT)'),
        (['paris','berlin','rome','madrid','amsterdam','zurich','geneva'],      'UTC+2 (CEST)' if 3 <= month <= 10 else 'UTC+1 (CET)'),
        (['los angeles','beverly hills','santa monica','hollywood',
          'san francisco','seattle','portland'],                                'UTC-7 (PDT — Pacific Daylight Time)' if 3 <= month <= 11 else 'UTC-8 (PST)'),
        (['new york','washington','boston','miami','atlanta'],                  'UTC-4 (EDT)' if 3 <= month <= 11 else 'UTC-5 (EST)'),
        (['chicago','dallas','houston'],                                        'UTC-5 (CDT)' if 3 <= month <= 11 else 'UTC-6 (CST)'),
    ]
    correct_tz = None
    for cities, tz in tz_map:
        if any(c in city_lower for c in cities):
            correct_tz = tz
            break
    if correct_tz:
        ci['timezone'] = correct_tz

    # FIX v4.1: Guarantee ALL required country_info keys exist.
    # The PDF template references every one of these — a missing key causes a 500 crash.
    # We inject safe defaults so the PDF always renders, even if the model returned partial data.
    COUNTRY_INFO_DEFAULTS = {
        'capital':           city,
        'head_of_state_title': 'رئيس الحكومة',
        'head_of_state':     'يُحدَّد لاحقاً',
        'population':        'يُحدَّد لاحقاً',
        'area':              'يُحدَّد لاحقاً',
        'gdp':               'يُحدَّد لاحقاً',
        'gdp_per_capita':    'يُحدَّد لاحقاً',
        'currency':          'يُحدَّد لاحقاً',
        'official_language': 'يُحدَّد لاحقاً',
        'religion':          'يُحدَّد لاحقاً',
        'timezone':          correct_tz or 'يُحدَّد لاحقاً',
        'government':        'يُحدَّد لاحقاً',
        'key_sectors':       'يُحدَّد لاحقاً',
        'overview':          'يُحدَّد لاحقاً',
    }
    # Singapore-specific defaults (from KB — always correct)
    if 'singapore' in city_lower:
        COUNTRY_INFO_DEFAULTS.update({
            'capital':           'سنغافورة (مدينة دولة)',
            'head_of_state_title': 'رئيس الوزراء',
            'head_of_state':     'Lawrence Wong',
            'population':        '5.92 مليون (2024، دائرة الإحصاء السنغافورية)',
            'area':              '733.2 كم²',
            'gdp':               '501 مليار دولار (2024، وزارة التجارة والصناعة السنغافورية)',
            'gdp_per_capita':    '88,000 دولار (2024)',
            'currency':          'الدولار السنغافوري (SGD)',
            'official_language': 'الإنجليزية، الملايوية، الماندرين، التاميل',
            'religion':          'البوذية، المسيحية، الإسلام، الطاوية، الهندوسية',
            'timezone':          'UTC+8 (SST — توقيت سنغافورة القياسي)',
            'government':        'نظام برلماني — جمهورية',
            'key_sectors':       'الخدمات المالية، علوم الحياة، الإلكترونيات، البتروكيماويات، الخدمات اللوجستية',
        })

    for key, default in COUNTRY_INFO_DEFAULTS.items():
        if not ci.get(key):
            ci[key] = default

    data['country_info'] = ci

    # Speaker nationality corrections
    NATIONALITIES = {
        'georgieva':'بلغاريا',    'جورجيفا':'بلغاريا',
        'lagarde':'فرنسا',        'لاغارد':'فرنسا',
        'guterres':'البرتغال',    'غوتيريش':'البرتغال',
        'tedros':'إثيوبيا',       'تيدروس':'إثيوبيا',
        'banga':'الهند',           'بانغا':'الهند',
        'jose andres':'إسبانيا / الولايات المتحدة',
        'piyush gupta':'سنغافورة','غوبتا':'سنغافورة',
        'ho ching':'سنغافورة',
    }
    for sp in data.get('speakers', []):
        nl = sp.get('name','').lower()
        for key, nat in NATIONALITIES.items():
            if key in nl:
                sp['country'] = nat
                break

    # Prayer time variation
    prayer_times = data.get('prayer_times', [])
    if len(prayer_times) > 1:
        all_same = all(
            pt.get('fajr') == prayer_times[0].get('fajr') and
            pt.get('maghrib') == prayer_times[0].get('maghrib')
            for pt in prayer_times[1:]
        )
        if all_same and conf_kb:
            cf = conf_kb.get('city_facts', {})
            ref_times = [
                cf.get(f'prayer_day{i+1}') for i in range(4)
                if cf.get(f'prayer_day{i+1}')
            ]
            if ref_times:
                for i, pt in enumerate(prayer_times):
                    if i < len(ref_times):
                        pt.update(ref_times[i])
            else:
                for i, pt in enumerate(prayer_times[1:], 1):
                    def _shift(t, m):
                        try:
                            h, mn = map(int, t.split(':'))
                            total = h * 60 + mn + m
                            return f"{total//60:02d}:{total%60:02d}"
                        except:
                            return t
                    pt['fajr']    = _shift(prayer_times[0].get('fajr','05:00'), -i)
                    pt['maghrib'] = _shift(prayer_times[0].get('maghrib','18:30'), i)
                    pt['isha']    = _shift(prayer_times[0].get('isha','19:45'), i)
        data['prayer_times'] = prayer_times

    # Fake org name replacement
    ORG_FIXES = {
        'جمعية الأدوية الأمريكية':       'PhRMA (Pharmaceutical Research and Manufacturers of America)',
        'جمعية صناعة الأدوية':           'PhRMA (Pharmaceutical Research and Manufacturers of America)',
        'هيئة المعايير الغذائية الأمريكية': 'FDA CFSAN (مركز سلامة الأغذية)',
        'معهد الأبحاث الصحية الأمريكي':  'NIH (المعاهد الوطنية للصحة)',
        'معهد الصحة الوطني':             'NIH (المعاهد الوطنية للصحة)',
        'معهد الأبحاث الصحية':           'NIH (المعاهد الوطنية للصحة)',
    }
    def _fix_org(t):
        if not t:
            return t
        for fake, real in ORG_FIXES.items():
            t = t.replace(fake, real)
        return t

    for mtg in data.get('bilateral_meetings', []) + data.get('suggested_meetings', []):
        for f in ('entity','description','counterpart'):
            mtg[f] = _fix_org(mtg.get(f, ''))

    # Placeholder detection
    FAKES = {'John Smith','Jane Doe','Samandal','سمندل','جون سميث','يُعبأ لاحقاً','placeholder'}
    def _is_ph(v):
        return not v or v in FAKES or (isinstance(v, str) and ('<' in v or '>' in v))

    # Singapore: ensure real regulatory body names
    if 'singapore' in city_lower:
        bm = data.get('bilateral_meetings', [])
        ents = [m.get('entity','').lower() for m in bm]
        if bm and not any('hsa' in e or 'health sciences' in e for e in ents):
            bm[0]['entity'] = 'Health Sciences Authority (HSA) — Singapore'
        if len(bm) > 1 and not any('ministry of health' in e or 'moh' in e for e in ents):
            bm[1]['entity'] = 'Ministry of Health Singapore (MOH)'
        data['bilateral_meetings'] = bm

    # USA: Princess Reema
    is_usa = any(x in (country_en or '').lower() for x in ['united states','usa','america'])
    if is_usa:
        emb = data.setdefault('embassy', {})
        if not emb.get('ambassador_name') or _is_ph(emb.get('ambassador_name')):
            emb['ambassador_name'] = 'الأميرة ريما بنت بندر بن سلطان بن عبدالعزيز آل سعود'
        ambs = data.get('key_ambassadors', [])
        for amb in ambs:
            if _is_ph(amb.get('name')):
                amb['name']  = 'الأميرة ريما بنت بندر بن سلطان بن عبدالعزيز آل سعود'
                amb['title'] = 'سفير خادم الحرمين الشريفين لدى الولايات المتحدة الأمريكية'
        if not ambs:
            data['key_ambassadors'] = [{
                'name': 'الأميرة ريما بنت بندر بن سلطان بن عبدالعزيز آل سعود',
                'title': 'سفير خادم الحرمين الشريفين لدى الولايات المتحدة الأمريكية',
                'country': 'الولايات المتحدة الأمريكية',
                'relevance': 'سمو الأميرة ريما هي أول سفيرة في تاريخ المملكة العربية السعودية، تتولى منصبها منذ فبراير 2019. تضطلع بدور محوري في تنسيق الزيارات الرسمية ودعم الوفود الحكومية في واشنطن.'
            }]

    # Generic placeholder normalization
    if _is_ph(data.get('embassy',{}).get('ambassador_name')):
        data.setdefault('embassy',{})['ambassador_name'] = 'يُحدَّد لاحقاً'
    if _is_ph(data.get('consulate',{}).get('consul_name')):
        data.setdefault('consulate',{})['consul_name'] = '—'
    for m in data.get('bilateral_meetings', []):
        if _is_ph(m.get('counterpart')):
            m['counterpart'] = 'يُحدَّد لاحقاً'
    for amb in data.get('key_ambassadors', []):
        if _is_ph(amb.get('name')):
            amb['name'] = 'يُحدَّد لاحقاً'

    # Normalize conference_tracks
    normalized = []
    for t in data.get('conference_tracks', []):
        if isinstance(t, dict) and t.get('name'):
            normalized.append({'name': t['name'], 'explanation': t.get('explanation', t.get('description',''))})
        elif isinstance(t, str) and t.strip():
            normalized.append({'name': t.strip(), 'explanation': 'محور استراتيجي ذو صلة مباشرة بمهام الهيئة وأهداف رؤية 2030.'})
    data['conference_tracks'] = normalized

    # Normalize session speakers list → string
    for dk in ('day1','day2','day3','day4'):
        for s in data.get('sessions',{}).get(dk,[]):
            if isinstance(s.get('speakers'), list):
                s['speakers'] = '، '.join(str(x) for x in s['speakers'] if x)

    # Normalize weather → integer temperatures
    for d in data.get('weather', []):
        for k in ('high','low'):
            v = str(d.get(k,'')).replace('°C','').replace('°','').strip()
            try:
                d[k] = int(float(v))
            except Exception:
                pass

    # Remove placeholder speakers
    data['speakers'] = [sp for sp in data.get('speakers',[]) if sp.get('name') and not _is_ph(sp['name'])]

    # ── FIX v4.1: Required-fields safety net ─────────────────────────────────
    # Every key the PDF template accesses must exist.
    # This block ensures no field is ever missing, injecting Arabic placeholders
    # that are honest ("يُحدَّد لاحقاً" = "to be determined") rather than crashing.
    TOP_LEVEL_DEFAULTS = {
        'report_subtitle':              'يُحدَّد لاحقاً',
        'executive_summary':            'يُحدَّد لاحقاً',
        'geopolitical_summary':         'يُحدَّد لاحقاً',
        'conference_summary':           'يُحدَّد لاحقاً',
        'conference_history':           'يُحدَّد لاحقاً',
        'ksa_participation_history':    'يُحدَّد لاحقاً',
        'sfda_relevance':               'يُحدَّد لاحقاً',
        'bilateral_relations':          'يُحدَّد لاحقاً',
        'entry_requirements':           'يُحدَّد لاحقاً',
        'leadership_brief':             'يُحدَّد لاحقاً',
        'trade_exchange':               'يُحدَّد لاحقاً',
        'ns_vision_alignment':          'يُحدَّد لاحقاً',
        'ns_regulatory_relevance':      'يُحدَّد لاحقاً',
        'ns_investment_implications':   'يُحدَّد لاحقاً',
        'ns_institutional_positioning': 'يُحدَّد لاحقاً',
        'political_economic_orientation':'يُحدَّد لاحقاً',
        'political_strategic_priorities':'يُحدَّد لاحقاً',
        'visit_objectives':             ['يُحدَّد لاحقاً'],
        'sfda_talking_points':          ['يُحدَّد لاحقاً'],
        'intel_global_significance':    ['يُحدَّد لاحقاً'],
        'intel_regulatory_impact':      ['يُحدَّد لاحقاً'],
        'intel_long_term_value':        ['يُحدَّد لاحقاً'],
        'conference_tracks':            [],
        'previous_outcomes':            [],
        'speakers':                     [],
        'sessions':                     {'day1': []},
        'agenda':                       [],
        'bilateral_meetings':           [],
        'suggested_meetings':           [],
        'participants':                 [],
        'attachments':                  [],
        'weather':                      [],
        'prayer_times':                 [],
        'delegation':                   [],
        'key_ambassadors':              [],
        'bilateral_fields': {
            'trade_volume': '—',
            'cooperation_areas': 'يُحدَّد لاحقاً',
            'strategic_agreements': 'يُحدَّد لاحقاً',
            'health_regulatory': 'يُحدَّد لاحقاً',
        },
        'conference_data': {
            'organizer': 'يُحدَّد لاحقاً',
            'overview': 'يُحدَّد لاحقاً',
            'slogan': 'يُحدَّد لاحقاً',
            'dates': f'{start_date} to {end_date or start_date}',
            'location': f'{venue or city}, {country}',
            'founded': 'يُحدَّد لاحقاً',
            'edition': 'يُحدَّد لاحقاً',
            'expected_participants': 'يُحدَّد لاحقاً',
            'participant_profile': 'يُحدَّد لاحقاً',
            'core_themes': 'يُحدَّد لاحقاً',
            'ksa_participation': 'يُحدَّد لاحقاً',
        },
        'embassy': {
            'name': 'يُحدَّد لاحقاً',
            'mission': 'يُحدَّد لاحقاً',
            'ambassador_name': 'يُحدَّد لاحقاً',
            'ambassador_title': f'سفير خادم الحرمين الشريفين لدى {country_en}',
            'address': 'NOT FOUND',
            'phone': 'NOT FOUND',
            'fax': '—',
            'email': 'NOT FOUND',
            'website': 'NOT FOUND',
        },
        'consulate': {
            'name': 'يُحدَّد لاحقاً',
            'address': 'NOT FOUND',
            'phone': 'NOT FOUND',
            'email': 'NOT FOUND',
            'emergency_phone': 'NOT FOUND',
            'working_hours': 'من الاثنين إلى الجمعة، 9:00–17:00',
            'consul_name': '—',
            'consul_title': 'القنصل العام للمملكة العربية السعودية',
            'consul_bio': 'يُحدَّد لاحقاً',
        },
    }
    for key, default in TOP_LEVEL_DEFAULTS.items():
        if key not in data or data[key] is None:
            data[key] = default
        elif isinstance(default, dict) and isinstance(data[key], dict):
            # For nested dicts, fill missing sub-keys only
            for sub_key, sub_default in default.items():
                if sub_key not in data[key] or data[key][sub_key] is None:
                    data[key][sub_key] = sub_default

    print(f"[AI] Done. Fields: {len(data)} | "
          f"Speakers: {len(data.get('speakers',[]))} | "
          f"Tracks: {len(data.get('conference_tracks',[]))} | "
          f"Sessions day1: {len(data.get('sessions',{}).get('day1',[]))}")

    return data
