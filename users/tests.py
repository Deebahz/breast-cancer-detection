import tempfile
from django.test import TestCase, Client
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from core.models import MedicalReport, Prediction
from django.contrib.auth.models import User
import os

class UploadPredictionTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', password='testpass')
        self.client.login(username='testuser', password='testpass')

    def test_upload_report_and_prediction_creation(self):
        # Create a temporary image file
        image_path = os.path.join(os.path.dirname(__file__), 'test_image.jpg')
        with open(image_path, 'wb') as f:
            f.write(b'\x47\x49\x46\x38\x39\x61\x01\x00\x01\x00\x80\x00\x00\x00\x00\x00\xFF\xFF\xFF\x21\xF9\x04\x01\x00\x00\x00\x00\x2C\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02\x4C\x01\x00\x3B')

        with open(image_path, 'rb') as img:
            response = self.client.post(reverse('upload_report'), {
                'report_file': SimpleUploadedFile('test_image.jpg', img.read(), content_type='image/jpeg'),
                'report_type': 'mammogram',
                'notes': 'Test note'
            })

        self.assertEqual(response.status_code, 302)  # Redirect after upload
        self.assertTrue(MedicalReport.objects.filter(user=self.user).exists())
        report = MedicalReport.objects.filter(user=self.user).first()
        self.assertTrue(Prediction.objects.filter(report=report).exists())

    def test_view_predictions(self):
        response = self.client.get(reverse('view_predictions'))
        self.assertEqual(response.status_code, 200)
        self.assertIn('predictions', response.context)
