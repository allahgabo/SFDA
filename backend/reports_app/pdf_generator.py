import io
from django.template.loader import render_to_string
from weasyprint import HTML


TOC_SECTIONS = [
    {"title": "نظرة عامة على الزيارة",                    "page":  "3"},
    {"title": "الملخص التنفيذي الاستراتيجي",              "page":  "4"},
    {"title": "التقييم الاستخباراتي الاستراتيجي",         "page":  "5"},
    {"title": "نظرة عامة على المؤتمر",                    "page":  "6"},
    {"title": "السياق التاريخي",                          "page":  "7"},
    {"title": "الصلة بالاستراتيجية الوطنية",              "page":  "8"},
    {"title": "السياق الثنائي",                           "page":  "9"},
    {"title": "الملف السياسي وملامح الدولة",              "page": "10"},
    {"title": "لمحة استخباراتية عن الدولة",               "page": "11"},
    {"title": "جدول الأعمال التفصيلي — اليوم الأول",      "page": "12"},
    {"title": "جدول الأعمال التفصيلي — اليوم الثاني",     "page": "13"},
    {"title": "جدول الأعمال التفصيلي — اليوم الثالث",     "page": "14"},
    {"title": "تشكيل الوفد الرسمي",                       "page": "15"},
    {"title": "محاور ومسارات الفعالية",                   "page": "16"},
    {"title": "تحليل الأثر الاستراتيجي للجلسات",          "page": "17"},
    {"title": "المتحدثون الرئيسيون",                      "page": "19"},
    {"title": "الاجتماعات الثنائية المقررة",               "page": "21"},
    {"title": "الاجتماعات المقترحة",                      "page": "22"},
    {"title": "معلومات السفارة والقنصلية",                 "page": "23"},
    {"title": "توقعات الطقس وأوقات الصلاة",               "page": "24"},
    {"title": "المرفقات والوثائق الداعمة",                 "page": "25"},
]

AVATAR_GRADIENTS = [
    ("#1c3370","#3b5bdb"), ("#0f766e","#14b8a6"), ("#7e22ce","#a855f7"),
    ("#b45309","#f59e0b"), ("#be123c","#fb7185"), ("#0369a1","#38bdf8"),
    ("#166534","#22c55e"), ("#7c2d12","#f97316"), ("#4c0519","#f43f5e"),
    ("#1e3a5f","#60a5fa"),
]


def _pairs(lst):
    out = []
    for i in range(0, len(lst), 2):
        out.append((lst[i], lst[i+1] if i+1 < len(lst) else None))
    return out


def _avatar_style(name):
    safe = (name or "A").strip() or "A"
    try:
        c = safe[0].upper()
        if ord(c) < 128:
            idx = (ord(c) - ord('A')) % len(AVATAR_GRADIENTS)
        else:
            idx = ord(c) % len(AVATAR_GRADIENTS)
    except Exception:
        idx = 0
    g1, g2 = AVATAR_GRADIENTS[idx]
    return f"background:linear-gradient(135deg,{g1},{g2});"


def _build_context(report):
    toc_pairs = _pairs(TOC_SECTIONS)

    # Track pairs with sequential numbers
    tracks = report.conference_tracks or []
    numbered_tracks = [{"n": i+1, "text": t} for i, t in enumerate(tracks)]
    track_pairs = _pairs(numbered_tracks)

    # Speaker pairs with avatar styling
    speakers = [dict(sp) for sp in (report.speakers or []) if (sp.get("name") or "").strip()]
    for sp in speakers:
        sp['style']   = _avatar_style(sp.get("name", ""))
        sp['initial'] = (((sp.get("name") or "") or "?").strip() or "?")[0].upper()
    speaker_pairs = _pairs(speakers[:18])  # top 18 for cards (3-col layout = 6 rows)

    return {
        "report":        report,
        "toc_pairs":     toc_pairs,
        "track_pairs":   track_pairs,
        "speaker_pairs": speaker_pairs,
    }


def generate_pdf(report) -> bytes:
    html = render_to_string("reports_app/milken_report.html", _build_context(report))
    buf  = io.BytesIO()
    HTML(string=html, base_url=None).write_pdf(buf)
    return buf.getvalue()


def generate_html_preview(report) -> str:
    return render_to_string("reports_app/milken_report.html", _build_context(report))
