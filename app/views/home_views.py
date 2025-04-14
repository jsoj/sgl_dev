from django.shortcuts import render
from django.contrib.auth.decorators import login_required

@login_required
def home(request):
    """View para a página inicial do site"""
    # Contexto básico para a página inicial
    context = {
        'title': 'Página Inicial',
    }
    
    return render(request, 'home.html', context)