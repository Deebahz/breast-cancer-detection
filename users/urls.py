from django.urls import path
from . import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('login/', views.user_login, name='login'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('logout/', views.user_logout, name='logout'),
    path('landingpage/', views.landing_page, name='landingpage'),
    path('register/', views.user_register, name='register'),  # Added registration path
    path('verify_otp/', views.verify_otp, name='verify_otp'),
    path('', views.landing_page, name='home'),
    path('upload_report/', views.upload_report, name='upload_report'),
    path('view_predictions/', views.view_predictions, name='view_predictions'),
    path('interpretation/', views.interpretation, name='interpretation'),
    path('interpretation/<int:prediction_id>/', views.interpretation_detail, name='interpretation_detail'),
    path('account_settings/', views.account_settings, name='account_settings'),
    path('about/', views.about, name='about'),
    path('admin/user-management/', views.admin_user_management, name='admin_user_management'),
    path('contact/', views.contact_view, name='contact'),

    # Password reset URLs
    path('login/reset_password/', views.CustomPasswordResetView.as_view(), name='password_reset'),
    path('login/password-reset/done/', views.CustomPasswordResetDoneView.as_view(), name='password_reset_done'),
    path('login/password-reset-confirm/<uidb64>/<token>/', views.CustomPasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('password-reset/complete/', views.CustomPasswordResetCompleteView.as_view(), name='password_reset_complete'),
]
