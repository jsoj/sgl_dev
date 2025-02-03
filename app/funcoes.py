# funcoes.py
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

def validar_data_recebimento(value):
    from .models import Projeto  # Import aqui para evitar importação circular
    
    def validate(self):
        if value and hasattr(self, 'data_envio') and self.data_envio and value < self.data_envio:
            raise ValidationError(
                _('A data de recebimento no laboratório não pode ser anterior à data de envio.'),
                code='invalid_data_recebimento'
            )
    return validate

def validar_data_liberacao(value):
    from .models import Projeto  # Import aqui para evitar importação circular
    
    def validate(self):
        if value and hasattr(self, 'data_recebimento_laboratorio') and \
           self.data_recebimento_laboratorio and value < self.data_recebimento_laboratorio:
            raise ValidationError(
                _('A data de liberação dos resultados não pode ser anterior à data de recebimento no laboratório.'),
                code='invalid_data_liberacao'
            )
    return validate