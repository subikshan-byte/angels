# ecom/views.py
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login,logout
from django.contrib import messages
from django.contrib.auth.models import User
def login_view(request):
    if request.method == "POST":
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('home')  # redirect to home after login
        else:
            messages.error(request, "Invalid username or password")
    return render(request, 'login.html')
def signup_view(request):
    if request.method == "POST":
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        username = request.POST.get('username')
        email = request.POST.get('email')
        password1 = request.POST.get('password1')
        password2 = request.POST.get('password2')

        if password1 != password2:
            messages.error(request, "Passwords do not match")
            return redirect('login')

        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already exists")
            return redirect('login')

        if User.objects.filter(email=email).exists():
            messages.error(request, "Email already exists")
            return redirect('login')

        user = User.objects.create_user(username=username, password=password1,
                                        email=email, first_name=first_name, last_name=last_name)
        user.save()
        messages.success(request, "Account created successfully")
        return redirect('login')

    return redirect('login')
def logout_view(request):
    logout(request)
    messages.success(request, "You have been logged out successfully")
    return redirect("login")