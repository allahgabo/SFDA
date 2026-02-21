from django.db import models
import json


class Report(models.Model):
    STATUS_CHOICES = [('draft', 'Draft'), ('ready', 'Ready'), ('archived', 'Archived')]
    RISK_CHOICES = [('low', 'Low'), ('medium', 'Medium'), ('high', 'High')]

    # Basic info
    title = models.CharField(max_length=500)
    event_name = models.CharField(max_length=500)
    event_type = models.CharField(max_length=200, blank=True, default='Conference')
    city = models.CharField(max_length=200)
    country = models.CharField(max_length=200)
    venue = models.CharField(max_length=500, blank=True)
    start_date = models.CharField(max_length=50)
    end_date = models.CharField(max_length=50, blank=True)
    event_website = models.URLField(blank=True)
    language = models.CharField(max_length=50, default='English')
    context = models.TextField(blank=True)

    # Meta
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='draft')
    risk_level = models.CharField(max_length=50, choices=RISK_CHOICES, default='low')
    traveler_name = models.CharField(max_length=300, default='Dr. Hisham Al Jadhey')
    traveler_title = models.CharField(max_length=300, default='الرئيس التنفيذي للهيئة العامة للغذاء والدواء')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    ai_generated = models.BooleanField(default=False)

    # Generated content (stored as JSON)
    report_subtitle = models.CharField(max_length=500, blank=True, default='')
    visit_objectives = models.JSONField(default=list)
    country_info = models.JSONField(default=dict)
    delegation = models.JSONField(default=list)
    agenda = models.JSONField(default=list)
    conference_data = models.JSONField(default=dict)
    conference_tracks = models.JSONField(default=list)
    sessions = models.JSONField(default=dict)
    speakers = models.JSONField(default=list)
    bilateral_meetings = models.JSONField(default=list)
    consulate = models.JSONField(default=dict)
    weather = models.JSONField(default=list)
    prayer_times = models.JSONField(default=list)
    previous_outcomes = models.JSONField(default=list)
    attachments = models.JSONField(default=list)
    executive_summary   = models.TextField(blank=True, default='')
    key_ambassadors     = models.JSONField(default=list)
    participants          = models.JSONField(default=list)
    suggested_meetings    = models.JSONField(default=list)
    # Rich intelligence sections
    conference_summary    = models.TextField(blank=True, default='')
    conference_history    = models.TextField(blank=True, default='')
    ksa_participation_history = models.TextField(blank=True, default='')
    sfda_relevance        = models.TextField(blank=True, default='')
    bilateral_relations   = models.TextField(blank=True, default='')
    geopolitical_summary  = models.TextField(blank=True, default='')
    entry_requirements    = models.TextField(blank=True, default='')
    leadership_brief      = models.TextField(blank=True, default='')
    trade_exchange        = models.TextField(blank=True, default='')
    sfda_talking_points   = models.JSONField(default=list)
    embassy               = models.JSONField(default=dict)

    # ── §3 Strategic Intelligence Assessment (3 bullet sub-sections) ──
    intel_global_significance = models.JSONField(default=list)   # list of bullet strings
    intel_regulatory_impact   = models.JSONField(default=list)
    intel_long_term_value     = models.JSONField(default=list)

    # ── §6 National Strategic Relevance (4 named blocks) ──
    ns_vision_alignment          = models.TextField(blank=True, default='')
    ns_regulatory_relevance      = models.TextField(blank=True, default='')
    ns_investment_implications   = models.TextField(blank=True, default='')
    ns_institutional_positioning = models.TextField(blank=True, default='')

    # ── §7 Bilateral Relations (structured field table) ──
    bilateral_fields = models.JSONField(default=dict)  # {trade_volume, cooperation_areas, strategic_agreements, health_regulatory}

    # ── §8 Political & Country Profile (field table) ──
    political_economic_orientation = models.TextField(blank=True, default='')
    political_strategic_priorities = models.TextField(blank=True, default='')

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} - {self.city}, {self.country}"

    @property
    def lat(self):
        coords = {
            'Los Angeles': 34.05, 'New York': 40.71, 'London': 51.5,
            'Paris': 48.85, 'Tokyo': 35.68, 'Singapore': 1.35,
            'Dubai': 25.2, 'Riyadh': 24.7, 'Sydney': -33.87,
            'Berlin': 52.52, 'Geneva': 46.2, 'Washington': 38.9,
            'Chicago': 41.88, 'San Francisco': 37.77, 'Miami': 25.76,
        }
        return coords.get(self.city, 0)

    @property
    def lon(self):
        coords = {
            'Los Angeles': -118.24, 'New York': -74.0, 'London': -0.12,
            'Paris': 2.35, 'Tokyo': 139.69, 'Singapore': 103.82,
            'Dubai': 55.27, 'Riyadh': 46.72, 'Sydney': 151.21,
            'Berlin': 13.4, 'Geneva': 6.15, 'Washington': -77.04,
            'Chicago': -87.63, 'San Francisco': -122.41, 'Miami': -80.19,
        }
        return coords.get(self.city, 0)


class UserProfile(models.Model):
    """Extends Django User with SFDA-specific fields."""
    user       = models.OneToOneField('auth.User', on_delete=models.CASCADE, related_name='profile')
    job_title  = models.CharField(max_length=300, blank=True)
    department = models.CharField(max_length=300, blank=True)

    def __str__(self):
        return f"Profile({self.user.email})"
