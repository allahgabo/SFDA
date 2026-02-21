from rest_framework import serializers

class DelegationMemberSerializer(serializers.Serializer):
    name = serializers.CharField()
    title = serializers.CharField()
    department = serializers.CharField()

class AgendaItemSerializer(serializers.Serializer):
    time = serializers.CharField()
    activity = serializers.CharField()
    location = serializers.CharField(required=False, default='')

class AgendaDaySerializer(serializers.Serializer):
    day_label = serializers.CharField()
    date = serializers.CharField()
    items = AgendaItemSerializer(many=True)

class SessionSpeakerSerializer(serializers.Serializer):
    name = serializers.CharField()
    role = serializers.CharField(required=False, default='')

class SessionSerializer(serializers.Serializer):
    time = serializers.CharField()
    title = serializers.CharField()
    participation_type = serializers.CharField(required=False, default='attending')
    location = serializers.CharField(required=False, default='The Beverly Hilton Hotel')
    speakers = SessionSpeakerSerializer(many=True, required=False)

class BilateralMeetingSerializer(serializers.Serializer):
    entity = serializers.CharField()
    counterpart = serializers.CharField(required=False, default='')
    date = serializers.CharField(required=False, default='')
    time = serializers.CharField(required=False, default='')
    location = serializers.CharField(required=False, default='')
    talking_points = serializers.ListField(child=serializers.CharField(), required=False)

class SpeakerSerializer(serializers.Serializer):
    name = serializers.CharField()
    role = serializers.CharField()
    linkedin_url = serializers.CharField(required=False, default='')

class PrayerTimeSerializer(serializers.Serializer):
    date = serializers.CharField()
    day = serializers.CharField()
    fajr = serializers.CharField()
    shurooq = serializers.CharField()
    dhuhr = serializers.CharField()
    asr = serializers.CharField()
    maghrib = serializers.CharField()
    isha = serializers.CharField()

class MilkenReportSerializer(serializers.Serializer):
    # Cover Page
    report_title = serializers.CharField(default='مشاركة معالي الرئيس التنفيذي في مؤتمر معهد ميلكن العالمي 4-6 مايو 2025م')
    report_subtitle = serializers.CharField(default='لوس انجلوس-الولايات المتحدة الامريكية')

    # Visit Basic Info
    meeting_date = serializers.CharField(default='4 – 6 مايو 2025')
    city = serializers.CharField(default='لوس أنجلوس- الولايات المتحدة الامريكية')
    visit_objectives = serializers.ListField(
        child=serializers.CharField(),
        default=[
            'عرض التجربة التنظيمية السعودية في قطاع التقنية الحيوية بما يشمل الأطر التشريعية الحديثة وتسريع إجراءات التسجيل باستخدام الذكاء الاصطناعي.',
            'تعزيز حضور المملكة في المحافل الصحية والاستثمارية الدولية وبناء شراكات استراتيجية مع جهات تنظيمية ومؤسسات بحثية وشركات عالمية.',
            'الاستفادة من تجارب الاستثمار في الصناعات الصحية ودورها في دعم الابتكار وتعزيز جودة وسلامة المنتجات الحيوية.',
        ]
    )

    # Delegation
    delegation = DelegationMemberSerializer(many=True, default=[
        {'name': 'معالي الرئيس التنفيذي الدكتور/ هشام بن سعد الجضعي', 'title': 'الرئيس التنفيذي', 'department': 'الرئيس التنفيذي'},
        {'name': 'سعادة الأستاذة/ الآء بنت فؤاد سندي', 'title': 'مساعد الرئيس لقطاع الشؤون التنفيذية', 'department': 'الشؤون التنفيذية'},
        {'name': 'الاستاذة/ ابرار الصبيحي', 'title': 'رئيس قسم المراسم', 'department': 'الرئيس التنفيذي'},
    ])

    # Agenda days
    agenda_days = AgendaDaySerializer(many=True, default=[
        {
            'day_label': 'اليوم الأول',
            'date': '3 مايو 2025م',
            'items': [
                {'time': '6:00 ص', 'activity': 'المغادرة من مطار الملك خالد الدولي', 'location': 'الرياض'},
                {'time': '16:05 م', 'activity': 'الوصول الى مطار لوس انجلوس الدولي', 'location': 'لوس انجلوس'},
                {'time': '19:00م', 'activity': 'جلسة اجتياز', 'location': 'مقر الإقامة الفندقية للوفد'},
            ]
        },
        {
            'day_label': 'اليوم الثاني',
            'date': '4 مايو 2025م',
            'items': [
                {'time': '8:00ص-20:00م', 'activity': 'افتتاح الجلسة الحوارية', 'location': 'فندق بيفرلي هيلتون – لوس أنجلوس'},
                {'time': '12:30-14:30م', 'activity': 'Leaders in Health', 'location': 'فندق بيفرلي هيلتون'},
                {'time': '15:00م-17:00م', 'activity': 'ورشة عمل البيت السعودي', 'location': 'لم يحدد'},
            ]
        },
        {
            'day_label': 'اليوم الثالث',
            'date': '5 مايو 2025م',
            'items': [
                {'time': '9:30ص-16:00م', 'activity': 'افتتاح الجلسة الحوارية', 'location': 'فندق بيفرلي هيلتون'},
            ]
        },
        {
            'day_label': 'اليوم الرابع',
            'date': '6 مايو 2025م',
            'items': [
                {'time': '10:00-11:00ص', 'activity': 'The Roadmap to Longevity', 'location': 'فندق بيفرلي هيلتون'},
                {'time': '11:30ص-12:30م', 'activity': 'Driving Investment into Health Innovations Investment (Invite Only)', 'location': 'فندق بيفرلي هيلتون'},
                {'time': '16:40م', 'activity': 'المغادرة من مطار لوس انجلوس الدولي', 'location': 'لوس انجلوس'},
            ]
        },
    ])

    # Conference data
    conference_responsible = serializers.CharField(default='السيد/ ريتشارد ديتيزيو')
    conference_responsible_title = serializers.CharField(default='الرئيس التنفيذي لمعهد ميلكن.')
    conference_overview = serializers.CharField(
        default='يُعد مؤتمر معهد ميلكن العالمي أحد أبرز المنصات الفكرية والاقتصادية في العالم ويُعقد سنويًا في مدينة لوس أنجلوس بالولايات المتحدة الأمريكية. ويعد هذا المؤتمر المنبثق من أعمال وفعاليات معهد ميلكن العالمي الذي يعتبر بمثابة "دافوس مصغر" حيث يجتمع فيه قادة العالم على المستوى الاقتصادي والسياسي والاستثماري والصحي. ويتطرق لمواضيع عالمية عدة ومنها علاقة الذكاء الاصطناعي بالصحة العامة. ويعد هذا المعهد منظمة غير ربحية. ويهدف إلى التحفيز وإيجاد الحلول العملية والقابلة للتطوير لمواجهة التحديات العالمية.'
    )
    conference_slogan = serializers.CharField(default='"نحو مستقبل مزدهر – Toward a Flourishing Future"')
    conference_dates = serializers.CharField(default='خلال الفترة من 4 إلى 7 مايو 2025.')
    conference_participants = serializers.CharField(default='أكثر من 4,000 مشارك من مختلف أنحاء العالم.')
    conference_speakers_count = serializers.CharField(default='ما يزيد عن 900 متحدث وقرابة 200 جلسة متخصصة.')

    # Conference tracks (12 main tracks)
    conference_tracks = serializers.ListField(
        child=serializers.CharField(),
        default=[
            'الوصول -الفرص -والتنقل الاقتصادي',
            'الأعمال والصناعة',
            'الطاقة والبيئة',
            'الأسواق المالية',
            'الصحة والبحوث الطبية',
            'رأس المال البشري- تطوير القوى العاملة- التعليم',
            'العلاقات الدولية والجيواقتصادية',
            'العمل الخيري والأثر الاجتماعي',
            'السياسات والتنظيمات',
            'الأمن والمخاطر',
            'المجتمع والثقافة',
            'التقنية والابتكار',
        ]
    )

    # Previous conference outcomes
    prev_2023_outcomes = serializers.ListField(child=serializers.CharField(), default=[
        'الذكاء الاصطناعي في الرعاية الصحية: تم التركيز على إمكانات الذكاء الاصطناعي في تحسين نظم الرعاية الصحية بما في ذلك التنبؤ بالتهديدات البيولوجية وتطوير اللقاحات.',
        'الصحة العامة والوقاية: نوقشت استراتيجيات تعزيز الصحة العامة من خلال التركيز على الوقاية من الأمراض غير المعدية مثل أمراض القلب والسكرى.',
    ])
    prev_2024_outcomes = serializers.ListField(child=serializers.CharField(), default=[
        'مبادرات صحية جديدة: أستعرض المعهد عدة مبادرات تهدف إلى تشكيل مستقبل الصحة من خلال الشراكات والتعاون مع التركيز على الوقاية والبحوث الطبية المجتمعية.',
        'التغير المناخي والاستدامة: تمت مناقشة المساهمات المالية لتحقيق أهداف الحد من الانبعاثات والحفاظ على البيئة.',
    ])
    ksa_participation_2023 = serializers.ListField(child=serializers.CharField(), default=[
        'شارك معالي وزير الاقتصاد والتخطيط فيصل الإبراهيم في جلسة حوارية بعنوان "العولمة : نماذج جديدة في الابتكار والتكامل" في 1 مايو 2023.',
        'شارك معالي وزير الاستثمار خالد الفالح في جلسة بعنوان "السعودية : من الرؤية إلى الواقع" في 2 مايو 2023.',
    ])
    ksa_participation_2024 = serializers.ListField(child=serializers.CharField(), default=[
        'شارك معالي رئيس مجلس هيئة السوق المالية محمد القويز في جلسة بعنوان "أسواق رأس المال في السعودية: استراتيجيات للتقدم" في مايو 2024.',
        'شاركت السيدة سارة السحيمي رئيسة مجلس إدارة مجموعة تداول السعودية كمتحدثة في المؤتمر ذاته.',
    ])

    # Sessions Day 1
    sessions_day1 = SessionSerializer(many=True, default=[
        {'time': '12:30-14:30', 'title': 'Leaders in Health', 'participation_type': 'attending', 'location': 'The Beverly Hilton Hotel'},
        {'time': '14:30-12:30', 'title': 'Invitation-only session (H.E the CEO has expressed interest in attending)', 'participation_type': 'attending', 'location': '-'},
        {'time': '15:00-17:00', 'title': 'ورشة عمل البيت السعودي', 'participation_type': 'attending', 'location': '-'},
    ])

    sessions_day3 = SessionSerializer(many=True, default=[
        {'time': '10:00-11:00', 'title': 'The Roadmap to Longevity', 'participation_type': 'attending', 'location': 'The Beverly Hilton Hotel'},
        {'time': '13:00-14:00', 'title': 'Driving Investment into Health Innovations Investment (Invite Only)', 'participation_type': 'attending', 'location': 'The Beverly Hilton Hotel'},
    ])

    # Key speakers
    key_speakers = SpeakerSerializer(many=True, default=[
        {'name': 'كريستالينا غورغييفا', 'role': 'المدير العام لصندوق النقد الدولي (IMF)', 'linkedin_url': 'https://www.linkedin.com/in/kristalina-georgieva/'},
        {'name': 'أجاى بانغا', 'role': 'رئيس البنك الدولي', 'linkedin_url': 'Ajay Banga Selected 14th President of the World Bank'},
        {'name': 'جين فريزر', 'role': 'الرئيس التنفيذي لشركة Citigroup', 'linkedin_url': 'https://www.linkedin.com/in/jane-fraser-3292068/'},
        {'name': 'فرناندو حداد', 'role': 'وزير المالية في البرازيل', 'linkedin_url': 'https://www.linkedin.com/today/author/fernandohaddad23/'},
        {'name': 'خالد الفالح', 'role': 'وزير الاستثمار، المملكة العربية السعودية', 'linkedin_url': ''},
        {'name': 'عبدالله بن عامر العيسى', 'role': 'وزير الاتصالات وتقنية المعلومات، المملكة العربية السعودية', 'linkedin_url': ''},
        {'name': 'توني بلير', 'role': 'الرئيس التنفيذي لمعهد توني بلير للتغيير العالمي؛ رئيس الوزراء البريطاني السابق', 'linkedin_url': ''},
        {'name': 'إيلون ماسك', 'role': 'المؤسس والرئيس التنفيذي لشركة Tesla', 'linkedin_url': ''},
    ])

    # Bilateral meetings
    bilateral_meetings = BilateralMeetingSerializer(many=True, default=[
        {
            'entity': '',
            'counterpart': '',
            'date': 'مايو 2025م',
            'time': '',
            'location': '',
            'talking_points': [
                'Opening Remark from the',
                'Opening Remark from the SFDA',
                'SFDA\'s Experience',
                'Q&A and discussion',
            ]
        }
    ])

    # Consulate info
    consulate_phone = serializers.CharField(default='0013104796000')
    consulate_email = serializers.CharField(default='uscacon@mofa.gov.sa')
    consulate_hours = serializers.CharField(default='من 9 صباحاً – حتى 4 مساءً')
    consulate_holidays = serializers.CharField(default='السبت الجمعة')
    consulate_address = serializers.CharField(default='The Royal Consulate General Of Saudi Arabia In Los Angeles California. 12400 Wilshire Blvd Suite 700 Los Angeles ,CA 90025')
    consul_general_name = serializers.CharField(default='الأستاذ/ بندر بن فهد الزيد')
    consul_general_title = serializers.CharField(default='القنصل العام للمملكة العربية السعودية في لوس أنجلوس')
    consul_appointment_since = serializers.CharField(default='منذ 2023 حتى الآن')

    # Prayer times
    prayer_times = PrayerTimeSerializer(many=True, default=[
        {'date': '4 مايو 2025م', 'day': 'الاحد', 'fajr': '4:45 AM', 'shurooq': '6:01 AM', 'dhuhr': '12:50 PM', 'asr': '4:33 PM', 'maghrib': '7:39 PM', 'isha': '8:56 PM'},
        {'date': '5 مايو 2025م', 'day': 'الاثنين', 'fajr': '4:43 AM', 'shurooq': '6:00 AM', 'dhuhr': '12:50 PM', 'asr': '4:33 PM', 'maghrib': '7:40 PM', 'isha': '8:57 PM'},
        {'date': '6 مايو 2025م', 'day': 'الخلافاء', 'fajr': '4:42 AM', 'shurooq': '5:59 AM', 'dhuhr': '12:50 PM', 'asr': '4:33 PM', 'maghrib': '7:41 PM', 'isha': '8:58 PM'},
        {'date': '7 مايو 2025م', 'day': 'الاربعاء', 'fajr': '4:41 AM', 'shurooq': '5:58 AM', 'dhuhr': '12:50 PM', 'asr': '4:33 PM', 'maghrib': '7:42 PM', 'isha': '8:59 PM'},
    ])

    # Weather
    weather_days = serializers.ListField(
        child=serializers.DictField(),
        default=[
            {'day': '4', 'high': '19°', 'low': '12°'},
            {'day': '5', 'high': '19°', 'low': '12°'},
            {'day': '6', 'high': '20°', 'low': '12°'},
            {'day': '7', 'high': '20°', 'low': '11°'},
        ]
    )
