from django.contrib import admin
from django.urls import path, include, re_path
from django.views.generic import TemplateView
from django.conf import settings
from django.conf.urls.static import static

def react_index(request, path=''):
    """Serve React's index.html for all non-API routes (client-side routing)."""
    from django.http import FileResponse, Http404
    index = settings.BASE_DIR / 'frontend_build' / 'index.html'
    if index.exists():
        return FileResponse(open(index, 'rb'), content_type='text/html')
    # Fallback: 404 with helpful message if frontend not built yet
    from django.http import HttpResponse
    return HttpResponse(
        '<h2>Frontend not built.</h2><p>Run <code>npm run build</code> in the frontend folder.</p>',
        status=404
    )

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('reports_app.urls')),
    # React Router catch-all — must be last
    re_path(r'^(?!api/|admin/|static/|media/).*$', react_index),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
