# from django.contrib.auth import get_user_model
# from django.contrib.auth.models import Group
# from rest_framework import permissions, viewsets
# from rest_framework.decorators import api_view, permission_classes
# from rest_framework.permissions import IsAuthenticated
# from rest_framework.response import Response
# from rest_framework.views import APIView

# from .serializers import GroupSerializer, UserSerializer

# User = get_user_model()  # Obtém o modelo de usuário atual

# class UserViewSet(viewsets.ModelViewSet):
#     """
#     API endpoint que permite visualizar ou editar usuários.
#     """
#     queryset = User.objects.all().order_by('-date_joined')
#     serializer_class = UserSerializer
#     permission_classes = [permissions.IsAuthenticated]

# class GroupViewSet(viewsets.ModelViewSet):
#     """
#     API endpoint que permite visualizar ou editar grupos.
#     """
#     queryset = Group.objects.all()
#     serializer_class = GroupSerializer
#     permission_classes = [permissions.IsAuthenticated]

# @api_view(['GET'])
# @permission_classes([IsAuthenticated])
# def protected_view(request):
#     return Response({"message": "Bem-vindo, você está autenticado!"})

# class ProtectedView(APIView):
#     permission_classes = [IsAuthenticated]

#     def get(self, request):
#         return Response({"message": "Bem-vindo, você está autenticado!"})

# @login_required
# def transferir_96_384(request):
#     if request.method == 'POST':
#         form = TransferPlacasForm(request.user, request.POST)
#         if form.is_valid():
#             try:
#                 with transaction.atomic():
#                     # Criar nova placa 384
#                     placa_384 = Placa384.objects.create(
#                         empresa=form.cleaned_data['empresa'],
#                         projeto=form.cleaned_data['projeto'],
#                         codigo_placa=form.cleaned_data['codigo_placa_384']
#                     )

#                     # Realizar transferência
#                     placas_96 = [
#                         form.cleaned_data['placa_1'],
#                         form.cleaned_data['placa_2'],
#                         form.cleaned_data['placa_3'],
#                         form.cleaned_data['placa_4']
#                     ]
                    
#                     placa_384.transfer_96_to_384(placas_96)
                    
#                     messages.success(request, 'Transferência realizada com sucesso!')
#                     return redirect('admin:app_placa384_change', placa_384.id)
                    
#             except ValidationError as e:
#                 messages.error(request, str(e))
#             except Exception as e:
#                 messages.error(request, f'Erro inesperado: {str(e)}')
#     else:
#         form = TransferPlacasForm(user=request.user)
    
#     context = {
#         'form': form,
#         'title': 'Transferir Placas 96 para 384',
#     }
    
#     return render(request, 'admin/app/placa384/transferir_96_384.html', context)

# views.py

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.contrib import messages
from django.db import transaction
from django.core.exceptions import ValidationError, PermissionDenied
from django.http import JsonResponse
import logging
from django.contrib import admin

from rest_framework import permissions, viewsets
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Placa384, Projeto, Placa96
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
    if request.method == 'POST':
        form = TransferPlacasForm(request.user, request.POST)
        if form.is_valid():
            try:
                with transaction.atomic():
                    # Criar nova placa 384
                    placa_384 = Placa384.objects.create(
                        empresa=form.cleaned_data['empresa'],
                        projeto=form.cleaned_data['projeto'],
                        codigo_placa=form.cleaned_data['codigo_placa_384']
                    )

                    # Realizar transferência
                    placas_96 = [
                        form.cleaned_data['placa_1'],
                        form.cleaned_data['placa_2'],
                        form.cleaned_data['placa_3'],
                        form.cleaned_data['placa_4']
                    ]
                    
                    placa_384.transfer_96_to_384(placas_96)
                    
                    messages.success(request, 'Transferência realizada com sucesso!')
                    return redirect('admin:app_placa384_change', placa_384.id)
                    
            except ValidationError as e:
                messages.error(request, str(e))
            except Exception as e:
                messages.error(request, f'Erro inesperado: {str(e)}')
                logger.error(f"Erro na transferência: {str(e)}", exc_info=True)
                
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
    """View para criação de placas 384"""
    if request.method == 'POST':
        try:
            with transaction.atomic():
                empresa_id = request.POST.get('empresa')
                projeto_id = request.POST.get('projeto')
                placas_ids = request.POST.getlist('placas[]')
                codigo_placa_384 = request.POST.get('codigo_placa_384')

                # Validações básicas
                if len(placas_ids) != 4:
                    raise ValidationError('Selecione exatamente 4 placas.')

                # Buscar objetos do banco
                empresa = Empresa.objects.get(id=empresa_id)
                projeto = Projeto.objects.get(id=projeto_id)
                placas_96 = list(Placa96.objects.filter(id__in=placas_ids))

                # Validações adicionais
                if not request.user.is_superuser and request.user.empresa != empresa:
                    raise ValidationError('Sem permissão para esta empresa.')

                if Placa384.objects.filter(codigo_placa=codigo_placa_384, empresa=empresa).exists():
                    raise ValidationError('Já existe uma placa 384 com este código.')

                # Criar nova placa 384
                placa_384 = Placa384.objects.create(
                    empresa=empresa,
                    projeto=projeto,
                    codigo_placa=codigo_placa_384
                )

                # Realizar transferência
                placa_384.transfer_96_to_384(placas_96)

                messages.success(request, 'Placa 384 criada com sucesso!')
                return redirect('home')

        except ValidationError as e:
            messages.error(request, str(e))
        except Exception as e:
            logger.error(f"Erro ao criar placa 384: {str(e)}", exc_info=True)
            messages.error(request, f'Erro ao criar placa: {str(e)}')

    # Se for GET ou se houver erro no POST, renderiza o formulário
    if request.user.is_superuser:
        empresas = Empresa.objects.all()
    else:
        empresas = Empresa.objects.filter(id=request.user.empresa.id)

    return render(request, 'criar_placa_384.html', {'empresas': empresas})

@login_required
def get_projetos(request, empresa_id):
    try:
        if not request.user.is_superuser and request.user.empresa.id != empresa_id:
            return JsonResponse({'error': 'Sem permissão'}, status=403)
            
        projetos = Projeto.objects.filter(
            empresa_id=empresa_id,
            is_active=True
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
    try:
        projeto = Projeto.objects.get(id=projeto_id)
        
        if not request.user.is_superuser and request.user.empresa != projeto.empresa:
            return JsonResponse({'error': 'Sem permissão'}, status=403)
        
        placas = Placa96.objects.filter(
            projeto_id=projeto_id,
            is_active=True
        ).values('id', 'codigo_placa')
        
        return JsonResponse(list(placas), safe=False)
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


@login_required
def get_placas_96(request, projeto_id):
    """API para buscar placas 96 disponíveis de um projeto"""
    try:
        projeto = Projeto.objects.get(id=projeto_id)
        
        # Verificar permissões
        if not request.user.is_superuser and request.user.empresa != projeto.empresa:
            return JsonResponse({'error': 'Sem permissão para acessar este projeto'}, status=403)
        
        # Buscar placas 96 ativas que não foram usadas em transferências
        placas = Placa96.objects.filter(
            projeto_id=projeto_id,
            is_active=True
        ).values('id', 'codigo_placa')
        
        # Converter para lista de dicionários
        placas_list = list(placas)
        
        return JsonResponse(placas_list, safe=False)
        
    except Projeto.DoesNotExist:
        return JsonResponse({'error': 'Projeto não encontrado'}, status=404)
    except Exception as e:
        logger.error(f"Erro ao buscar placas 96: {str(e)}", exc_info=True)
        return JsonResponse({'error': f'Erro ao buscar placas: {str(e)}'}, status=400)

@login_required
def logout_view(request):
    """View para realizar logout"""
    from django.contrib.auth import logout
    logout(request)
    return redirect('login')


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
]