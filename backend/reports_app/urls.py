from django.urls import path
from . import views
from . import auth_views

urlpatterns = [
    # ── Auth endpoints ────────────────────────────────────────────
    path('auth/login/',   auth_views.LoginView.as_view(),          name='auth-login'),
    path('auth/signup/',  auth_views.SignupView.as_view(),         name='auth-signup'),
    path('auth/forgot/',  auth_views.ForgotPasswordView.as_view(), name='auth-forgot'),
    path('auth/logout/',  auth_views.LogoutView.as_view(),         name='auth-logout'),
    path('auth/me/',      auth_views.MeView.as_view(),             name='auth-me'),

    # ── Reports endpoints ─────────────────────────────────────────
    path('health/',                           views.HealthCheckView.as_view(),       name='health'),
    path('reports/',                          views.ReportListView.as_view(),        name='report-list'),
    path('reports/<int:pk>/',                 views.ReportDetailView.as_view(),      name='report-detail'),
    path('reports/<int:pk>/generate/',        views.GenerateAIContentView.as_view(), name='generate-ai'),
    path('reports/<int:pk>/pdf/',             views.GeneratePDFView.as_view(),       name='generate-pdf'),
    path('reports/<int:pk>/pdf/inline/',      views.InlinePDFView.as_view(),         name='inline-pdf'),
    path('reports/<int:pk>/preview/',         views.PreviewHTMLView.as_view(),       name='preview-html'),
    path('assistant/',                        views.AIAssistantView.as_view(),       name='ai-assistant'),
    path('stats/',                            views.DashboardStatsView.as_view(),    name='dashboard-stats'),
]
