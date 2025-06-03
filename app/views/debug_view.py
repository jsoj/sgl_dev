from django.http import HttpResponse
import sys
import os
import django

def debug_view(request):
    """
    View simples para diagnosticar problemas com o Django
    """
    output = []
    output.append(f"Python version: {sys.version}")
    output.append(f"Django version: {django.get_version()}")
    output.append(f"Working directory: {os.getcwd()}")
    output.append(f"Python path: {sys.path}")
    
    # Verificar configurações do Django
    from django.conf import settings
    output.append(f"DEBUG: {settings.DEBUG}")
    output.append(f"ALLOWED_HOSTS: {settings.ALLOWED_HOSTS}")
    output.append(f"MIDDLEWARE: {settings.MIDDLEWARE}")
    output.append(f"INSTALLED_APPS: {settings.INSTALLED_APPS}")
    
    # Verificar headers de requisição
    output.append("Request Headers:")
    for key, value in request.headers.items():
        output.append(f"  {key}: {value}")
    
    return HttpResponse("<br>".join(output), content_type="text/html")
