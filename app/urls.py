# from django.urls import path
# from django.contrib.auth import views as auth_views
# from . import views
# from django.urls import path, include
# from django.contrib import admin
# from rest_framework import routers
# from rest_framework_simplejwt.views import (
#     TokenObtainPairView,
#     TokenRefreshView,
# )
# from app import views
# from app.views import (
#     UserViewSet, 
#     GroupViewSet,
#     get_projetos,
#     get_placas_96,
#     transferir_96_384
# )

# # Configuração do router para as ViewSets
# router = routers.DefaultRouter()
# router.register(r'users', UserViewSet)
# router.register(r'groups', GroupViewSet)

# urlpatterns = [
#     # URLs da API JWT
#     path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
#     path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    
#     # URLs da API REST
#     path('api/', include(router.urls)),
#     path('api-auth/', include('rest_framework.urls', namespace='rest_framework')),
    
#     # URLs para transferência de placas
#     path(
#         'admin/app/placa384/get-projetos/<int:empresa_id>/',
#         views.get_projetos,
#         name='get_projetos'
#     ),
#     path(
#         'admin/app/placa384/get-placas/<int:projeto_id>/',
#         get_placas_96,
#         name='get_placas_96'
#     ),
#     path(
#         'admin/app/placa384/transferir-96-384/',
#         transferir_96_384,
#         name='placa384_transferir_96_384'
#     ),
    
#     # URLs protegidas
#     path('api/protected/', views.protected_view, name='protected'),
#     path('api/protected-class/', views.ProtectedView.as_view(), name='protected-class'),

#       # Autenticação
#     path('login/', auth_views.LoginView.as_view(), name='login'),
#     path('logout/', views.logout_view, name='logout'),
    
#     # Páginas principais
#     path('', views.home, name='home'),
#     path('criar-projeto/', views.criar_projeto, name='criar_projeto'),
#     path('criar-placa-384/', views.criar_placa_384, name='criar_placa_384'),
    
#     # APIs para carregar dados dinâmicos
#     path('api/projetos/<int:empresa_id>/', views.get_projetos, name='get_projetos'),
#     path('api/placas-96/<int:projeto_id>/', views.get_placas_96, name='get_placas_96'),
# ]

from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    # Autenticação
    path('login/', auth_views.LoginView.as_view(), name='login'),
    path('logout/', views.logout_view, name='logout'),
    
    # Páginas principais
    path('', views.home, name='home'),
    path('criar-projeto/', views.criar_projeto, name='criar_projeto'),
    path('criar-placa-384/', views.criar_placa_384, name='criar_placa_384'),
    
    # APIs para carregar dados dinâmicos
    path('api/projetos/<int:empresa_id>/', views.get_projetos, name='get_projetos'),
    path('api/placas-96/<int:projeto_id>/', views.get_placas_96, name='get_placas_96'),

    path(
        'admin/api/placas-1536/<int:projeto_id>/',
        views.get_placas_1536,
        name='api-placas-1536'
    ),
]

