from django.contrib import admin
from .models import EmailOTP, UserLoginRecord, Profile

@admin.register(EmailOTP)
class EmailOTPAdmin(admin.ModelAdmin):
    list_display = ('user', 'otp_code', 'created_at', 'is_verified')
    list_filter = ('is_verified', 'created_at')
    search_fields = ('user__username', 'otp_code')

@admin.register(UserLoginRecord)
class UserLoginRecordAdmin(admin.ModelAdmin):
    list_display = ('user', 'login_time')
    search_fields = ('user__username',)

@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'first_name', 'last_name', 'username', 'created_at', 'updated_at')
    search_fields = ('user__username', 'first_name', 'last_name', 'username')
