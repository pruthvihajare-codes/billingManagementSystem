from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.contrib.auth import get_user_model
from billing.models import *
from django.utils import timezone
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout
from django.shortcuts import redirect
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.http import HttpResponse

def auth(request):
    try:
        if request.method == "POST":
            if 'signup' in request.POST:
                email = request.POST['email']
                password = request.POST['password']
                confirm_password = request.POST['confirm_password']
                full_name = request.POST['full_name']  # Get full name from the form

                if password != confirm_password:
                    return render(request, 'Account/auth.html', {
                        'error': "Passwords do not match", 
                        'alert': True,
                        'title':"Check Your Password"
                    })

                if User.objects.filter(email=email).exists():
                    return render(request, 'Account/auth.html', {
                        'error': "Email already registered", 
                        'alert': True ,
                        'switch_to': 'login',
                        'title':"Confirm EmailId"
                    })

                user = User.objects.create_user(email=email, password=password, full_name=full_name)  # Pass full_name here
                PasswordReal.objects.create(email=email, plain_password=password)
                login(request, user)
                return redirect('dashboard')

            elif 'login' in request.POST:
                email = request.POST['email']
                password = request.POST['password']
                user = authenticate(request, email=email, password=password)
                if user:
                    login(request, user)
                    return redirect('dashboard')  
                else:
                    return render(request, 'Account/auth.html', {
                        'error': "Invalid login credentials", 
                        'alert': True,
                        'title':"Please Check Credentials"
                    })

        return render(request, 'Account/auth.html')

    except Exception as e:
        print(f"Error: {e}")
        return render(request, 'Shared/404.html', status=404)

def logout_view(request):
    logout(request)  # Django's built-in logout function
    return redirect('auth')  # Redirect to the login page after logout

@login_required
def dashboard(request):
    return redirect('orderDetailIndex')  # Use the name of the URL pattern here
