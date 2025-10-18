from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.contrib import messages
from django.core.mail import send_mail
from django.conf import settings
from .models import PasswordResetOTP
from .forms import ForgotPasswordForm, VerifyOTPForm, ResetPasswordForm
import random

# 1️⃣ Forgot password — send OTP
def forgot_password(request):
    if request.method == "POST":
        form = ForgotPasswordForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            try:
                user = User.objects.get(email=email)
                otp = str(random.randint(100000, 999999))
                PasswordResetOTP.objects.create(user=user, otp=otp)

                # Send email
                send_mail(
                    subject="Your Password Reset OTP",
                    message=f"Your OTP is {otp}. It is valid for 5 minutes.",
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[email],
                )

                request.session['reset_user_id'] = user.id
                messages.success(request, "OTP sent to your email.")
                return redirect('verify_otp')

            except User.DoesNotExist:
                messages.error(request, "No account found with this email.")
    else:
        form = ForgotPasswordForm()
    return render(request, 'forgot_password.html', {'form': form})


# 2️⃣ Verify OTP
def verify_otp(request):
    user_id = request.session.get('reset_user_id')
    if not user_id:
        return redirect('forgot_password')

    user = User.objects.get(id=user_id)
    if request.method == "POST":
        form = VerifyOTPForm(request.POST)
        if form.is_valid():
            otp = form.cleaned_data['otp']
            otp_obj = PasswordResetOTP.objects.filter(user=user, otp=otp, is_verified=False).last()
            if otp_obj and otp_obj.is_valid():
                otp_obj.is_verified = True
                otp_obj.save()
                request.session['otp_verified'] = True
                messages.success(request, "OTP verified! You can now reset your password.")
                return redirect('reset_password')
            else:
                messages.error(request, "Invalid or expired OTP.")
    else:
        form = VerifyOTPForm()
    return render(request, 'verify_otp.html', {'form': form})


# 3️⃣ Reset Password
from django.contrib.auth.hashers import make_password

def reset_password(request):
    user_id = request.session.get('reset_user_id')
    otp_verified = request.session.get('otp_verified', False)
    if not (user_id and otp_verified):
        return redirect('forgot_password')

    user = User.objects.get(id=user_id)
    if request.method == "POST":
        form = ResetPasswordForm(request.POST)
        if form.is_valid():
            new_password = form.cleaned_data['new_password']
            user.password = make_password(new_password)
            user.save()

            # Clear session and OTP
            request.session.pop('reset_user_id', None)
            request.session.pop('otp_verified', None)

            messages.success(request, "Password reset successful! You can now log in.")
            return redirect('login')
    else:
        form = ResetPasswordForm()
    return render(request, 'reset_password.html', {'form': form})
