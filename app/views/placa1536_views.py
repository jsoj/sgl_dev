from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.db import transaction
from django.core.exceptions import ValidationError
from app.models import Empresa, Projeto, Placa96, Placa1536, ResultadoUpload1536
import logging
from app.servico import processar_arquivo_1536

logger = logging.getLogger(__name__)

@login_required
def criar_placa_1536(request):
    """View para criação de placas 1536"""
    if request.method == 'POST':
        try:
            with transaction.atomic():
                empresa_id = request.POST.get('empresa')
                projeto_id = request.POST.get('projeto')
                placas_ids = request.POST.getlist('placas[]')
                codigo_placa_1536 = request.POST.get('codigo_placa_1536')

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

                if Placa1536.objects.filter(codigo_placa=codigo_placa_1536, projeto=projeto, empresa=empresa).exists():
                    raise ValidationError('Já existe uma placa 1536 com este código para este projeto.')

                # Criar nova placa 1536
                placa_1536 = Placa1536.objects.create(
                    empresa=empresa,
                    projeto=projeto,
                    codigo_placa=codigo_placa_1536
                )

                # Realizar transferência
                placa_1536.transfer_96_to_1536(placas_96)

                messages.success(request, 'Placa 1536 criada com sucesso!')
                return redirect('home')

        except ValidationError as e:
            messages.error(request, str(e))
        except Exception as e:
            messages.error(request, f'Erro ao criar placa: {str(e)}')

    # Se for GET ou se houver erro no POST, renderiza o formulário
    if request.user.is_superuser:
        empresas = Empresa.objects.all()
    else:
        empresas = Empresa.objects.filter(id=request.user.empresa.id)

    return render(request, 'criar_placa_1536.html', {'empresas': empresas})

@login_required
def processar_arquivo_1536_view(request, object_id):
    try:
        # Log para debugging
        logger.info(f"View processar_arquivo_1536 chamada para ID: {object_id}")
        
        # Chamar a função de processamento
        stats = processar_arquivo_1536(object_id)
        
        # Mensagem de sucesso
        mensagem = (
            f"Arquivo processado com sucesso. "
            f"Total de registros: {stats['total_registros']}, "
            f"Registros criados: {stats['registros_criados']}, "
            f"Registros duplicados: {stats['registros_duplicados']}"
        )
        messages.success(request, mensagem)
        
    except Exception as e:
        logger.exception(f"Erro ao processar arquivo ID {object_id}: {str(e)}")
        messages.error(request, f"Erro ao processar arquivo: {str(e)}")
    
    # Redirecionar para a lista
    return redirect("admin:app_resultadoupload1536_changelist")