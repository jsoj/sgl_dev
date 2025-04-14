from django.urls import path
from django.contrib.auth import views as auth_views
from app.views import placa384_views, placa384_htmx
from . import views
from .views import api_views, project_views

urlpatterns = [
    # Autenticação
    path('login/', auth_views.LoginView.as_view(), name='login'),
    path('logout/', views.logout_view, name='logout'),
    
    # Páginas principais
    path('', views.home, name='home'),
    path('criar-projeto/', views.criar_projeto, name='criar_projeto'),
    path('criar-placa-384/', placa384_views.criar_placa_384, name='criar_placa_384'),
    
    # APIs para carregar dados dinâmicos
    path('api/projetos/<int:empresa_id>/', views.get_projetos, name='get_projetos'),
    path('api/placas-96/<int:projeto_id>/', views.get_placas_96, name='get_placas_96'),

    path(
        'admin/api/placas-1536/<int:projeto_id>/',
        views.get_placas_1536,
        name='api-placas-1536'
    ),

    path('api/verificar-projeto/', api_views.verificar_projeto, name='verificar_projeto_api'),

    # HTMX routes
    path('criar-placas-384-htmx/', placa384_htmx.criar_placas_384_htmx, name='criar_placas_384_htmx'),
    path('carregar-projetos-por-empresa/', placa384_htmx.carregar_projetos_por_empresa, name='carregar_projetos_por_empresa'),
    path('carregar-placas-por-projeto/', views.carregar_placas_por_projeto, name='carregar_placas_por_projeto'),
    path('criar-placas-384/', placa384_htmx.criar_placas_384, name='criar_placas_384'),
    path('criar-placas-384-lote/', placa384_htmx.criar_placas_384_lote, name='criar_placas_384_lote'),

    # Outras URLs...
    path('projetos/', project_views.projetos_lista, name='projetos_lista'),
    path('projetos/parcial/', project_views.projetos_lista_parcial, name='projetos_lista_parcial'),
    path('projetos/acoes/', project_views.projetos_acoes, name='projetos_acoes'),
]

