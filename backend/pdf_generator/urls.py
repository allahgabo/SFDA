from django.urls import path
from .views import GenerateMilkenPDFView, GetDefaultDataView

urlpatterns = [
    path('generate-pdf/', GenerateMilkenPDFView.as_view(), name='generate-pdf'),
    path('default-data/', GetDefaultDataView.as_view(), name='default-data'),
]
