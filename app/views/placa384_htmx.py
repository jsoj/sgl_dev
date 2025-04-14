import logging
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, JsonResponse
from django.template.loader import render_to_string
from django.db import transaction
from app.models import Empresa, Projeto, Placa96, Placa384

logger = logging.getLogger(__name__)

@login_required
def criar_placas_384_htmx(request):
    """View para a página principal de criação de placas 384 com HTMX."""
    # Obtém as empresas que o usuário tem acesso
    if request.user.is_superuser:
        empresas = Empresa.objects.all()
    else:
        empresas = request.user.empresas.all()
    
    return render(request, 'criar_placas_384_htmx.html', {
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
def carregar_placas_por_projeto(request):
    """Carrega as placas 96 de um projeto selecionado via HTMX."""
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
        
        # Obtém as placas 96 do projeto - apenas placas ativas
        placas_96 = Placa96.objects.filter(
            projeto=projeto,
            is_active=True
        ).order_by('codigo_placa')
        
        logger.info(f"Encontradas {placas_96.count()} placas para o projeto {projeto.codigo_projeto}")
        logger.info(f"Primeiras 5 placas: {[p.codigo_placa for p in placas_96[:5]]}")
        
        # Alterando aqui para usar o template de listagem de placas
        html = render_to_string('partials/placas_96_listagem.html', {
            'placas_96': placas_96,
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
def criar_placas_384(request):
    """Cria placas 384 a partir das placas 96 selecionadas via HTMX POST."""
    if request.method != 'POST':
        return HttpResponse("<p class='text-danger'>Método não permitido.</p>")
    
    projeto_id = request.POST.get('projeto_id')
    placas_96_ids = request.POST.getlist('placas_96')
    codigo_placa_384 = request.POST.get('codigo_placa_384')
    
    if not projeto_id:
        return HttpResponse("<p class='text-danger'>Projeto não especificado.</p>")
        
    if not codigo_placa_384:
        return HttpResponse("<p class='text-danger'>Código da placa 384 não especificado.</p>")
    
    if len(placas_96_ids) != 4:
        return HttpResponse("<p class='text-danger'>Selecione exatamente 4 placas 96.</p>")
    
    try:
        # Buscar objetos do banco
        projeto = Projeto.objects.get(id=projeto_id)
        empresa = projeto.empresa
        placas_96 = list(Placa96.objects.filter(id__in=placas_96_ids))
        
        # Verificar se o usuário tem permissão para esta empresa
        if not request.user.is_superuser and empresa not in request.user.empresas.all():
            return HttpResponse("<p class='text-danger'>Você não tem permissão para acessar esta empresa.</p>")
        
        # Verificar se já existe uma placa 384 com o mesmo código
        if Placa384.objects.filter(codigo_placa=codigo_placa_384, projeto=projeto, empresa=empresa).exists():
            return HttpResponse("<p class='text-danger'>Já existe uma placa 384 com este código para este projeto.</p>")
        
        # Criar a placa 384
        with transaction.atomic():
            placa_384 = Placa384.objects.create(
                empresa=empresa,
                projeto=projeto,
                codigo_placa=codigo_placa_384,
            )
            
            # Transferir as placas 96 para a placa 384
            placa_384.transfer_96_to_384(placas_96)
            
            # Retornar o resultado
            html = render_to_string('partials/resultado_criar_placas_384.html', {
                'placas_384_criadas': [placa_384],
                'placas_96_processadas': len(placas_96)
            })
            return HttpResponse(html)
    
    except Exception as e:
        import traceback
        traceback_str = traceback.format_exc()
        return HttpResponse(f"<p class='text-danger'>Erro ao criar placa 384: {str(e)}</p><pre>{traceback_str}</pre>")

@login_required
def criar_placas_384_lote(request):
    """Cria múltiplas placas 384 em lote a partir das placas 96 selecionadas."""
    if request.method != 'POST':
        return HttpResponse("<p class='text-danger'>Método não permitido.</p>")
    
    projeto_id = request.POST.get('projeto_id')
    placas_96_ids = request.POST.getlist('placas_96')
    codigo_placa_384 = request.POST.get('codigo_placa_384')
    
    if not projeto_id:
        return HttpResponse("<p class='text-danger'>Projeto não especificado.</p>")
        
    if not codigo_placa_384:
        return HttpResponse("<p class='text-danger'>Código base da placa 384 não especificado.</p>")
    
    # Validar se a quantidade de placas é múltiplo de 4
    if len(placas_96_ids) < 4 or len(placas_96_ids) % 4 != 0:
        return HttpResponse("<p class='text-danger'>A quantidade de placas 96 deve ser múltiplo de 4.</p>")
    
    try:
        # Buscar objetos do banco
        projeto = Projeto.objects.get(id=projeto_id)
        empresa = projeto.empresa
        placas_96 = list(Placa96.objects.filter(id__in=placas_96_ids).order_by('codigo_placa'))
        
        # Verificar permissões
        if not request.user.is_superuser and empresa not in request.user.empresas.all():
            return HttpResponse("<p class='text-danger'>Você não tem permissão para acessar esta empresa.</p>")
        
        # Criar as placas 384 em lote
        placas_384_criadas = []
        
        with transaction.atomic():
            total_placas = len(placas_96)
            num_placas_384 = total_placas // 4
            
            for i in range(num_placas_384):
                # Gerar código para a placa 384
                codigo_incrementado = f"{codigo_placa_384}-{i+1:02d}"
                
                # Verificar se já existe uma placa com este código
                if Placa384.objects.filter(codigo_placa=codigo_incrementado, projeto=projeto).exists():
                    return HttpResponse(f"<p class='text-danger'>Já existe uma placa com o código {codigo_incrementado}. O processo foi abortado.</p>")
                
                # Criar a placa 384
                placa_384 = Placa384.objects.create(
                    empresa=empresa,
                    projeto=projeto,
                    codigo_placa=codigo_incrementado,
                    created_by=request.user
                )
                
                # Selecionar as próximas 4 placas para esta placa 384
                placas_para_transferir = placas_96[i*4:(i+1)*4]
                
                # Transferir as placas para a placa 384
                placa_384.transfer_96_to_384(placas_para_transferir)
                
                placas_384_criadas.append(placa_384)
        
        # Retornar resultado
        html = render_to_string('partials/resultado_criar_placas_384.html', {
            'placas_384_criadas': placas_384_criadas,
            'placas_96_processadas': total_placas
        })
        return HttpResponse(html)
        
    except Exception as e:
        import traceback
        traceback_str = traceback.format_exc()
        return HttpResponse(f"<p class='text-danger'>Erro ao criar placas em lote: {str(e)}</p><pre>{traceback_str}</pre>")