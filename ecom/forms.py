from django import forms

class ForgotPasswordForm(forms.Form):
    email = forms.EmailField(label="Enter your registered email")

class VerifyOTPForm(forms.Form):
    otp = forms.CharField(label="Enter OTP", max_length=6)

class ResetPasswordForm(forms.Form):
    new_password = forms.CharField(widget=forms.PasswordInput)
    confirm_password = forms.CharField(widget=forms.PasswordInput)

    def clean(self):
        cleaned_data = super().clean()
        if cleaned_data.get("new_password") != cleaned_data.get("confirm_password"):
            raise forms.ValidationError("Passwords do not match")
        return cleaned_data
