from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model, authenticate
from django.contrib.auth.models import Group
from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes as drf_permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated # IsAuthenticated is used for logout
from rest_framework.views import APIView # Fixed this line - removed incorrect import
from rest_framework.authtoken.models import Token
from rest_framework.authentication import SessionAuthentication, TokenAuthentication

from ..models import Projeto, Placa96, Placa384, Placa1536, Empresa, Cultivo, Tecnologia, MarcadorTrait, MarcadorCustomizado, Status, Etapa
from ..serializers import UserSerializer, GroupSerializer, UserLoginSerializer, DashboardAPISerializer, EmpresaSerializer, ProjetoSerializer
from app.models import MarcadorTrait, MarcadorCustomizado

from rest_framework import serializers as drf_serializers
from ..models import Cultivo, Status, Etapa, Tecnologia # Removed MarcadorTrait, MarcadorCustomizado as they are imported from app.models


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

# Serializers for new models
# Ideally, these would be in a separate app/serializers.py file

class CultivoSerializer(drf_serializers.ModelSerializer):
    class Meta:
        model = Cultivo
        fields = '__all__'

class StatusSerializer(drf_serializers.ModelSerializer):
    class Meta:
        model = Status
        fields = '__all__'

class EtapaSerializer(drf_serializers.ModelSerializer):
    class Meta:
        model = Etapa
        fields = '__all__'

class TecnologiaSerializer(drf_serializers.ModelSerializer):
    class Meta:
        model = Tecnologia
        fields = '__all__'

class MarcadorTraitSerializer(drf_serializers.ModelSerializer):
    class Meta:
        model = MarcadorTrait
        fields = '__all__'

class MarcadorCustomizadoSerializer(drf_serializers.ModelSerializer):
    class Meta:
        model = MarcadorCustomizado
        fields = '__all__'

# ViewSets for new models

class ProjetoViewSet(viewsets.ModelViewSet):
    """API endpoint que permite visualizar ou editar projetos."""
    queryset = Projeto.objects.all().select_related('empresa', 'cultivo', 'status', 'etapa').prefetch_related('marcador_trait', 'marcador_customizado')
    serializer_class = ProjetoSerializer
    authentication_classes = [SessionAuthentication, TokenAuthentication]
    permission_classes = [permissions.IsAuthenticated]
    
    # Adicione este método para garantir que OPTIONS requests funcionem corretamente com CORS
    def get_permissions(self):
        if self.request.method == 'OPTIONS':
            return []
        return super().get_permissions()

    def get_queryset(self):
        user = self.request.user
        queryset = Projeto.objects.all().select_related('empresa', 'cultivo', 'status', 'etapa').prefetch_related('marcador_trait', 'marcador_customizado')
        
        # Filter by empresa_id from query parameters if provided
        empresa_id = self.request.query_params.get('empresa', None)
        if empresa_id:
            queryset = queryset.filter(empresa_id=empresa_id)
        
        # Apply user permissions filtering
        if not user.is_superuser:
            # For non-superusers, filter by their associated empresa(s)
            if hasattr(user, 'empresa') and user.empresa:  # Single empresa
                queryset = queryset.filter(empresa=user.empresa)
            elif hasattr(user, 'empresas') and user.empresas.exists():  # Multiple empresas (ManyToMany)
                queryset = queryset.filter(empresa__in=user.empresas.all())
            else:
                queryset = Projeto.objects.none()  # No access if no empresa is associated
        
        return queryset

    def perform_create(self, serializer):
        user = self.request.user
        empresa = serializer.validated_data.get('empresa')
        
        if not user.is_superuser:
            # Ensure non-superuser can only create for their own company
            user_empresa = getattr(user, 'empresa', None)
            if not user_empresa:
                 # If user has multiple companies, one must be specified in the request
                 if hasattr(user, 'empresas') and not empresa:
                     raise drf_serializers.ValidationError("Empresa é obrigatória para este usuário.")
                 elif hasattr(user, 'empresas') and empresa not in user.empresas.all():
                     raise drf_serializers.ValidationError("Usuário não tem permissão para criar projetos para esta empresa.")
                 elif not hasattr(user, 'empresas'): # Should not happen if user.empresa is also checked
                     raise drf_serializers.ValidationError("Usuário não associado a nenhuma empresa.")

            elif empresa and empresa != user_empresa:
                 raise drf_serializers.ValidationError("Usuário não tem permissão para criar projetos para esta empresa.")
            elif not empresa: # If empresa not provided, assign user's empresa
                 serializer.validated_data['empresa'] = user_empresa

        serializer.save(criado_por=user)

class EmpresaViewSet(viewsets.ModelViewSet):
    """API endpoint que permite visualizar ou editar empresas."""
    queryset = Empresa.objects.all()
    serializer_class = EmpresaSerializer
    authentication_classes = [SessionAuthentication, TokenAuthentication] # Explicitly add SessionAuthentication
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # Overriding get_queryset to filter by user's companies
        if self.request.user.is_superuser:
            return Empresa.objects.all()
        return Empresa.objects.filter(id__in=self.request.user.empresas.values_list('id', flat=True))

class CultivoViewSet(viewsets.ModelViewSet):
    queryset = Cultivo.objects.all()
    serializer_class = CultivoSerializer
    authentication_classes = [SessionAuthentication, TokenAuthentication] # Added for consistency
    permission_classes = [permissions.IsAuthenticated]

class StatusViewSet(viewsets.ModelViewSet):
    queryset = Status.objects.all()
    serializer_class = StatusSerializer
    permission_classes = [permissions.IsAuthenticated]

class EtapaViewSet(viewsets.ModelViewSet):
    queryset = Etapa.objects.all()
    serializer_class = EtapaSerializer
    permission_classes = [permissions.IsAuthenticated]

class TecnologiaViewSet(viewsets.ModelViewSet):
    queryset = Tecnologia.objects.all()
    serializer_class = TecnologiaSerializer
    authentication_classes = [SessionAuthentication, TokenAuthentication] # Added for consistency
    permission_classes = [permissions.IsAuthenticated]

class MarcadorTraitViewSet(viewsets.ModelViewSet):
    queryset = MarcadorTrait.objects.all()
    serializer_class = MarcadorTraitSerializer
    authentication_classes = [SessionAuthentication, TokenAuthentication] # Added for consistency
    permission_classes = [permissions.IsAuthenticated]

class MarcadorCustomizadoViewSet(viewsets.ModelViewSet):
    queryset = MarcadorCustomizado.objects.all()
    serializer_class = MarcadorCustomizadoSerializer
    authentication_classes = [SessionAuthentication, TokenAuthentication] # Added for consistency
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

@api_view(['POST'])
@drf_permission_classes([AllowAny])
def api_login_view(request):
    """
    API endpoint for user login and token generation.
    Accepts username and password.
    Returns auth token on success.
    """
    username = request.data.get('username')
    password = request.data.get('password')

    if not username or not password:
        return Response(
            {'error': 'Please provide both username and password'},
            status=status.HTTP_400_BAD_REQUEST
        )

    user = authenticate(username=username, password=password)

    if not user:
        return Response(
            {'error': 'Invalid Credentials'},
            status=status.HTTP_401_UNAUTHORIZED
        )

    token, created = Token.objects.get_or_create(user=user)
    user_data = UserLoginSerializer(user).data
    
    return Response({
        'token': token.key,
        'user': user_data
    })

@api_view(['POST'])
@drf_permission_classes([IsAuthenticated]) # Use IsAuthenticated from rest_framework.permissions
def api_logout_view(request):
    """
    API endpoint for user logout.
    Deletes the user's auth token.
    """
    try:
        request.user.auth_token.delete()
        return Response({'message': 'Successfully logged out.'}, status=status.HTTP_200_OK)
    except (AttributeError, Token.DoesNotExist):
        return Response({'error': 'No active session found or token already invalidated.'}, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class DashboardAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        # Geral Stats
        total_empresas = Empresa.objects.count()
        total_projetos_count = Projeto.objects.count()
        
        placas96_count = Placa96.objects.count()
        placas384_count = Placa384.objects.count()
        placas1536_count = Placa1536.objects.count()
        total_placas_geral = placas96_count + placas384_count + placas1536_count
        
        placa_stats_geral = {
            'placas96': placas96_count,
            'placas384': placas384_count,
            'placas1536': placas1536_count,
            'total': total_placas_geral
        }

        # Media marcadores por projeto & Total Datapoints
        media_marcadores_sum = 0
        projetos_com_marcadores_count = 0
        total_datapoints_global = 0
        
        projetos_qs = Projeto.objects.prefetch_related('marcador_trait', 'marcador_customizado').all()
        for p in projetos_qs:
            marcadores_no_projeto = p.marcador_trait.count() + p.marcador_customizado.count()
            total_datapoints_global += p.quantidade_amostras * marcadores_no_projeto
            if marcadores_no_projeto > 0:
                media_marcadores_sum += marcadores_no_projeto
                projetos_com_marcadores_count += 1
        
        avg_marcadores = (media_marcadores_sum / projetos_com_marcadores_count) if projetos_com_marcadores_count > 0 else 0

        geral_stats = {
            'total_empresas': total_empresas,
            'total_projetos': total_projetos_count,
            'total_placas': placa_stats_geral,
            'media_marcadores_por_projeto': avg_marcadores,
            'total_datapoints': total_datapoints_global
        }

        # Datapoints por MarcadorTrait
        dp_por_trait = []
        for trait in MarcadorTrait.objects.prefetch_related('projeto_set').all():
            datapoints = sum(p.quantidade_amostras for p in trait.projeto_set.all() if p.quantidade_amostras)
            dp_por_trait.append({'nome': trait.nome, 'datapoints': datapoints})

        # Datapoints por MarcadorCustomizado
        dp_por_custom = []
        for custom_marker in MarcadorCustomizado.objects.prefetch_related('projeto_set').all():
            datapoints = sum(p.quantidade_amostras for p in custom_marker.projeto_set.all() if p.quantidade_amostras)
            dp_por_custom.append({'nome': custom_marker.nome, 'datapoints': datapoints})

        # Metricas por Empresa
        metricas_empresa_list = []
        empresas_qs = Empresa.objects.prefetch_related(
            'projeto_set', 
            'projeto_set__marcador_trait', 
            'projeto_set__marcador_customizado'
        ).all()

        for empresa_obj in empresas_qs:
            empresa_projetos = empresa_obj.projeto_set.all()
            empresa_total_projetos = empresa_projetos.count()
            empresa_total_amostras = sum(p.quantidade_amostras for p in empresa_projetos if p.quantidade_amostras)
            
            empresa_placas96 = Placa96.objects.filter(empresa=empresa_obj).count()
            empresa_placas384 = Placa384.objects.filter(empresa=empresa_obj).count()
            empresa_placas1536 = Placa1536.objects.filter(empresa=empresa_obj).count()
            empresa_total_placas = empresa_placas96 + empresa_placas384 + empresa_placas1536

            empresa_placa_stats = {
                'placas96': empresa_placas96,
                'placas384': empresa_placas384,
                'placas1536': empresa_placas1536,
                'total': empresa_total_placas
            }
            
            empresa_total_datapoints = 0
            for p in empresa_projetos:
                 empresa_total_datapoints += (p.quantidade_amostras or 0) * \
                                            (p.marcador_trait.count() + p.marcador_customizado.count())
            
            metricas_empresa_list.append({
                'empresa_id': empresa_obj.id,
                'empresa_nome': empresa_obj.nome,
                'total_projetos': empresa_total_projetos,
                'total_amostras': empresa_total_amostras,
                'total_placas': empresa_placa_stats,
                'total_datapoints': empresa_total_datapoints
            })

        dashboard_data = {
            'geral': geral_stats,
            'datapoints_por_marcador_trait': dp_por_trait,
            'datapoints_por_marcador_customizado': dp_por_custom,
            'metricas_por_empresa': metricas_empresa_list
        }
        
        serializer = DashboardAPISerializer(dashboard_data)
        return Response(serializer.data, status=status.HTTP_200_OK)