# Importar os ViewSets do arquivo api_views.py
from .api_views import UserViewSet, GroupViewSet, get_projetos, get_placas_96, get_placas_1536, api_login_view, api_logout_view, DashboardAPIView

# Importar as views HTMX
from .placa384_htmx import (
    criar_placas_384_htmx,
    carregar_projetos_por_empresa,
    carregar_placas_por_projeto,
    criar_placas_384
)

# Importar views de autenticação
from .auth_views import logout_view

# Importar views de páginas principais
from .home_views import home

# Importar views de projetos
from .project_views import criar_projeto

# Importar views de placas (tradicional, sem HTMX)
from .placa384_views import criar_placa_384, processar_arquivo_384_view

from .project_views import criar_projeto
from .project_views import projetos_lista, projetos_lista_parcial, projetos_acoes
from .projeto_pdf_views import projeto_pdf_view, generate_project_pdf
from .projeto_pdf_views import projeto_pdf_download