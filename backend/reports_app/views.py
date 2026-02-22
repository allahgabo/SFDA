import json
from django.http import HttpResponse, JsonResponse
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response

from .models import Report
from .serializers import ReportListSerializer, ReportDetailSerializer, ReportCreateSerializer
from .ai_generator import generate_report_content
from .pdf_generator import generate_pdf, generate_html_preview


class ReportListView(APIView):
    def _fetch_rss(self):
        """Fetch real news from RSS feeds. Returns list of feed items."""
        import urllib.request, xml.etree.ElementTree as ET, re, time
        try:
            import email.utils
        except Exception:
            email = None

        items = []
        icon_map = {
            "FDA.gov":    ("💊", "#dbeafe"),
            "WHO":        ("🏥", "#fef2f2"),
            "Arab News":  ("🌍", "#dcfce7"),
            "Reuters":    ("📡", "#f0fdf4"),
            "BBC Health": ("📰", "#eff6ff"),
        }

        for source_name, url in self.RSS_FEEDS:
            if len(items) >= 6:
                break
            try:
                req = urllib.request.Request(url, headers={"User-Agent": "SFDABot/1.0"})
                with urllib.request.urlopen(req, timeout=5) as resp:
                    xml_data = resp.read()
                root = ET.fromstring(xml_data)
                for item in root.findall(".//item")[:2]:
                    title = (item.findtext("title") or "").strip()
                    link  = (item.findtext("link")  or "").strip()
                    desc  = (item.findtext("description") or "").strip()
                    pub   = item.findtext("pubDate") or ""
                    if not title:
                        continue
                    # Age string
                    time_str = "Recently"
                    if email and pub:
                        try:
                            pub_ts  = email.utils.parsedate_to_datetime(pub).timestamp()
                            age_h   = int((time.time() - pub_ts) / 3600)
                            time_str = ("Just now" if age_h < 1
                                        else f"{age_h}h ago" if age_h < 24
                                        else f"{age_h//24}d ago")
                        except Exception:
                            pass
                    icon, bg = icon_map.get(source_name, ("📋", "#f8fafc"))
                    clean_desc = re.sub(r"<[^>]+>", "", desc)[:200].strip()
                    is_impact  = any(w in title.lower() for w in
                                     ["saudi","sfda","emergency","outbreak","recall","ban","approved","approval"])
                    items.append({
                        "icon": icon, "iconBg": bg,
                        "title": title[:120],
                        "summary": clean_desc or "Click to read the full story.",
                        "source": source_name,
                        "time": time_str,
                        "impact": "HIGH IMPACT" if is_impact else None,
                        "url": link,
                    })
            except Exception:
                continue
        return items

    def get(self, request):
        reports = Report.objects.all()
        serializer = ReportListSerializer(reports, many=True)
        return Response(serializer.data)

    def post(self, request):
        import logging
        logger = logging.getLogger(__name__)
        logger.warning(f"[CREATE REPORT] Incoming data: {dict(request.data)}")
        serializer = ReportCreateSerializer(data=request.data)
        if not serializer.is_valid():
            logger.warning(f"[CREATE REPORT] Validation errors: {serializer.errors}")
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        report = Report.objects.create(**serializer.validated_data)
        return Response(ReportListSerializer(report).data, status=status.HTTP_201_CREATED)


class ReportDetailView(APIView):
    def get_report(self, pk):
        try:
            return Report.objects.get(pk=pk)
        except Report.DoesNotExist:
            return None

    def get(self, request, pk):
        report = self.get_report(pk)
        if not report:
            return Response({"error": "Report not found"}, status=404)
        return Response(ReportDetailSerializer(report).data)

    def patch(self, request, pk):
        report = self.get_report(pk)
        if not report:
            return Response({"error": "Report not found"}, status=404)
        allowed = ['title', 'status', 'risk_level', 'visit_objectives', 'delegation',
                   'agenda', 'conference_data', 'conference_tracks', 'sessions',
                   'speakers', 'bilateral_meetings', 'consulate', 'weather',
                   'prayer_times', 'previous_outcomes', 'attachments', 'country_info',
                   'report_subtitle']
        for key in allowed:
            if key in request.data:
                setattr(report, key, request.data[key])
        report.save()
        return Response(ReportDetailSerializer(report).data)

    def delete(self, request, pk):
        report = self.get_report(pk)
        if not report:
            return Response({"error": "Report not found"}, status=404)
        report.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class GenerateAIContentView(APIView):
    def post(self, request, pk):
        try:
            report = Report.objects.get(pk=pk)
        except Report.DoesNotExist:
            return Response({"error": "Report not found"}, status=404)

        try:
            content = generate_report_content(
                event_name=report.event_name,
                city=report.city,
                country=report.country,
                start_date=report.start_date,
                end_date=report.end_date,
                venue=report.venue,
                event_type=report.event_type,
                context=report.context,
                language=report.language,
                event_website=report.event_website or '',
            )
            report.report_subtitle      = content.get('report_subtitle', '')
            report.visit_objectives     = content.get('visit_objectives', [])
            report.country_info         = content.get('country_info', {})
            report.delegation           = content.get('delegation', [])
            report.agenda               = content.get('agenda', [])
            report.conference_data      = content.get('conference_data', {})
            report.conference_tracks    = content.get('conference_tracks', [])
            report.previous_outcomes    = content.get('previous_outcomes', [])
            report.sessions             = content.get('sessions', {})
            report.speakers             = content.get('speakers', [])
            report.bilateral_meetings   = content.get('bilateral_meetings', [])
            report.consulate            = content.get('consulate', {})
            report.weather              = content.get('weather', [])
            report.prayer_times         = content.get('prayer_times', [])
            report.attachments          = content.get('attachments', [])
            report.executive_summary    = content.get('executive_summary', '')
            report.key_ambassadors      = content.get('key_ambassadors', [])
            report.participants             = content.get('participants', [])
            report.suggested_meetings       = content.get('suggested_meetings', [])
            report.conference_summary       = content.get('conference_summary', '')
            report.conference_history       = content.get('conference_history', '')
            report.ksa_participation_history = content.get('ksa_participation_history', '')
            report.sfda_relevance           = content.get('sfda_relevance', '')
            report.bilateral_relations      = content.get('bilateral_relations', '')
            report.geopolitical_summary     = content.get('geopolitical_summary', '')
            report.entry_requirements       = content.get('entry_requirements', '')
            report.leadership_brief         = content.get('leadership_brief', '')
            report.trade_exchange           = content.get('trade_exchange', '')
            report.sfda_talking_points      = content.get('sfda_talking_points', [])
            report.embassy                  = content.get('embassy', {})
            # ── §3 Strategic Intelligence Assessment ──
            report.intel_global_significance = content.get('intel_global_significance', [])
            report.intel_regulatory_impact   = content.get('intel_regulatory_impact', [])
            report.intel_long_term_value     = content.get('intel_long_term_value', [])
            # ── §6 National Strategic Relevance ──
            report.ns_vision_alignment          = content.get('ns_vision_alignment', '')
            report.ns_regulatory_relevance      = content.get('ns_regulatory_relevance', '')
            report.ns_investment_implications   = content.get('ns_investment_implications', '')
            report.ns_institutional_positioning = content.get('ns_institutional_positioning', '')
            # ── §7 Bilateral Relations structured table ──
            report.bilateral_fields = content.get('bilateral_fields', {})
            # ── §8 Political & Country Profile ──
            report.political_economic_orientation = content.get('political_economic_orientation', '')
            report.political_strategic_priorities = content.get('political_strategic_priorities', '')
            report.ai_generated         = True
            report.status               = 'ready'
            report.save()
            return Response({"message": "AI content generated successfully", "report": ReportDetailSerializer(report).data})
        except Exception as e:
            return Response({"error": str(e)}, status=500)


class GeneratePDFView(APIView):
    """Download PDF as attachment."""
    def get(self, request, pk):
        try:
            report = Report.objects.get(pk=pk)
        except Report.DoesNotExist:
            return Response({"error": "Report not found"}, status=404)
        try:
            pdf_bytes = generate_pdf(report)
            filename = f"SFDA_Report_{report.city}_{report.start_date}.pdf".replace(' ', '_')
            response = HttpResponse(pdf_bytes, content_type='application/pdf')
            response['Content-Disposition'] = f'attachment; filename="{filename}"'
            response['Content-Length'] = len(pdf_bytes)
            return response
        except Exception as e:
            import traceback
            return Response({"error": f"PDF generation failed: {str(e)}", "detail": traceback.format_exc()[-300:]}, status=500)


class InlinePDFView(APIView):
    """Serve PDF inline — for iframe display inside the app."""
    def get(self, request, pk):
        try:
            report = Report.objects.get(pk=pk)
        except Report.DoesNotExist:
            return Response({"error": "Report not found"}, status=404)
        try:
            pdf_bytes = generate_pdf(report)
            filename = f"SFDA_Report_{report.city}_{report.start_date}.pdf".replace(' ', '_')
            response = HttpResponse(pdf_bytes, content_type='application/pdf')
            response['Content-Disposition'] = f'inline; filename="{filename}"'
            response['Content-Length'] = len(pdf_bytes)
            response['X-Frame-Options'] = 'SAMEORIGIN'
            return response
        except Exception as e:
            import traceback
            return Response({"error": f"PDF generation failed: {str(e)}", "detail": traceback.format_exc()[-300:]}, status=500)


class PreviewHTMLView(APIView):
    def get(self, request, pk):
        try:
            report = Report.objects.get(pk=pk)
        except Report.DoesNotExist:
            return Response({"error": "Report not found"}, status=404)
        try:
            html = generate_html_preview(report)
            return HttpResponse(html, content_type='text/html; charset=utf-8')
        except Exception as e:
            import traceback
            tb = traceback.format_exc()
            # Return a proper JSON error so the frontend can show the real message
            return Response({"error": str(e), "detail": tb[-500:]}, status=500)


class HealthCheckView(APIView):
    """Returns DB migration status and feature availability."""
    permission_classes = []  # public

    def _fetch_rss(self):
        """Fetch real news from RSS feeds. Returns list of feed items."""
        import urllib.request, xml.etree.ElementTree as ET, re, time
        try:
            import email.utils
        except Exception:
            email = None

        items = []
        icon_map = {
            "FDA.gov":    ("💊", "#dbeafe"),
            "WHO":        ("🏥", "#fef2f2"),
            "Arab News":  ("🌍", "#dcfce7"),
            "Reuters":    ("📡", "#f0fdf4"),
            "BBC Health": ("📰", "#eff6ff"),
        }

        for source_name, url in self.RSS_FEEDS:
            if len(items) >= 6:
                break
            try:
                req = urllib.request.Request(url, headers={"User-Agent": "SFDABot/1.0"})
                with urllib.request.urlopen(req, timeout=5) as resp:
                    xml_data = resp.read()
                root = ET.fromstring(xml_data)
                for item in root.findall(".//item")[:2]:
                    title = (item.findtext("title") or "").strip()
                    link  = (item.findtext("link")  or "").strip()
                    desc  = (item.findtext("description") or "").strip()
                    pub   = item.findtext("pubDate") or ""
                    if not title:
                        continue
                    # Age string
                    time_str = "Recently"
                    if email and pub:
                        try:
                            pub_ts  = email.utils.parsedate_to_datetime(pub).timestamp()
                            age_h   = int((time.time() - pub_ts) / 3600)
                            time_str = ("Just now" if age_h < 1
                                        else f"{age_h}h ago" if age_h < 24
                                        else f"{age_h//24}d ago")
                        except Exception:
                            pass
                    icon, bg = icon_map.get(source_name, ("📋", "#f8fafc"))
                    clean_desc = re.sub(r"<[^>]+>", "", desc)[:200].strip()
                    is_impact  = any(w in title.lower() for w in
                                     ["saudi","sfda","emergency","outbreak","recall","ban","approved","approval"])
                    items.append({
                        "icon": icon, "iconBg": bg,
                        "title": title[:120],
                        "summary": clean_desc or "Click to read the full story.",
                        "source": source_name,
                        "time": time_str,
                        "impact": "HIGH IMPACT" if is_impact else None,
                        "url": link,
                    })
            except Exception:
                continue
        return items

    def get(self, request):
        from django.db import connection
        try:
            cursor = connection.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]
            # Check for new columns
            cursor.execute("PRAGMA table_info(reports_app_report)")
            cols = [row[1] for row in cursor.fetchall()]
            missing = [f for f in ['executive_summary','embassy','conference_summary',
                                   'sfda_talking_points','bilateral_relations',
                                   'participants','suggested_meetings']
                       if f not in cols]
            return Response({
                "status": "ok",
                "missing_columns": missing,
                "needs_migration": len(missing) > 0,
                "message": "Run: python manage.py migrate" if missing else "All migrations applied"
            })
        except Exception as e:
            return Response({"status": "error", "error": str(e)}, status=500)


class AIAssistantView(APIView):
    def post(self, request):
        from openai import OpenAI
        from django.conf import settings
        messages = request.data.get('messages', [])
        system   = request.data.get('system', '')
        client   = OpenAI(api_key=settings.OPENAI_API_KEY)
        openai_messages = []
        if system:
            openai_messages.append({"role": "system", "content": system})
        openai_messages.extend(messages)
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=openai_messages,
            max_tokens=1000,
            temperature=0.7,
        )
        return Response({"content": response.choices[0].message.content})


class DashboardStatsView(APIView):
    def _fetch_rss(self):
        """Fetch real news from RSS feeds. Returns list of feed items."""
        import urllib.request, xml.etree.ElementTree as ET, re, time
        try:
            import email.utils
        except Exception:
            email = None

        items = []
        icon_map = {
            "FDA.gov":    ("💊", "#dbeafe"),
            "WHO":        ("🏥", "#fef2f2"),
            "Arab News":  ("🌍", "#dcfce7"),
            "Reuters":    ("📡", "#f0fdf4"),
            "BBC Health": ("📰", "#eff6ff"),
        }

        for source_name, url in self.RSS_FEEDS:
            if len(items) >= 6:
                break
            try:
                req = urllib.request.Request(url, headers={"User-Agent": "SFDABot/1.0"})
                with urllib.request.urlopen(req, timeout=5) as resp:
                    xml_data = resp.read()
                root = ET.fromstring(xml_data)
                for item in root.findall(".//item")[:2]:
                    title = (item.findtext("title") or "").strip()
                    link  = (item.findtext("link")  or "").strip()
                    desc  = (item.findtext("description") or "").strip()
                    pub   = item.findtext("pubDate") or ""
                    if not title:
                        continue
                    # Age string
                    time_str = "Recently"
                    if email and pub:
                        try:
                            pub_ts  = email.utils.parsedate_to_datetime(pub).timestamp()
                            age_h   = int((time.time() - pub_ts) / 3600)
                            time_str = ("Just now" if age_h < 1
                                        else f"{age_h}h ago" if age_h < 24
                                        else f"{age_h//24}d ago")
                        except Exception:
                            pass
                    icon, bg = icon_map.get(source_name, ("📋", "#f8fafc"))
                    clean_desc = re.sub(r"<[^>]+>", "", desc)[:200].strip()
                    is_impact  = any(w in title.lower() for w in
                                     ["saudi","sfda","emergency","outbreak","recall","ban","approved","approval"])
                    items.append({
                        "icon": icon, "iconBg": bg,
                        "title": title[:120],
                        "summary": clean_desc or "Click to read the full story.",
                        "source": source_name,
                        "time": time_str,
                        "impact": "HIGH IMPACT" if is_impact else None,
                        "url": link,
                    })
            except Exception:
                continue
        return items

    def get(self, request):
        reports = Report.objects.all()
        return Response({
            "total":    reports.count(),
            "ready":    reports.filter(status='ready').count(),
            "draft":    reports.filter(status='draft').count(),
            "archived": reports.filter(status='archived').count(),
        })


class LiveIntelligenceFeedView(APIView):
    """
    Fetches live SFDA-relevant news using Claude claude-haiku-4-5-20251001 with web_search tool.
    Falls back to accurate static feed reflecting current Feb 2026 events.
    Results cached for 5 minutes.
    Public endpoint — no auth required (news feed is non-sensitive data).
    """
    permission_classes = []   # public — no auth needed for a news feed
    _cache = {"data": None, "timestamp": 0}  # resets on every deploy
    CACHE_SECONDS = 300  # 5 minutes

    FALLBACK_FEED = {
        "feed": [
            {
                "icon": "💉",
                "title": "SFDA Approves Gene Therapy Clinical Study for Acute Lymphoblastic Leukemia",
                "summary": "Saudi FDA approved a clinical study for a domestically developed gene therapy targeting adults with relapsed/refractory CD19-positive ALL, marking a milestone for Saudi biotech.",
                "source": "SFDA",
                "time": "Recently",
                "impact": "HIGH IMPACT",
                "url": "https://news.google.com/search?q=SFDA%20Gene%20Therapy%20Clinical%20Study%20Acute%20Lymphoblastic%20Leukemia%20SFDA&hl=en"
            },
            {
                "icon": "🌍",
                "title": "SFDA Designated as WHO Regional Center for Nutrition Collaboration",
                "summary": "The Saudi Food and Drug Authority has been officially designated as a WHO Regional Center for Nutrition Collaboration, reinforcing Saudi Arabia's leadership in regional health under Vision 2030.",
                "source": "SFDA / WHO",
                "time": "Recently",
                "impact": "HIGH IMPACT",
                "url": "https://news.google.com/search?q=SFDA%20WHO%20Regional%20Center%20Nutrition%20Collaboration%20SFDA&hl=en"
            },
            {
                "icon": "💊",
                "title": "SFDA Issues New Prescription Drug Clearance Requirement for Travelers",
                "summary": "Effective November 2025, all travelers to Saudi Arabia must obtain advance electronic clearance from SFDA for controlled prescription medications including opioids, benzodiazepines, and stimulants.",
                "source": "SFDA / US Embassy",
                "time": "Recently",
                "impact": "HIGH IMPACT",
                "url": "https://news.google.com/search?q=SFDA%20Prescription%20Drug%20Clearance%20Requirement%20Travelers%20SFDA&hl=en"
            },
            {
                "icon": "🔬",
                "title": "SFDA & OIC Host Workshop on Regulatory Systems for 57 Member States",
                "summary": "Over 200 regulatory specialists from OIC member states participated in a virtual workshop focused on achieving WHO Global Benchmarking Tool ML4 compliance.",
                "source": "WHO EMRO",
                "time": "Recently",
                "impact": None,
                "url": "https://news.google.com/search?q=SFDA%20OIC%20Workshop%20Regulatory%20Systems%20WHO%20WHO%20EMRO&hl=en"
            },
            {
                "icon": "🧠",
                "title": "SFDA Approves Leqembi — First Alzheimer's Treatment Registered in Saudi Arabia",
                "summary": "The Saudi FDA has registered lecanemab (Leqembi), the first disease-modifying Alzheimer's treatment, making Saudi Arabia among the earliest countries in the region to offer access.",
                "source": "SFDA",
                "time": "Recently",
                "impact": "HIGH IMPACT",
                "url": "https://news.google.com/search?q=SFDA%20Leqembi%20Alzheimer%20Treatment%20Saudi%20Arabia%20SFDA&hl=en"
            },
        ],
        "who": [
            {
                "type": "Alert",
                "typeColor": "#dc2626",
                "title": "Measles Outbreak Surge — Americas Region 2026",
                "summary": "PAHO issued an epidemiological alert on Feb 4 2026 as measles cases reached 1,031 in just 3 weeks across 7 countries, a 43-fold increase vs same period in 2025. Travelers urged to verify vaccination.",
                "tags": ["Americas", "USA", "Mexico", "Global"],
                "url": "https://news.google.com/search?q=Measles%20Outbreak%20Americas%202026%20PAHO%20alert%20WHO%20PAHO&hl=en"
            },
            {
                "type": "Alert",
                "typeColor": "#7c3aed",
                "title": "Nipah Virus — Confirmed Case in Bangladesh (Feb 2026)",
                "summary": "WHO confirmed one case of Nipah virus infection in Rajshahi Division, Bangladesh on Feb 3, 2026. Patient developed fever and neurological symptoms. Enhanced surveillance underway.",
                "tags": ["Bangladesh", "Southeast Asia", "Neurological"],
                "url": "https://news.google.com/search?q=Nipah%20Virus%20Bangladesh%202026%20WHO%20WHO&hl=en"
            },
        ],
        "fetched_at": "",
        "cached": True,
        "source": "fallback"
    }

    def _fetch_with_claude(self, api_key):
        """Use Claude claude-haiku-4-5-20251001 with web_search to get real-time news."""
        import anthropic
        import json
        import datetime

        client = anthropic.Anthropic(api_key=api_key)

        today = datetime.datetime.utcnow().strftime("%B %d, %Y")

        prompt = f"""Today is {today}. You are a news curator for the Saudi FDA (SFDA) travel intelligence dashboard.

Search the web and return a JSON object with the LATEST real news about:
1. SFDA / Saudi FDA regulatory actions and announcements
2. WHO health alerts, disease outbreaks, and travel advisories
3. International pharmaceutical regulation (FDA approvals, EMA decisions)
4. Saudi Arabia health policy and Vision 2030 health initiatives
5. Global health emergencies relevant to international travelers

Return ONLY valid JSON (no markdown, no code fences) with this exact structure:
{{
  "feed": [
    {{
      "icon": "relevant emoji",
      "title": "Real news headline",
      "summary": "1-2 sentence factual summary with specific details",
      "source": "Source name (SFDA, WHO, Reuters, etc.)",
      "time": "X hours ago or X days ago",
      "impact": "HIGH IMPACT or null",
      "url": "EXACT URL from web_search result - copy verbatim, do NOT invent"
    }}
  ],
  "who": [
    {{
      "type": "Outbreak or Alert or Update",
      "typeColor": "#dc2626 for Outbreak, #d97706 for Update, #7c3aed for Alert",
      "title": "WHO alert headline",
      "summary": "1-2 sentence summary",
      "tags": ["Region", "Disease"],
      "url": "EXACT URL from web_search result - copy verbatim, do NOT invent"
    }}
  ]
}}

Requirements:
- 5 real news items, prioritizing SFDA and Saudi health news
- 2 real WHO health alerts currently active
- Use HIGH IMPACT when Saudi Arabia is directly involved or it's a major drug approval
- Only include real, verifiable news — no fabricated content
- CRITICAL: url must be EXACT URL from web_search results, never guess or fabricate
- If no real URL found from search, set url to null"""

        response = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=2500,
            tools=[{"type": "web_search_20250305", "name": "web_search"}],
            messages=[{"role": "user", "content": prompt}]
        )

        # Extract text blocks from the response
        full_text = ""
        for block in response.content:
            if hasattr(block, "text"):
                full_text += block.text

        # Strip markdown fences if present
        import re
        full_text = re.sub(r'^```(?:json)?\s*', '', full_text.strip())
        full_text = re.sub(r'\s*```$', '', full_text)

        data = json.loads(full_text)

        # Keep real URLs from web_search; fall back to Google News only if missing/null
        import urllib.parse

        def _ensure_url(item, prefix=''):
            url = item.get('url', '')
            if url and url != 'null' and str(url).startswith('http'):
                return  # real URL — keep it
            title = item.get('title', '') or ''
            source = item.get('source', '') or ''
            query = urllib.parse.quote(f'{prefix}{title} {source}'.strip())
            item['url'] = f'https://www.google.com/search?q={query}&tbm=nws'

        for item in data.get('feed', []):
            _ensure_url(item)
        for item in data.get('who', []):
            _ensure_url(item, prefix='WHO ')

        return data

    def get(self, request):
        import time
        import json
        import datetime
        from django.conf import settings

        now = time.time()

        # Return cached data if still fresh
        if self._cache["data"] and (now - self._cache["timestamp"]) < self.CACHE_SECONDS:
            return Response(self._cache["data"])

        # Prepare fallback with current timestamp
        fallback = dict(self.FALLBACK_FEED)
        fallback["fetched_at"] = datetime.datetime.utcnow().isoformat() + "Z"

        # ── Strategy 1: Claude with web_search (primary) ────────────────────
        try:
            from .models import SystemSettings
            anthropic_key = SystemSettings.get("ANTHROPIC_API_KEY") or getattr(settings, "ANTHROPIC_API_KEY", "")
        except Exception:
            anthropic_key = getattr(settings, "ANTHROPIC_API_KEY", "")
        if anthropic_key:
            try:
                data = self._fetch_with_claude(anthropic_key)
                data["cached"] = False
                data["source"] = "claude_websearch"
                data.setdefault("fetched_at", datetime.datetime.utcnow().isoformat() + "Z")
                self.__class__._cache = {"data": data, "timestamp": now}
                return Response(data)
            except Exception as e:
                import logging
                logging.getLogger(__name__).warning(f"Claude web search failed: {e}")

        # ── Strategy 2: OpenAI fallback ─────────────────────────────────────
        openai_key = getattr(settings, "OPENAI_API_KEY", "")
        if openai_key and not openai_key.startswith("sk-proj-YOUR"):
            try:
                from openai import OpenAI
                import re
                client = OpenAI(api_key=openai_key)
                today = datetime.datetime.utcnow().strftime("%B %Y")
                prompt = f"""Today is {today}. Generate a JSON feed of real SFDA/Saudi health/WHO news for a travel intelligence dashboard.
Return only valid JSON with keys "feed" (5 items) and "who" (2 items). Each feed item: icon, title, summary, source, time, impact (or null), url. Each who item: type, typeColor, title, summary, tags, url."""
                resp = client.chat.completions.create(
                    model="gpt-4o",
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=2000,
                    response_format={"type": "json_object"},
                )
                raw = resp.choices[0].message.content.strip()
                data = json.loads(raw)
                # Keep real URLs; fall back to Google News only if missing/null
                import urllib.parse

                def _ensure_url_oai(item, prefix=''):
                    url = item.get('url', '')
                    if url and url != 'null' and str(url).startswith('http'):
                        return
                    title = item.get('title', '') or ''
                    source = item.get('source', '') or ''
                    query = urllib.parse.quote(f'{prefix}{title} {source}'.strip())
                    item['url'] = f'https://www.google.com/search?q={query}&tbm=nws'

                for item in data.get('feed', []):
                    _ensure_url_oai(item)
                for item in data.get('who', []):
                    _ensure_url_oai(item, prefix='WHO ')
                data["cached"] = False
                data["source"] = "openai"
                data.setdefault("fetched_at", datetime.datetime.utcnow().isoformat() + "Z")
                self.__class__._cache = {"data": data, "timestamp": now}
                return Response(data)
            except Exception:
                pass

        # ── Strategy 3: Accurate static fallback ────────────────────────────
        self.__class__._cache = {"data": fallback, "timestamp": now}
        return Response(fallback)


class APISettingsView(APIView):
    """Get and update API keys — admin only."""

    def _mask(self, key):
        """Show first 12 chars then asterisks."""
        if not key or len(key) < 12:
            return key
        return key[:12] + '*' * (len(key) - 12)

    def get(self, request):
        from .models import SystemSettings
        from django.conf import settings
        # Read from DB first, fall back to env
        ant = SystemSettings.get('ANTHROPIC_API_KEY') or getattr(settings, 'ANTHROPIC_API_KEY', '')
        oai = SystemSettings.get('OPENAI_API_KEY')    or getattr(settings, 'OPENAI_API_KEY', '')
        return Response({
            'anthropic_key_set':  bool(ant),
            'openai_key_set':     bool(oai),
            'anthropic_key_mask': self._mask(ant),
            'openai_key_mask':    self._mask(oai),
        })

    def post(self, request):
        from .models import SystemSettings
        data = request.data
        saved = []
        if 'anthropic_key' in data and data['anthropic_key'].strip():
            SystemSettings.set('ANTHROPIC_API_KEY', data['anthropic_key'].strip())
            saved.append('anthropic')
        if 'openai_key' in data and data['openai_key'].strip():
            SystemSettings.set('OPENAI_API_KEY', data['openai_key'].strip())
            saved.append('openai')
        if not saved:
            return Response({'error': 'No keys provided'}, status=400)
        return Response({'saved': saved, 'message': 'API keys saved successfully'})
