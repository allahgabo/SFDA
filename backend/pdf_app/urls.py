from django.urls import path
from .views import GeneratePDFView, PreviewHTMLView

urlpatterns = [
    path('generate-pdf/', GeneratePDFView.as_view(), name='generate-pdf'),
    path('preview-html/', PreviewHTMLView.as_view(), name='preview-html'),
]
