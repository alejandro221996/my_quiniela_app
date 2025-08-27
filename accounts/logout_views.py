from django.shortcuts import redirect
from django.contrib.auth import logout
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_protect

@login_required
@require_POST 
@csrf_protect
def custom_logout(request):
    """Vista personalizada para logout"""
    logout(request)
    return redirect('quinielas:home')
