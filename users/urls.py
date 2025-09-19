from django.urls import path
from . import views

urlpatterns = [
    path('login/', views.user_login, name='login'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('logout/', views.user_logout, name='logout'),
    path('landing_page/', views.landing_page, name='landing'),
    path('register/', views.user_register, name='register'),  # Added registration path
    path('verify_otp/', views.verify_otp, name='verify_otp'),
    path('', views.landing_page, name='home'), 
    path('upload_report/', views.upload_report, name='upload_report'),
    path('view_predictions/', views.view_predictions, name='view_predictions'),
    path('interpretation/', views.interpretation, name='interpretation'),
    path('interpretation/<int:prediction_id>/', views.interpretation_detail, name='interpretation_detail'),
    path('account_settings/', views.account_settings, name='account_settings'),
    path('about/', views.about, name='about'),
    path('admin/user-management/', views.admin_user_management, name='admin_user_management')
]
