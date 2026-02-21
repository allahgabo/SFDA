from rest_framework import serializers
from .models import Report


class ReportListSerializer(serializers.ModelSerializer):
    lat = serializers.FloatField(read_only=True)
    lon = serializers.FloatField(read_only=True)

    class Meta:
        model = Report
        fields = [
            'id', 'title', 'event_name', 'event_type', 'city', 'country',
            'venue', 'start_date', 'end_date', 'status', 'risk_level',
            'traveler_name', 'created_at', 'ai_generated', 'lat', 'lon',
        ]


class ReportDetailSerializer(serializers.ModelSerializer):
    lat = serializers.FloatField(read_only=True)
    lon = serializers.FloatField(read_only=True)

    class Meta:
        model = Report
        fields = '__all__'


class ReportCreateSerializer(serializers.ModelSerializer):
    title         = serializers.CharField(required=False, allow_blank=True, default='')
    # Use CharField so we can normalise partial URLs before validation
    event_website = serializers.CharField(required=False, allow_blank=True, default='')

    class Meta:
        model = Report
        fields = [
            'title', 'event_name', 'event_type', 'city', 'country',
            'venue', 'start_date', 'end_date', 'event_website',
            'language', 'context', 'traveler_name', 'traveler_title',
        ]

    def validate_event_website(self, value):
        if not value or not value.strip():
            return ''
        v = value.strip()
        # Auto-prefix bare domains so storage stays consistent
        if not v.startswith(('http://', 'https://')):
            v = 'https://' + v
        return v

    def validate(self, attrs):
        # Auto-set title from event_name if not provided
        if not attrs.get('title'):
            attrs['title'] = attrs.get('event_name', 'Untitled Report')
        return attrs
