# forms.py
from django.db import models, transaction  # Adicione transaction aqui
from django import forms
from django.core.exceptions import ValidationError
from .models import Empresa, Projeto, Placa96, Placa384, PlacaMap384to384, Placa1536
import logging
logger = logging.getLogger(__name__)


class TransferPlacasForm(forms.Form):
   empresa = forms.ModelChoiceField(
       queryset=Empresa.objects.all(),
       label='Empresa',
       empty_label="Selecione uma empresa",
       help_text='Selecione a empresa para ver os projetos disponíveis'
   )
   
   projeto = forms.ModelChoiceField(
       queryset=Projeto.objects.none(),
       label='Projeto',
       empty_label="Selecione um projeto",
       help_text='Selecione o projeto para ver as placas disponíveis'
   )
   
   placa_1 = forms.ModelChoiceField(
       queryset=Placa96.objects.none(),
       label='Placa 96 (Posição 1)',
       help_text='Será intercalada em linhas/colunas pares',
       required=False
   )
   
   placa_2 = forms.ModelChoiceField(
       queryset=Placa96.objects.none(),
       label='Placa 96 (Posição 2)',
       help_text='Será intercalada em linhas pares/colunas ímpares',
       required=False
   )
   
   placa_3 = forms.ModelChoiceField(
       queryset=Placa96.objects.none(),
       label='Placa 96 (Posição 3)',
       help_text='Será intercalada em linhas ímpares/colunas pares',
       required=False
   )
   
   placa_4 = forms.ModelChoiceField(
       queryset=Placa96.objects.none(),
       label='Placa 96 (Posição 4)',
       help_text='Será intercalada em linhas/colunas ímpares',
       required=False
   )
   
   codigo_placa_384 = forms.CharField(
       max_length=20,
       label='Código da Nova Placa 384',
       help_text='Digite o código para a nova placa de 384 poços'
   )

   def __init__(self, user, *args, **kwargs):
       super().__init__(*args, **kwargs)
       
       # Configurar queryset de empresas baseado no usuário
       if user.is_superuser:
           self.fields['empresa'].queryset = Empresa.objects.all()
       else:
           self.fields['empresa'].queryset = Empresa.objects.filter(id=user.empresa.id)
           self.fields['empresa'].initial = user.empresa
           
       # Inicialmente, deixar campos dependentes vazios
       self.fields['projeto'].queryset = Projeto.objects.none()
       self.fields['placa_1'].queryset = Placa96.objects.none()
       self.fields['placa_2'].queryset = Placa96.objects.none()
       self.fields['placa_3'].queryset = Placa96.objects.none()
       self.fields['placa_4'].queryset = Placa96.objects.none()

       # Se dados foram fornecidos, configurar querysets relacionados
       if 'empresa' in self.data:
           try:
               empresa_id = int(self.data.get('empresa'))
               self.fields['projeto'].queryset = Projeto.objects.filter(
                   empresa_id=empresa_id, 
                   ativo=True
               )
           except (ValueError, TypeError):
               pass

       if 'projeto' in self.data:
           try:
               projeto_id = int(self.data.get('projeto'))
               placas_qs = Placa96.objects.filter(
                   projeto_id=projeto_id,
                   is_active=True
               )
               self.fields['placa_1'].queryset = placas_qs
               self.fields['placa_2'].queryset = placas_qs
               self.fields['placa_3'].queryset = placas_qs
               self.fields['placa_4'].queryset = placas_qs
           except (ValueError, TypeError):
               pass

   def clean(self):
       cleaned_data = super().clean()
       logger.info("metodo clean de transferplacasform  Dados do formulário validados: %s", cleaned_data)  # Log dos dados
       
       # Coletar todas as placas selecionadas (de 1 a 4)
       placas = [
            cleaned_data.get('placa_1'),
            cleaned_data.get('placa_2'),
            cleaned_data.get('placa_3'),
            cleaned_data.get('placa_4')
        ]
       placas = [placa for placa in placas if placa is not None]  # Filtrar nulos
       
       logger.info("metodo clean do formulario Placas selecionadas: %s", placas)  # Log das placas

       if not placas:
           logger.error("Nenhuma placa selecionada")  # Log de erro
           raise ValidationError('Selecione pelo menos uma placa.')

       # Verificar se placas são diferentes
       if len(set(placas)) != len(placas):
           raise ValidationError('Cada placa só pode ser usada uma vez.')

       empresa = cleaned_data.get('empresa')
       projeto = cleaned_data.get('projeto')
       codigo_placa_384 = cleaned_data.get('codigo_placa_384')

       # Validar se placas são do mesmo projeto/empresa
       for placa in placas:
           if placa.projeto != projeto:
               raise ValidationError('Todas as placas devem pertencer ao mesmo projeto.')
           if placa.empresa != empresa:
               raise ValidationError('Todas as placas devem pertencer à mesma empresa.')

       # Validar se o código da placa 384 é único
       if Placa384.objects.filter(codigo_placa=codigo_placa_384, empresa=empresa).exists():
           raise ValidationError('Já existe uma placa 384 com este código.')

       # Validar se as placas origem têm amostras
       for placa in placas:
           if not placa.poco96_set.exists():
               raise ValidationError(f'A placa {placa.codigo_placa} não possui amostras.')

       cleaned_data['placas'] = placas
       return cleaned_data

   def validate_placa(self, placa):
        """Valida uma    placa individual"""
        if not placa.is_active:
            raise ValidationError(f'A placa {placa.codigo_placa} já foi utilizada em outra transferência.')

        if not placa.poco96_set.exists():
            raise ValidationError(f'A placa {placa.codigo_placa} não possui poços com amostras.')

        return placa

   def save(self):
    """Cria a placa 384 e realiza a transferência"""
    empresa = self.cleaned_data['empresa']
    projeto = self.cleaned_data['projeto']
    codigo_placa_384 = self.cleaned_data['codigo_placa_384']
    placas = self.cleaned_data['placas']

    with transaction.atomic():
        # Criar placa 384
        placa_384 = Placa384.objects.create(
            empresa=empresa,
            projeto=projeto,
            codigo_placa=codigo_placa_384
        )

        # Realizar transferência
        placa_384.transfer_96_to_384(placas)

        return placa_384

    class Meta:
        fields = ['empresa', 'projeto', 'placa_1', 'placa_2', 'placa_3', 'placa_4', 'codigo_placa_384']
        labels = {
            'placa_1': 'Placa 96 (Quadrante 1 - Linhas pares, Colunas pares)',
            'placa_2': 'Placa 96 (Quadrante 2 - Linhas pares, Colunas ímpares)',
            'placa_3': 'Placa 96 (Quadrante 3 - Linhas ímpares, Colunas pares)',
            'placa_4': 'Placa 96 (Quadrante 4 - Linhas ímpares, Colunas ímpares)',
        }
        help_texts = {
            'placa_1': 'Amostras serão distribuídas nas posições A1, A3, C1, C3, etc.',
            'placa_2': 'Amostras serão distribuídas nas posições A2, A4, C2, C4, etc.',
            'placa_3': 'Amostras serão distribuídas nas posições B1, B3, D1, D3, etc.',
            'placa_4': 'Amostras serão distribuídas nas posições B2, B4, D2, D4, etc.',
        }


# forms.py

class Transfer384to384Form(forms.Form):
    empresa = forms.ModelChoiceField(
        queryset=Empresa.objects.all(),
        label='Empresa',
        empty_label="Selecione uma empresa",
        help_text='Selecione a empresa para ver os projetos disponíveis'
    )
    
    projeto = forms.ModelChoiceField(
        queryset=Projeto.objects.none(),
        label='Projeto',
        empty_label="Selecione um projeto",
        help_text='Selecione o projeto para ver as placas disponíveis'
    )
    
    placa_origem = forms.ModelChoiceField(
        queryset=Placa384.objects.none(),
        label='Placa 384 Origem',
        empty_label="Selecione a placa origem",
        help_text='Selecione a placa 384 que será copiada'
    )
    
    codigo_placa_384_destino = forms.CharField(
        max_length=20,
        label='Código da Nova Placa 384',
        help_text='Digite o código para a nova placa de 384 poços'
    )

# forms.py - na classe Transfer384to384Form

    def __init__(self, *args, user=None, **kwargs):
            self.user = user
            super().__init__(*args, **kwargs)
            
            # Configurar queryset de empresas baseado no usuário
            if self.user.is_superuser:
                self.fields['empresa'].queryset = Empresa.objects.all()
            else:
                self.fields['empresa'].queryset = Empresa.objects.filter(id=self.user.empresa.id)
                self.fields['empresa'].initial = self.user.empresa
                
            # Inicialmente, deixar campos dependentes vazios
            self.fields['projeto'].queryset = Projeto.objects.none()
            self.fields['placa_origem'].queryset = Placa384.objects.none()

            # Se dados foram fornecidos, configurar querysets relacionados
            if 'empresa' in self.data:
                try:
                    empresa_id = int(self.data.get('empresa'))
                    self.fields['projeto'].queryset = Projeto.objects.filter(
                        empresa_id=empresa_id,
                        ativo=True
                    )
                except (ValueError, TypeError):
                    pass

            if 'projeto' in self.data:
                try:
                    projeto_id = int(self.data.get('projeto'))
                    self.fields['placa_origem'].queryset = Placa384.objects.filter(
                        projeto_id=projeto_id,
                        is_active=True
                    )
                except (ValueError, TypeError):
                    pass

    def clean(self):
        cleaned_data = super().clean()
        empresa = cleaned_data.get('empresa')
        projeto = cleaned_data.get('projeto')
        placa_origem = cleaned_data.get('placa_origem')
        codigo_placa_384_destino = cleaned_data.get('codigo_placa_384_destino')

        if not placa_origem:
            raise ValidationError('Selecione uma placa origem.')

        # Validar se a placa é do mesmo projeto/empresa
        if placa_origem and placa_origem.projeto != projeto:
            raise ValidationError('A placa deve pertencer ao projeto selecionado.')
        
        if placa_origem and placa_origem.empresa != empresa:
            raise ValidationError('A placa deve pertencer à empresa selecionada.')

        # Validação mais detalhada do código da placa
        if codigo_placa_384_destino:
            # Verificar se já existe uma placa com este código na empresa
            placa_existente = Placa384.objects.filter(
                codigo_placa=codigo_placa_384_destino,
                empresa=empresa
            ).first()
            
            if placa_existente:
                raise ValidationError({
                    'codigo_placa_384_destino': 
                    f'Já existe uma placa com o código "{codigo_placa_384_destino}" '
                    f'nesta empresa (Projeto: {placa_existente.projeto.codigo_projeto}). '
                    'Por favor, escolha um código diferente.'
                })
            
            # Se quiser adicionar validação para o formato do código
            if not codigo_placa_384_destino.strip():
                raise ValidationError({
                    'codigo_placa_384_destino': 'O código da placa não pode estar em branco.'
                })

        # Validar se a placa origem tem amostras
        if not placa_origem.poco384_set.exists():
            raise ValidationError(f'A placa {placa_origem.codigo_placa} não possui amostras.')

        # Validar se a placa origem está ativa
        if not placa_origem.is_active:
            raise ValidationError(
                f'A placa {placa_origem.codigo_placa} está inativa. '
                'Não é possível usar uma placa inativa como origem.'
            )

        # Validar se a placa origem já foi usada em outra transferência
        if PlacaMap384to384.objects.filter(placa_origem=placa_origem).exists():
            raise ValidationError(
                f'A placa {placa_origem.codigo_placa} já foi utilizada como origem '
                'em outra transferência.'
            )

        return cleaned_data

# forms.py

class Transfer384to1536Form(forms.Form):
    empresa = forms.ModelChoiceField(
        queryset=Empresa.objects.all(),
        label='Empresa',
        empty_label="Selecione uma empresa",
        help_text='Selecione a empresa para ver os projetos disponíveis'
    )
    
    projeto = forms.ModelChoiceField(
        queryset=Projeto.objects.none(),
        label='Projeto',
        empty_label="Selecione um projeto",
        help_text='Selecione o projeto para ver as placas disponíveis'
    )
    
    placa_1 = forms.ModelChoiceField(
        queryset=Placa384.objects.none(),
        label='Placa 384 (Posição 1)',
        help_text='Será intercalada em linhas/colunas pares',
        required=False
    )
    
    placa_2 = forms.ModelChoiceField(
        queryset=Placa384.objects.none(),
        label='Placa 384 (Posição 2)',
        help_text='Será intercalada em linhas pares/colunas ímpares',
        required=False
    )
    
    placa_3 = forms.ModelChoiceField(
        queryset=Placa384.objects.none(),
        label='Placa 384 (Posição 3)',
        help_text='Será intercalada em linhas ímpares/colunas pares',
        required=False
    )
    
    placa_4 = forms.ModelChoiceField(
        queryset=Placa384.objects.none(),
        label='Placa 384 (Posição 4)',
        help_text='Será intercalada em linhas/colunas ímpares',
        required=False
    )
    
    codigo_placa_1536 = forms.CharField(
        max_length=20,
        label='Código da Nova Placa 1536',
        help_text='Digite o código para a nova placa de 1536 poços'
    )

    def __init__(self, *args, user=None, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)
        
        # Configurar queryset de empresas baseado no usuário
        if self.user.is_superuser:
            self.fields['empresa'].queryset = Empresa.objects.all()
        else:
            self.fields['empresa'].queryset = Empresa.objects.filter(id=self.user.empresa.id)
            self.fields['empresa'].initial = self.user.empresa
            
        # Inicialmente, deixar campos dependentes vazios
        self.fields['projeto'].queryset = Projeto.objects.none()
        self.fields['placa_1'].queryset = Placa384.objects.none()
        self.fields['placa_2'].queryset = Placa384.objects.none()
        self.fields['placa_3'].queryset = Placa384.objects.none()
        self.fields['placa_4'].queryset = Placa384.objects.none()

        # Se dados foram fornecidos, configurar querysets relacionados
        if 'empresa' in self.data:
            try:
                empresa_id = int(self.data.get('empresa'))
                self.fields['projeto'].queryset = Projeto.objects.filter(
                    empresa_id=empresa_id,
                    ativo=True
                )
            except (ValueError, TypeError):
                pass

        if 'projeto' in self.data:
            try:
                projeto_id = int(self.data.get('projeto'))
                placas_qs = Placa384.objects.filter(
                    projeto_id=projeto_id,
                    is_active=True
                )
                self.fields['placa_1'].queryset = placas_qs
                self.fields['placa_2'].queryset = placas_qs
                self.fields['placa_3'].queryset = placas_qs
                self.fields['placa_4'].queryset = placas_qs
            except (ValueError, TypeError):
                pass

    def clean(self):
        cleaned_data = super().clean()
        
        # Coletar todas as placas selecionadas (de 1 a 4)
        placas = [
            cleaned_data.get('placa_1'),
            cleaned_data.get('placa_2'),
            cleaned_data.get('placa_3'),
            cleaned_data.get('placa_4')
        ]
        placas = [placa for placa in placas if placa is not None]

        if not placas:
            raise ValidationError('Selecione pelo menos uma placa.')

        # Verificar se placas são diferentes
        if len(set(placas)) != len(placas):
            raise ValidationError('Cada placa só pode ser usada uma vez.')

        empresa = cleaned_data.get('empresa')
        projeto = cleaned_data.get('projeto')
        codigo_placa_1536 = cleaned_data.get('codigo_placa_1536')

        # Validar se as placas são do mesmo projeto/empresa
        for placa in placas:
            if placa.projeto != projeto:
                raise ValidationError('Todas as placas devem pertencer ao mesmo projeto.')
            if placa.empresa != empresa:
                raise ValidationError('Todas as placas devem pertencer à mesma empresa.')

        # Validar se o código da placa 1536 é único
        if Placa1536.objects.filter(codigo_placa=codigo_placa_1536, empresa=empresa).exists():
            raise ValidationError('Já existe uma placa 1536 com este código.')

        # Validar se as placas origem têm amostras
        for placa in placas:
            if not placa.poco384_set.exists():
                raise ValidationError(f'A placa {placa.codigo_placa} não possui amostras.')

        # Validar se as placas origem estão ativas
        for placa in placas:
            if not placa.is_active:
                raise ValidationError(
                    f'A placa {placa.codigo_placa} está inativa. '
                    'Não é possível usar uma placa inativa como origem.'
                )

        cleaned_data['placas'] = placas
        return cleaned_data