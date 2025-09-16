import logging
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, JsonResponse
from django.template.loader import render_to_string
from django.db import transaction
from app.models import Empresa, Projeto, Placa96, Placa384, Placa1536

logger = logging.getLogger(__name__)

@login_required
def criar_placas_1536_htmx(request):
    """View para a página principal de criação de placas 1536 com HTMX."""
    # Obtém as empresas que o usuário tem acesso
    if request.user.is_superuser:
        empresas = Empresa.objects.all()
    else:
        empresas = request.user.empresas.all()
    
    return render(request, 'criar_placas_1536_htmx.html', {
        'empresas': empresas
    })

@login_required
def carregar_projetos_por_empresa(request):
    """Carrega os projetos associados a uma empresa via HTMX."""
    empresa_id = request.GET.get('empresa')
    
    logger.info(f"Carregando projetos para empresa_id: {empresa_id}")
    
    if not empresa_id:
        return HttpResponse("<p>Selecione uma empresa válida</p>")
    
    try:
        empresa = Empresa.objects.get(id=empresa_id)
        
        # Verifica se o usuário tem acesso à empresa
        if not request.user.is_superuser and empresa not in request.user.empresas.all():
            logger.warning(f"Usuário {request.user} sem permissão para empresa {empresa}")
            return HttpResponse("<p class='text-danger'>Você não tem permissão para acessar esta empresa.</p>")
        
        # Obtém os projetos da empresa
        projetos = Projeto.objects.filter(empresa=empresa).order_by('codigo_projeto')
        logger.info(f"Encontrados {projetos.count()} projetos para a empresa {empresa}")
        
        # Log para depuração - removemos a referência ao nome do projeto
        for projeto in projetos:
            logger.info(f"Projeto: {projeto.id} - {projeto.codigo_projeto}")
        
        html = render_to_string('partials/projetos_por_empresa.html', {
            'projetos': projetos
        })
        return HttpResponse(html)
    
    except Empresa.DoesNotExist:
        logger.error(f"Empresa {empresa_id} não encontrada")
        return HttpResponse("<p class='text-danger'>Empresa não encontrada.</p>")
    except Exception as e:
        import traceback
        traceback_str = traceback.format_exc()
        logger.error(f"Erro ao carregar projetos: {str(e)}", exc_info=True)
        return HttpResponse(f"<p class='text-danger'>Erro ao carregar projetos: {str(e)}</p><pre>{traceback_str}</pre>")

@login_required
def carregar_placas_384_por_projeto(request):
    """Carrega as placas 384 de um projeto selecionado via HTMX."""
    projeto_id = request.GET.get('projeto')
    
    logger.info(f"Tentando carregar placas para projeto_id: {projeto_id}")
    
    if not projeto_id:
        return HttpResponse("<p>Selecione um projeto válido</p>")
    
    try:
        projeto = Projeto.objects.get(id=projeto_id)
        logger.info(f"Projeto encontrado: {projeto.codigo_projeto}")
        
        # Verifica se o usuário tem acesso à empresa do projeto
        if not request.user.is_superuser and projeto.empresa not in request.user.empresas.all():
            logger.warning(f"Usuário {request.user} sem permissão para projeto {projeto.codigo_projeto}")
            return HttpResponse("<p class='text-danger'>Você não tem permissão para acessar este projeto.</p>")
        
        # Obtém as placas 384 do projeto - apenas placas ativas
        placas_384 = Placa384.objects.filter(
            projeto=projeto,
            is_active=True
        ).order_by('codigo_placa')
        
        logger.info(f"Encontradas {placas_384.count()} placas para o projeto {projeto.codigo_projeto}")
        logger.info(f"Primeiras 5 placas: {[p.codigo_placa for p in placas_384[:5]]}")

        # Alterando aqui para usar o template de listagem de placas
        html = render_to_string('partials/placas_384_listagem.html', {
            'placas_384': placas_384,
            'projeto': projeto
        })
        return HttpResponse(html)
    
    except Projeto.DoesNotExist:
        logger.error(f"Projeto {projeto_id} não encontrado")
        return HttpResponse("<p class='text-danger'>Projeto não encontrado.</p>")
    except Exception as e:
        import traceback
        traceback_str = traceback.format_exc()
        logger.error(f"Erro ao carregar placas: {str(e)}", exc_info=True)
        return HttpResponse(f"<p class='text-danger'>Erro ao carregar placas: {str(e)}</p><pre>{traceback_str}</pre>")

@login_required
def criar_placas_1536(request):
    """Cria placas 1536 a partir das placas 384 selecionadas via HTMX POST."""
    if request.method != 'POST':
        error_html = render_to_string('partials/resultado_criar_placas_1536.html', {
            'sucesso': False,
            'mensagem': 'Método não permitido.'
        })
        return HttpResponse(error_html, status=405)
    
    projeto_id = request.POST.get('projeto_id')
    placas_384_ids_str = request.POST.getlist('placas_384')
    
    if not projeto_id:
        error_html = render_to_string('partials/resultado_criar_placas_1536.html', {
            'sucesso': False,
            'mensagem': 'Projeto não especificado.'
        })
        return HttpResponse(error_html, status=400)

    if not placas_384_ids_str:
        error_html = render_to_string('partials/resultado_criar_placas_1536.html', {
            'sucesso': False,
            'mensagem': 'Nenhuma placa 384 selecionada.'
        })
        return HttpResponse(error_html, status=400)
    
    try:
        # Buscar objetos do banco
        projeto = Projeto.objects.get(id=projeto_id)
        empresa = projeto.empresa

        # Verificar se o usuário tem permissão para esta empresa
        if not request.user.is_superuser and empresa not in request.user.empresas.all():
            error_html = render_to_string('partials/resultado_criar_placas_1536.html', {
                'sucesso': False,
                'mensagem': 'Você não tem permissão para acessar esta empresa.'
            })
            return HttpResponse(error_html, status=403)
        
        placas_1536_criadas = []
        
        try:
            placas_384_ids = [int(pid) for pid in placas_384_ids_str]
        except ValueError:
            error_html = render_to_string('partials/resultado_criar_placas_1536.html', {
                'sucesso': False,
                'mensagem': 'IDs de placas 384 inválidos.'
            })
            return HttpResponse(error_html, status=400)

        placas_384 = list(Placa384.objects.filter(id__in=placas_384_ids, projeto=projeto, is_active=True).order_by('codigo_placa'))
     
        if not placas_384:
            error_html = render_to_string('partials/resultado_criar_placas_1536.html', {
                'sucesso': False,
                'mensagem': 'Nenhuma placa 384 ativa encontrada para os IDs fornecidos ou para este projeto.'
            })
            return HttpResponse(error_html, status=400)

        # Criar placas 1536 em grupos de 4 placas 384
        with transaction.atomic():
            for i in range(0, len(placas_384), 4):
                grupo_placas = placas_384[i:min(i+4, len(placas_384))]

                # Gerar código baseado na primeira e última placa do grupo
                primeira_placa = grupo_placas[0].codigo_placa
                ultima_placa = grupo_placas[-1].codigo_placa
                
                # Extrair os últimos 3 dígitos de cada código
                primeira_numero = primeira_placa.split('-')[-1][-3:]
                ultima_numero = ultima_placa.split('-')[-1][-3:]
                codigo_placa_1536 = f"{primeira_numero}-{ultima_numero}"
                
                # Criar a placa 1536
                placa_1536 = Placa1536.objects.create(
                    empresa=empresa,
                    projeto=projeto,
                    codigo_placa=codigo_placa_1536,
                )

                # Transferir as placas 384 para a placa 1536
                placa_1536.transfer_384_to_1536(grupo_placas)
                placas_1536_criadas.append(placa_1536)

                # Inativar as placas 384 utilizadas
                for placa_384_obj in grupo_placas: # Renamed to avoid conflict with outer scope if any
                    placa_384_obj.is_active = False
                    placa_384_obj.save()

        # Retornar o resultado
        html = render_to_string('partials/resultado_criar_placas_1536.html', {
            'sucesso': True,
            'placas_1536_criadas': placas_1536_criadas,
            'placas_384_processadas': len(placas_384)
        })
        return HttpResponse(html)
    
    except Projeto.DoesNotExist:
        logger.error(f"Projeto {projeto_id} não encontrado ao tentar criar placas 1536.")
        error_html = render_to_string('partials/resultado_criar_placas_1536.html', {
            'sucesso': False,
            'mensagem': 'Projeto não encontrado.'
        })
        return HttpResponse(error_html, status=404)
    except Exception as e:
        import traceback
        traceback_str = traceback.format_exc()
        logger.error(f"Erro ao criar placa 1536: {str(e)}\n{traceback_str}")
        error_html = render_to_string('partials/resultado_criar_placas_1536.html', {
            'sucesso': False,
            'mensagem': f'Erro interno ao criar placa 1536.'
        })
        return HttpResponse(error_html, status=500)

@login_required
def criar_placas_1536_lote(request):
    """
    View para criar múltiplas placas 1536 em lote a partir das placas 384 selecionadas.
    """
    if request.method != 'POST':
        return render(request, 'partials/resultado_criacao_placa.html', {
            'sucesso': False,
            'mensagem': 'Método não permitido.'
        }, status=405)
    
    try:
        projeto_id = request.POST.get('projeto_id')
        placas_384_ids_str = request.POST.getlist('placas_384')
        
        if not projeto_id or not placas_384_ids_str:
            return render(request, 'partials/resultado_criacao_placa.html', {
                'sucesso': False,
                'mensagem': 'Projeto não especificado ou nenhuma placa 384 selecionada.'
            }, status=400)
        
        projeto = Projeto.objects.get(id=projeto_id)
        empresa = projeto.empresa
        
        # Verificar permissões
        if not request.user.is_superuser and empresa not in request.user.empresas.all():
            return render(request, 'partials/resultado_criacao_placa.html', {
                'sucesso': False,
                'mensagem': 'Sem permissão para esta operação.'
            }, status=403)
        
        placas_1536_criadas = []
        
        try:
            placas_384_ids = [int(pid) for pid in placas_384_ids_str]
        except ValueError:
            return render(request, 'partials/resultado_criacao_placa.html', {
                'sucesso': False,
                'mensagem': 'IDs de placas 384 inválidos.'
            }, status=400)

        placas_384 = list(Placa384.objects.filter(id__in=placas_384_ids, projeto=projeto, is_active=True).order_by('codigo_placa'))

        if not placas_384:
            return render(request, 'partials/resultado_criacao_placa.html', {
                'sucesso': False,
                'mensagem': 'Nenhuma placa 384 ativa encontrada para os IDs fornecidos ou para este projeto.'
            }, status=400)

        with transaction.atomic():
            # Criar placas 1536 com as placas disponíveis
            for i in range(0, len(placas_384), 4):
                grupo_placas = placas_384[i:min(i+4, len(placas_384))]
                
                # Gerar código usando primeira e última placa do grupo
                primeira_placa = grupo_placas[0].codigo_placa.split('-')[0] #[-1]
                ultima_placa = grupo_placas[-1].codigo_placa.split('-')[-1]
                codigo_placa = f"{primeira_placa}-{ultima_placa}"
                
                # Criar placa 1536
                placa_1536 = Placa1536.objects.create(
                    empresa=empresa,
                    projeto=projeto,
                    codigo_placa=codigo_placa
                )
                
                # Transferir as placas 384 para a nova placa 1536
                placa_1536.transfer_384_to_1536(grupo_placas)
                placas_1536_criadas.append(placa_1536)
        
        return render(request, 'partials/resultado_criacao_placa.html', {
            'sucesso': True,
            'placas_1536_criadas': placas_1536_criadas,
            'placas_384_processadas': len(placas_384)
        })

    except Projeto.DoesNotExist:
        logger.error(f"Projeto {projeto_id} não encontrado em criar_placas_1536_lote.")
        return render(request, 'partials/resultado_criacao_placa.html', {
            'sucesso': False,
            'mensagem': 'Projeto não encontrado.'
        }, status=404)
    except Exception as e:
        import traceback
        logger.error(f"Erro ao criar placas 1536 em lote: {str(e)}\n{traceback.format_exc()}")
        return render(request, 'partials/resultado_criacao_placa.html', {
            'sucesso': False,
            'mensagem': f'Erro interno ao criar placas.'
        }, status=500)