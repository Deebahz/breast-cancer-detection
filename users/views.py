from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.core.mail import send_mail
from .models import EmailOTP, UserLoginRecord, Profile
from core.models import MedicalReport, Prediction
from core.views import create_prediction_for_report
import datetime
from django.utils import timezone

@login_required
def upload_report(request):
    if request.method == 'POST':
        report_file = request.FILES.get('report_file')
        report_type = request.POST.get('report_type')
        notes = request.POST.get('notes', '').strip()
        report_name = request.POST.get('report_name', '').strip()
        patient_id = request.POST.get('patient_id', '').strip()

        # Validate file presence
        if not report_file:
            messages.error(request, 'Please select a file to upload.')
            return redirect('upload_report')

        # Validate file type
        allowed_extensions = ['.pdf', '.jpg', '.jpeg', '.png']
        file_extension = '.' + report_file.name.split('.')[-1].lower()
        if file_extension not in allowed_extensions:
            messages.error(request, 'Invalid file type. Only PDF, JPG, PNG files are allowed.')
            return redirect('upload_report')

        # Validate file size (10MB limit)
        max_size = 10 * 1024 * 1024  # 10MB in bytes
        if report_file.size > max_size:
            messages.error(request, 'File size too large. Maximum size is 10MB.')
            return redirect('upload_report')

        try:
            # Create MedicalReport instance
            medical_report = MedicalReport.objects.create(
                user=request.user,
                file=report_file,
                report_type=report_type,
                notes=notes,
                report_name=report_name if report_name else None,
                patient_id=patient_id if patient_id else None
            )

            # Create prediction for the report
            from django.conf import settings
            from core.views import create_prediction_for_report
            import os
            import torch

            # Load model path from settings
            model_path = getattr(settings, 'BREAST_CANCER_MODEL_PATH', None)
            if model_path and os.path.exists(model_path):
                # Optionally, you can reload the model here if needed
                pass
            else:
                messages.warning(request, 'Model path is not configured or model file not found. Using fallback.')

            prediction = create_prediction_for_report(medical_report)

            # Check if fallback model was used
            from core.views import model
            is_fallback = hasattr(model, '_is_fallback') and model._is_fallback

            if is_fallback:
                messages.warning(request, 'Report uploaded successfully! Using test model for prediction (random results). For accurate predictions, please ensure a trained model is available.')
            else:
                messages.success(request, 'Report uploaded successfully! Prediction has been generated.')
            return redirect('view_predictions')

        except Exception as e:
            messages.error(request, f'Error uploading report: {str(e)}')
            return redirect('upload_report')

    # GET request - show recent uploads
    recent_reports = MedicalReport.objects.filter(user=request.user).order_by('-uploaded_at')[:5]
    context = {
        'recent_reports': recent_reports
    }
    return render(request, 'users/upload_report.html', context)

@login_required
def view_predictions(request):
    try:
        import pytz
        from django.utils.timezone import localtime

        # Get filter parameters
        date_range = request.GET.get('date_range', 'all')
        risk_level = request.GET.get('risk_level', 'all')
        report_type_filter = request.GET.get('report_type', 'all')

        # Base queryset
        predictions = Prediction.objects.filter(report__user=request.user).select_related('report').order_by('-created_at')

        # Apply filters
        if date_range != 'all':
            from datetime import datetime, timedelta
            if date_range == 'last_30':
                cutoff = datetime.now() - timedelta(days=30)
            elif date_range == 'last_90':
                cutoff = datetime.now() - timedelta(days=90)
            elif date_range == 'last_year':
                cutoff = datetime.now() - timedelta(days=365)
            predictions = predictions.filter(created_at__gte=cutoff)

        if risk_level != 'all':
            predictions = predictions.filter(result=risk_level)

        if report_type_filter != 'all':
            predictions = predictions.filter(report__report_type=report_type_filter)

        # Convert created_at to local time
        import os
        local_tz = pytz.timezone(os.environ.get('TZ', 'UTC'))
        for prediction in predictions:
            prediction.created_at_local = localtime(prediction.created_at, local_tz)

        context = {
            'predictions': predictions,
            'date_range': date_range,
            'risk_level': risk_level,
            'report_type_filter': report_type_filter,
        }
        return render(request, 'users/view_predictions.html', context)
    except Exception as e:
        print(f"Error in view_predictions: {e}")
        import traceback
        traceback.print_exc()
        raise

@login_required
def interpretation(request):
    # Show the latest prediction of the logged-in user
    from core.models import Prediction
    prediction = Prediction.objects.filter(report__user=request.user).order_by('-created_at').first()
    context = {'prediction': prediction}
    return render(request, 'users/interpretation.html', context)

@login_required
def interpretation_detail(request, prediction_id):
    prediction = get_object_or_404(Prediction, id=prediction_id, report__user=request.user)
    context = {
        'prediction': prediction
    }
    return render(request, 'users/interpretation.html', context)

@login_required
def account_settings(request):
    try:
        # Get or create user profile
        profile, created = Profile.objects.get_or_create(
            user=request.user,
            defaults={
                'first_name': '',
                'last_name': '',
                'username': request.user.username
            }
        )

        if request.method == 'POST':
            action = request.POST.get('action')

            if action == 'update_profile':
                # Handle profile updates
                first_name = request.POST.get('first_name', '').strip()
                last_name = request.POST.get('last_name', '').strip()
                email = request.POST.get('email', '').strip()

                # Validate required fields
                if not first_name or not last_name:
                    messages.error(request, 'First name and last name are required.')
                    return redirect('account_settings')

                if not email:
                    messages.error(request, 'Email address is required.')
                    return redirect('account_settings')

                # Validate email format
                import re
                email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
                if not re.match(email_pattern, email):
                    messages.error(request, 'Please enter a valid email address.')
                    return redirect('account_settings')

                # Validate email uniqueness (if changed)
                if email != request.user.email:
                    if User.objects.filter(email=email).exclude(id=request.user.id).exists():
                        messages.error(request, 'Email already exists. Please use a different email.')
                        return redirect('account_settings')

                try:
                    # Update user email
                    request.user.email = email
                    request.user.save()

                    # Update profile
                    profile.first_name = first_name
                    profile.last_name = last_name
                    profile.save()

                    messages.success(request, 'Profile updated successfully!')
                    return redirect('account_settings')
                except Exception as e:
                    messages.error(request, f'Error updating profile: {str(e)}')
                    return redirect('account_settings')

            elif action == 'change_password':
                # Handle password changes
                current_password = request.POST.get('current_password')
                new_password = request.POST.get('new_password')
                confirm_password = request.POST.get('confirm_password')

                # Validate current password
                if not current_password:
                    messages.error(request, 'Current password is required.')
                    return redirect('account_settings')

                # Verify current password
                if not request.user.check_password(current_password):
                    messages.error(request, 'Current password is incorrect.')
                    return redirect('account_settings')

                # Validate new password
                if not new_password:
                    messages.error(request, 'New password is required.')
                    return redirect('account_settings')

                if len(new_password) < 8:
                    messages.error(request, 'New password must be at least 8 characters long.')
                    return redirect('account_settings')

                # Check password strength
                import re
                if not re.search(r'[A-Z]', new_password):
                    messages.error(request, 'New password must contain at least one uppercase letter.')
                    return redirect('account_settings')

                if not re.search(r'[a-z]', new_password):
                    messages.error(request, 'New password must contain at least one lowercase letter.')
                    return redirect('account_settings')

                if not re.search(r'\d', new_password):
                    messages.error(request, 'New password must contain at least one number.')
                    return redirect('account_settings')

                if new_password != confirm_password:
                    messages.error(request, 'New passwords do not match.')
                    return redirect('account_settings')

                # Check if new password is different from current
                if current_password == new_password:
                    messages.error(request, 'New password must be different from current password.')
                    return redirect('account_settings')

                try:
                    # Update password
                    request.user.set_password(new_password)
                    request.user.save()

                    # Update session to prevent logout
                    from django.contrib.auth import update_session_auth_hash
                    update_session_auth_hash(request, request.user)

                    messages.success(request, 'Password changed successfully!')
                    return redirect('account_settings')
                except Exception as e:
                    messages.error(request, f'Error changing password: {str(e)}')
                    return redirect('account_settings')

        # GET request - display current profile data
        context = {
            'profile': profile,
            'user': request.user,
        }
        return render(request, 'users/account_settings.html', context)

    except Exception as e:
        messages.error(request, f'An error occurred: {str(e)}')
        return redirect('account_settings')

def landing_page(request):
    return render(request, 'users/landingpage.html')

def about(request):
    return render(request, 'users/about.html')


def user_login(request):
    if request.method == "POST":
        try:
            username_or_email = request.POST.get('username_or_email')
            password = request.POST.get('password')
            user = None
            # Try to get user by username
            try:
                user = User.objects.get(username=username_or_email)
            except User.DoesNotExist:
                # Try to get user by email
                try:
                    user_obj = User.objects.get(email=username_or_email)
                    user = user_obj
                except User.DoesNotExist:
                    user = None
            if user is not None:
                user = authenticate(request, username=user.username, password=password)
            if user is not None:
                # Generate OTP and send email
                otp_code = EmailOTP.generate_otp()
                EmailOTP.objects.create(user=user, otp_code=otp_code)
                send_mail(
                    'Your Login OTP',
                    f'Your OTP code is {otp_code}',
                    'no-reply@cancermamo.com',
                    [user.email],
                    fail_silently=False,
                )
                request.session['otp_user_id'] = user.id
                return redirect('verify_otp')
            else:
                return render(request, 'users/login.html', {'error': 'Invalid credentials'})
        except Exception as e:
            import traceback
            traceback.print_exc()
            return render(request, 'users/login.html', {'error': f'An error occurred: {str(e)}'})
    return render(request, 'users/login.html')

@login_required
def dashboard(request):
    return render(request, 'users/dashboard.html')

def user_logout(request):
    logout(request)
    return redirect('landing_page')

def user_register(request):
    if request.method == "POST":
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')

        # Check if username already exists
        if User.objects.filter(username=username).exists():
            return render(request, 'users/register.html', {'error': 'Username already exists'})

        # Check if email already exists
        if User.objects.filter(email=email).exists():
            return render(request, 'users/register.html', {'error': 'Email already exists'})

        # Store registration data in session instead of creating user immediately
        request.session['registration_first_name'] = first_name
        request.session['registration_last_name'] = last_name
        request.session['registration_username'] = username
        request.session['registration_email'] = email
        request.session['registration_password'] = password

        # Generate OTP and send email without user object
        otp_code = EmailOTP.generate_otp()
        request.session['registration_otp'] = otp_code
        request.session['registration_otp_created_at'] = timezone.now()
        send_mail(
            'Your Registration OTP',
            f'Your OTP code is {otp_code}',
            'no-reply@cancermamo.com',
            [email],
            fail_silently=False,
        )
        return redirect('verify_otp')
    return render(request, 'users/register.html')

def verify_otp(request):
    user_id = request.session.get('otp_user_id')
    registration_email = request.session.get('registration_email')
    registration_password = request.session.get('registration_password')
    registration_username = request.session.get('registration_username')
    registration_first_name = request.session.get('registration_first_name')
    registration_last_name = request.session.get('registration_last_name')
    registration_otp = request.session.get('registration_otp')
    user = None
    if user_id:
        user = User.objects.get(id=user_id)
    if request.method == "POST":
        otp_input = request.POST.get('otp')
        if user:
            # OTP verification for login
            try:
                otp_record = EmailOTP.objects.filter(user=user, otp_code=otp_input, is_verified=False).latest('created_at')
                if otp_record.is_expired():
                    messages.error(request, 'OTP expired. Please request a new one.')
                    return redirect('login')
                otp_record.is_verified = True
                otp_record.save()

                # Clean up old OTPs for this user
                EmailOTP.objects.filter(
                    user=user,
                    is_verified=False
                ).exclude(id=otp_record.id).delete()

                login(request, user)
                # Send login confirmation email
                send_mail(
                    'Login Successful',
                    'You have successfully logged in to CancerMamo.',
                    'no-reply@cancermamo.com',
                    [user.email],
                    fail_silently=True,
                )
                return redirect('dashboard')
            except EmailOTP.DoesNotExist:
                messages.error(request, 'Invalid OTP. Please try again.')
        elif registration_email and registration_password and registration_otp:
            # OTP verification for registration
            # Check expiration for registration OTP (10 minutes)
            otp_created_time = request.session.get('registration_otp_created_at')
            if otp_created_time:
                otp_age = timezone.now() - otp_created_time
                if otp_age.total_seconds() > 600:
                    messages.error(request, 'OTP expired. Please request a new one.')
                    return redirect('register')
            if otp_input == registration_otp:
                # Create user after successful OTP verification
                user = User.objects.create_user(username=registration_username, password=registration_password, email=registration_email)

                # Create and populate Profile
                Profile.objects.create(
                    user=user,
                    first_name=registration_first_name,
                    last_name=registration_last_name,
                    username=registration_username
                )

                # Mark OTP as verified in DB
                EmailOTP.objects.create(user=user, otp_code=otp_input, is_verified=True)

                # Clean up any old OTPs for this user
                EmailOTP.objects.filter(
                    user=user,
                    is_verified=False
                ).delete()

                login(request, user)
                # Clear registration session data
                del request.session['registration_first_name']
                del request.session['registration_last_name']
                del request.session['registration_username']
                del request.session['registration_email']
                del request.session['registration_password']
                del request.session['registration_otp']
                del request.session['registration_otp_created_at']
                # Send registration confirmation email
                send_mail(
                    'Good News: Registration Successful',
                    'Dear, You have successfully registered at CancerMamo.',
                    'no-reply@cancermamo.com',
                    [registration_email],
                    fail_silently=True,
                )
                return redirect('dashboard')
            else:
                messages.error(request, 'Invalid OTP. Please try again.')
        else:
            messages.error(request, 'Session expired or invalid. Please try again.')
            return redirect('register')
    return render(request, 'users/verify_otp.html')

from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.models import User
from django.utils.dateparse import parse_date
from django.db.models import Count
from django.http import HttpResponseRedirect
from django.urls import reverse

def about(request):
    return render(request, 'users/about.html')


#Admin user management view
@staff_member_required
def admin_user_management(request):
    # Get date range from GET parameters
    start_date_str = request.GET.get('start_date')
    end_date_str = request.GET.get('end_date')
    start_date = parse_date(start_date_str) if start_date_str else None
    end_date = parse_date(end_date_str) if end_date_str else None

    # Filter UserLoginRecord by date range
    login_records = UserLoginRecord.objects.all()
    if start_date:
        login_records = login_records.filter(login_time__date__gte=start_date)
    if end_date:
        login_records = login_records.filter(login_time__date__lte=end_date)

    # Aggregate login counts per user
    user_login_counts = login_records.values('user__id', 'user__username', 'user__email').annotate(login_count=Count('id')).order_by('-login_count')

    # Handle user deletion
    if request.method == 'POST':
        user_id_to_delete = request.POST.get('delete_user_id')
        if user_id_to_delete:
            try:
                user_to_delete = User.objects.get(id=user_id_to_delete)
                user_to_delete.delete()
                return HttpResponseRedirect(reverse('admin_user_management'))
            except User.DoesNotExist:
                pass

    context = {
        'user_login_counts': user_login_counts,
        'start_date': start_date_str,
        'end_date': end_date_str,
    }
    return render(request, 'users/admin_user_management.html', context)
from django import template
register = template.Library()
@register.filter
def sum_field(queryset, field_name):
    """Sum a specific field from a queryset of dictionaries"""
    return sum(int(item[field_name]) for item in queryset if field_name in item)
