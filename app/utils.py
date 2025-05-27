from django.http import JsonResponse
from app.models import Empresa, Projeto, Placa96, Placa384

def carregar_projetos_por_empresa(request):
    """Carrega os projetos associados a uma empresa."""
    empresa_id = request.GET.get('empresa')
    
    if not empresa_id:
        return JsonResponse({'error': 'Empresa não especificada.'}, status=400)
    
    try:
        empresa = Empresa.objects.get(id=empresa_id)
        
        # Verifica se o usuário tem acesso à empresa
        if not request.user.is_superuser and empresa not in request.user.empresas.all():
            return JsonResponse({'error': 'Você não tem permissão para acessar esta empresa.'}, status=403)
        
        # Obtém os projetos da empresa
        projetos = Projeto.objects.filter(empresa=empresa, ativo=True).order_by('codigo_projeto')
        projetos_data = [{'id': projeto.id, 'nome': projeto.codigo_projeto} for projeto in projetos]
        return JsonResponse({'projetos': projetos_data})
    
    except Empresa.DoesNotExist:
        return JsonResponse({'error': 'Empresa não encontrada.'}, status=404)
    except Exception as e:
        return JsonResponse({'error': f'Erro ao carregar projetos: {str(e)}'}, status=500)

def carregar_placas_por_projeto(request):
    """Carrega as placas ativas de um projeto selecionado."""
    projeto_id = request.GET.get('projeto')
    
    if not projeto_id:
        return JsonResponse({'error': 'Projeto não especificado.'}, status=400)
    
    try:
        projeto = Projeto.objects.get(id=projeto_id)
        
        # Verifica se o usuário tem acesso ao projeto
        if not request.user.is_superuser and projeto.empresa not in request.user.empresas.all():
            return JsonResponse({'error': 'Você não tem permissão para acessar este projeto.'}, status=403)
        
        # Obtém as placas 96 ou 384 ativas do projeto
        placas_96 = Placa96.objects.filter(projeto=projeto, is_active=True).order_by('codigo_placa')
        placas_data = [{'id': placa.id, 'codigo': placa.codigo_placa} for placa in placas_96]
        return JsonResponse({'placas': placas_data})
    
    except Projeto.DoesNotExist:
        return JsonResponse({'error': 'Projeto não encontrado.'}, status=404)
    except Exception as e:
        return JsonResponse({'error': f'Erro ao carregar placas: {str(e)}'}, status=500)
