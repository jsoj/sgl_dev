from django.urls import path, include # Add include
from django.contrib.auth import views as auth_views
from app.views import placa384_views, placa384_htmx
from . import views
from .views import api_views, project_views, projeto_pdf_views, api_login_view
from rest_framework.routers import DefaultRouter
from .views.debug_view import debug_view

# Create a router and register our viewsets with it.
router = DefaultRouter()
router.register(r'users', api_views.UserViewSet, basename='user')
router.register(r'groups', api_views.GroupViewSet, basename='group')
router.register(r'empresa', api_views.EmpresaViewSet, basename='empresa') # Changed 'empresas' to 'empresa'
router.register(r'cultivos', api_views.CultivoViewSet, basename='cultivo')
router.register(r'statuses', api_views.StatusViewSet, basename='status')
router.register(r'etapas', api_views.EtapaViewSet, basename='etapa')
router.register(r'tecnologias', api_views.TecnologiaViewSet, basename='tecnologia')
router.register(r'marcador-traits', api_views.MarcadorTraitViewSet, basename='marcadortrait')
router.register(r'marcador-customizados', api_views.MarcadorCustomizadoViewSet, basename='marcadorcustomizado')
router.register(r'projetos', api_views.ProjetoViewSet, basename='projeto') # Added ProjetoViewSet
# Register other viewsets for other models here following the same pattern

urlpatterns = [
    # Debug URL - keep this at the beginning of urlpatterns
    path('debug/', debug_view, name='debug_view'),

    # API router URLS
    path('api/', include(router.urls)), # Add this line for DRF router

    # Autenticação
    path('login/', auth_views.LoginView.as_view(), name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('api/login/', api_login_view, name='api_login'),
    path('api/logout/', api_views.api_logout_view, name='api_logout'),
    path('api/dashboard/', api_views.DashboardAPIView.as_view(), name='api_dashboard'),

    
    # Páginas principais
    path('', views.home, name='home'),
    path('criar-projeto/', views.criar_projeto, name='criar_projeto'),
    path('criar-placa-384/', placa384_views.criar_placa_384, name='criar_placa_384'),
    
    # APIs para carregar dados dinâmicos
    path('api/projetos/<int:empresa_id>/', views.get_projetos, name='get_projetos'),
    path('api/placas-96/<int:projeto_id>/', views.get_placas_96, name='get_placas_96'),
    path('api/verificar-projeto/', api_views.verificar_projeto, name='verificar_projeto_api'),

    path(
        'admin/api/placas-1536/<int:projeto_id>/',
        views.get_placas_1536,
        name='api-placas-1536'
    ),
    path(
        'htmx/carregar-placas-por-projeto/',
        views.carregar_placas_por_projeto,
        name='carregar-placas-por-projeto'
    ),

    # HTMX routes
    path('criar-placas-384-htmx/', placa384_htmx.criar_placas_384_htmx, name='criar_placas_384_htmx'),
    path('carregar-projetos-por-empresa/', placa384_htmx.carregar_projetos_por_empresa, name='carregar_projetos_por_empresa'),
    path('carregar-placas-por-projeto/', views.carregar_placas_por_projeto, name='carregar_placas_por_projeto'),
    path('criar-placas-384/', placa384_htmx.criar_placas_384, name='criar_placas_384'),
    path('criar-placas-384-lote/', placa384_htmx.criar_placas_384_lote, name='criar_placas_384_lote'),

    path('projetos/', project_views.projetos_lista, name='projetos_lista'),
    path('projetos/parcial/', project_views.projetos_lista_parcial, name='projetos_lista_parcial'),
    
    path('projetos/acoes/', project_views.projetos_acoes, name='projetos_acoes'),
    path('admin/api/placas-1536/<int:projeto_id>/', views.get_placas_1536, name='api-placas-1536'),
    path('admin/app/resultadoupload384/<path:object_id>/processar/', views.processar_arquivo_384_view, name='processar-arquivo-384'),
    path('projetos/<int:projeto_id>/pdf/', projeto_pdf_views.projeto_pdf_view, name='projeto_pdf'),
    path('projetos/<int:projeto_id>/pdf-download/', projeto_pdf_views.projeto_pdf_download, name='projeto_pdf_download'),
        ]

