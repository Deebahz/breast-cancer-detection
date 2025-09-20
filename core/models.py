from django.db import models
from django.contrib.auth.models import User
from django.core.files.storage import default_storage
import os

class MedicalReport(models.Model):
    REPORT_TYPES = [
        ('mammogram', 'Mammogram'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    file = models.FileField(upload_to='medical_reports/')
    grad_cam_image = models.ImageField(upload_to='grad_cam_images/', blank=True, null=True)
    report_name = models.CharField(max_length=255, blank=True, null=True, help_text="Name/identifier for this report")
    patient_id = models.CharField(max_length=100, blank=True, null=True, help_text="Patient unique identifier")
    report_type = models.CharField(max_length=20, choices=REPORT_TYPES, default='mammogram')
    notes = models.TextField(blank=True, null=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        report_name = self.report_name or f"Report {self.id}"
        return f"{self.user.username} - {report_name} - {self.uploaded_at.date()}"

    def delete(self, *args, **kwargs):
        # Delete the files from storage when the model is deleted
        if self.file:
            if default_storage.exists(self.file.name):
                default_storage.delete(self.file.name)
        if self.grad_cam_image:
            if default_storage.exists(self.grad_cam_image.name):
                default_storage.delete(self.grad_cam_image.name)
        super().delete(*args, **kwargs)


class Prediction(models.Model):
    RISK_LEVELS = [
        ('low', 'Low Risk'),
        ('medium', 'Medium Risk'),
        ('high', 'High Risk'),
    ]

    report = models.OneToOneField(MedicalReport, on_delete=models.CASCADE)
    result = models.CharField(max_length=20, choices=RISK_LEVELS, default='low')
    confidence = models.DecimalField(max_digits=5, decimal_places=2, help_text="Confidence percentage (0-100)")
    findings = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Prediction for {self.report} - {self.result} ({self.confidence}%)"

    @property
    def risk_color(self):
        if self.result == 'high':
            return 'danger'
        elif self.result == 'medium':
            return 'warning'
        else:
            return 'success'
