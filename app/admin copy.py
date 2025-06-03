from rest_framework.authtoken.models import TokenProxy
from rest_framework.authtoken.admin import TokenAdmin as AuthTokenTokenAdmin # Renomeie para evitar conflito
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import ResultadoAmostra384, ResultadoUpload384 
from django.db import transaction  # Adicionando esta importação
from .forms import TransferPlacasForm, Transfer384to384Form, Transfer384to1536Form, ResultadoAmostra1536, ResultadoUpload1536Form# Adicione esta importação no início do arquivo
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth import get_user_model
from django.db.models import Q
from .models import ( ResultadoUpload384, Tecnologia, Cultivo, MarcadorTrait, MarcadorCustomizado, Projeto, Status, 
                        Etapa, User,  Amostra, Placa96, ResultadoUpload384, ResultadoAmostra384,
                        Placa384, Placa1536, Empresa,  Poco96, Poco384, Poco1536,    
                        PlacaMap384, PlacaMap1536, ResultadoAmostra1536, ResultadoUpload1536, PlacaMap384to384)

from django.shortcuts import render, redirect
from django.contrib import messages
from django import forms
from django.core.exceptions import ValidationError  # Adicione esta linha
from django.http import JsonResponse
from django.contrib.admin import AdminSite
from django.contrib.auth.models import Group
from django.contrib.auth.admin import GroupAdmin
from import_export.admin import ImportExportModelAdmin
from django.utils.html import format_html  # Adicionando a importação necessária
from import_export import resources, fields
from import_export.widgets import ForeignKeyWidget
from django.urls import path, reverse
import csv
from estoque.models import ( # Supondo que seu app de estoque se chama 'estoque'
    UnidadeMedida, CategoriaProduto, Fornecedor, LocalEstoque,
    Produto, ItemEstoque, MovimentacaoEstoque
)

import logging
import traceback

from django.http import HttpResponseRedirect
from .servico import processar_arquivo_384



logger = logging.getLogger(__name__)

#-----------------------------------------------
# FILTROS

class EmpresaFilter(admin.SimpleListFilter):
    title = 'Empresa'
    parameter_name = 'empresa'

    def lookups(self, request, model_admin):
        if request.user.is_superuser:
            empresas = Empresa.objects.all()
        else:
            empresas = Empresa.objects.filter(id=request.user.empresa.id)
        return [(empresa.id, empresa.nome) for empresa in empresas]

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(empresa_id=self.value())
        return queryset

class ProjetoFilter(admin.SimpleListFilter):
    title = 'Projeto'
    parameter_name = 'projeto'

    def lookups(self, request, model_admin):
        # Pega o valor do filtro de empresa
        empresa_id = request.GET.get('empresa')
        if empresa_id:
            projetos = Projeto.objects.filter(empresa_id=empresa_id, ativo=True)
        else:
            if request.user.is_superuser:
                projetos = Projeto.objects.filter(ativo=True)
            else:
                projetos = Projeto.objects.filter(empresa=request.user.empresa, ativo=True)
        return [(projeto.id, f"{projeto.codigo_projeto} - {projeto.nome_projeto_cliente or 'Sem nome'}") 
                for projeto in projetos]

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(projeto_id=self.value())
        return queryset

class PlacaFilter(admin.SimpleListFilter):
    title = 'Placa'
    parameter_name = 'placa'

    def lookups(self, request, model_admin):
        # Pega o valor do filtro de projeto
        projeto_id = request.GET.get('projeto')
        if projeto_id:
            # Ajuste o modelo de placa conforme necessário (Placa96, Placa384, Placa1536)
            placas = model_admin.placa_model.objects.filter(
                projeto_id=projeto_id,
                is_active=True
            )
            return [(placa.id, placa.codigo_placa) for placa in placas]
        return []

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(placa_id=self.value())
        return queryset

class ProjetoFilterPoco(admin.SimpleListFilter):
    title = 'Projeto'
    parameter_name = 'projeto'

    def lookups(self, request, model_admin):
        empresa_id = request.GET.get('empresa')
        if empresa_id:
            projetos = Projeto.objects.filter(empresa_id=empresa_id, ativo=True)
        else:
            if request.user.is_superuser:
                projetos = Projeto.objects.filter(ativo=True)
            else:
                projetos = Projeto.objects.filter(empresa=request.user.empresa, ativo=True)
        return [(projeto.id, f"{projeto.codigo_projeto} - {projeto.nome_projeto_cliente or 'Sem nome'}") 
                for projeto in projetos]

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(placa__projeto_id=self.value())
        return queryset

class PlacaFilterPoco(admin.SimpleListFilter):
    title = 'Placa'
    parameter_name = 'placa'

    def lookups(self, request, model_admin):
        projeto_id = request.GET.get('projeto')
        if projeto_id:
            placas = model_admin.placa_model.objects.filter(
                projeto_id=projeto_id,
                is_active=True
            )
            return [(placa.id, placa.codigo_placa) for placa in placas]
        return []

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(placa_id=self.value())
        return queryset

class ProjetoFilterMap(admin.SimpleListFilter):
    title = 'Projeto'
    parameter_name = 'projeto'

    def lookups(self, request, model_admin):
        empresa_id = request.GET.get('empresa')
        if empresa_id:
            projetos = Projeto.objects.filter(empresa_id=empresa_id, ativo=True)
        else:
            if request.user.is_superuser:
                projetos = Projeto.objects.filter(ativo=True)
            else:
                projetos = Projeto.objects.filter(empresa=request.user.empresa, ativo=True)
        return [(projeto.id, f"{projeto.codigo_projeto} - {projeto.nome_projeto_cliente or 'Sem nome'}") 
                for projeto in projetos]

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(placa_destino__projeto_id=self.value())
        return queryset

class PlacaOrigemFilter(admin.SimpleListFilter):
    title = 'Placa Origem'
    parameter_name = 'placa_origem'

    def lookups(self, request, model_admin):
        projeto_id = request.GET.get('projeto')
        if projeto_id:
            placas = model_admin.placa_origem_model.objects.filter(
                projeto_id=projeto_id,
                is_active=True
            )
            return [(placa.id, placa.codigo_placa) for placa in placas]
        return []

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(placa_origem_id=self.value())
        return queryset

class PlacaDestinoFilter(admin.SimpleListFilter):
    title = 'Placa Destino'
    parameter_name = 'placa_destino'

    def lookups(self, request, model_admin):
        projeto_id = request.GET.get('projeto')
        if projeto_id:
            placas = model_admin.placa_destino_model.objects.filter(
                projeto_id=projeto_id,
                is_active=True
            )
            return [(placa.id, placa.codigo_placa) for placa in placas]
        return []

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(placa_destino_id=self.value())
        return queryset

#-----------------------------------------------
# CUSTOMIZACAO DO ADMIN SITE

class CustomAdminSite(AdminSite):
    site_header = 'SGL'
    site_title = 'SGL Admin'
    index_title = 'Administração do Sistema'

    def get_app_list(self, request, app_label=None):
        app_list = super().get_app_list(request)
        
        # Definição dos grupos e seus modelos
        app_dict = {
            'Core': {
                'models': {
                    'Empresa': 'app.empresa',
                    'Projeto': 'app.projeto',
                    'Amostra': 'app.amostra',
                },
            },
            'Placas': {
                'models': {
                    'Placa 96': 'app.placa96',
                    'Placa 384': 'app.placa384',
                    'Placa 1536': 'app.placa1536',
                },
            },
            'Mapeamentos': {
                'models': {
                    'Map 96 -> 384': 'app.placamap384',
                    'Map 384 -> 384': 'app.placamap384to384',
                    'Map 384 -> 1536': 'app.placamap1536',
                },
            },
            'Poços': {
                'models': {
                    'Poços das Placas 96': 'app.poco96',
                    'Poços das Placas 384': 'app.poco384',
                    'Poços das Placas 1536': 'app.poco1536',
                },
            },
            'Resultados': {
                'models': {
                    'Upload de Resultados 1536': 'app.resultadoupload',
                    'Resultados por Amostra 1536': 'app.resultadoamostra1536',
                    'Upload de Resultados 384': 'app.ResultadoUpload384',
                    'Resultados por Amostra 384': 'app.ResultadoAmostra384',
                },
            },
            'Cadastros': {
                'models': {
                    'Cultivo': 'app.cultivo',
                    'Etapa': 'app.etapa',
                    'Tecnologia': 'app.tecnologia',
                    'Marcador Trait': 'app.marcadortrait',
                    'Marcador Custom': 'app.marcadorcustomizado',
                    'Status': 'app.status',
                    'Usuário': 'app.user',
                },
            },
            # NOVO GRUPO PARA ESTOQUE
            'Estoque': {
                'models': {
                    'Unidades de Medida': 'estoque.unidademedida',
                    'Categorias de Produto': 'estoque.categoriaproduto',
                    'Fornecedores': 'estoque.fornecedor',
                    'Locais de Estoque': 'estoque.localestoque',
                    'Produtos': 'estoque.produto',
                    'Itens em Estoque': 'estoque.itemestoque',
                    'Movimentações de Estoque': 'estoque.movimentacaoestoque',
                }
            },
            # FIM DO NOVO GRUPO

            'Configurações': {
                'models': {
                    'Grupos de Usuários': 'auth.group',
                },
            }
        }

        # Reorganiza a lista de apps
        ordered_apps = []
        for app_name, app_config in app_dict.items():
            app = {
                'name': app_name,
                'app_label': 'app',
                'models': []
            }

            for model_name, model_path in app_config['models'].items():
                for existing_app in app_list:
                    for model in existing_app['models']:
                        if f"{existing_app['app_label']}.{model['object_name'].lower()}" == model_path.lower():
                            model_copy = model.copy()
                            model_copy['name'] = model_name
                            app['models'].append(model_copy)

            if app['models']:
                ordered_apps.append(app)

        return ordered_apps

admin_site = CustomAdminSite(name='admin')
admin_site.register(Group, GroupAdmin)
admin_site.register(TokenProxy, AuthTokenTokenAdmin)
User = get_user_model()

class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'empresa', 'empresa__nome','is_staff', 'is_active')
    list_filter = ('is_staff', 'is_active', 'groups', 'empresa')
    search_fields = ('username', 'first_name', 'last_name', 'email')
    ordering = ('username',)
    
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Informações Pessoais', {'fields': ('first_name', 'last_name', 'email', 'telefone', 'empresa')}),
        ('Permissões', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'password1', 'password2', 'empresa'),
        }),
    )

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(empresa=request.user.empresa)

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "empresa" and not request.user.is_superuser:
            kwargs["queryset"] = Empresa.objects.filter(id=request.user.empresa.id)
            kwargs["initial"] = request.user.empresa
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

class EmpresaAdmin(admin.ModelAdmin):
    list_display = ('codigo', 'nome', 'cnpj', 'is_active', 'data_cadastro')
    list_filter = ('is_active',)
    search_fields = ('nome', 'codigo', 'cnpj')
    ordering = ('nome',)
    
    fieldsets = (
        (None, {'fields': ('nome', 'codigo', 'cnpj', 'is_active')}),
        ('Informações de Contato', {'fields': ('email', 'telefone')}),
        ('Endereço', {'fields': ('cep', 'endereco', 'complemento', 'bairro', 'cidade', 'estado')}),
    )
    
    def has_delete_permission(self, request, obj=None):
        # Apenas superuser pode deletar empresas
        return request.user.is_superuser

class EmpresaAdminMixin:
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        if request.user.empresa:
            return qs.filter(empresa=request.user.empresa)
        return qs.none()

    def save_model(self, request, obj, form, change):
        if not obj.empresa and not request.user.is_superuser:
            obj.empresa = request.user.empresa
        super().save_model(request, obj, form, change)

    def get_list_filter(self, request):
        list_filter = list(super().get_list_filter(request) or [])
        if request.user.is_superuser:
            if 'empresa' not in list_filter:
                list_filter.append('empresa')
        return list_filter

class ProjetoAdmin(EmpresaAdminMixin, admin.ModelAdmin):
    list_display = ('empresa__codigo','empresa__nome','codigo_projeto', 'quantidade_amostras', 'status', 'cultivo', 'created_at')
    list_display_links = ["codigo_projeto"]
    list_filter = (EmpresaFilter,ProjetoFilter,'empresa','codigo_projeto', 'status', 'cultivo')  # Empresa primeiro para facilitar filtragem
    search_fields = ('codigo_projeto', 'nome_projeto_cliente', 'empresa__nome')
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs.select_related('empresa', 'status', 'cultivo')
        if request.user.empresa:
            return qs.filter(empresa=request.user.empresa).select_related('empresa', 'status', 'cultivo')
        return qs.none()
    
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if not request.user.is_superuser:
            if db_field.name == "empresa":
                kwargs["queryset"] = Empresa.objects.filter(id=request.user.empresa.id)
                kwargs["initial"] = request.user.empresa
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

#-----------------------------------------------
# POCO E PLACA INLINE 

class Poco96Inline(admin.TabularInline):
    model = Poco96
    extra = 1
    autocomplete_fields = ['amostra']

class Poco384Inline(admin.TabularInline):
    model = Poco384
    extra = 1
    raw_id_fields = ['amostra']

class Poco1536Inline(admin.TabularInline):
    model = Poco1536
    extra = 1
    autocomplete_fields = ['amostra']

class PlacaMap384Inline(admin.TabularInline):
    model = PlacaMap384
    extra = 1
    autocomplete_fields = ['placa_origem']

class PlacaMap1536Inline(admin.TabularInline):
    model = PlacaMap1536
    extra = 1
    autocomplete_fields = ['placa_origem']

class ResultadoAmostra1536Inline(admin.TabularInline):
    model = ResultadoAmostra1536
    fields = ('amostra', 'resultado_fh', 'resultado_aj', 'data_processamento')
    readonly_fields = ('amostra', 'resultado_fh', 'resultado_aj', 'data_processamento')
    can_delete = False
    max_num = 0
    extra = 0

    def has_add_permission(self, request, obj=None):
        return False
#-----------------------------------------------
# AMOSTRA

class AmostraResource(resources.ModelResource):
    class Meta:
        model = Amostra
        fields = ('codigo_amostra', 'barcode_cliente')
        import_id_fields = ['codigo_amostra']
        skip_unchanged = True
        use_bulk = True
        batch_size = 1000

    def before_import_row(self, row, **kwargs):
        # Converte para string e limpa os dados
        if 'codigo_amostra' in row:
            row['codigo_amostra'] = str(row['codigo_amostra']).strip()
        if 'barcode_cliente' in row:
            row['barcode_cliente'] = str(row['barcode_cliente']).strip() if row['barcode_cliente'] else None

    def skip_row(self, instance, original, row, import_validation_errors=None):
        # Pula a criação de novos registros, apenas permite atualização
        return not instance.pk

class AmostraAdmin(ImportExportModelAdmin):
    resource_class = AmostraResource
    list_display = ('codigo_amostra', 'barcode_cliente', 'projeto', 'empresa')
    list_filter = (EmpresaFilter, ProjetoFilter)
    search_fields = ('codigo_amostra', 'barcode_cliente')
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        qs = qs.select_related('projeto', 'projeto__empresa')
        
        if not request.user.is_superuser:
            qs = qs.filter(projeto__empresa=request.user.empresa)
            
        return qs

    def empresa(self, obj):
        return obj.projeto.empresa.nome
    empresa.admin_order_field = 'projeto__empresa__nome'

#-----------------------------------------------
# Placas
class Placa96Admin(EmpresaAdminMixin, admin.ModelAdmin):
    list_display = ('empresa__codigo', 'empresa__nome','projeto','codigo_placa', 'get_amostras_count',  'data_criacao', 'is_active')
    list_display_links=['codigo_placa']
    list_filter = (EmpresaFilter, ProjetoFilter,  'data_criacao', 'is_active')
    search_fields = ('codigo_placa', 'projeto__codigo_projeto')
    # inlines = [Poco96Inline]
    autocomplete_fields = ['projeto']

    def get_queryset(self, request):

        return super().get_queryset(request).select_related('projeto', 'empresa')

class Placa384Admin(admin.ModelAdmin):
   list_display = ('empresa__codigo', 'empresa__nome','projeto','codigo_placa', 'get_amostras_count', 'data_criacao', 'is_active')
   list_display_links=['codigo_placa']
   list_filter = (EmpresaFilter, ProjetoFilter, 'codigo_placa','is_active')
   search_fields = ('codigo_placa', 'projeto__codigo_projeto')

   def get_urls(self):
       urls = super().get_urls()
       custom_urls = [
           path(
               'transferir-96-384/',
               self.admin_site.admin_view(self.transferir_96_384_view),
               name='app_placa384_transferir_96_384'
           ),
           path(
               'get-projetos/<int:empresa_id>/',
               self.admin_site.admin_view(self.get_projetos_view),
               name='get_projetos_admin'
           ),
           path(
               'get-placas-96/<int:projeto_id>/',
               self.admin_site.admin_view(self.get_placas_96_view),
               name='get_placas_96_admin'
           ),
        path(
            'transferir-384-384/',
            self.admin_site.admin_view(self.transferir_384_384_view),
            name='app_placa384_transferir_384_384'
        ),
        path(
            'get-projetos-384/<int:empresa_id>/',
            self.admin_site.admin_view(self.get_projetos_384_view),
            name='get_projetos_384_admin'
        ),
        path(
            'get-placas-384-origem/<int:projeto_id>/',
            self.admin_site.admin_view(self.get_placas_384_origem_view),
            name='get_placas_384_origem_admin'
        ),
                path(
            'transferir-384-1536/',
            self.admin_site.admin_view(self.transferir_384_1536_view),
            name='app_placa384_transferir_384_1536'
        ),
        path(
            'get-projetos-1536/<int:empresa_id>/',
            self.admin_site.admin_view(self.get_projetos_1536_view),
            name='get_projetos_1536_admin'
        ),
        path(
            'get-placas-384-para-1536/<int:projeto_id>/',
            self.admin_site.admin_view(self.get_placas_384_para_1536_view),
            name='get_placas_384_para_1536_admin'
        ),
       ]
       return custom_urls + urls

# admin.py - na classe Placa384Admin

   def get_projetos_384_view(self, request, empresa_id):
        """API endpoint para buscar projetos de uma empresa"""
        try:
            if not request.user.is_superuser and request.user.empresa.id != empresa_id:
                return JsonResponse({'error': 'Sem permissão'}, status=403)
            
            # Buscar projetos ativos com placas 384
            projetos = Projeto.objects.filter(
                empresa_id=empresa_id,
                ativo=True,
                placa384__isnull=False  # Garante que só retorna projetos com placas 384
            ).distinct().values('id', 'codigo_projeto', 'nome_projeto_cliente')
            
            projetos_list = [
                {
                    'id': projeto['id'],
                    'text': f"{projeto['codigo_projeto']} - {projeto['nome_projeto_cliente'] or ''}"
                }
                for projeto in projetos
            ]
            
            return JsonResponse({'results': projetos_list})
            
        except Exception as e:
            print(f"Erro ao buscar projetos: {str(e)}")  # Adicione este log
            return JsonResponse({'error': str(e)}, status=400)
        
   def get_placas_384_origem_view(self, request, projeto_id):
        """API endpoint para buscar placas 384 disponíveis de um projeto"""
        try:
            projeto = Projeto.objects.get(id=projeto_id)
            
            if not request.user.is_superuser and request.user.empresa != projeto.empresa:
                return JsonResponse({'error': 'Sem permissão'}, status=403)
            
            # Buscar placas 384 ativas do projeto
            placas = Placa384.objects.filter(
                projeto_id=projeto_id,
                is_active=True
            ).values('id', 'codigo_placa')
            
            placas_list = [
                {
                    'id': placa['id'],
                    'text': f"{placa['codigo_placa']}"
                }
                for placa in placas
            ]
            
            return JsonResponse({'results': placas_list})
            
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)

   def get_projetos_view(self, request, empresa_id):
       """API para buscar projetos de uma empresa"""
       try:
           if not request.user.is_superuser and request.user.empresa.id != empresa_id:
               return JsonResponse({'error': 'Sem permissão'}, status=403)
               
           projetos = Projeto.objects.filter(
               empresa_id=empresa_id,
               ativo=True,
               placa96__is_active=True,
           ).distinct().values('id', 'codigo_projeto', 'nome_projeto_cliente')
           
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

   def get_placas_96_view(self, request, projeto_id):
       """API para buscar placas 96 disponíveis"""
       try:
           projeto = Projeto.objects.get(id=projeto_id)
           
           if not request.user.is_superuser and request.user.empresa != projeto.empresa:
               return JsonResponse({'error': 'Sem permissão'}, status=403)
           
           placas = Placa96.objects.filter(
               projeto_id=projeto_id,
               is_active=True
           ).values('id', 'codigo_placa')
           
           return JsonResponse(list(placas), safe=False)
           
       except Exception as e:
           return JsonResponse({'error': str(e)}, status=400)

   def transferir_96_384_view(self, request):
       context = {
           'title': 'Transferir Placas 96 para 384',
           'opts': self.model._meta,
           **self.admin_site.each_context(request),
       }

       if request.method == 'POST':
           form = TransferPlacasForm(request.user, request.POST)
           if form.is_valid():
               try:
                   with transaction.atomic():
                       empresa = form.cleaned_data['empresa']
                       projeto = form.cleaned_data['projeto']
                    #    placas_ids = request.POST.getlist('placas[]')
                       codigo_placa_384 = form.cleaned_data['codigo_placa_384']
                       placas_96 = [
                            form.cleaned_data['placa_1'],
                            form.cleaned_data['placa_2'],
                            form.cleaned_data['placa_3'],
                            form.cleaned_data['placa_4']
                    ]
                       logger.info(f"Dados recebidos: empresa={empresa.id}, projeto={projeto.id}, placas={placas_96}, código={codigo_placa_384}")

                        # Filtrar placas não nulas
                       placas_96 = [placa for placa in placas_96 if placa is not None]

                       logger.info(f"Placa 96 selecionada:(ID: {placas_96})")  # Log das placas
                       
                       placa_384 = Placa384.objects.create(
                           empresa=empresa,
                           projeto=projeto,
                           codigo_placa=codigo_placa_384
                       )
                       logger.info(f"Placa 384 criada: {placa_384.codigo_placa}")  # Confirma criação

                       placa_384.transfer_96_to_384(placas_96)
                       logger.info("Transferência concluída com sucesso!")  # Confirma transferência

                       messages.success(request, 'Placa 384 criada com sucesso!')
                       return redirect('admin:app_placa384_change', placa_384.id)

               except ValidationError as e:
                   logger.error(f"Erro crítico validation: {str(e)}", exc_info=True)  # Log detalhado
                   messages.error(request, str(e))
               except Exception as e:
                   logger.error(f"Erro crítico exception: {str(e)}", exc_info=True)  # Log detalhado
                   messages.error(request, f'Erro: {str(e)}')
       else:
           form = TransferPlacasForm(user=request.user)

       context['form'] = form
       return render(request, 'admin/app/placa384/transferir_96_384.html', context)

   def transferir_384_384_view(self, request):
        context = {
            'title': 'Transferir Placa 384 para 384',
            'opts': self.model._meta,
            **self.admin_site.each_context(request),
        }

        if request.method == 'POST':
            form = Transfer384to384Form(request.POST, user=request.user)
            if form.is_valid():
                try:
                    with transaction.atomic():
                        empresa = form.cleaned_data['empresa']
                        projeto = form.cleaned_data['projeto']
                        placa_origem = form.cleaned_data['placa_origem']
                        codigo_placa_384_destino = form.cleaned_data['codigo_placa_384_destino']

                        # Criar nova placa 384
                        placa_destino = Placa384.objects.create(
                            empresa=empresa,
                            projeto=projeto,
                            codigo_placa=codigo_placa_384_destino
                        )

                        # Realizar a transferência
                        placa_origem.transfer_384_to_384(placa_destino)

                        messages.success(request, 'Placa 384 criada com sucesso!')
                        return redirect('admin:app_placa384_change', placa_destino.id)

                except ValidationError as e:
                    messages.error(request, str(e))
                except Exception as e:
                    messages.error(request, f'Erro: {str(e)}')
        else:
            form = Transfer384to384Form(user=request.user)

        context['form'] = form
        return render(request, 'admin/app/placa384/transferir_384_384.html', context)
   
   def transferir_384_1536_view(self, request):
        context = {
            'title': 'Transferir Placas 384 para 1536',
            'opts': self.model._meta,
            **self.admin_site.each_context(request),
        }

        if request.method == 'POST':
            form = Transfer384to1536Form(request.POST, user=request.user)
            if form.is_valid():
                try:
                    with transaction.atomic():
                        empresa = form.cleaned_data['empresa']
                        projeto = form.cleaned_data['projeto']
                        codigo_placa_1536 = form.cleaned_data['codigo_placa_1536']
                        placas_384 = [
                            form.cleaned_data['placa_1'],
                            form.cleaned_data['placa_2'],
                            form.cleaned_data['placa_3'],
                            form.cleaned_data['placa_4']
                        ]
                        
                        # Filtrar placas não nulas
                        placas_384 = [placa for placa in placas_384 if placa is not None]

                        # Criar placa 1536
                        placa_1536 = Placa1536.objects.create(
                            empresa=empresa,
                            projeto=projeto,
                            codigo_placa=codigo_placa_1536
                        )

                        # Realizar transferência
                        placa_1536.transfer_384_to_1536(placas_384)

                        messages.success(request, 'Placa 1536 criada com sucesso!')
                        return redirect('admin:app_placa1536_change', placa_1536.id)

                except ValidationError as e:
                    messages.error(request, str(e))
                except Exception as e:
                    messages.error(request, f'Erro: {str(e)}')
        else:
            form = Transfer384to1536Form(user=request.user)

        context['form'] = form
        return render(request, 'admin/app/placa384/transferir_384_1536.html', context)

   def get_projetos_1536_view(self, request, empresa_id):
        """API endpoint para buscar projetos de uma empresa"""
        try:
            if not request.user.is_superuser and request.user.empresa.id != empresa_id:
                return JsonResponse({'error': 'Sem permissão'}, status=403)
            
            # Buscar projetos ativos com placas 384 disponíveis
            projetos = Projeto.objects.filter(
                empresa_id=empresa_id,
                ativo=True,
                placa384__is_active=True
            ).distinct().values('id', 'codigo_projeto')
            
            projetos_list = [
                {
                    'id': projeto['id'],
                    'text': f"{projeto['codigo_projeto']}"
                }
                for projeto in projetos
            ]
            
            return JsonResponse({'results': projetos_list})
            
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)

   def get_placas_384_para_1536_view(self, request, projeto_id):
        """API endpoint para buscar placas 384 disponíveis"""
        try:
            projeto = Projeto.objects.get(id=projeto_id)
            
            if not request.user.is_superuser and request.user.empresa != projeto.empresa:
                return JsonResponse({'error': 'Sem permissão'}, status=403)
            
            placas = Placa384.objects.filter(
                projeto_id=projeto_id,
                is_active=True
            ).values('id', 'codigo_placa')
            
            placas_list = [
                {
                    'id': placa['id'],
                    'text': f"{placa['codigo_placa']}"
                }
                for placa in placas
            ]
            
            return JsonResponse({'results': placas_list})
            
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)

   def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        extra_context['show_transfer_button'] = True
        return super().changelist_view(request, extra_context)

class Placa1536Admin(EmpresaAdminMixin, admin.ModelAdmin):
    list_display = ('empresa__codigo', 'empresa__nome','projeto', 'codigo_placa', 'get_amostras_count','data_criacao',  'is_active')
    list_display_links=['codigo_placa']
    list_filter = (EmpresaFilter, ProjetoFilter,  'data_criacao', 'is_active')
    search_fields = ('codigo_placa', 'projeto__codigo_projeto')
    # inlines = [Poco1536Inline, PlacaMap1536Inline]
    autocomplete_fields = ['projeto']

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('projeto', 'empresa')

    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        extra_context['show_transfer_button'] = True
        return super().changelist_view(request, extra_context)
    

#-----------------------------------------------
# Mapeamentos

class PlacaMap384Admin(EmpresaAdminMixin, admin.ModelAdmin):
    list_display = ('empresa', 'empresa__nome', 'placa_origem', 'placa_destino', 'quadrante')
    list_display_links=['placa_origem']
    list_filter = (EmpresaFilter, ProjetoFilterMap, PlacaOrigemFilter, PlacaDestinoFilter)
    search_fields = ('placa_origem__codigo_placa', 'placa_destino__codigo_placa')
    raw_id_fields = ['placa_origem', 'placa_destino']

    placa_origem_model = Placa96
    placa_destino_model = Placa384

    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'placa_origem', 'placa_destino', 'empresa',
            'placa_origem__projeto', 'placa_destino__projeto'
        )

class PlacaMap1536Admin(EmpresaAdminMixin, admin.ModelAdmin):
    list_display = ('empresa', 'empresa__nome', 'placa_origem', 'placa_destino', 'quadrante')  
    list_display_links=['placa_origem']
    list_filter = (EmpresaFilter, ProjetoFilterMap, PlacaOrigemFilter, PlacaDestinoFilter)
    search_fields = ('placa_origem__codigo_placa', 'placa_destino__codigo_placa')
    raw_id_fields = ['placa_origem', 'placa_destino']

    placa_origem_model = Placa384
    placa_destino_model = Placa1536

    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'placa_origem', 'placa_destino', 'empresa',
            'placa_origem__projeto', 'placa_destino__projeto'
        )

class PlacaMap384to384Admin(EmpresaAdminMixin, admin.ModelAdmin):
    list_display = ('empresa', 'empresa__nome', 'placa_origem', 'placa_destino', 'data_transferencia')
    list_display_links=['placa_origem']
    list_filter = (EmpresaFilter, ProjetoFilterMap, PlacaOrigemFilter, PlacaDestinoFilter)
    search_fields = ('placa_origem__codigo_placa', 'placa_destino__codigo_placa')
    raw_id_fields = ['placa_origem', 'placa_destino']

    placa_origem_model = Placa384
    placa_destino_model = Placa384

    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'placa_origem', 'placa_destino', 'empresa',
            'placa_origem__projeto', 'placa_destino__projeto'
        )

    
#-----------------------------------------------
# Poços


class Poco96Resource(resources.ModelResource):
    empresa_codigo = fields.Field(column_name='Código da Empresa', attribute='amostra__projeto__empresa__codigo')
    empresa_nome = fields.Field(column_name='Nome da Empresa', attribute='amostra__projeto__empresa__nome')
    projeto_codigo = fields.Field(column_name='Codigo do Projeto', attribute='amostra__projeto__codigo_projeto')
    projeto_nome = fields.Field(column_name='Nome do Projeto', attribute='amostra__projeto__nome_projeto_cliente')
    placa_codigo = fields.Field(column_name='Código da Placa de 96', attribute='placa__codigo_placa')
    amostra_codigo = fields.Field(column_name='Código da Amostra', attribute='amostra__codigo_amostra')

    class Meta:
        model = Poco96
        fields = ('id', 'empresa_codigo', 'empresa_nome', 'projeto_codigo', 'projeto_nome', 'placa_codigo', 'amostra_codigo', 'posicao')

class Poco384Resource(resources.ModelResource):
    empresa_codigo = fields.Field(column_name='Código da Empresa', attribute='amostra__projeto__empresa__codigo')
    empresa_nome = fields.Field(column_name='Nome da Empresa', attribute='amostra__projeto__empresa__nome')
    projeto_codigo = fields.Field(column_name='Codigo do Projeto', attribute='amostra__projeto__codigo_projeto')
    projeto_nome = fields.Field(column_name='Nome do Projeto', attribute='amostra__projeto__nome_projeto_cliente')
    placa_codigo = fields.Field(column_name='Código da Placa de 384', attribute='placa__codigo_placa')
    amostra_codigo = fields.Field(column_name='Código da Amostra', attribute='amostra__codigo_amostra')

    class Meta:
        model = Poco384
        fields = ('id', 'empresa_codigo', 'empresa_nome', 'projeto_codigo', 'projeto_nome', 'placa_codigo', 'amostra_codigo', 'posicao')

# Modifique as classes Admin existentes

class Poco96Admin(EmpresaAdminMixin, ImportExportModelAdmin):
    resource_class = Poco96Resource
    list_display = ('empresa__codigo', 'empresa__nome', 'amostra__projeto__codigo_projeto', 'amostra__projeto__nome_projeto_cliente', 'placa', 'posicao', 'amostra')
    list_display_links = ['posicao']
    list_filter = (EmpresaFilter, ProjetoFilterPoco, PlacaFilterPoco)
    search_fields = ('placa__codigo_placa', 'posicao', 'amostra__codigo_amostra')
    autocomplete_fields = ['placa', 'amostra']
    placa_model = Placa96

    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'placa', 'placa__projeto', 'empresa', 'amostra'
        )

class Poco384Admin(EmpresaAdminMixin, ImportExportModelAdmin):
    resource_class = Poco384Resource
    list_display = ('empresa__codigo', 'empresa__nome', 'amostra__projeto__codigo_projeto', 'amostra__projeto__nome_projeto_cliente', 'placa', 'posicao', 'amostra')
    list_display_links = ['posicao']
    list_filter = (EmpresaFilter, ProjetoFilterPoco, PlacaFilterPoco)
    search_fields = ('placa__codigo_placa', 'posicao', 'amostra__codigo_amostra')
    raw_id_fields = ['placa', 'amostra']
    placa_model = Placa384

    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'placa', 'placa__projeto', 'empresa', 'amostra'
        )

class Poco1536Resource(resources.ModelResource):
    empresa_codigo = fields.Field(          column_name='Código da Empresa',        attribute='amostra__projeto__empresa__codigo'    )
    empresa_nome = fields.Field(            column_name='Nome da Empresa',          attribute='amostra__projeto__empresa__nome'    )
    projeto_codigo = fields.Field(          column_name='Codigo do Projeto',        attribute='amostra__projeto__codigo_projeto'    )
    projeto_nome = fields.Field(            column_name='Nome do Projeto',          attribute='amostra__projeto__nome_projeto_cliente'    )
    placa_codigo = fields.Field(            column_name='Código da Placa de 1536',  attribute='placa__codigo_placa'    )
    amostra_codigo = fields.Field(          column_name='Código da Amostra',        attribute='amostra__codigo_amostra'    )
    # amostra_barcode = fields.Field (        column_name='Código Barcode do Cliente',attribute='amostra__barcode_cliente')

    class Meta:
        model = Poco1536
        fields = ('id', 'empresa_codigo','empresa_nome','projeto_codigo', 'projeto_nome', 'placa_codigo', 'amostra_codigo','posicao')

class Poco1536Admin(EmpresaAdminMixin, ImportExportModelAdmin):
    resource_class = Poco1536Resource
    list_display = ('empresa', 'empresa__nome','amostra__projeto__codigo_projeto','amostra__projeto__nome_projeto_cliente','placa', 'posicao', 'amostra','amostra__barcode_cliente')
    list_display_links=['posicao']
    list_filter = (EmpresaFilter, ProjetoFilterPoco, PlacaFilterPoco) 
    search_fields = ('placa__codigo_placa', 'posicao', 'amostra__codigo_amostra')
    autocomplete_fields = ['placa', 'amostra']
    placa_model = Placa1536


########### Cadastros

class ModeloBaseAdmin(admin.ModelAdmin):
    """Classe base para administração de modelos com campo is_active"""
    list_display = ('nome', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('nome',)
    actions = ['ativar', 'desativar']
    
    def ativar(self, request, queryset):
        queryset.update(is_active=True)
        self.message_user(request, f"{queryset.count()} registros ativados com sucesso.")
    ativar.short_description = "Ativar registros selecionados"
    
    def desativar(self, request, queryset):
        queryset.update(is_active=False)
        self.message_user(request, f"{queryset.count()} registros desativados com sucesso.")
    desativar.short_description = "Desativar registros selecionados"



# Manter sua classe admin existente para Projeto se já existir

#-----------------------------------------------
# Resultados 

class ResultadoUpload1536Form(forms.ModelForm):
    class Meta:
        model = ResultadoUpload1536
        fields = ['projeto', 'placa_1536', 'arquivo', 'marcador_fh', 'marcador_aj']
        widgets = {
            'projeto': forms.Select(attrs={'class': 'select2'}),
            'placa_1536': forms.Select(attrs={'class': 'select2'}),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        if self.user and not self.user.is_superuser:
            # Filtrar por empresa do usuário
            empresa = self.user.empresa
            self.fields['projeto'].queryset = Projeto.objects.filter(empresa=empresa)
            self.fields['placa_1536'].queryset = Placa1536.objects.filter(empresa=empresa)
        
        # Adicionar classe select2 para melhor UX
        self.fields['projeto'].widget.attrs['class'] = 'select2'
        self.fields['placa_1536'].widget.attrs['class'] = 'select2'

        # Atualizar placas quando projeto for selecionado via JavaScript
        self.fields['placa_1536'].widget.attrs['data-depends-on'] = 'projeto'

    def clean(self):
        cleaned_data = super().clean()
        projeto = cleaned_data.get('projeto')
        placa_1536 = cleaned_data.get('placa_1536')
        
        if projeto and placa_1536:
            # Verificar se a placa pertence ao projeto
            if placa_1536.projeto != projeto:
                raise forms.ValidationError(
                    {'placa_1536': 'A placa selecionada não pertence ao projeto informado.'}
                )
            
            # Verificar se já existe um upload não processado para esta placa
            if ResultadoUpload1536.objects.filter(
                placa_1536=placa_1536,
                processado=False
            ).exists():
                raise forms.ValidationError(
                    'Já existe um upload pendente para esta placa. ' + 
                    'Processe o upload anterior antes de enviar um novo.'
                )
        
        # Garantir que pelo menos um marcador está definido
        if not (cleaned_data.get('marcador_fh') or cleaned_data.get('marcador_aj')):
            raise forms.ValidationError(
                'Pelo menos um marcador (FH ou AJ) deve ser especificado.'
            )
        
        return cleaned_data

class ResultadoUpload1536Admin(EmpresaAdminMixin, admin.ModelAdmin):
    form = ResultadoUpload1536Form
    inlines = [ResultadoAmostra1536Inline]
    
    list_display = (
        'empresa',
        'empresa__nome',
        'get_codigo_placa',
        'get_projeto_display',
        'data_upload',
        'get_status_processamento',
        'get_contagem_resultados',
        'get_acoes'
    )
    
    list_filter = [
        EmpresaFilter,
        ProjetoFilter,
        'processado',
        'data_upload',
    ]
    
    search_fields = [
        'placa_1536__codigo_placa',
        'projeto__codigo_projeto',
        'projeto__nome_projeto_cliente'
    ]
    
    readonly_fields = ['data_upload', 'processado']

    def get_form(self, request, obj=None, **kwargs):
        """
        Sobrescreve o método para passar o usuário atual para o formulário
        """
        Form = super().get_form(request, obj, **kwargs)
        
        class FormWithRequest(Form):
            def __new__(cls, *args, **kwargs):
                kwargs['user'] = request.user
                return Form(*args, **kwargs)
                
        return FormWithRequest

    def get_codigo_placa(self, obj):
        return obj.placa_1536.codigo_placa if obj.placa_1536 else '-'
    get_codigo_placa.short_description = 'Placa'
    get_codigo_placa.admin_order_field = 'placa_1536__codigo_placa'
    
    def get_projeto_display(self, obj):
        if obj.projeto:
            return f"{obj.projeto.codigo_projeto} - {obj.projeto.nome_projeto_cliente or 'Sem nome'}"
        return '-'
    get_projeto_display.short_description = 'Projeto'
    get_projeto_display.admin_order_field = 'projeto__codigo_projeto'
    
    def get_status_processamento(self, obj):
        if obj.processado:
            return format_html(
                '<span style="color: green;">✓ Processado</span>'
            )
        return format_html(
            '<span style="color: orange;">⌛ Pendente</span>'
        )
    get_status_processamento.short_description = 'Status'
    get_status_processamento.admin_order_field = 'processado'

    def get_contagem_resultados(self, obj):
        count = obj.resultadoamostra1536_set.count()
        return f"{count} resultados"
    get_contagem_resultados.short_description = 'Resultados'
    
    def get_acoes(self, obj):
        if not obj.processado:
            return format_html(
                '<a class="button" href="{}">Processar Resultados</a>',
                f'processar/{obj.id}/'
            )
        return "Processamento completo"
    get_acoes.short_description = 'Ações'

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                'processar/<int:upload_id>/',
                self.admin_site.admin_view(self.process_upload),
                name='processo-resultado-upload'
            ),
        ]
        return custom_urls + urls

    def process_upload(self, request, upload_id):
        try:
            processor = ResultadoProcessor(upload_id)
            stats = processor.process()
            
            messages.success(
                request,
                f'Arquivo processado com sucesso! '
                f'Processados: {stats["processed"]}, '
                f'Erros: {stats["errors"]}'
            )
        except Exception as e:
            messages.error(
                request,
                f'Erro ao processar arquivo: {str(e)}'
            )
        
        return redirect('admin:app_resultadoupload1536_changelist')

    def save_model(self, request, obj, form, change):
        if not change:  # Apenas para novos registros
            obj.empresa = request.user.empresa if not request.user.is_superuser else obj.projeto.empresa
        super().save_model(request, obj, form, change)

class ResultadoAmostra1536Resource(resources.ModelResource):
    """
    Resource para importação e exportação de ResultadoAmostra1536
    """
    # Campos da Empresa
    empresa_codigo = fields.Field(
        column_name='Código da Empresa',
        attribute='empresa',
        widget=ForeignKeyWidget(Empresa, 'codigo')
    )
    empresa_nome = fields.Field(
        column_name='Nome da Empresa',
        attribute='empresa',
        widget=ForeignKeyWidget(Empresa, 'nome')
    )
    
    # Campos do Projeto
    projeto_codigo = fields.Field(
        column_name='Código do Projeto',
        attribute='upload__projeto__codigo_projeto'
    )
    
    projeto_nome = fields.Field(
        column_name='Nome do Projeto',
        attribute='amostra__projeto__nome_projeto_cliente'
    )
    
    # Campos da Placa
    placa_1536 = fields.Field(
        column_name='Código da Placa 1536',
        attribute='upload__placa_1536__codigo_placa'
    )
    poco_1536 = fields.Field(
        column_name='Poço 1536',
        attribute='amostra__placa_1536__poco_1536'
    )
    
    # Campos da Amostra
    codigo_amostra = fields.Field(
        column_name='Código da Amostra',
        attribute='amostra__codigo_amostra'
    )
    barcode_cliente = fields.Field(
        column_name='Barcode do Cliente',
        attribute='amostra__barcode_cliente'
    )
    
    # Campos dos Resultados
    # upload_data = fields.Field(
    #     column_name='Data do Upload',
    #     attribute='upload__data_upload'
    # )
    # data_processamento = fields.Field(
    #     column_name='Data do Processamento',
    #     attribute='data_processamento'
    # )
    resultado_fh = fields.Field(
        column_name='Resultado FH',
        attribute='resultado_fh'
    )
    resultado_aj = fields.Field(
        column_name='Resultado AJ',
        attribute='resultado_aj'
    )
    # coordenada_x_fh = fields.Field(
    #     column_name='Coordenada X FH',
    #     attribute='coordenada_x_fh'
    # )
    # coordenada_y_fh = fields.Field(
    #     column_name='Coordenada Y FH',
    #     attribute='coordenada_y_fh'
    # )
    # coordenada_x_aj = fields.Field(
    #     column_name='Coordenada X AJ',
    #     attribute='coordenada_x_aj'
    # )
    # coordenada_y_aj = fields.Field(
    #     column_name='Coordenada Y AJ',
    #     attribute='coordenada_y_aj'
    # )
    poco_1536 = fields.Field(
        column_name='Poço 1536')  # Declarando o campo    

    class Meta:
        model = ResultadoAmostra1536
        fields = (
            'id',
            'empresa_codigo',
            'empresa_nome',
            'projeto_codigo',  # Add this field to the whitelist
            'projeto_nome',
            'placa_1536',
            'poco_1536',
            'codigo_amostra',
            'barcode_cliente',
            'resultado_fh',
            'resultado_aj',
            'coordenada_x_fh',
            'coordenada_y_fh',
            'coordenada_x_aj',
            'coordenada_y_aj'
        )
        export_order = fields
        import_id_fields = ['id']
        skip_unchanged = True
        report_skipped = False

    def dehydrate_poco_1536(self, resultado_amostra):
        """
        Busca a posição do poço 1536 correspondente à amostra.
        """
        try:
            poco_1536 = resultado_amostra.amostra.poco1536_set.filter(
                placa=resultado_amostra.upload.placa_1536
            ).first()
            return poco_1536.posicao if poco_1536 else '-'
        except Exception as e:
            print(f"Erro ao buscar posição do poço 1536: {e}")
            return '-'

class ResultadoAmostra1536Admin(ImportExportModelAdmin):
    """
    Admin customizado para ResultadoAmostra1536 com recursos de importação/exportação
    """
    resource_class = ResultadoAmostra1536Resource
    
    # Campos mostrados na listagem
    list_display = (
        'empresa_nome',
        'projeto_codigo',
        'get_placa_1536',
        'get_poco_1536',
        'get_codigo_amostra',
        'get_barcode_cliente',
        'resultado_fh',
        'resultado_aj',
        'data_processamento'
    )
    
    # Campos para filtro
    list_filter = (
        'empresa',
        'upload__projeto',
        'upload__placa_1536',
        'data_processamento',
        'resultado_fh',
        'resultado_aj'
    )
    
    # Campos para busca
    search_fields = (
        'amostra__codigo_amostra',
        'amostra__barcode_cliente',
        'upload__placa_1536__codigo_placa',
        'resultado_fh',
        'resultado_aj',
     )
    
    # Define campos somente leitura
    readonly_fields = (
        'data_processamento',
        'upload',
        'empresa'
    )

    def get_queryset(self, request):
        """
        Otimiza as queries usando select_related para campos relacionados
        """
        return super().get_queryset(request).select_related(
            'empresa',
            'upload',
            'upload__projeto',
            'upload__placa_1536',
            'amostra'
        )

    # Métodos para campos personalizados no list_display
    def empresa_nome(self, obj):
        return obj.empresa.nome
    empresa_nome.short_description = 'Empresa'
    empresa_nome.admin_order_field = 'empresa__nome'
    
    def projeto_codigo(self, obj):
        return obj.upload.projeto.codigo_projeto
    projeto_codigo.short_description = 'Projeto'
    projeto_codigo.admin_order_field = 'upload__projeto__codigo_projeto'
    
    def get_placa_1536(self, obj):
        return obj.upload.placa_1536.codigo_placa
    get_placa_1536.short_description = 'Placa 1536'
    get_placa_1536.admin_order_field = 'upload__placa_1536__codigo_placa'
    
    def get_poco_1536(self, obj):
        poco = obj.amostra.poco1536_set.filter(
            placa=obj.upload.placa_1536
        ).first()
        return poco.posicao if poco else '-'
    get_poco_1536.short_description = 'Poço 1536'
    
    def get_codigo_amostra(self, obj):
        return obj.amostra.codigo_amostra
    get_codigo_amostra.short_description = 'Código Amostra'
    get_codigo_amostra.admin_order_field = 'amostra__codigo_amostra'
    
    def get_barcode_cliente(self, obj):
        return obj.amostra.barcode_cliente or '-'
    get_barcode_cliente.short_description = 'Barcode Cliente'
    get_barcode_cliente.admin_order_field = 'amostra__barcode_cliente'
    
    def has_add_permission(self, request):
        """
        Desabilita a adição manual de resultados
        """
        return False


#-----------------------------------------------
# UPLOADS E TRATAMETNO RESULTADOS PLACA 384 PHERASTAR  

class ResultadoAmostra384Resource(resources.ModelResource):
    """
    Resource for import and export of ResultadoAmostra384
    """
    class Meta:
        model = ResultadoAmostra384
        fields = (
            'id',
            'empresa',
            'projeto',
            'placa_384',
            'poco_placa_384',
            'teste',
            'resultado',
            'x',
            'y',
            'chave',
            'arquivo_upload'
        )
        export_order = fields
        import_id_fields = ['id']
        skip_unchanged = True
        report_skipped = False

class ResultadoAmostra384Admin(ImportExportModelAdmin):
    resource_class = ResultadoAmostra384Resource
   
    # Include all fields from the model in list_display
    list_display = (
        'id',
        'empresa',
        'projeto',
        'placa_384',
        'poco_placa_384',
        'teste',
        'resultado',
        'x',
        'y',
        'chave',
        'arquivo_upload'
    )
   
    list_filter = ('teste', 'resultado', 'arquivo_upload')
    search_fields = ('placa_384', 'poco_placa_384', 'chave', 'empresa', 'projeto')
    readonly_fields = ('chave',)
   
    fieldsets = (
        ('Informações de Identificação', {
            'fields': ('arquivo_upload', 'empresa', 'projeto')
        }),
        ('Informações da Placa', {
            'fields': ('placa_384', 'poco_placa_384', 'teste')
        }),
        ('Resultados', {
            'fields': ('resultado', 'x', 'y')
        }),
        ('Metadados', {
            'fields': ('chave',),
            'classes': ('collapse',)
        }),
    )

    def get_queryset(self, request):
        """
        Optimize queries using select_related for related fields
        Only include valid relational fields
        """
        return super().get_queryset(request).select_related(
            'arquivo_upload'  # Only include this field as it's the only valid relational field
        )

class ResultadoUpload384Admin(admin.ModelAdmin):
    list_display = ('id', 'projeto', 'empresa', 'data_upload', 'processado', 'data_processamento', 'botao_processar')
    list_filter = ('processado', 'empresa', 'projeto')
    search_fields = ('empresa__nome', 'projeto__codigo_projeto')
    readonly_fields = ('data_upload', 'processado', 'data_processamento')
    actions = ['processar_selecionados']
    
    fieldsets = (
        ('Informações do Upload', {
            'fields': ('empresa', 'projeto', 'arquivo')
        }),
        ('Status de Processamento', {
            'fields': ('processado', 'data_upload', 'data_processamento'),
            'classes': ('collapse',)
        }),
    )
    
    def botao_processar(self, obj):
        """
        Exibe um botão para processar o arquivo se ele ainda não foi processado.
        """
        if not obj.processado:
            return mark_safe(f'<a class="button" href="{reverse("admin:processar_arquivo", args=[obj.id])}">Processar</a>')
        return "Já processado"
    botao_processar.short_description = "Processar"
    botao_processar.allow_tags = True
    
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                'processar/<int:upload_id>/',
                self.admin_site.admin_view(self.processar_view),
                name='processar_arquivo',
            ),
        ]
        return custom_urls + urls
    
    def processar_view(self, request, upload_id):
        """
        View para processar um arquivo de upload.
        """
        try:
            from app.servico import process_upload # Corrected import path
            
            # Processar o arquivo
            stats = process_upload(upload_id)
            
            # Adicionar mensagem de sucesso
            self.message_user(
                request, 
                f"Arquivo processado com sucesso. Registros criados: {stats.get('registros_criados', 0)}", 
                messages.SUCCESS
            )
        except Exception as e:
            # Adicionar mensagem de erro
            self.message_user(
                request,
                f"Erro ao processar o arquivo: {str(e)}",
                messages.ERROR
            )
        
        # Redirecionar de volta para a lista
        return HttpResponseRedirect(reverse("admin:app_resultadoupload384_changelist"))
        
    def processar_selecionados(self, request, queryset):
        """
        Ação para processar múltiplos arquivos selecionados.
        """
        count = 0
        errors = 0
        
        for upload in queryset.filter(processado=False):
            try:
                from .servico import process_upload
                stats = process_upload(upload.id)
                count += 1
            except Exception as e:
                errors += 1
                self.message_user(
                    request,
                    f"Erro ao processar o arquivo ID {upload.id}: {str(e)}",
                    messages.ERROR
                )
        
        if count > 0:
            self.message_user(
                request,
                f"{count} arquivo(s) processado(s) com sucesso.",
                messages.SUCCESS
            )
        
        if errors > 0:
            self.message_user(
                request,
                f"{errors} arquivo(s) não puderam ser processados. Verifique os erros acima.",
                messages.WARNING
            )
    
    processar_selecionados.short_description = "Processar arquivos selecionados"

################################################### ESTOQUE #############################################

# ADMIN PARA O APP ESTOQUE
# (Coloque isso antes da seção '# Ordem correta de registros' ou onde achar mais organizado)

class UnidadeMedidaEstoqueAdmin(admin.ModelAdmin): # Use admin.ModelAdmin como base
    list_display = ('nome', 'simbolo')
    search_fields = ('nome', 'simbolo')

class CategoriaProdutoEstoqueAdmin(admin.ModelAdmin):
    list_display = ('nome', 'descricao')
    search_fields = ('nome',)

class FornecedorEstoqueAdmin(admin.ModelAdmin):
    list_display = ('nome', 'contato')
    search_fields = ('nome',)

class LocalEstoqueAdmin(admin.ModelAdmin):
    list_display = ('nome', 'descricao')
    search_fields = ('nome',)

class ProdutoEstoqueAdmin(admin.ModelAdmin):
    list_display = ('nome_padrao', 'categoria', 'unidade_medida_primaria', 'sku', 'fornecedor_principal')
    list_filter = ('categoria', 'unidade_medida_primaria', 'fornecedor_principal')
    search_fields = ('nome_padrao', 'sku', 'nome_alternativo_fornecedor', 'descricao')
    autocomplete_fields = ['categoria', 'unidade_medida_primaria', 'fornecedor_principal']

class MovimentacaoEstoqueInlineEstoque(admin.TabularInline):
    model = MovimentacaoEstoque
    extra = 0
    fields = ('tipo_movimentacao', 'quantidade_movimentada', 'unidade_medida_movimentacao', 'data_movimentacao', 'usuario', 'notas')
    readonly_fields = ('quantidade_convertida',)
    autocomplete_fields = ['unidade_medida_movimentacao'] # 'usuario' foi removido anteriormente devido a um erro

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "usuario":
            kwargs['initial'] = request.user.id
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

class ItemEstoqueAdmin(admin.ModelAdmin):
    list_display = ('produto', 'local', 'quantidade', 'saldo_minimo', 'esta_abaixo_minimo', 'ultima_atualizacao') # Removido 'media_consumo_display' por simplicidade aqui, adicione se necessário
    list_filter = ('local', 'produto__categoria', 'produto__unidade_medida_primaria')
    search_fields = ('produto__nome_padrao', 'local__nome')
    readonly_fields = ('quantidade', 'ultima_atualizacao')
    autocomplete_fields = ['produto', 'local']
    inlines = [MovimentacaoEstoqueInlineEstoque]

class MovimentacaoEstoqueAdmin(admin.ModelAdmin):
    list_display = (
        'data_movimentacao', 'item_estoque', 'tipo_movimentacao',
        'quantidade_movimentada', 'unidade_medida_movimentacao',
        'quantidade_convertida', 'usuario'
    )
    list_filter = ('tipo_movimentacao', 'data_movimentacao', 'item_estoque__local', 'item_estoque__produto__categoria', 'usuario')
    search_fields = ('item_estoque__produto__nome_padrao', 'notas', 'usuario__username')
    readonly_fields = ('quantidade_convertida',)
    date_hierarchy = 'data_movimentacao'
    autocomplete_fields = ['item_estoque', 'unidade_medida_movimentacao'] # 'usuario' removido

    def save_model(self, request, obj, form, change):
        if not obj.usuario_id:
            obj.usuario = request.user
        super().save_model(request, obj, form, change)


#-----------------------------------------------
# Ordem correta de registros
@admin.register(Empresa)
class EmpresaAdmin(ModeloBaseAdmin):
   pass

@admin.register(Cultivo)
class CultivoAdmin(ModeloBaseAdmin):
  pass

@admin.register(Tecnologia)
class TecnologiaAdmin(ModeloBaseAdmin):
    pass

@admin.register(MarcadorTrait)
class MarcadorTraitAdmin(ModeloBaseAdmin):
    pass

@admin.register(MarcadorCustomizado)
class MarcadorCustomizadoAdmin(ModeloBaseAdmin):
    pass

@admin.register(Status)
class StatusAdmin(ModeloBaseAdmin):
    pass

@admin.register(Etapa)
class EtapaAdmin(ModeloBaseAdmin):
    pass

admin_site.register(User, CustomUserAdmin)
admin_site.register(Empresa, EmpresaAdmin)
admin_site.register(Amostra, AmostraAdmin)
admin_site.register(Projeto, ProjetoAdmin)
admin_site.register(Placa96, Placa96Admin)
admin_site.register(Placa384, Placa384Admin)
admin_site.register(Placa1536, Placa1536Admin)
admin_site.register(Poco96, Poco96Admin)
admin_site.register(Poco384, Poco384Admin)
admin_site.register(Poco1536, Poco1536Admin)
admin_site.register(PlacaMap384, PlacaMap384Admin)
admin_site.register(PlacaMap1536, PlacaMap1536Admin)
admin_site.register(PlacaMap384to384, PlacaMap384to384Admin)
admin_site.register(Tecnologia, TecnologiaAdmin)
admin_site.register(Cultivo, CultivoAdmin)
admin_site.register(MarcadorTrait, MarcadorTraitAdmin)
admin_site.register(MarcadorCustomizado, MarcadorCustomizadoAdmin)
admin_site.register(Status, StatusAdmin)
admin_site.register(Etapa, EtapaAdmin)
admin_site.register(ResultadoUpload1536, ResultadoUpload1536Admin)
admin_site.register(ResultadoAmostra1536, ResultadoAmostra1536Admin)
admin_site.register(ResultadoUpload384, ResultadoUpload384Admin)
admin_site.register(ResultadoAmostra384, ResultadoAmostra384Admin)

# NOVOS REGISTROS PARA O APP ESTOQUE:
admin_site.register(UnidadeMedida, UnidadeMedidaEstoqueAdmin)
admin_site.register(CategoriaProduto, CategoriaProdutoEstoqueAdmin)
admin_site.register(Fornecedor, FornecedorEstoqueAdmin)
admin_site.register(LocalEstoque, LocalEstoqueAdmin) # Corrigido para usar o ModelAdmin definido
admin_site.register(Produto, ProdutoEstoqueAdmin)
admin_site.register(ItemEstoque, ItemEstoqueAdmin) # Corrigido para usar o ModelAdmin definido
admin_site.register(MovimentacaoEstoque, MovimentacaoEstoqueAdmin) # Corrigido para usar o ModelAdmin definido