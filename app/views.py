# views.py

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.contrib import messages
from django.db import transaction
from django.core.exceptions import ValidationError, PermissionDenied
from django.http import JsonResponse, HttpResponse
import logging
from django.contrib import admin

from rest_framework import permissions, viewsets
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Placa384, Projeto, Placa96, Empresa, Placa1536
from .forms import TransferPlacasForm
from .serializers import GroupSerializer, UserSerializer

User = get_user_model()

logger = logging.getLogger(__name__)

class UserViewSet(viewsets.ModelViewSet):
    """
    API endpoint que permite visualizar ou editar usuários.
    """
    queryset = User.objects.all().order_by('-date_joined')
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

class GroupViewSet(viewsets.ModelViewSet):
    """
    API endpoint que permite visualizar ou editar grupos.
    """
    queryset = Group.objects.all()
    serializer_class = GroupSerializer
    permission_classes = [permissions.IsAuthenticated]

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def protected_view(request):
    return Response({"message": "Bem-vindo, você está autenticado!"})

class ProtectedView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response({"message": "Bem-vindo, você está autenticado!"})



@login_required
def get_placas_96(request, projeto_id):
    """
    Retorna todas as placas 96 ativas de um projeto específico.
    """
    try:
        # Filtra placas ativas do projeto que não foram usadas em transferências
        placas = Placa96.objects.filter(
            projeto_id=projeto_id,
            is_active=True
        ).values('id', 'codigo_placa')
        
        return JsonResponse(list(placas), safe=False)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)

@login_required
def transferir_96_384(request):
    """
    View para transferência de 4 placas de 96 poços para uma placa de 384 poços.
    """
    logger.info(f"Iniciando transferência para projeto {form.cleaned_data['projeto'].codigo_projeto}, código placa: {form.cleaned_data['codigo_placa_384']}")
    if request.method == 'POST':
        form = TransferPlacasForm(request.user, request.POST)
        if form.is_valid():
            try:
                with transaction.atomic():
                    logger.info(f"Verificando se existe placa: empresa={form.cleaned_data['empresa'].codigo}, projeto={form.cleaned_data['projeto'].codigo_projeto}, codigo_placa={form.cleaned_data['codigo_placa_384']}")
                    # Criar nova placa 384
                    placa_384 = Placa384.objects.create(
                        empresa=form.cleaned_data['empresa'],
                        projeto=form.cleaned_data['projeto'],
                        codigo_placa=form.cleaned_data['codigo_placa_384']
                    )
                    logger.info(f"Placa 384 criada com sucesso: {placa_384.id}")

                    # Realizar transferência
                    placas_96 = [
                        form.cleaned_data['placa_1'],
                        form.cleaned_data['placa_2'],
                        form.cleaned_data['placa_3'],
                        form.cleaned_data['placa_4']
                    ]
                    logger.info(f"Iniciando transferência para placas: {[p.codigo_placa for p in placas_96 if p]}")
                    placa_384.transfer_96_to_384(placas_96)
                    
                    messages.success(request, 'Transferência realizada com sucesso!')
                    return redirect('admin:app_placa384_change', placa_384.id)
                    
            except ValidationError as e:
                messages.error(request, str(e))
            except Exception as e:
                messages.error(request, f'Erro inesperado: {str(e)}')
                logger.error(f"Erro na transferência: {str(e)}", exc_info=True)

            messages.error(request, f'Erro inesperado: {str(e)}')
            # Em caso de erro, redireciona de volta para o formulário
            return redirect('admin:app_placa384_transferir_96_384')
    else:
        form = TransferPlacasForm(user=request.user)
    
    context = {
        'form': form,
        'title': 'Transferir Placas 96 para 384',
        'opts': Placa384._meta,  # Necessário para o template admin
        **admin.site.each_context(request),  # Contexto padrão do admin
    }
    
    return render(request, 'admin/app/placa384/transferir_96_384.html', context)

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.db import transaction
from django.core.exceptions import ValidationError
from .models import Empresa, Projeto, Placa96, Placa384
import logging

logger = logging.getLogger(__name__)

@login_required
def home(request):
    """Página inicial após o login"""
    return render(request, 'base.html')

@login_required
def criar_projeto(request):
    """View para criação de projetos"""
    # Implementar lógica de criação de projeto
    return render(request, 'criar_projeto.html')

@login_required
def criar_placa_384(request):
    """
    View para criar uma placa 384 a partir de placas 96 selecionadas.
    """
    if request.method != 'POST':
        return HttpResponse("Método não permitido", status=405)
    
    try:
        # Obter IDs das placas selecionadas
        placa_ids = request.POST.getlist('placas_selecionadas')
        
        if not placa_ids:
            return render(request, 'partials/resultado_criacao_placa.html', {
                'sucesso': False,
                'mensagem': 'Nenhuma placa 96 foi selecionada.'
            })
        
        # Obter as placas pelo ID
        placas_96 = Placa96.objects.filter(id__in=placa_ids)
        
        if not placas_96.exists():
            return render(request, 'partials/resultado_criacao_placa.html', {
                'sucesso': False,
                'mensagem': 'Placas não encontradas.'
            })
            
        if placas_96.count() > 4:
            return render(request, 'partials/resultado_criacao_placa.html', {
                'sucesso': False,
                'mensagem': 'Só é possível transferir até 4 placas 96 para uma placa 384.'
            })
        
        # Todas as placas devem ser do mesmo projeto
        projeto = placas_96.first().projeto
        if placas_96.exclude(projeto=projeto).exists():
            return render(request, 'partials/resultado_criacao_placa.html', {
                'sucesso': False,
                'mensagem': 'Todas as placas devem pertencer ao mesmo projeto.'
            })
        
        # Criar a placa 384
        empresa = projeto.empresa
        codigo_placa = f"384-{projeto.codigo_projeto}-{Placa384.objects.filter(projeto=projeto).count() + 1:03d}"
        
        placa_384 = Placa384.objects.create(
            empresa=empresa,
            projeto=projeto,
            codigo_placa=codigo_placa
        )
        
        # Transferir placas 96 para a placa 384
        placa_384.transfer_96_to_384(placas_96)
        
        return render(request, 'partials/resultado_criacao_placa.html', {
            'sucesso': True,
            'placa_384': placa_384,
            'placas_96': placas_96
        })
        
    except Exception as e:
        traceback.print_exc()
        return render(request, 'partials/resultado_criacao_placa.html', {
            'sucesso': False,
            'mensagem': f'Erro ao criar placa 384: {str(e)}'
        })

@login_required
def criar_placa_384_htmx(request):
    """
    View para exibir o formulário inicial de criação de placas 384 usando HTMX.
    Mostra as empresas disponíveis para o usuário logado.
    """
    # Obtém as empresas que o usuário tem acesso
    if request.user.is_superuser:
        empresas = Empresa.objects.all()
    else:
        empresas = request.user.empresas.all()
    
    context = {
        'empresas': empresas
    }
    
    return render(request, 'criar_placas_384_htmx.html', context)

@login_required
def carregar_projetos_por_empresa(request):
    """
    Endpoint HTMX para carregar projetos baseado na empresa selecionada
    """
    empresa_id = request.GET.get('empresa_id')
    if not empresa_id:
        return HttpResponse("<div class='alert alert-danger'>Selecione uma empresa</div>")
    
    try:
        empresa = Empresa.objects.get(id=empresa_id)
        # Verificar se o usuário tem acesso à empresa
        if not request.user.is_superuser and empresa not in request.user.empresas.all():
            return HttpResponse("<div class='alert alert-danger'>Acesso negado</div>")
        
        # Obter projetos da empresa
        projetos = Projeto.objects.filter(empresa=empresa)
        
        return render(request, 'partials/projetos_dropdown.html', {'projetos': projetos})
    
    except Empresa.DoesNotExist:
        return HttpResponse("<div class='alert alert-danger'>Empresa não encontrada</div>")


@login_required
def carregar_placas_por_projeto(request):
    """
    View para carregar placas 96 de um projeto selecionado via HTMX.
    """
    projeto_id = request.GET.get('projeto')
    placas_96 = []
    
    if projeto_id:
        try:
            # Buscar as placas 96 do projeto selecionado
            placas_96 = Placa96.objects.filter(
                projeto_id=projeto_id,
                is_active=True
            ).order_by('codigo_placa')
            
            # Verificar se essas placas já foram usadas em alguma placa 384
            # Para evitar exibir placas que já foram transferidas
            from app.models import PlacaMap384
            placas_usadas = PlacaMap384.objects.filter(
                placa_origem__in=placas_96
            ).values_list('placa_origem_id', flat=True)
            
            # Filtrar apenas placas que não foram usadas
            placas_96 = placas_96.exclude(id__in=placas_usadas)
            
        except Exception as e:
            print(f"Erro ao carregar placas 96 do projeto {projeto_id}: {e}")
    
    return render(request, 'partials/placas_96_listagem.html', {
        'placas_96': placas_96
    })


# views.py

from django.http import JsonResponse
from django.contrib.admin.views.decorators import staff_member_required
from .models import Placa1536

@staff_member_required
def get_placas_1536(request, projeto_id):
    """
    API endpoint para buscar placas 1536 de um projeto específico
    """
    if not request.user.is_superuser and projeto_id:
        # Verificar se o projeto pertence à empresa do usuário
        placas = Placa1536.objects.filter(
            projeto_id=projeto_id,
            empresa=request.user.empresa,
            is_active=True
        ).values('id', 'codigo_placa')
    else:
        placas = Placa1536.objects.filter(
            projeto_id=projeto_id,
            is_active=True
        ).values('id', 'codigo_placa')
    
    return JsonResponse(list(placas), safe=False)

# urls.py

from django.urls import path
from . import views

urlpatterns = [
    path(
        'admin/api/placas-1536/<int:projeto_id>/',
        views.get_placas_1536,
        name='api-placas-1536'
    ),
    path(
        'htmx/carregar-placas-por-projeto/',
        views.carregar_placas_por_projeto,
        name='carregar-placas-por-projeto'
    ),
]