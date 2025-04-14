from django.shortcuts import redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout

@login_required
def logout_view(request):
    """View para realizar logout"""
    logout(request)
    return redirect('login')