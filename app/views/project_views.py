from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
from django.contrib import messages
from django.urls import reverse
from django.http import HttpResponse
from django.db import transaction, IntegrityError
from django.core.exceptions import ValidationError
from app.models import Projeto, Empresa, Status, Cultivo, Tecnologia, MarcadorTrait, MarcadorCustomizado, Etapa
from django import forms
import logging
import csv
from io import StringIO
import datetime

logger = logging.getLogger(__name__)

class ProjetoForm(forms.ModelForm):
    class Meta:
        model = Projeto
        fields = [
            'codigo_projeto', 'responsavel', 'quantidade_amostras', 
            'cultivo', 'origem_amostra', 'nome_projeto_cliente', 
            'prioridade', 'codigo_ensaio', 'comentarios'
        ]

@login_required
def criar_projeto(request):
    """View para criação de projetos"""
    
    # Preparar objetos para o contexto do template
    context = {
        'empresas': Empresa.objects.filter(is_active=True),
        'cultivos': Cultivo.objects.filter(is_active=True),
        'tecnologias': Tecnologia.objects.filter(is_active=True),
        'marcador_traits': MarcadorTrait.objects.filter(is_active=True),
        'marcador_customizados': MarcadorCustomizado.objects.filter(is_active=True),
        'statuses': Status.objects.filter(is_active=True),
        'etapas': Etapa.objects.filter(is_active=True),
    }
    
    if request.method == 'POST':
        try:
            # Extrair dados básicos do projeto
            empresa_id = request.POST.get('empresa')
            codigo_projeto = request.POST.get('codigo_projeto', '').strip()
            nome_projeto_cliente = request.POST.get('nome_projeto_cliente', '').strip()
            responsavel = request.POST.get('responsavel', '').strip()
            
            # Validações básicas
            if not empresa_id:
                raise ValidationError({'empresa': ['A empresa é obrigatória.']})
            
            if not codigo_projeto:
                raise ValidationError({'codigo_projeto': ['O código do projeto é obrigatório.']})
            
            if not responsavel:
                raise ValidationError({'responsavel': ['O email do responsável é obrigatório.']})
            
            # Verificar se já existe um projeto com o mesmo código para a empresa
            if Projeto.objects.filter(empresa_id=empresa_id, codigo_projeto=codigo_projeto).exists():
                empresa = Empresa.objects.get(id=empresa_id)
                raise ValidationError({
                    'codigo_projeto': [f'Já existe um projeto com este código para a empresa {empresa.nome}.']
                })
            
            # Processar dentro de uma transação para garantir atomicidade
            with transaction.atomic():
                # Criar o objeto projeto
                projeto = Projeto()
                
                # Dados básicos
                projeto.empresa_id = empresa_id
                projeto.codigo_projeto = codigo_projeto
                projeto.nome_projeto_cliente = nome_projeto_cliente
                projeto.responsavel = responsavel
                
                # Informações da amostra
                projeto.quantidade_amostras = int(request.POST.get('quantidade_amostras', 0) or 0)
                projeto.numero_placas_96 = int(request.POST.get('numero_placas_96', 0) or 0)
                
                if request.POST.get('placas_inicial'):
                    projeto.placas_inicial = int(request.POST.get('placas_inicial'))
                
                if request.POST.get('placas_final'):
                    projeto.placas_final = int(request.POST.get('placas_final'))
                
                if request.POST.get('cultivo'):
                    projeto.cultivo_id = request.POST.get('cultivo')
                
                projeto.origem_amostra = request.POST.get('origem_amostra', 'FOLHA')
                projeto.tipo_amostra = request.POST.get('tipo_amostra', 'PLANTA 02 DISCOS')
                
                if request.POST.get('status'):
                    projeto.status_id = request.POST.get('status')
                
                # Tecnologias
                if request.POST.get('tecnologia_parental1'):
                    projeto.tecnologia_parental1_id = request.POST.get('tecnologia_parental1')
                
                if request.POST.get('tecnologia_parental2'):
                    projeto.tecnologia_parental2_id = request.POST.get('tecnologia_parental2')
                
                if request.POST.get('tecnologia_target'):
                    projeto.tecnologia_target_id = request.POST.get('tecnologia_target')
                
                if request.POST.get('proporcao'):
                    projeto.proporcao = float(request.POST.get('proporcao'))
                
                # Validar que tecnologia target é parental1 ou parental2
                if (projeto.tecnologia_target_id and 
                    projeto.tecnologia_target_id != projeto.tecnologia_parental1_id and 
                    projeto.tecnologia_target_id != projeto.tecnologia_parental2_id):
                    raise ValidationError({
                        'tecnologia_target': ['A tecnologia target deve ser igual a uma das parentais.']
                    })
                
                # Validar que parental1 != parental2
                if (projeto.tecnologia_parental1_id and projeto.tecnologia_parental2_id and
                    projeto.tecnologia_parental1_id == projeto.tecnologia_parental2_id):
                    raise ValidationError({
                        'tecnologia_parental2': ['A tecnologia parental 2 não pode ser igual à parental 1.']
                    })
                
                # Marcadores
                projeto.quantidade_traits = int(request.POST.get('quantidade_traits', 0) or 0)
                projeto.quantidade_marcador_customizado = int(request.POST.get('quantidade_marcador_customizado', 0) or 0)
                
                # Informações complementares
                if request.POST.get('etapa'):
                    projeto.etapa_id = request.POST.get('etapa')
                
                projeto.prioridade = int(request.POST.get('prioridade', 0) or 0)
                projeto.codigo_ensaio = request.POST.get('codigo_ensaio', '')
                projeto.setor_cliente = request.POST.get('setor_cliente', '')
                projeto.local_cliente = request.POST.get('local_cliente', '')
                
                if request.POST.get('ano_plantio_ensaio'):
                    projeto.ano_plantio_ensaio = int(request.POST.get('ano_plantio_ensaio'))
                
                if request.POST.get('data_planejada_envio'):
                    projeto.data_planejada_envio = request.POST.get('data_planejada_envio')
                
                # Checkbox fields
                projeto.herbicida = 'herbicida' in request.POST
                projeto.marcador_analisado = 'marcador_analisado' in request.POST
                
                if projeto.marcador_analisado:
                    projeto.se_marcador_analisado = request.POST.get('se_marcador_analisado', '---')
                
                projeto.comentarios = request.POST.get('comentarios', '')
                
                # Campos de auditoria
                projeto.criado_por = request.user
                
                # Salvar o projeto
                projeto.save()
                
                # Processar marcadores de traits (muitos para muitos)
                marcador_traits = request.POST.getlist('marcador_trait')
                if marcador_traits:
                    for trait_id in marcador_traits:
                        projeto.marcador_trait.add(trait_id)
                
                # Processar marcadores customizados (muitos para muitos)
                marcador_customizados = request.POST.getlist('marcador_customizado')
                if marcador_customizados:
                    for marcador_id in marcador_customizados:
                        projeto.marcador_customizado.add(marcador_id)
                
                # Registrar log de criação do projeto
                logger.info(f"Projeto {projeto.codigo_projeto} criado pelo usuário {request.user.username}")
                
                # Mensagem de sucesso
                messages.success(request, f'Projeto "{projeto.codigo_projeto}" criado com sucesso!')
                
                # Resposta para requisição HTMX ou redirecionamento normal
                if request.headers.get('HX-Request'):
                    # Usar cabeçalhos HTMX para redirecionamento em vez de retornar texto
                    response = HttpResponse()
                    response['HX-Redirect'] = reverse('projetos_lista')
                    return response
                else:
                    # Redirecionamento normal para requisições não-HTMX
                    return redirect('projetos_lista')
                
        except ValidationError as e:
            # Processar erros de validação
            messages.error(request, 'Ocorreram erros no preenchimento do formulário. Por favor, verifique os campos destacados.')
            
            # Adicionar erros aos campos específicos
            if hasattr(e, 'message_dict'):
                context['field_errors'] = e.message_dict
            else:
                context['form_error'] = str(e)
                
        except ValueError as e:
            # Erro de conversão de valores
            messages.error(request, f'Erro ao processar valores do formulário: {e}')
            context['form_error'] = f'Verifique os valores informados: {str(e)}'
            logger.warning(f"Erro de conversão no formulário de projeto: {str(e)}")
                
        except IntegrityError as e:
            # Erro de integridade do banco de dados
            messages.error(request, 'Este projeto não pode ser criado devido a um conflito no banco de dados.')
            logger.error(f"Erro de integridade ao criar projeto: {str(e)}")
            
            if 'unique constraint' in str(e).lower() and 'codigo_projeto' in str(e).lower():
                context['field_errors'] = {'codigo_projeto': ['Este código de projeto já está em uso.']}
            else:
                context['form_error'] = f'Erro de integridade do banco de dados: {str(e)}'
                
        except PermissionError as e:
            # Erro de permissão
            messages.error(request, 'Você não tem permissão para criar este projeto.')
            context['form_error'] = str(e)
            logger.warning(f"Erro de permissão: usuário {request.user.username} tentou criar projeto sem autorização: {str(e)}")
                
        except Exception as e:
            # Outros erros não previstos
            messages.error(request, 'Ocorreu um erro inesperado ao processar o formulário.')
            context['form_error'] = f'Erro interno do servidor: {str(e)}'
            logger.error(f"Erro inesperado ao criar projeto: {str(e)}", exc_info=True)
            
        # Em caso de erro, repopular o formulário com os dados enviados
        context.update(request.POST)
    
    # Renderizar o template com o contexto apropriado
    return render(request, 'criar_projeto.html', context)

@login_required
def carregar_projetos_por_empresa(request):
    """
    Endpoint HTMX para carregar projetos baseado na empresa selecionada
    """
    empresa_id = request.GET.get('empresa')
    if not empresa_id:
        return HttpResponse("<div class='alert alert-danger'>Selecione uma empresa</div>")
    
    try:
        empresa = Empresa.objects.get(id=empresa_id)
        # Verificar se o usuário tem acesso à empresa
        if not request.user.is_superuser and request.user.empresa.id != int(empresa_id):
            return HttpResponse("<div class='alert alert-danger'>Acesso negado</div>")
        
        # Obter projetos da empresa
        projetos = Projeto.objects.filter(empresa=empresa)
        
        return render(request, 'partials/projetos_dropdown.html', {'projetos': projetos})
    
    except Empresa.DoesNotExist:
        return HttpResponse("<div class='alert alert-danger'>Empresa não encontrada</div>")

def get_projetos_filtrados(request):
    """Função auxiliar para obter projetos filtrados com base nos parâmetros da requisição"""
    
    # Parâmetros de filtro
    search_query = request.GET.get('q')
    empresa_filter = request.GET.get('empresa', '')
    cultivo_filter = request.GET.get('cultivo', '')
    status_filter = request.GET.get('status', '')
    etapa_filter = request.GET.get('etapa', '')
    origem_filter = request.GET.get('origem_amostra', '')
    ativo_filter = request.GET.get('ativo', None)
    order_by = request.GET.get('order_by', '-id')
    
    # Obter todos os projetos ou filtrados por empresa do usuário
    if request.user.is_superuser:
        projetos_qs = Projeto.objects.all()
    else:
        projetos_qs = Projeto.objects.filter(empresa=request.user.empresa)
    
    # Adicionar related para melhorar performance
    projetos_qs = projetos_qs.select_related(
        'empresa', 
        'cultivo', 
        'status', 
        'etapa',
        'tecnologia_parental1',
        'tecnologia_parental2',
        'tecnologia_target'
    )
    
    # Aplicar filtros de busca
    if search_query:
        projetos_qs = projetos_qs.filter(
            Q(codigo_projeto__icontains=search_query) | 
            Q(nome_projeto_cliente__icontains=search_query) |
            Q(responsavel__icontains=search_query) |
            Q(codigo_ensaio__icontains=search_query)
        )
    
    # Filtros avançados
    if empresa_filter and empresa_filter.strip():
        projetos_qs = projetos_qs.filter(empresa_id=empresa_filter)
        
    if cultivo_filter and cultivo_filter.strip():
        projetos_qs = projetos_qs.filter(cultivo_id=cultivo_filter)
        
    if status_filter and status_filter.strip():
        projetos_qs = projetos_qs.filter(status_id=status_filter)
        
    if etapa_filter and etapa_filter.strip():
        projetos_qs = projetos_qs.filter(etapa_id=etapa_filter)
        
    if origem_filter and origem_filter.strip():
        projetos_qs = projetos_qs.filter(origem_amostra=origem_filter)
        
    if ativo_filter is not None and ativo_filter.strip() in ['0', '1']:
        is_ativo = ativo_filter == '1'
        projetos_qs = projetos_qs.filter(ativo=is_ativo)
    
    # Ordenação
    projetos_qs = projetos_qs.order_by(order_by)
    
    return projetos_qs, {
        'search_query': search_query,
        'empresa_filter': empresa_filter,
        'cultivo_filter': cultivo_filter,
        'status_filter': status_filter,
        'etapa_filter': etapa_filter,
        'origem_filter': origem_filter,
        'ativo_filter': ativo_filter,
        'order_by': order_by
    }

@login_required
def projetos_lista(request):
    """View principal para a página de listagem de projetos"""
    
    # Preparar dados iniciais para o template completo
    empresas = Empresa.objects.filter(is_active=True).order_by('nome')
    cultivos = Cultivo.objects.filter(is_active=True).order_by('nome')
    statuses = Status.objects.filter(is_active=True).order_by('nome')
    etapas = Etapa.objects.filter(is_active=True).order_by('nome')
    
    # Obter projetos filtrados usando a função auxiliar
    projetos_qs, filter_params = get_projetos_filtrados(request)
    
    # Paginação
    paginator = Paginator(projetos_qs, 25)  # 25 projetos por página
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    # Criar um range personalizado para a paginação
    page_range = []
    for i in paginator.page_range:
        if i <= 3 or i >= paginator.num_pages - 2 or abs(i - page_obj.number) <= 2:
            page_range.append(i)
    
    # Contexto para o template
    context = {
        'empresas': empresas,
        'cultivos': cultivos, 
        'statuses': statuses,
        'etapas': etapas,
        'origem_opcoes': [('FOLHA', 'FOLHA'), ('SEMENTE', 'SEMENTE')],
        'ativo_opcoes': [(None, 'Todos'), ('1', 'Ativo'), ('0', 'Inativo')],
        'hide_sidebar': True,
        'page_obj': page_obj,
        'page_range': page_range,
        # Adicionar os parâmetros de filtro ao contexto
        **filter_params
    }
    
    return render(request, 'projetos_lista.html', context)

@login_required
def projetos_lista_parcial(request):
    """View para retornar apenas o conteúdo atualizado da lista de projetos (para HTMX)"""
    
    # Obter projetos filtrados usando a função auxiliar
    projetos_qs, filter_params = get_projetos_filtrados(request)
    
    # Paginação
    paginator = Paginator(projetos_qs, 25)  # 25 projetos por página
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    # Criar um range personalizado para a paginação
    page_range = []
    for i in paginator.page_range:
        if i <= 3 or i >= paginator.num_pages - 2 or abs(i - page_obj.number) <= 2:
            page_range.append(i)
    
    # Contexto para o template parcial
    context = {
        'page_obj': page_obj,
        'page_range': page_range,
        # Adicionar os parâmetros de filtro ao contexto
        **filter_params
    }
    
    # Retornar apenas o conteúdo parcial
    return render(request, 'projetos_lista_content.html', context)

@login_required
def projetos_acoes(request):
    """View para processar ações em lote via HTMX"""
    if request.method == 'POST':
        selected_ids = request.POST.getlist('_selected_action')
        action = request.POST.get('action')
        
        if not selected_ids:
            messages.warning(request, 'Nenhum projeto foi selecionado.')
        elif not action:
            messages.warning(request, 'Nenhuma ação foi selecionada.')
        else:
            projetos = Projeto.objects.filter(id__in=selected_ids)
            
            if action == 'ativar':
                count = projetos.update(ativo=True)
                messages.success(request, f'{count} projetos foram ativados com sucesso.')
            elif action == 'desativar':
                count = projetos.update(ativo=False)
                messages.success(request, f'{count} projetos foram desativados com sucesso.')
            elif action == 'exportar_csv':
                # Implementar a exportação para CSV
                messages.success(request, f'{len(selected_ids)} projetos exportados para CSV.')
    
    # Redirecionar para a visualização parcial para obter o conteúdo atualizado
    # Preservar os parâmetros de pesquisa, filtros, etc.
    params = request.GET.copy()
    url = reverse('projetos_lista_parcial')
    if params:
        url += '?' + params.urlencode()
    
    return redirect(url)

def export_projetos_csv(request, queryset):
    """Função para exportar projetos selecionados para CSV"""
    output = StringIO()
    writer = csv.writer(output)
    
    # Cabeçalhos
    writer.writerow([
        'Código', 'Nome', 'Empresa', 'Responsável', 'Quantidade Amostras',
        'Cultivo', 'Status', 'Etapa', 'Origem Amostra', 'Data Criação', 'Ativo'
    ])
    
    # Dados
    for projeto in queryset:
        writer.writerow([
            projeto.codigo_projeto,
            projeto.nome_projeto_cliente or '',
            projeto.empresa.nome if projeto.empresa else '',
            projeto.responsavel or '',
            projeto.quantidade_amostras or 0,
            projeto.cultivo.nome if projeto.cultivo else '',
            projeto.status.nome if projeto.status else '',
            projeto.etapa.nome if projeto.etapa else '',
            projeto.origem_amostra or '',
            projeto.created_at.strftime('%d/%m/%Y') if projeto.created_at else '',
            'Sim' if projeto.ativo else 'Não',
        ])
    
    # Criar resposta HTTP
    response = HttpResponse(output.getvalue(), content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="projetos_{datetime.date.today()}.csv"'
    
    return response