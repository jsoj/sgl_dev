from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from app.models import Projeto

@login_required
def listar_projetos_por_empresa(request):
    empresa_id = request.GET.get('empresa')
    
    if not empresa_id:
        return HttpResponse("<p>Selecione uma empresa para ver seus projetos</p>")
    
    # Buscar projetos da empresa
    projetos = Projeto.objects.filter(empresa_id=empresa_id, ativo=True)
    
    # Retornar apenas o HTML parcial com a lista de projetos
    return render(request, 'partials/lista_projetos.html', {'projetos': projetos})
