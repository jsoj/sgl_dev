from django.db import transaction  # Adicionando esta importação
from .forms import TransferPlacasForm, Transfer384to384Form, Transfer384to1536Form# Adicione esta importação no início do arquivo
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth import get_user_model
from django.db.models import Q
from app.models import ( Tecnologia, Cultivo, Marcador, Projeto, Status, 
                        Protocolo, Etapa, User,  Amostra, Placa96, 
                        Placa384, Placa1536, Empresa,  Poco96, Poco384, Poco1536,    
                        PlacaMap384, PlacaMap1536, Resultado, PlacaMap384to384)

from django.urls import path
from django.shortcuts import render, redirect
from django.contrib import messages
from django import forms
from django.core.exceptions import ValidationError  # Adicione esta linha
from django.http import JsonResponse
from django.contrib.admin import AdminSite
from django.contrib.auth.models import Group
import logging
from django.contrib.auth.admin import GroupAdmin
# from admin_interface.models import Theme

logger = logging.getLogger(__name__)


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
                    'Resultados': 'app.resultado',
                },
            },
            'Cadastros': {
                'models': {
                    'Cultivo': 'app.cultivo',
                    'Etapa': 'app.etapa',
                    'Tecnologia': 'app.tecnologia',
                    'Marcador': 'app.marcador',
                    'Protocolo': 'app.protocolo',
                    'Status': 'app.status',
                    'Usuário': 'app.user',
                },
            },
            'Configurações': {
                'models': {
                    'Grupos de Usuários': 'auth.group',
                    # 'Temas da Interface': 'admin_interface.theme',
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

# Criar instância do site customizado
admin_site = CustomAdminSite(name='admin')
admin_site.register(Group, GroupAdmin)
# admin_site.register(Theme)

# CUSTOMIZACAO DO USER 
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

# Manter apenas este registro do User
admin_site.register(User, CustomUserAdmin)

# CUSTOMIZACAO DOS DEMAIS MODELOS
# @admin_site.register(Empresa)  # Agora admin_site está definido

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

admin_site.register(Empresa, EmpresaAdmin)

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

# @admin_site.register(Projeto)
class ProjetoAdmin(EmpresaAdminMixin, admin.ModelAdmin):
    list_display = ('empresa','empresa__nome','codigo_projeto', 'quantidade_amostras', 'status', 'cultivo', 'created_at')
    list_display_links = ["codigo_projeto"]
    list_filter = ('empresa','codigo_projeto', 'status', 'cultivo')  # Empresa primeiro para facilitar filtragem
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
admin_site.register(Projeto, ProjetoAdmin)

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

# @admin_site.register(Amostra)
class AmostraAdmin(EmpresaAdminMixin, admin.ModelAdmin):
    list_display = ('empresa', 'empresa__nome','projeto','codigo_amostra',  'data_cadastro')
    list_filter = ('empresa','projeto__codigo_projeto', 'data_cadastro')
    search_fields = ('codigo_amostra', 'projeto__codigo_projeto')
    autocomplete_fields = ['projeto']
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('projeto', 'empresa')
admin_site.register(Amostra, AmostraAdmin)


# Placas

# @admin_site.register(Placa96)
class Placa96Admin(EmpresaAdminMixin, admin.ModelAdmin):
    list_display = ('empresa', 'empresa__nome','projeto','codigo_placa', 'get_amostras_count',  'data_criacao', 'is_active')
    list_display_links=['codigo_placa']
    list_filter = (EmpresaFilter, ProjetoFilter,  'data_criacao', 'is_active')
    search_fields = ('codigo_placa', 'projeto__codigo_projeto')
    # inlines = [Poco96Inline]
    autocomplete_fields = ['projeto']

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('projeto', 'empresa')
admin_site.register(Placa96, Placa96Admin)


# @admin_site.register(Placa384)
class Placa384Admin(admin.ModelAdmin):
   list_display = ('empresa', 'empresa__nome','projeto','codigo_placa', 'get_amostras_count', 'data_criacao', 'is_active')
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
           **admin.site.each_context(request),
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
            **admin.site.each_context(request),
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
            **admin.site.each_context(request),
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

admin_site.register(Placa384, Placa384Admin)
   

# @admin_site.register(Placa1536)
class Placa1536Admin(EmpresaAdminMixin, admin.ModelAdmin):
    list_display = ('empresa', 'empresa__nome','projeto', 'codigo_placa', 'get_amostras_count','data_criacao',  'is_active')
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

admin_site.register(Placa1536, Placa1536Admin)

# Mapeamentos

# @admin_site.register(PlacaMap384)
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
admin_site.register(PlacaMap384, PlacaMap384Admin)


# @admin_site.register(PlacaMap1536)
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
admin_site.register(PlacaMap1536, PlacaMap1536Admin)


# @admin_site.register(PlacaMap384to384)
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
admin_site.register(PlacaMap384to384, PlacaMap384to384Admin)


# Resultados

# @admin_site.register(Resultado)
class ResultadoAdmin(EmpresaAdminMixin, admin.ModelAdmin):
    list_display = ('empresa', 'empresa__nome','amostra', 'get_poco_display', 'valor', 'data_resultado')
    list_filter = ('empresa','amostra__projeto',  'data_resultado')
    search_fields = (
        'amostra__codigo_amostra',
        'poco_96__placa__codigo_placa',
        'poco_384__placa__codigo_placa',
        'poco_1536__placa__codigo_placa'
    )
    autocomplete_fields = ['amostra', 'poco_96', 'poco_384', 'poco_1536']
    
    def get_poco_display(self, obj):
        if obj.poco_96:
            return f"P96: {obj.poco_96}"
        elif obj.poco_384:
            return f"P384: {obj.poco_384}"
        elif obj.poco_1536:
            return f"P1536: {obj.poco_1536}"
        return "-"
    get_poco_display.short_description = "Poço"

    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'amostra', 'poco_96', 'poco_384', 'poco_1536', 
            'empresa', 'amostra__projeto'
        )
admin_site.register(Resultado, ResultadoAdmin)

# Poços

# @admin_site.register(Poco96)
class Poco96Admin(EmpresaAdminMixin, admin.ModelAdmin):
    list_display = ('empresa', 'empresa__nome', 'placa', 'posicao', 'amostra',)
    list_display_links=['posicao']
    list_filter = (EmpresaFilter, ProjetoFilterPoco, PlacaFilterPoco)
    search_fields = ('placa__codigo_placa', 'posicao', 'amostra__codigo_amostra')
    autocomplete_fields = ['placa', 'amostra']
    placa_model = Placa96
    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'placa', 'placa__projeto', 'empresa', 'amostra'
        )
    
admin_site.register(Poco96, Poco96Admin)


# @admin_site.register(Poco384)
class Poco384Admin(EmpresaAdminMixin, admin.ModelAdmin):
    list_display = ('empresa', 'empresa__nome','placa', 'posicao', 'amostra')
    list_display_links=['posicao']
    list_filter = (EmpresaFilter, ProjetoFilterPoco, PlacaFilterPoco)  # Filtros aninhados
    search_fields = ('placa__codigo_placa', 'posicao', 'amostra__codigo_amostra')
    raw_id_fields = ['placa', 'amostra']  # Mudando de autocomplete para raw_id
    placa_model = Placa384  # Necessário para o PlacaFilter

admin_site.register(Poco384, Poco384Admin)


# @admin_site.register(Poco1536)
class Poco1536Admin(EmpresaAdminMixin, admin.ModelAdmin):
    list_display = ('empresa', 'empresa__nome','placa', 'posicao', 'amostra')
    list_display_links=['posicao']
    list_filter = (EmpresaFilter, ProjetoFilterPoco, PlacaFilterPoco) 
    search_fields = ('placa__codigo_placa', 'posicao', 'amostra__codigo_amostra')
    autocomplete_fields = ['placa', 'amostra']
    placa_model = Placa1536

admin_site.register(Poco1536, Poco1536Admin)


# Cadastros

# @admin_site.register(Tecnologia)
class TecnologiaAdmin(EmpresaAdminMixin, admin.ModelAdmin):
    list_display = ('nome', 'caracteristica', 'vencimento_patente', 'data_cadastro')
    search_fields = ('nome',)
admin_site.register(Tecnologia, TecnologiaAdmin)


# @admin_site.register(Cultivo)
class CultivoAdmin(EmpresaAdminMixin, admin.ModelAdmin):
    list_display = ('nome', 'nome_cientifico', 'data_cadastro')
    search_fields = ('nome',)
admin_site.register(Cultivo, CultivoAdmin)


# @admin_site.register(Marcador)
class MarcadorAdmin(EmpresaAdminMixin, admin.ModelAdmin):
    list_display = ('nome', 'cultivo', 'is_customizado')
    search_fields = ('nome',)
admin_site.register(Marcador, MarcadorAdmin)


# @admin_site.register(Status)
class StatusAdmin(EmpresaAdminMixin, admin.ModelAdmin):
    list_display = ('nome',)
    search_fields = ('nome',)
admin_site.register(Status, StatusAdmin)


# @admin_site.register(Protocolo)
class ProtocoloAdmin(EmpresaAdminMixin, admin.ModelAdmin):
    list_display = ('nome',)
    search_fields = ('nome',)
admin_site.register(Protocolo, ProtocoloAdmin)


# @admin_site.register(Etapa)
class EtapaAdmin(EmpresaAdminMixin, admin.ModelAdmin):
    list_display = ('nome',)
    search_fields = ('nome',)
admin_site.register(Etapa, EtapaAdmin)


