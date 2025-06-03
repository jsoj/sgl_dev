import os
import sys

# Add o diretório pai ao path
path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if path not in sys.path:
    sys.path.append(path)

def application(environ, start_response):
    """Aplicação WSGI simples para testar se o serviço está funcionando"""
    status = '200 OK'
    headers = [('Content-type', 'text/plain; charset=utf-8')]
    start_response(status, headers)
    
    message = "Aplicação WSGI de teste funcionando!\n\n"
    message += "Erro na aplicação principal: ModuleNotFoundError: No module named 'corsheaders'\n\n"
    message += "Para resolver:\n"
    message += "1. Instale o pacote: pip install django-cors-headers\n"
    message += "2. Ou remova as referências ao CORS do arquivo settings.py\n"
    
    return [message.encode('utf-8')]
