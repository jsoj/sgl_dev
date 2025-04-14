from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.db import transaction
from django.core.exceptions import ValidationError
from app.models import Empresa, Projeto, Placa96, Placa384

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

                if Placa384.objects.filter(codigo_placa=codigo_placa_384, projeto=projeto, empresa=empresa).exists():
                    raise ValidationError('Já existe uma placa 384 com este código para este projeto.')

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
            messages.error(request, f'Erro ao criar placa: {str(e)}')

    # Se for GET ou se houver erro no POST, renderiza o formulário
    if request.user.is_superuser:
        empresas = Empresa.objects.all()
    else:
        empresas = Empresa.objects.filter(id=request.user.empresa.id)

    return render(request, 'criar_placa_384.html', {'empresas': empresas})