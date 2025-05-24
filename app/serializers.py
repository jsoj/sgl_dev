from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from rest_framework import serializers
from .models import Empresa, Projeto, Cultivo, Tecnologia, Status, Etapa, MarcadorTrait, MarcadorCustomizado

# Obter o modelo de usuário personalizado
User = get_user_model()

class UserSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = User
        fields = ['url', 'username', 'email', 'groups']

class GroupSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Group
        fields = ['url', 'name']

class EmpresaBasicSerializer(serializers.ModelSerializer):
    class Meta:
        model = Empresa
        fields = ['id', 'nome', 'codigo']

class UserLoginSerializer(serializers.ModelSerializer):
    empresa = EmpresaBasicSerializer(read_only=True)

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'empresa']

class EmpresaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Empresa
        fields = '__all__'

class ProjetoSerializer(serializers.ModelSerializer):
    # To display names instead of IDs for foreign keys
    empresa_nome = serializers.CharField(source='empresa.nome', read_only=True)
    cultivo_nome = serializers.CharField(source='cultivo.nome', read_only=True, allow_null=True)
    status_nome = serializers.CharField(source='status.nome', read_only=True, allow_null=True)
    etapa_nome = serializers.CharField(source='etapa.nome', read_only=True, allow_null=True)
    
    # For ManyToMany fields, you might want to list IDs or use nested serializers
    marcador_trait = serializers.PrimaryKeyRelatedField(queryset=MarcadorTrait.objects.all(), many=True, required=False)
    marcador_customizado = serializers.PrimaryKeyRelatedField(queryset=MarcadorCustomizado.objects.all(), many=True, required=False)
    
    tecnologia_parental1 = serializers.PrimaryKeyRelatedField(queryset=Tecnologia.objects.all(), allow_null=True, required=False)
    tecnologia_parental2 = serializers.PrimaryKeyRelatedField(queryset=Tecnologia.objects.all(), allow_null=True, required=False)
    tecnologia_target = serializers.PrimaryKeyRelatedField(queryset=Tecnologia.objects.all(), allow_null=True, required=False)


    class Meta:
        model = Projeto
        fields = [
            'id', 'empresa', 'empresa_nome', 'codigo_projeto', 'responsavel', 'quantidade_amostras', 
            'numero_placas_96', 'placas_inicial', 'placas_final', 'cultivo', 'cultivo_nome', 
            'origem_amostra', 'tecnologia_parental1', 'tecnologia_parental2', 'tecnologia_target',
            'proporcao', 'marcador_trait', 'marcador_customizado', 'quantidade_traits', 
            'quantidade_marcador_customizado', 'status', 'status_nome', 'etapa', 'etapa_nome', 
            'nome_projeto_cliente', 'prioridade', 'codigo_ensaio', 'setor_cliente', 
            'local_cliente', 'ano_plantio_ensaio', 'tipo_amostra', 'herbicida', 
            'marcador_analisado', 'se_marcador_analisado', 'data_planejada_envio', 
            'data_envio', 'data_planejada_liberacao_resultados', 'data_recebimento_laboratorio', 
            'data_liberacao_resultados', 'data_validacao_cliente', 'data_prevista_destruicao', 
            'data_destruicao', 'comentarios', 'created_at', 'data_alteracao', 'ativo', 'destruido'
        ]
        read_only_fields = ('created_at', 'data_alteracao', 'ativo', 'destruido', 'numero_placas_96')

    def validate(self, data):
        # Example custom validation: Ensure tecnologia_target is one of the parentals if set
        t_target = data.get('tecnologia_target')
        t_p1 = data.get('tecnologia_parental1')
        t_p2 = data.get('tecnologia_parental2')

        if t_target and t_target not in [t_p1, t_p2]:
            raise serializers.ValidationError({
                'tecnologia_target': 'A tecnologia target deve ser igual a uma das parentais.'
            })
        
        if t_p1 and t_p2 and t_p1 == t_p2:
            raise serializers.ValidationError({
                'tecnologia_parental2': 'A tecnologia parental 2 não pode ser igual à parental 1.'
            })
            
        return data

# Dashboard Serializers
class DashboardPlacaStatsSerializer(serializers.Serializer):
    placas96 = serializers.IntegerField()
    placas384 = serializers.IntegerField()
    placas1536 = serializers.IntegerField()
    total = serializers.IntegerField()

class DashboardGeralSerializer(serializers.Serializer):
    total_empresas = serializers.IntegerField()
    total_projetos = serializers.IntegerField()
    total_placas = DashboardPlacaStatsSerializer()
    media_marcadores_por_projeto = serializers.FloatField()
    total_datapoints = serializers.IntegerField()

class DashboardDatapointsPorMarcadorSerializer(serializers.Serializer):
    nome = serializers.CharField()
    datapoints = serializers.IntegerField()

class DashboardEmpresaStatsSerializer(serializers.Serializer):
    empresa_id = serializers.IntegerField()
    empresa_nome = serializers.CharField()
    total_projetos = serializers.IntegerField()
    total_amostras = serializers.IntegerField()
    total_placas = DashboardPlacaStatsSerializer()
    total_datapoints = serializers.IntegerField()

class DashboardAPISerializer(serializers.Serializer):
    geral = DashboardGeralSerializer()
    datapoints_por_marcador_trait = DashboardDatapointsPorMarcadorSerializer(many=True)
    datapoints_por_marcador_customizado = DashboardDatapointsPorMarcadorSerializer(many=True)
    metricas_por_empresa = DashboardEmpresaStatsSerializer(many=True)