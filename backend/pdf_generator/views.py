import os
import io
from datetime import datetime
from django.http import HttpResponse
from django.template.loader import render_to_string
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

# ── Patch fontTools bug: bit 123 out of valid range 0-122 ──────────────────
try:
    import fontTools.ttLib.tables.O_S_2f_2 as _os2_module

    def _patched_set_unicode_ranges(self, bits):
        ul1, ul2, ul3, ul4 = 0, 0, 0, 0
        for bit in bits:
            if not isinstance(bit, int) or bit > 122:
                continue  # silently skip invalid bits
            if 0 <= bit < 32:
                ul1 |= (1 << bit)
            elif 32 <= bit < 64:
                ul2 |= (1 << (bit - 32))
            elif 64 <= bit < 96:
                ul3 |= (1 << (bit - 64))
            elif 96 <= bit < 123:
                ul4 |= (1 << (bit - 96))
        self.ulUnicodeRange1, self.ulUnicodeRange2 = ul1, ul2
        self.ulUnicodeRange3, self.ulUnicodeRange4 = ul3, ul4

    _os2_module.table_O_S_2f_2.setUnicodeRanges = _patched_set_unicode_ranges
except Exception:
    pass
# ────────────────────────────────────────────────────────────────────────────

import weasyprint

from .serializers import MilkenReportSerializer

DEFAULT_DELEGATION = [
    {"number": 1, "name": "معالي الرئيس التنفيذى الدكتور/ هشام بن سعد الجضعى", "position": "الرئيس التنفيذى", "department": "الرئيس التنفيذى"},
    {"number": 2, "name": "سعادة الأستاذة/ الآء بنت فؤاد سندى", "position": "مساعد الرئيس لقطاع الشؤون التنفيذية", "department": "الشؤون التنفيذية"},
    {"number": 3, "name": "الاستاذة/ ابرار الصبيحى", "position": "رئيس قسم المراسم", "department": "الرئيس التنفيذى"},
]

DEFAULT_SCHEDULE = [
    {"day_label": "اليوم الأول | 3 مايو 2025م", "time": "6:00 ص", "activity": "المغادرة من مطار الملك خالد الدولى", "location": "الرياض", "highlight": False},
    {"day_label": "", "time": "16:05 م", "activity": "الوصول الى مطار لوس أنجلوس الدولى", "location": "لوس أنجلوس", "highlight": False},
    {"day_label": "", "time": "19:00 م", "activity": "جلسة اِبجاز", "location": "مقر الإقامة الفندقية للوفد", "highlight": False},
    {"day_label": "اليوم الثانى| 4 مايو 2025م", "time": "8:00ص-20:00م", "activity": "افتتاح الجلسة الحوارية", "location": "فندق بيفرلى هيلتون – لوس أنجلوس", "highlight": False},
    {"day_label": "", "time": "12:30-14:30م", "activity": "Leaders in Health", "location": "فندق بيفرلى هيلتون", "highlight": False},
    {"day_label": "", "time": "15:00م-17:00م", "activity": "ورشة عمل البيت السعودى", "location": "لم يحدد", "highlight": False},
    {"day_label": "", "time": "", "activity": "غداء عمل \\ عشاء على هامش ورشة عمل البيت السعودى", "location": "", "highlight": True},
    {"day_label": "اليوم الثالث| 5 مايو 2025م", "time": "9:30ص-16:00م", "activity": "افتتاح الجلسة الحوارية", "location": "فندق بيفرلى هيلتون", "highlight": False},
    {"day_label": "اليوم الرابع| 6 مايو 2025م", "time": "10:00-11:00ص", "activity": "The Roadmap to Longevity", "location": "فندق بيفرلى هيلتون", "highlight": False},
    {"day_label": "", "time": "11:30ص-12:30م", "activity": "Driving Investment into Health Innovations Investment (Invite Only)", "location": "فندق بيفرلى هيلتون", "highlight": False},
    {"day_label": "", "time": "16:40م", "activity": "المغادرة من مطار لوس أنجلوس الدولى", "location": "لوس أنجلوس", "highlight": False},
]

DEFAULT_DAY1_SESSIONS = [
    {"time": "13:30-12:30", "session_title": "Leaders in Health", "participation_type": "attending", "speaker_owner": "Moderator: Esther Krofah\nExecutive Vice President, Milken Institute Health", "place": "The Beverly Hilton Hotel"},
    {"time": "14:30-12:30", "session_title": "invitation-only session and H.E the CEO has expressed interest in attending", "participation_type": "attending", "speaker_owner": "-", "place": "The Beverly Hilton Hotel"},
    {"time": "15:00-17:00", "session_title": 'Dinner/Saudi House "Biotech and Medical Device Research in KSA"', "participation_type": "Statement about Biotech and Medical Device Research in KSA", "speaker_owner": "Ministry of Investment (5 min)\nKing Abdullah International Medical Research Center (10 min)\nH.E Dr.Hisham Al jadhey-SFDA (10 min)\nKing Faisal Specialist Hospital & Research Centre (10 min)\nSaudi National Institute of Health (10 min)\nSeha virtual Hospital (10 min)\nAll (10 min)", "place": "-"},
]

DEFAULT_DAY2_SESSIONS = [
    {"time": "16:00-9:00", "session_title": "Opening session", "participation_type": "attending", "speaker_owner": "-", "place": "The Beverly Hilton Hotel"},
]

DEFAULT_DAY3_SESSIONS = [
    {"time": "11:00-10:00", "session_title": "The Roadmap to Longevity", "participation_type": "attending",
     "speaker_owner": "MODERATOR: Gadi Schwartz - Correspondent, NBC News\nSPEAKERS:\nDan Buettner - Founder, Blue Zones, LLC\nLaura Deming - CEO, Cradle\nRichard Isaacson - Director, Atria Precision Prevention Program\nEric Verdin - CEO and President, Buck Institute for Research on Aging\nVonda Wright - Orthopaedic Surgeon; Founder, Precision Longevity",
     "place": "The Beverly Hilton Hotel"},
    {"time": "14:00-13:00", "session_title": "Driving Investment into Health Innovations Investment (Invite Only)", "participation_type": "attending",
     "speaker_owner": "MODERATOR: Caitlin MacLean - Managing Director, Milken Institute Finance\nSPEAKERS:\nMarina Balobanova - Investment Officer, Private Equity, CalPERS\nCam Black - Treasurer and CIO, Blue Cross Blue Shield of Arizona\nMike Negussie - Investment Director, Children's Healthcare of Atlanta\nScott Pittman - SVP and CIO, Mount Sinai Health System\nJeanne Shen - CIO, Gavi, The Vaccine Alliance",
     "place": "The Beverly Hilton Hotel"},
]

DEFAULT_SPEAKERS = [
    {"name": "كريستالينا غورغييفا", "title": "المدير العام لصندوق النقد الدولى (IMF)", "linkedin_url": "https://www.linkedin.com/in/kristalina-georgieva/"},
    {"name": "أجاى بانغا", "title": "رئيس البنك الدولى", "linkedin_url": "https://www.worldbank.org/en/about/president"},
    {"name": "جين فريزر", "title": "الرئيس التنفيذى لشركة Citigroup", "linkedin_url": "https://www.linkedin.com/in/jane-fraser-3292068/"},
    {"name": "فرناندو حداد", "title": "وزير المالية فى البرازيل", "linkedin_url": "https://www.linkedin.com/today/author/fernandohaddad23/"},
    {"name": "خالد الفالح", "title": "وزير الاستثمار، المملكة العربية السعودية", "linkedin_url": ""},
    {"name": "عبدالله بن عامر العيسى", "title": "وزير الاتصالات وتقنية المعلومات، المملكة العربية السعودية", "linkedin_url": ""},
    {"name": "توني بلير", "title": "الرئيس التنفيذى لمعهد توني بلير للتغيير العالمى؛ رئيس الوزراء البريطانى الأسبق", "linkedin_url": ""},
    {"name": "إيلون ماسك", "title": "المؤسس والرئيس التنفيذى لشركة Tesla", "linkedin_url": ""},
]

DEFAULT_BILATERAL = [
    {
        "entity": "",
        "counterpart": "",
        "date": "مايو 2025م",
        "time": "",
        "location": "",
        "talking_points": ["Opening Remark from the", "Opening Remark from the SFDA", "Suggested talking points:\n1. SFDA's Experience", "Q&A and discussion"]
    }
]

DEFAULT_WEATHER = [
    {"day_number": 4, "high": "19°", "low": "12°"},
    {"day_number": 5, "high": "19°", "low": "12°"},
    {"day_number": 6, "high": "20°", "low": "12°"},
    {"day_number": 7, "high": "20°", "low": "11°"},
]

DEFAULT_PRAYER = [
    {"date": "4 مايو 2025م", "day_name": "الاحد", "fajr": "4:45 AM", "sunrise": "6:01 AM", "dhuhr": "12:50 PM", "asr": "4:33 PM", "maghrib": "7:39 PM", "isha": "8:56 PM"},
    {"date": "5 مايو 2025م", "day_name": "الاثنين", "fajr": "4:43 AM", "sunrise": "6:00 AM", "dhuhr": "12:50 PM", "asr": "4:33 PM", "maghrib": "7:40 PM", "isha": "8:57 PM"},
    {"date": "6 مايو 2025م", "day_name": "الخلاثاء", "fajr": "4:42 AM", "sunrise": "5:59 AM", "dhuhr": "12:50 PM", "asr": "4:33 PM", "maghrib": "7:41 PM", "isha": "8:58 PM"},
    {"date": "7 مايو 2025م", "day_name": "الاربعاء", "fajr": "4:41 AM", "sunrise": "5:58 AM", "dhuhr": "12:50 PM", "asr": "4:33 PM", "maghrib": "7:42 PM", "isha": "8:59 PM"},
]


class GenerateMilkenPDFView(APIView):
    def post(self, request):
        serializer = MilkenReportSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        data = serializer.validated_data

        # Apply defaults if not provided
        if not data.get('delegation_members'):
            data['delegation_members'] = DEFAULT_DELEGATION
        if not data.get('schedule_items'):
            data['schedule_items'] = DEFAULT_SCHEDULE
        if not data.get('day1_sessions'):
            data['day1_sessions'] = DEFAULT_DAY1_SESSIONS
        if not data.get('day2_sessions'):
            data['day2_sessions'] = DEFAULT_DAY2_SESSIONS
        if not data.get('day3_sessions'):
            data['day3_sessions'] = DEFAULT_DAY3_SESSIONS
        if not data.get('keynote_speakers'):
            data['keynote_speakers'] = DEFAULT_SPEAKERS
        if not data.get('bilateral_meetings'):
            data['bilateral_meetings'] = DEFAULT_BILATERAL
        if not data.get('weather_days'):
            data['weather_days'] = DEFAULT_WEATHER
        if not data.get('prayer_times'):
            data['prayer_times'] = DEFAULT_PRAYER

        # Build schedule grouped by day
        schedule_grouped = []
        current_day = None
        for item in data['schedule_items']:
            if item.get('day_label'):
                current_day = {'day_label': item['day_label'], 'rows': []}
                schedule_grouped.append(current_day)
            if current_day:
                current_day['rows'].append(item)

        data['schedule_grouped'] = schedule_grouped

        # Get static dir path
        static_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static')
        data['static_dir'] = static_dir

        # Render HTML template
        html_string = render_to_string('milken_report.html', {'data': data})

        # Generate PDF with WeasyPrint
        pdf_file = weasyprint.HTML(string=html_string, base_url=static_dir).write_pdf()

        # Generate filename
        report_date = data.get('report_date', datetime.now().strftime('%Y-%m-%d'))
        filename = f"Milken_Report_{report_date}.pdf"

        response = HttpResponse(pdf_file, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        response['Access-Control-Expose-Headers'] = 'Content-Disposition'
        return response


class GetDefaultDataView(APIView):
    """Returns default/example data to pre-fill the form"""
    def get(self, request):
        return Response({
            "visit_date_ar": "4 – 6 مايو 2025",
            "visit_city_ar": "لوس أنجلوس- الولايات المتحدة الامريكية",
            "goal_1": "عرض التجربة التنظيمية السعودية في قطاع التقنية الحيوية بما يشمل الأطر التشريعية الحديثة وتسريع إجراءات التسجيل باستخدام الذكاء الاصطناعي.",
            "goal_2": "تعزيز حضور المملكة في المحافل الصحية والاستثمارية الدولية وبناء شراكات استراتيجية مع جهات تنظيمية ومؤسسات بحثية وشركات عالمية.",
            "goal_3": "الاستفادة من تجارب الاستثمار في الصناعات الصحية ودورها في دعم الابتكار وتعزيز جودة وسلامة المنتجات الحيوية.",
            "delegation_members": DEFAULT_DELEGATION,
            "schedule_items": DEFAULT_SCHEDULE,
            "conference_slogan": "نحو مستقبل مزدهر – Toward a Flourishing Future",
            "conference_date_range": "خلال الفترة من 4 إلى 7 مايو 2025.",
            "conference_participants": "4,000",
            "conference_speakers": "900",
            "conference_sessions": "200",
            "conference_responsible": "السيد/ ريتشارد ديتيزيو",
            "day1_sessions": DEFAULT_DAY1_SESSIONS,
            "day2_sessions": DEFAULT_DAY2_SESSIONS,
            "day3_sessions": DEFAULT_DAY3_SESSIONS,
            "keynote_speakers": DEFAULT_SPEAKERS,
            "bilateral_meetings": DEFAULT_BILATERAL,
            "consul_name": "الأستاذ/ بندر بن فهد الزيد",
            "consul_phone": "0013104796000",
            "consul_email": "uscacon@mofa.gov.sa",
            "consul_address": "12400 Wilshire Blvd Suite 700 Los Angeles, CA 90025",
            "consul_appointment_date": "منذ 2023 حتى الآن",
            "weather_days": DEFAULT_WEATHER,
            "prayer_times": DEFAULT_PRAYER,
            "report_date": datetime.now().strftime('%Y-%m-%d'),
            "document_number": "02-05-2025",
        })
