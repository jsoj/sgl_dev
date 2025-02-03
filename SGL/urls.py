# from django.contrib import admin
# from django.urls import include, path
# from rest_framework import routers
# from app import views
# from rest_framework_simplejwt.views import (
#     TokenObtainPairView,
#     TokenRefreshView,
# )
# from django.conf.urls.static import static
# from django.conf import settings
# from app.admin import admin_site 

# router = routers.DefaultRouter()
# router.register(r'users', views.UserViewSet)
# router.register(r'groups', views.GroupViewSet)

# urlpatterns = [
#     path('admin/', admin.site.urls),
#     path('', include('app.urls')),
#     path('api/', include(router.urls)),
#     path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
#     path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
#     path('api-auth/', include('rest_framework.urls', namespace='rest_framework')),
#     # path('selecionar-empresa/<int:empresa_id>/', views.selecionar_empresa, name='selecionar_empresa'),
# ] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT) + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

from django.urls import include, path
from rest_framework import routers
from app import views
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)
from django.conf.urls.static import static
from django.conf import settings
from app.admin import admin_site  # Importe o admin_site customizado

router = routers.DefaultRouter()
router.register(r'users', views.UserViewSet)
router.register(r'groups', views.GroupViewSet)

urlpatterns = [
    path('admin/', admin_site.urls),  # Use admin_site ao invés de admin.site.urls
    path('', include('app.urls')),
    path('api/', include(router.urls)),
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api-auth/', include('rest_framework.urls', namespace='rest_framework')),
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT) + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)