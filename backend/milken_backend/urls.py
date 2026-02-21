from django.urls import path, include

urlpatterns = [
    path('api/', include('pdf_generator.urls')),
]
