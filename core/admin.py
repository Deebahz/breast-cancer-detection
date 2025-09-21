from django.contrib import admin
from .models import MedicalReport, Prediction

@admin.register(MedicalReport)
class MedicalReportAdmin(admin.ModelAdmin):
    list_display = ('user', 'report_name', 'report_type', 'patient_id', 'uploaded_at')
    search_fields = ('user__username', 'report_name', 'patient_id')
    list_filter = ('report_type', 'uploaded_at')

@admin.register(Prediction)
class PredictionAdmin(admin.ModelAdmin):
    list_display = ('report', 'result', 'confidence', 'created_at')
    search_fields = ('report__report_name', 'result')
    list_filter = ('result', 'created_at')
