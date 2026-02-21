import io
import os
from datetime import datetime
from django.template.loader import render_to_string
from django.http import HttpResponse
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .serializers import MilkenReportSerializer

try:
    import weasyprint
    WEASYPRINT_AVAILABLE = True
except ImportError:
    WEASYPRINT_AVAILABLE = False


class GeneratePDFView(APIView):
    def post(self, request):
        serializer = MilkenReportSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        data = serializer.validated_data
        today = datetime.now().strftime('%Y-%m-%d')
        filename = f"Milken_Report_{today}.pdf"

        html_content = render_to_string('pdf_app/milken_report.html', {'data': data})

        if not WEASYPRINT_AVAILABLE:
            return Response(
                {'error': 'WeasyPrint not installed. Run: pip install WeasyPrint'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        pdf_buffer = io.BytesIO()
        weasyprint.HTML(string=html_content, base_url=request.build_absolute_uri('/')).write_pdf(pdf_buffer)
        pdf_buffer.seek(0)

        response = HttpResponse(pdf_buffer.read(), content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        response['Access-Control-Expose-Headers'] = 'Content-Disposition'
        return response


class PreviewHTMLView(APIView):
    """Returns HTML preview for development"""
    def post(self, request):
        serializer = MilkenReportSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        data = serializer.validated_data
        html_content = render_to_string('pdf_app/milken_report.html', {'data': data})
        return HttpResponse(html_content, content_type='text/html; charset=utf-8')
