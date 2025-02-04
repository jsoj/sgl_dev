from django.db import models, transaction  # Adicione transaction aqui
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from app.funcoes import validar_data_liberacao, validar_data_recebimento
from django.contrib.auth.models import User
from django.core.exceptions import PermissionDenied
from django.contrib.auth.models import AbstractUser
from SGL.settings import AUTH_USER_MODEL
from django.conf import settings
import logging

logger = logging.getLogger(__name__)



class Empresa(models.Model):
    nome = models.CharField(max_length=100)
    codigo = models.CharField(max_length=4)
    cnpj = models.CharField(max_length=14, unique=True)
    cep = models.CharField(max_length=10, blank=True, null=True)
    endereco = models.CharField(max_length=100, blank=True, null=True)
    complemento = models.CharField(max_length=100, blank=True, null=True)
    bairro = models.CharField(max_length=100, blank=True, null=True)
    cidade = models.CharField(max_length=100, blank=True, null=True)
    estado = models.CharField(max_length=2, blank=True, null=True)
    telefone = models.CharField(max_length=20, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    data_cadastro = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Empresa'
        verbose_name_plural = 'Empresas'
        ordering = ['nome']

    def __str__(self):
        return self.codigo

class User(AbstractUser):
    telefone = models.CharField(max_length=20, blank=True, null=True)
    data_cadastro = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    empresa = models.ForeignKey('Empresa', on_delete=models.SET_NULL, null=True, blank=True, related_name='usuarios')

    class Meta:
        verbose_name = 'Usuário'
        verbose_name_plural = 'Usuários'
        ordering = ['username']

    def __str__(self):
        return self.email or self.username

class EmpresaMixin(models.Model):
    empresa = models.ForeignKey(
        Empresa,
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )

    class Meta:
        abstract = True

# MODELOS CHOICES 

ORIGEM_CHOICES = [
    ("FOLHA","FOLHA"),
     ("SEMENTE","SEMENTE",)]

class Tecnologia(EmpresaMixin, models.Model):
    nome = models.CharField(max_length=40, unique=True)
    caracteristica = models.TextField(max_length=100, blank=True)
    vencimento_patente = models.DateField(blank=True, null=True)
    data_cadastro = models.DateField(auto_now_add=True)

    def __str__(self):
        return self.nome
    class Meta:
        verbose_name_plural = 'Tecnologias'
 
class Protocolo(EmpresaMixin, models.Model):
    nome = models.CharField(max_length=40, unique=True)

    def __str__(self) -> str:
        return self.nome
    class Meta:
       verbose_name_plural = 'Protocolos'

class Cultivo(EmpresaMixin, models.Model):
    nome = models.CharField(max_length=40)
    nome_cientifico = models.CharField(max_length=40, blank=True, null=True)
    data_cadastro = models.DateField(auto_now_add=True)

    def __str__(self) -> str:
        return self.nome
    class Meta:
       verbose_name_plural = 'Cultivos'

class Status(EmpresaMixin, models.Model):
    nome = models.CharField(max_length=40)

    def __str__(self) -> str:
        return self.nome
    class Meta:
       verbose_name_plural = 'Status'

class Etapa(EmpresaMixin, models.Model):
    nome = models.CharField(max_length=40)

    def __str__(self) -> str:
        return self.nome
    class Meta:
       verbose_name_plural = 'Etapas'

class Marcador(EmpresaMixin, models.Model):
    cultivo = models.ForeignKey(Cultivo, on_delete=models.CASCADE, blank=False, null=False, help_text='Escolha ou cadastre um cultivo para este marcador. Exemplo: Soja')
    nome = models.CharField(max_length=40)
    caracteristica = models.TextField(blank=True, null=True)
    is_customizado = models.BooleanField(default=False)
    data_cadastro = models.DateField(auto_now_add=True)

    def __str__(self) -> str:
        return self.nome
    class Meta:
       verbose_name_plural = 'Marcadores'

# INICIO PROJETO 

class Projeto(EmpresaMixin, models.Model):
    codigo_projeto = models.CharField(max_length=3, blank=False, 
                                    help_text='Código do projeto são 3 números sequenciais e únicos para o cliente. Exemplo: 001')
    quantidade_amostras = models.PositiveIntegerField(                  blank=False,    null=False,                                         help_text='Quantidade de amostras deste projeto. Exemplo: 15.000')
    cultivo = models.ForeignKey(Cultivo,                                blank=True,     null=True,  default=1,  on_delete=models.CASCADE,   help_text='Escolha ou cadastre um cultivo. Exemplo: Soja')
    origem_amostra = models.CharField(                  max_length=10,  blank=True, choices=ORIGEM_CHOICES, default=1,                      help_text='Origem da amostra no cliente. Exemplo: Planta, Linha, Semente')
    tecnologia = models.ForeignKey(Tecnologia,                          blank=True,     null=True,              on_delete=models.CASCADE,   help_text='Escolha ou cadastre um evento biotecnológico deste projeto. Exemplo: RR, CE3, I2X')
    marcador = models.ManyToManyField(Marcador,                         blank=True,                                                         help_text='Escolha ou cadastre os marcadores que serão analisados neste projeto. Exemplo: RR2BT1, E3BT, RGH1-2')
    quantidade_traits = models.PositiveSmallIntegerField(               blank=True,     null=True,                                          help_text='Quantidade de traits a serem avaliados neste projeto. Exemplo: 1, 2')
    quantidade_marcador_customizado = models.PositiveSmallIntegerField( blank=True,     null=True,                                          help_text='Quantidade de marcadores customizados a serem analisados neste projeto. Exmmplo: 2')
    status = models.ForeignKey(Status,                                  blank=True,     null=True,  default=1,  on_delete=models.CASCADE,   help_text='Escolha o status do projeto')
    etapa = models.ForeignKey(Etapa,                                    blank=True,     null=True,  default=1,  on_delete=models.CASCADE,   help_text='Escolha a estapa da amostra do projeto')
    protocolo = models.ForeignKey(Protocolo,                            blank=True,     null=True,  default=1,  on_delete=models.CASCADE,   help_text ='Escolha o protocolo ex. PCR em tempo real, microsatelites')
    nome_projeto_cliente = models.CharField(            max_length=100, blank=True,     null=True,                                          help_text='Nome de guerra do projeto. Exemplo: RV_CZF4_MULTIPGN_1x3_02_01')
    numero_placas_96 = models.PositiveSmallIntegerField(                blank=True,     null=True,                                          help_text='O número de Placas de 96 será calculado automaticamente com base no número de amostras')
    placas_inicial =  models.CharField(                 max_length=10,  blank=True,     null=True,                                          help_text='Placa inicial. Exemplo: 1')
    placas_final =  models.CharField(                   max_length=10,  blank=True,                                                         help_text='Placa final. Exemplo: 96')
    responsavel = models.CharField(                     max_length=100, blank=True,                                                         help_text='Nome do responsável pelo projeto no cliente. Exemplo: Osmaria')
    prioridade = models.PositiveSmallIntegerField(default=0,                                                                                help_text='Prioridade do projeto. Exemplo: 01 prioridade máxima, 09 baixa prioridade')
    codigo_ensaio = models.CharField(                   max_length=10,  blank=True,                                                         help_text='Código de ensaio do cliente. Exemplo: 51899137 ')
    setor_cliente = models.CharField(                   max_length=40,  blank=True,                                                         help_text='Setor interno do cliente. Exemplo: Nursery, Pureza, Produção, QAQC' )
    local_cliente = models.CharField(                   max_length=40,  blank=True,                                                         help_text='Local de referência do cliente. Exemplo: Porto Nacional, Rio Verde')
    ano_plantio_ensaio = models.IntegerField(                           blank=True,     null=True,                                          help_text='Ano do plantio com 4 dígitos. Exemplo: 2024')
    numero_discos = models.CharField(                   max_length=40,  blank=True,                                                         help_text='Números de discos. Exemplo: TRIFÓLIO #4 PUNCHS ou TRIFÓLIO #8 PUNCHS')
    data_planejada_envio = models.DateField(                            blank=True, null=True)
    data_envio = models.DateField(                                      blank=True, null=True)
    data_planejada_liberacao_resultados = models.DateField(             blank=True, null=True)
    data_recebimento_laboratorio = models.DateField(                    blank=True, null=True,  validators=[validar_data_recebimento])
    data_liberacao_resultados = models.DateField(                       blank=True, null=True,  validators=[validar_data_liberacao])
    data_validacao_cliente = models.DateField(                          blank=True, null=True)
    data_prevista_destruicao = models.DateField(                        blank=True, null=True)
    data_destruicao = models.DateField(                                 blank=True, null=True)
    created_at = models.DateField(   auto_now_add=True)
    data_alteracao = models.DateField(  auto_now=True)
    tem_template = models.BooleanField(                                                         default=False)
    ativo = models.BooleanField(                                                                default=True)
    destruido = models.BooleanField(                                                            default=False)
    data_destruicao = models.DateField( auto_now=True)
    comentarios = models.TextField(                                    blank=True, null=True,                                               help_text='Registre toda e qualquer informação acessória para este projeto')
    
    class Meta:
        unique_together = ['empresa', 'codigo_projeto']
        verbose_name = 'Projeto'
        verbose_name_plural = 'Projetos'

    objects = models.Manager()

    def __str__(self):
        empresa_codigo = self.empresa.codigo if self.empresa else 'SEM-EMPRESA'
        return f"{self.codigo_projeto}"
    
       
    def clean(self):
        """Validações personalizadas do modelo"""
        super().clean()
        # Validar datas em sequência
        self._validar_sequencia_datas()
        # Calcular número de placas automaticamente
        self._calcular_numero_placas()

    def _validar_sequencia_datas(self):
        """Valida a sequência lógica de todas as datas do projeto"""
        datas = [
            ('data_planejada_envio', 'data_envio'),
            ('data_envio', 'data_recebimento_laboratorio'),
            ('data_recebimento_laboratorio', 'data_liberacao_resultados'),
            ('data_liberacao_resultados', 'data_validacao_cliente'),
            ('data_validacao_cliente', 'data_prevista_destruicao'),
            ('data_prevista_destruicao', 'data_destruicao')
        ]
        
        for data_anterior, data_posterior in datas:
            if (getattr(self, data_anterior) and getattr(self, data_posterior) and 
                getattr(self, data_anterior) > getattr(self, data_posterior)):
                raise ValidationError(f'{data_posterior} não pode ser anterior a {data_anterior}')

    def _calcular_numero_placas(self):
        """Calcula automaticamente o número de placas de 96 necessárias"""
        if self.quantidade_amostras:
            self.numero_placas_96 = -(-self.quantidade_amostras // 96)  # Arredondamento para cima

    @property
    def status_atual(self):
        """Retorna o status atual do projeto baseado nas datas preenchidas"""
        if self.destruido:
            return "Destruído"
        if self.data_validacao_cliente:
            return "Validado"
        if self.data_liberacao_resultados:
            return "Aguardando Validação"
        if self.data_recebimento_laboratorio:
            return "Em Análise"
        if self.data_envio:
            return "Enviado"
        return "Planejado"

    @property
    def prazo_cumprido(self):
        """Verifica se o projeto está dentro do prazo planejado"""
        if self.data_liberacao_resultados and self.data_planejada_liberacao_resultados:
            return self.data_liberacao_resultados <= self.data_planejada_liberacao_resultados
        return None

    @property
    def dias_em_analise(self):
        """Retorna o número de dias que o projeto está em análise"""
        if self.data_recebimento_laboratorio:
            if self.data_liberacao_resultados:
                return (self.data_liberacao_resultados - self.data_recebimento_laboratorio).days
            from datetime import date
            return (date.today() - self.data_recebimento_laboratorio).days
        return 0

    @property
    def total_marcadores(self):
        """Retorna o total de marcadores (traits + customizados)"""
        return (self.quantidade_traits or 0) + (self.quantidade_marcador_customizado or 0)

    @property
    def codigo_completo(self):
        """Retorna o código completo do projeto (código empresa + código projeto)"""
        return f"{self.empresa.codigo}-{self.codigo_projeto}"

    def get_marcadores_por_tipo(self):
        """Retorna os marcadores separados por tipo (customizados e não customizados)"""
        return {
            'customizados': self.marcador.filter(is_customizado=True),
            'padroes': self.marcador.filter(is_customizado=False)
        }

    def gerar_codigo_unico(self):
        """Gera um código único para o projeto baseado em regras de negócio"""
        ano = str(self.ano_plantio_ensaio)[-2:]
        return f"{self.empresa.codigo}{self.codigo_projeto}{ano}"

    @property
    def nome_arquivo_template(self):
        """Retorna o nome padrão para arquivos de template"""
        return f"template_{self.empresa.codigo}_{self.codigo_projeto}_{self.cultivo.nome}"

    def registrar_alteracao(self, campo, valor_antigo, valor_novo):
        """Registra alterações significativas no projeto"""
        return f"Campo '{campo}' alterado de '{valor_antigo}' para '{valor_novo}' em {self.data_alteracao}"

    @property
    def dias_ate_destruicao(self):
        """Calcula dias restantes até a data prevista de destruição"""
        if self.data_prevista_destruicao:
            from datetime import date
            return (self.data_prevista_destruicao - date.today()).days
        return None

    ## DASHBOARD

    @property   
    def total_datapoints_esperados(self):
        """Calcula o total de datapoints esperados para o projeto"""
        if self.quantidade_amostras and self.marcador.count():
            return self.quantidade_amostras * self.marcador.count()
        return 0
    
    @classmethod
    def get_metricas_gerais(cls):
        """Retorna métricas gerais de todos os projetos"""
        from django.db.models import Sum, Count, Avg
        return {
            'total_projetos': cls.objects.count(),
            'total_amostras': cls.objects.aggregate(Sum('quantidade_amostras'))['quantidade_amostras__sum'],
            'total_placas': cls.objects.aggregate(Sum('numero_placas_96'))['numero_placas_96__sum'],
            'media_marcadores': cls.objects.annotate(
                num_marcadores=Count('marcador')).aggregate(Avg('num_marcadores'))['num_marcadores__avg']
        }

    @classmethod
    def get_metricas_por_empresa(cls):  # Renomeado de get_metricas_por_cliente
        """Retorna métricas agrupadas por empresa"""
        from django.db.models import Count, Sum
        return cls.objects.values(
            'empresa__nome'  # Alterado de cliente__nome
        ).annotate(
            total_projetos=Count('id'),
            total_amostras=Sum('quantidade_amostras'),
            total_placas=Sum('numero_placas_96')
        ).order_by('-total_projetos')

    @classmethod
    def get_metricas_por_cultivo(cls):
        """Retorna métricas agrupadas por cultivo"""
        from django.db.models import Count, Sum
        return cls.objects.values(
            'cultivo__nome'
        ).annotate(
            total_projetos=Count('id'),
            total_amostras=Sum('quantidade_amostras')
        ).order_by('-total_projetos')

    @classmethod
    def get_metricas_temporais(cls):
        """Retorna métricas ao longo do tempo"""
        from django.db.models import Count
        from django.db.models.functions import TruncMonth
        return cls.objects.annotate(
            mes=TruncMonth('data_cadastro')
        ).values('mes').annotate(
            total_projetos=Count('id'),
            total_amostras=Sum('quantidade_amostras')
        ).order_by('mes')

    @classmethod
    def get_metricas_status(cls):
        """Retorna métricas por status"""
        from django.db.models import Count, Sum
        return cls.objects.values(
            'status__nome'
        ).annotate(
            total_projetos=Count('id'),
            total_amostras=Sum('quantidade_amostras')
        ).order_by('status__nome')

    @classmethod
    def get_metricas_prazo(cls):
        """Retorna métricas de cumprimento de prazo"""
        from django.db.models import Count, Case, When, IntegerField
        return cls.objects.aggregate(
            no_prazo=Count(Case(
                When(data_liberacao_resultados__lte=models.F('data_planejada_liberacao_resultados'), then=1),
                output_field=IntegerField(),
            )),
            atrasados=Count(Case(
                When(data_liberacao_resultados__gt=models.F('data_planejada_liberacao_resultados'), then=1),
                output_field=IntegerField(),
            ))
        )

    @property
    def tempo_processamento(self):
        """Calcula o tempo de processamento em dias"""
        if self.data_recebimento_laboratorio and self.data_liberacao_resultados:
            return (self.data_liberacao_resultados - self.data_recebimento_laboratorio).days
        return None

    @classmethod
    def get_metricas_avancadas(cls):
        """Retorna métricas avançadas dos projetos"""
        from django.db.models import Avg, Count, Sum, F, ExpressionWrapper, FloatField
        from django.db.models.functions import ExtractMonth, ExtractYear
        
        # Cálculo de tempo de processamento
        tempo_processamento = ExpressionWrapper(
            F('data_liberacao_resultados') - F('data_recebimento_laboratorio'),
            output_field=FloatField()
        )

        return {
            # Média de datapoints
            'media_datapoints': cls.objects.annotate(
                num_marcadores=Count('marcador'),
                datapoints=F('quantidade_amostras') * F('num_marcadores')
            ).aggregate(avg_datapoints=Avg('datapoints'))['avg_datapoints'],

            # Taxa de conclusão (projetos com data_liberacao_resultados / total)
            'taxa_conclusao': cls.objects.annotate(
                concluido=Count('data_liberacao_resultados')
            ).aggregate(
                total=Count('id'),
                concluidos=Count('data_liberacao_resultados')
            ),

            # Tempo médio de processamento
            'tempo_medio_processamento': cls.objects.filter(
                data_liberacao_resultados__isnull=False,
                data_recebimento_laboratorio__isnull=False
            ).annotate(
                tempo=tempo_processamento
            ).aggregate(media_tempo=Avg('tempo'))['media_tempo'],
        }

    @classmethod
    def get_distribuicao_tecnologias(cls):
        """Retorna distribuição de tecnologias por cultivo"""
        from django.db.models import Count
        return cls.objects.values(
            'cultivo__nome',
            'tecnologia__nome'
        ).annotate(
            total_projetos=Count('id'),
            total_amostras=Sum('quantidade_amostras')
        ).order_by('cultivo__nome', '-total_projetos')

    @classmethod
    def get_analise_sazonalidade(cls):
        """Retorna análise de sazonalidade por mês"""
        from django.db.models import Count, Avg
        from django.db.models.functions import ExtractMonth
        return cls.objects.annotate(
            mes=ExtractMonth('data_cadastro')
        ).values('mes').annotate(
            total_projetos=Count('id'),
            media_amostras=Avg('quantidade_amostras')
        ).order_by('mes')

    @classmethod
    def get_correlacao_amostras_tempo(cls):
        """Retorna dados para análise de correlação entre número de amostras e tempo de processamento"""
        from django.db.models import F, ExpressionWrapper, FloatField
        projetos = cls.objects.filter(
            data_liberacao_resultados__isnull=False,
            data_recebimento_laboratorio__isnull=False
        ).annotate(
            tempo_processamento=ExpressionWrapper(
                F('data_liberacao_resultados') - F('data_recebimento_laboratorio'),
                output_field=FloatField()
            )
        ).values('quantidade_amostras', 'tempo_processamento')
        return list(projetos)


# Métodos para criação automatica de placas, amostras e poços 
#---------------------------------------------------------------------------


    def generate_plate_code(self, plate_number):
        """Gera um código único para a placa baseado no projeto e número sequencial"""
        return f"{self.empresa}-{self.codigo_projeto}-{str(plate_number).zfill(3)}"

    def generate_sample_code(self, sample_number):
        """Gera um código único para a amostra baseado no projeto e número sequencial"""
        return f"{self.empresa}-{self.codigo_projeto}-{str(sample_number).zfill(5)}"

    def calculate_well_position(self, index):
        """
        Calcula a posição do poço (A01-H12) baseado no índice sequencial.
        A placa é preenchida por linha, da esquerda para direita.
        """
        row = chr(65 + (index // 12))  # A-H (divisão inteira por 12 para linha)
        col = (index % 12) + 1         # 1-12 (resto da divisão por 12 para coluna)
        return f"{row}{str(col).zfill(2)}"

    def create_project_resources(self):
        """
        Cria placas, amostras e poços para o projeto.
        Retorna um dicionário com os recursos criados.
        """
        try:
            with transaction.atomic():
                # Calcula número de placas necessárias (96 poços por placa)
                num_plates = -(-self.quantidade_amostras // 92)  # 92 poços úteis por placa
                
                # Cria a amostra de controle NTC
                ntc_sample = Amostra.objects.create(
                    empresa=self.empresa,
                    projeto=self,
                    codigo_amostra=f"{self.codigo_projeto}NTC"
                )
                
                # Cria as placas
                plates = []
                for plate_num in range(1, num_plates + 1):
                    plate = Placa96.objects.create(
                        empresa=self.empresa,
                        projeto=self,
                        codigo_placa=self.generate_plate_code(plate_num)
                    )
                    plates.append(plate)

                # Cria as amostras
                samples = []
                for sample_num in range(1, self.quantidade_amostras + 1):
                    sample = Amostra.objects.create(
                        empresa=self.empresa,
                        projeto=self,
                        codigo_amostra=self.generate_sample_code(sample_num)
                    )
                    samples.append(sample)

                # Cria os poços e atribui as amostras
                wells = []
                sample_index = 0
                
                for plate in plates:
                    # Cria os poços de controle NTC (A01, B1, C1, D1)
                    control_positions = ['A01', 'B01', 'C01', 'D01']
                    for pos in control_positions:
                        well = Poco96.objects.create(
                            empresa=self.empresa,
                            placa=plate,
                            amostra=ntc_sample,  # Usa a amostra NTC
                            posicao=pos
                        )
                        wells.append(well)

                    # Cria os poços para as amostras
                    for well_idx in range(96):
                        pos = self.calculate_well_position(well_idx)
                        if pos in control_positions:
                            continue
                            
                        if sample_index < len(samples):
                            well = Poco96.objects.create(
                                empresa=self.empresa,
                                placa=plate,
                                amostra=samples[sample_index],
                                posicao=pos
                            )
                            wells.append(well)
                            sample_index += 1

                return {
                    'plates': plates,
                    'samples': samples,
                    'wells': wells,
                    'ntc_sample': ntc_sample,
                    'total_plates': len(plates),
                    'total_samples': len(samples),
                    'total_wells': len(wells)
                }

        except Exception as e:
            print(f"Erro ao criar recursos do projeto: {str(e)}")
            raise

    def get_resources_summary(self):
        """
        Retorna um resumo dos recursos associados ao projeto
        """
        return {
            'total_plates': self.placa96_set.count(),
            'total_samples': self.amostra_set.count(),
            'total_wells': sum(placa.poco96_set.count() for placa in self.placa96_set.all()),
            'control_wells': sum(
                placa.poco96_set.filter(posicao__in=['A01', 'B01', 'C01', 'D01']).count() 
                for placa in self.placa96_set.all()
            )
        }

#---------------------------------------------------------------------------

    def save(self, *args, **kwargs):
        is_new = self.pk is None  # Verifica se é uma criação nova
        user = kwargs.pop('user', None)
        empresa = kwargs.pop('empresa', None)
        
        if not self.empresa_id:  # Se ainda não tem empresa definida
            if empresa:  # Se foi passada uma empresa
                self.empresa = empresa
            elif user and not user.is_superuser and user.empresa:  # Se foi passado um user
                self.empresa = user.empresa
                
        super().save(*args, **kwargs)
        
        if is_new:
            self.create_project_resources()


        # num_placas96 = math.ceil(self.quantidade_amostras / 92)

        # for i in range(num_placas96):
        #     Placa96.objects.create(
        #         projeto=self,
        #         codigo_placa=i+1
        #     )

        # for j in range(self.quantidade_amostras):
        #     codigo_amostra = f"{self.empresa.codigo} - {self.codigo_projeto} - {j+1:03d}"
        #     Amostra.objects.create(
        #         projeto=self,
        #         codigo_amostra=codigo_amostra
        #     )

# FIM PROJETO

# PLACAS

class Amostra(EmpresaMixin, models.Model):
    projeto = models.ForeignKey('Projeto', on_delete=models.CASCADE)
    codigo_amostra = models.CharField(
        max_length=50,
        help_text='Código único da amostra no projeto'
    )
    data_cadastro = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['empresa', 'projeto', 'codigo_amostra']
        verbose_name = 'Amostra'
        verbose_name_plural = 'Amostras'

    def __str__(self):
        return f"{self.codigo_amostra}"

class Placa96(EmpresaMixin, models.Model):
    projeto = models.ForeignKey('Projeto', on_delete=models.CASCADE)
    codigo_placa = models.CharField(
        max_length=20,
        help_text='Código identificador da placa de 96 poços'
    )
    data_criacao = models.DateTimeField(auto_now_add=True)
    observacoes = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        unique_together = ['empresa', 'projeto', 'codigo_placa']
        verbose_name = 'Placa   96'
        verbose_name_plural = 'Placas   96'

    def __str__(self):
        return f"{self.codigo_placa}"

    def get_amostras_count(self):
        """Retorna a contagem de amostras, excluindo os NTCs"""
        return self.poco96_set.exclude(
            amostra__codigo_amostra__icontains='NTC'
        ).count()

class Placa384(EmpresaMixin, models.Model):
    projeto = models.ForeignKey('Projeto', on_delete=models.CASCADE)
    codigo_placa = models.CharField(
        max_length=20,
        help_text='Código identificador da placa de 384 poços'
    )
    data_criacao = models.DateTimeField(auto_now_add=True)
    observacoes = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        unique_together = ['empresa', 'projeto', 'codigo_placa']
        verbose_name = 'Placa  384'
        verbose_name_plural = 'Placas  384'

    def __str__(self):
        return f"{self.empresa.codigo}-{self.projeto.codigo_projeto}-384-{self.codigo_placa}"

    def get_placas_96_origem(self):
        return Placa96.objects.filter(
            placamap384__placa_destino=self
        ).order_by('placamap384__quadrante')

    def get_amostras_count(self):
        """Retorna a contagem de amostras, excluindo os NTCs"""
        return self.poco384_set.exclude(
            amostra__codigo_amostra__icontains='NTC'
        ).count()

    CONTROL_WELL_POSITIONS = ['A01', 'B01', 'C01', 'D01']
    WELLS_PER_PLATE = 96

    def calculate_384_well_position(self, row_96, col_96, plate_index):
        """Calcula a nova posição do poço na placa 384"""
        if plate_index == 0:  # Primeira placa
            new_row = row_96 * 2
            new_col = col_96 * 2
        elif plate_index == 1:  # Segunda placa
            new_row = row_96 * 2 + 1
            new_col = col_96 * 2 
        elif plate_index == 2:  # Terceira placa
            new_row = row_96 * 2 
            new_col = col_96 * 2 + 1
        else:  # Quarta placa
            new_row = row_96 * 2 + 1
            new_col = col_96 * 2 + 1
        
        return f"{chr(ord('A') + new_row)}{str(new_col + 1).zfill(2)}"

    def transfer_96_to_384(self, placas_96_list):
        try:
            with transaction.atomic():
                if not placas_96_list:
                    raise ValidationError("Nenhuma placa 96 selecionada.")
                
                # Aceita de 1 a 4 placas
                for index, placa_96 in enumerate(placas_96_list[:4], start=1):  # Máximo 4 placas
                    quadrante = index  # Posição 1-4 conforme a ordem das placas
                    
                    # Criar mapeamento
                    PlacaMap384.objects.create(
                        empresa=self.empresa,
                        placa_origem=placa_96,
                        placa_destino=self,
                        quadrante=quadrante
                    )
                    
                    # Transferir poços (mesma lógica de intercalação)
                    for poco_96 in placa_96.poco96_set.all():
                        nova_pos = self.calculate_384_well_position(
                            ord(poco_96.posicao[0]) - ord('A'),  # Linha original (0-7)
                            int(poco_96.posicao[1:]) - 1,        # Coluna original (0-11)
                            quadrante - 1                        # Índice 0-3
                        )
                        Poco384.objects.create(
                            empresa=self.empresa,
                            placa=self,
                            amostra=poco_96.amostra,
                            posicao=nova_pos
                        )
                    
                    # Inativar placa 96
                    placa_96.is_active = False
                    placa_96.save()
                    
        except Exception as e:
            raise ValidationError(f"Erro na transferência: {str(e)}")

    def transfer_384_to_384(self, placa_destino):
        """Transfere os poços e amostras desta placa para uma nova placa 384"""
        try:
            with transaction.atomic():
                # Criar mapeamento
                PlacaMap384to384.objects.create(
                    empresa=self.empresa,
                    placa_origem=self,
                    placa_destino=placa_destino
                )
                
                # Copiar poços e amostras
                for poco_origem in self.poco384_set.all():
                    Poco384.objects.create(
                        empresa=self.empresa,
                        placa=placa_destino,
                        amostra=poco_origem.amostra,
                        posicao=poco_origem.posicao
                    )
                
                # Inativar placa origem
                self.is_active = False
                self.save()
                
        except Exception as e:
            raise ValidationError(f"Erro na transferência: {str(e)}")


class Placa1536(EmpresaMixin, models.Model):
    projeto = models.ForeignKey('Projeto', on_delete=models.CASCADE)
    codigo_placa = models.CharField(
        max_length=20,
        help_text='Código identificador da placa de 1536 poços'
    )
    data_criacao = models.DateTimeField(auto_now_add=True)
    observacoes = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        unique_together = ['empresa', 'projeto', 'codigo_placa']
        verbose_name = 'Placa 1536'
        verbose_name_plural = 'Placas 1536'

    def __str__(self):
        return f"{self.empresa.codigo}-{self.projeto.codigo_projeto}-1536-{self.codigo_placa}"

    def get_placas_384_origem(self):
        return Placa384.objects.filter(
            placamap1536__placa_destino=self
        ).order_by('placamap1536__quadrante')

    def get_amostras_count(self):
        """Retorna a contagem de amostras, excluindo os NTCs"""
        return self.poco1536_set.exclude(
            amostra__codigo_amostra__icontains='NTC'
        ).count()

    # models.py - na classe Placa1536

    def calculate_1536_well_position(self, row_384, col_384, plate_index):
        """Calcula a nova posição do poço na placa 1536"""
        if plate_index == 0:  # Primeira placa
            new_row = row_384 * 2
            new_col = col_384 * 2
        elif plate_index == 1:  # Segunda placa
            new_row = row_384 * 2 + 1
            new_col = col_384 * 2 
        elif plate_index == 2:  # Terceira placa
            new_row = row_384 * 2 
            new_col = col_384 * 2 + 1
        else:  # Quarta placa
            new_row = row_384 * 2 + 1
            new_col = col_384 * 2 + 1
        
        # Converter número da linha para formato de letra(s)
        row_letter = ''
        while new_row >= 0:
            row_letter = chr(65 + (new_row % 26)) + row_letter
            new_row = (new_row // 26) - 1
        
        return f"{row_letter}{str(new_col + 1).zfill(2)}"

    def transfer_384_to_1536(self, placas_384_list):
        """Transfere amostras de placas 384 para uma placa 1536"""
        try:
            with transaction.atomic():
                if not placas_384_list:
                    raise ValidationError("Nenhuma placa 384 selecionada.")
                
                # Aceita de 1 a 4 placas
                for index, placa_384 in enumerate(placas_384_list[:4], start=1):
                    quadrante = index
                    
                    # Criar mapeamento
                    PlacaMap1536.objects.create(
                        empresa=self.empresa,
                        placa_origem=placa_384,
                        placa_destino=self,
                        quadrante=quadrante
                    )
                    
                    # Transferir poços
                    for poco_384 in placa_384.poco384_set.all():
                        # Extrair linha e coluna da posição original
                        row_384 = ord(poco_384.posicao[0]) - ord('A')
                        col_384 = int(poco_384.posicao[1:]) - 1
                        
                        # Calcular nova posição
                        nova_pos = self.calculate_1536_well_position(
                            row_384,
                            col_384,
                            quadrante - 1
                        )
                        
                        # Criar novo poço
                        Poco1536.objects.create(
                            empresa=self.empresa,
                            placa=self,
                            amostra=poco_384.amostra,
                            posicao=nova_pos
                        )
                    
                    # Inativar placa 384
                    placa_384.is_active = False
                    placa_384.save()
                    
        except Exception as e:
            raise ValidationError(f"Erro na transferência: {str(e)}")

# POÇOS

class Poco96(EmpresaMixin, models.Model):
    placa = models.ForeignKey(Placa96, on_delete=models.CASCADE)
    amostra = models.ForeignKey(
        Amostra, 
        on_delete=models.CASCADE,
        null=True,  # Adicione isso
        blank=True)  # E isso)
    posicao = models.CharField(
        max_length=3,
        help_text='Posição do poço (ex: A01, H12)'
    )

    class Meta:
        unique_together = ['placa', 'posicao']
        verbose_name = 'Poço de Placa   96'
        verbose_name_plural = 'Poços de Placas   96'

    def __str__(self):
        return f"{self.placa.codigo_placa} - {self.posicao}"

    def clean(self):
        if not self.posicao:
            return
        # Validar formato da posição (A01-H12)
        linha = self.posicao[0].upper()
        coluna = self.posicao[1:].zfill(2)
        if not (linha in 'ABCDEFGH' and coluna.isdigit() and 1 <= int(coluna) <= 12):
            raise ValidationError({
                'posicao': _('Posição inválida. Use formato A01-H12.')
            })

class Poco384(EmpresaMixin, models.Model):
    placa = models.ForeignKey(Placa384, on_delete=models.CASCADE)
    amostra = models.ForeignKey(Amostra, on_delete=models.CASCADE)
    posicao = models.CharField(
        max_length=3,
        help_text='Posição do poço (ex: A01, P24)'
    )

    class Meta:
        unique_together = ['placa', 'posicao']
        verbose_name = 'Poço de placa  384'
        verbose_name_plural = 'Poços de Placas  384'

    def __str__(self):
        return f"{self.placa.codigo_placa} - {self.posicao}"

    def clean(self):
        if not self.posicao:
            return
        # Validar formato da posição (A01-P24)
        linha = self.posicao[0].upper()
        coluna = self.posicao[1:]
        if not (linha in 'ABCDEFGHIJKLMNOP' and coluna.isdigit() and 1 <= int(coluna) <= 24):
            raise ValidationError({
                'posicao': _('Posição inválida. Use formato A01-P24.')
            })

class Poco1536(EmpresaMixin, models.Model):
    placa = models.ForeignKey(Placa1536, on_delete=models.CASCADE)
    amostra = models.ForeignKey(Amostra, on_delete=models.CASCADE)
    posicao = models.CharField(
        max_length=4,
        help_text='Posição do poço (ex: A01, AF48)'
    )

    class Meta:
        unique_together = ['placa', 'posicao']
        verbose_name = 'Poço de placa 1536'
        verbose_name_plural = 'Poços de Placas 1536'

    def __str__(self):
        return f"{self.placa.codigo_placa} - {self.posicao}"

    def clean(self):
        if not self.posicao:
            return
        # Validar formato da posição (A01-AF48)
        linha = self.posicao[0:2].upper()
        coluna = self.posicao[2:]
        linhas_validas = [chr(i) + (chr(j) if j else '') for i in range(65, 91) for j in range(65, 71)]
        if not (linha in linhas_validas and coluna.isdigit() and 1 <= int(coluna) <= 48):
            raise ValidationError({
                'posicao': _('Posição inválida. Use formato A01-AF48.')
            })

# MAPEAMENTO

class PlacaMap384(EmpresaMixin, models.Model):
    placa_origem = models.ForeignKey(Placa96, on_delete=models.CASCADE)
    placa_destino = models.ForeignKey(Placa384, on_delete=models.CASCADE)
    quadrante = models.IntegerField(
        choices=[(i, f"Quadrante {i}") for i in range(1, 5)],
        help_text='Quadrante da placa 384 (1-4)'
    )

    class Meta:
        unique_together = [
            ['placa_origem', 'placa_destino'],
            ['placa_destino', 'quadrante']
        ]
        verbose_name = 'Mapeamento 96->384'
        verbose_name_plural = 'Mapeamentos 96->384'

    def __str__(self):
        return f"{self.placa_origem} -> {self.placa_destino} (Q{self.quadrante})"

    def clean(self):
        if self.placa_origem.projeto != self.placa_destino.projeto:
            raise ValidationError(_('As placas devem pertencer ao mesmo projeto.'))

class PlacaMap1536(EmpresaMixin, models.Model):
    placa_origem = models.ForeignKey(Placa384, on_delete=models.CASCADE)
    placa_destino = models.ForeignKey(Placa1536, on_delete=models.CASCADE)
    quadrante = models.IntegerField(
        choices=[(i, f"Quadrante {i}") for i in range(1, 5)],
        help_text='Quadrante da placa 1536 (1-4)'
    )

    class Meta:
        unique_together = [
            ['placa_origem', 'placa_destino'],
            ['placa_destino', 'quadrante']
        ]
        verbose_name = 'Mapeamento 384->1536'
        verbose_name_plural = 'Mapeamentos 384->1536'

    def __str__(self):
        return f"{self.placa_origem} -> {self.placa_destino} (Q{self.quadrante})"

    def clean(self):
        if self.placa_origem.projeto != self.placa_destino.projeto:
            raise ValidationError(_('As placas devem pertencer ao mesmo projeto.'))

class PlacaMap384to384(EmpresaMixin, models.Model):
    placa_origem = models.ForeignKey(Placa384, on_delete=models.CASCADE, related_name='origem_maps')
    placa_destino = models.ForeignKey(Placa384, on_delete=models.CASCADE, related_name='destino_maps')
    data_transferencia = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = [
            ['placa_origem', 'placa_destino'],
            ['empresa', 'placa_destino']
        ]
        verbose_name = 'Mapeamento 384->384'
        verbose_name_plural = 'Mapeamentos 384->384'

    def __str__(self):
        return f"{self.placa_origem} -> {self.placa_destino}"

    def clean(self):
        if not self.placa_origem or not self.placa_destino:
            return
            
        if self.placa_origem.empresa != self.placa_destino.empresa:
            raise ValidationError('As placas devem pertencer à mesma empresa.')
            
        if self.placa_origem.projeto != self.placa_destino.projeto:
            raise ValidationError('As placas devem pertencer ao mesmo projeto.')
            
        if self.placa_origem == self.placa_destino:
            raise ValidationError('A placa destino deve ser diferente da placa origem.')
            
        if not Poco384.objects.filter(placa=self.placa_origem).exists():
            raise ValidationError('A placa origem deve conter poços com amostras.')
            
        if Poco384.objects.filter(placa=self.placa_destino).exists():
            raise ValidationError('A placa destino deve estar vazia.')
            
        if self.placa_destino.codigo_placa == self.placa_origem.codigo_placa:
            raise ValidationError('O código da placa destino deve ser diferente da origem.')
            
        if PlacaMap384to384.objects.filter(placa_origem=self.placa_origem).exists():
            raise ValidationError('Esta placa origem já foi utilizada em outra transferência.')

# RESULTADO

class Resultado(EmpresaMixin, models.Model):
    amostra = models.ForeignKey(Amostra, on_delete=models.CASCADE)
    poco_96 = models.ForeignKey(Poco96, on_delete=models.CASCADE, null=True, blank=True)
    poco_384 = models.ForeignKey(Poco384, on_delete=models.CASCADE, null=True, blank=True)
    poco_1536 = models.ForeignKey(Poco1536, on_delete=models.CASCADE, null=True, blank=True)
    valor = models.FloatField(help_text='Valor do resultado')
    data_resultado = models.DateTimeField(auto_now_add=True)
    observacoes = models.TextField(blank=True, null=True)

    class Meta:
        verbose_name = 'Resultado'
        verbose_name_plural = 'Resultados'

    def __str__(self):
        poco = self.poco_96 or self.poco_384 or self.poco_1536
        return f"{self.amostra} - {poco} = {self.valor}"

    def clean(self):
        # Garantir que apenas um tipo de poço está associado
        pocos = [self.poco_96, self.poco_384, self.poco_1536]
        if len([p for p in pocos if p is not None]) != 1:
            raise ValidationError(_('Associe exatamente um tipo de poço ao resultado.'))


