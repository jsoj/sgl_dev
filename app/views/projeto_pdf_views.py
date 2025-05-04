from django.http import HttpResponse
from app.models import Projeto
from app.project_pdf import generate_project_pdf  # Importa a função que corrigimos
from django.contrib.auth.decorators import login_required

@login_required
def projeto_pdf_view(request, projeto_id):
    try:
        projeto = Projeto.objects.get(id=projeto_id)
        
        # Gera o PDF e obtém o nome do arquivo
        pdf, nome_arquivo = generate_project_pdf(projeto)
        
        # Configura a resposta HTTP 
        response = HttpResponse(pdf, content_type='application/pdf')
        
        # Se não for uma solicitação AJAX, configura para download
        if not request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            response['Content-Disposition'] = f'attachment; filename="{nome_arquivo}"'
        
        return response
    except Projeto.DoesNotExist:
        return HttpResponse("Projeto não encontrado", status=404)

@login_required
def projeto_pdf_download(request, projeto_id):
    try:
        projeto = Projeto.objects.get(id=projeto_id)
        
        # Gera o PDF e obtém o nome do arquivo
        pdf, nome_arquivo = generate_project_pdf(projeto)
        
        # Configura a resposta HTTP para forçar o download
        response = HttpResponse(pdf, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="{nome_arquivo}"'
        
        # Adiciona cabeçalhos para evitar cache
        response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        response['Pragma'] = 'no-cache'
        response['Expires'] = '0'
        
        return response
    except Projeto.DoesNotExist:
        return HttpResponse("Projeto não encontrado", status=404)