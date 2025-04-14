from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from rest_framework import viewsets
from rest_framework import permissions
from app.serializers import UserSerializer, GroupSerializer
from app.models import Projeto, Placa96, Empresa, Placa1536

User = get_user_model()

class UserViewSet(viewsets.ModelViewSet):
    """API endpoint que permite visualizar ou editar usuários."""
    queryset = User.objects.all().order_by('-date_joined')
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

class GroupViewSet(viewsets.ModelViewSet):
    """API endpoint que permite visualizar ou editar grupos."""
    queryset = Group.objects.all()
    serializer_class = GroupSerializer
    permission_classes = [permissions.IsAuthenticated]

@login_required
def get_projetos(request, empresa_id):
    """API endpoint para buscar projetos de uma empresa"""
    try:
        if not request.user.is_superuser and request.user.empresa.id != empresa_id:
            return JsonResponse({'error': 'Sem permissão'}, status=403)
            
        projetos = Projeto.objects.filter(
            empresa_id=empresa_id,
            ativo=True
        ).values('id', 'codigo_projeto', 'nome_projeto_cliente')
        
        projetos_list = [
            {
                'id': projeto['id'],
                'text': f"{projeto['codigo_projeto']} - {projeto['nome_projeto_cliente'] or 'Sem nome'}"
            }
            for projeto in projetos
        ]
        
        return JsonResponse({'results': projetos_list})
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)

@login_required
def get_placas_96(request, projeto_id):
    """API endpoint para buscar placas 96 de um projeto"""
    try:
        projeto = Projeto.objects.get(id=projeto_id)
        
        # Verificar permissões
        if not request.user.is_superuser and projeto.empresa not in request.user.empresas.all():
            return JsonResponse({'error': 'Sem permissão para este projeto'}, status=403)
            
        # Buscar placas 96 disponíveis (não transferidas para 384)
        placas = Placa96.objects.filter(
            projeto_id=projeto_id,
            transferida_para_384=False
        ).values('id', 'codigo_placa', 'nome')
        
        placas_list = [
            {
                'id': placa['id'],
                'text': f"{placa['codigo_placa']} - {placa['nome']}"
            }
            for placa in placas
        ]
        
        return JsonResponse({'results': placas_list})
        
    except Projeto.DoesNotExist:
        return JsonResponse({'error': 'Projeto não encontrado'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)

@login_required
def get_placas_1536(request, projeto_id):
    """API endpoint para buscar placas 1536 de um projeto específico"""
    try:
        projeto = Projeto.objects.get(id=projeto_id)
        
        # Verificar permissões
        if not request.user.is_superuser and projeto.empresa not in request.user.empresas.all():
            return JsonResponse({'error': 'Sem permissão para este projeto'}, status=403)
        
        # Buscar placas 1536 do projeto
        if request.user.is_superuser:
            placas = Placa1536.objects.filter(
                projeto_id=projeto_id,
                is_active=True
            ).values('id', 'codigo_placa')
        else:
            placas = Placa1536.objects.filter(
                projeto_id=projeto_id,
                empresa=request.user.empresa,
                is_active=True
            ).values('id', 'codigo_placa')
        
        return JsonResponse(list(placas), safe=False)
        
    except Projeto.DoesNotExist:
        return JsonResponse({'error': 'Projeto não encontrado'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)

@login_required
def verificar_projeto(request):
    """API para verificar se já existe um projeto com o mesmo código para uma empresa"""
    empresa_id = request.GET.get('empresa_id')
    codigo_projeto = request.GET.get('codigo_projeto')
    
    if not empresa_id or not codigo_projeto:
        return JsonResponse({
            'exists': False,
            'error': 'Empresa ID e código do projeto são necessários'
        })
    
    try:
        # Verificar se o projeto existe
        projeto_existente = Projeto.objects.filter(
            empresa_id=empresa_id,
            codigo_projeto=codigo_projeto
        ).exists()
        
        empresa_nome = ""
        if projeto_existente:
            empresa = Empresa.objects.get(id=empresa_id)
            empresa_nome = empresa.nome
            
        return JsonResponse({
            'exists': projeto_existente,
            'empresa_nome': empresa_nome
        })
    except Exception as e:
        return JsonResponse({
            'exists': False,
            'error': str(e)
        })