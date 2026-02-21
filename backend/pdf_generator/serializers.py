from rest_framework import serializers


class DelegationMemberSerializer(serializers.Serializer):
    number = serializers.IntegerField()
    name = serializers.CharField()
    position = serializers.CharField()
    department = serializers.CharField()


class ScheduleItemSerializer(serializers.Serializer):
    day_label = serializers.CharField()  # e.g. "اليوم الأول | 3 مايو 2025م"
    time = serializers.CharField()
    activity = serializers.CharField()
    location = serializers.CharField()
    highlight = serializers.BooleanField(default=False)


class SessionSerializer(serializers.Serializer):
    time = serializers.CharField()
    session_title = serializers.CharField()
    participation_type = serializers.CharField()
    speaker_owner = serializers.CharField(required=False, allow_blank=True)
    place = serializers.CharField(required=False, allow_blank=True)


class BilateralMeetingSerializer(serializers.Serializer):
    entity = serializers.CharField()
    counterpart = serializers.CharField(required=False, allow_blank=True)
    date = serializers.CharField()
    time = serializers.CharField(required=False, allow_blank=True)
    location = serializers.CharField(required=False, allow_blank=True)
    talking_points = serializers.ListField(child=serializers.CharField(), required=False)


class SpeakerSerializer(serializers.Serializer):
    name = serializers.CharField()
    title = serializers.CharField()
    linkedin_url = serializers.CharField(required=False, allow_blank=True)


class PrayerTimeSerializer(serializers.Serializer):
    date = serializers.CharField()
    day_name = serializers.CharField()
    fajr = serializers.CharField()
    sunrise = serializers.CharField()
    dhuhr = serializers.CharField()
    asr = serializers.CharField()
    maghrib = serializers.CharField()
    isha = serializers.CharField()


class WeatherDaySerializer(serializers.Serializer):
    day_number = serializers.IntegerField()
    high = serializers.CharField()
    low = serializers.CharField()


class MilkenReportSerializer(serializers.Serializer):
    # === PAGE 3: BASIC VISIT INFO ===
    visit_date_ar = serializers.CharField(default="4 – 6 مايو 2025")
    visit_city_ar = serializers.CharField(default="لوس أنجلوس- الولايات المتحدة الامريكية")
    goal_1 = serializers.CharField(default="عرض التجربة التنظيمية السعودية في قطاع التقنية الحيوية بما يشمل الأطر التشريعية الحديثة وتسريع إجراءات التسجيل باستخدام الذكاء الاصطناعي.")
    goal_2 = serializers.CharField(default="تعزيز حضور المملكة في المحافل الصحية والاستثمارية الدولية وبناء شراكات استراتيجية مع جهات تنظيمية ومؤسسات بحثية وشركات عالمية.")
    goal_3 = serializers.CharField(default="الاستفادة من تجارب الاستثمار في الصناعات الصحية ودورها في دعم الابتكار وتعزيز جودة وسلامة المنتجات الحيوية.")

    # === PAGE 5: DELEGATION ===
    delegation_members = DelegationMemberSerializer(many=True, required=False)

    # === PAGE 6: SCHEDULE ===
    schedule_items = ScheduleItemSerializer(many=True, required=False)

    # === PAGE 8: CONFERENCE INFO ===
    conference_slogan = serializers.CharField(default="نحو مستقبل مزدهر – Toward a Flourishing Future")
    conference_date_range = serializers.CharField(default="خلال الفترة من 4 إلى 7 مايو 2025.")
    conference_participants = serializers.CharField(default="4,000")
    conference_speakers = serializers.CharField(default="900")
    conference_sessions = serializers.CharField(default="200")
    conference_responsible = serializers.CharField(default="السيد/ ريتشارد ديتيزيو")

    # === PAGE 10: SESSIONS AGENDA ===
    day1_sessions = SessionSerializer(many=True, required=False)
    day2_sessions = SessionSerializer(many=True, required=False)
    day3_sessions = SessionSerializer(many=True, required=False)

    # === PAGE 12+: SPEAKERS ===
    keynote_speakers = SpeakerSerializer(many=True, required=False)

    # === PAGE 17+: BILATERAL MEETINGS ===
    bilateral_meetings = BilateralMeetingSerializer(many=True, required=False)

    # === PAGE 21: CONSULATE INFO ===
    consul_name = serializers.CharField(default="الأستاذ/ بندر بن فهد الزيد")
    consul_phone = serializers.CharField(default="0013104796000")
    consul_email = serializers.CharField(default="uscacon@mofa.gov.sa")
    consul_address = serializers.CharField(default="12400 Wilshire Blvd Suite 700 Los Angeles, CA 90025")
    consul_appointment_date = serializers.CharField(default="منذ 2023 حتى الآن")

    # === PAGE 23: WEATHER & PRAYER ===
    weather_days = WeatherDaySerializer(many=True, required=False)
    prayer_times = PrayerTimeSerializer(many=True, required=False)

    # === REPORT METADATA ===
    report_date = serializers.CharField(default="2025-05-02")
    document_number = serializers.CharField(default="02-05-2025")
