from django.db import models
from django.contrib.auth.models import User
import random
import string
import datetime
from django.utils import timezone
from django.dispatch import receiver
from django.contrib.auth.signals import user_logged_in

class EmailOTP(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    otp_code = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    is_verified = models.BooleanField(default=False)

    def is_expired(self):
        expiration_time = self.created_at + datetime.timedelta(minutes=10)
        return timezone.now() > expiration_time

    @staticmethod
    def generate_otp():
        return ''.join(random.choices(string.digits, k=6))

class UserLoginRecord(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    login_time = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} logged in at {self.login_time}"

@receiver(user_logged_in)
def log_user_login(sender, request, user, **kwargs):
    UserLoginRecord.objects.create(user=user)

# Create your models here.
