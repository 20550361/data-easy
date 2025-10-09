from django.urls import path
from . import views
from django.contrib.auth.views import LogoutView

urlpatterns = [
    path('', views.index, name='index'),  # login
    path('home/', views.home, name='home'),
    path('configuracion/', views.configuracion, name='configuracion'),
    path('logout/', LogoutView.as_view(next_page='index'), name='logout'),
    path('perfil/', views.perfil, name='perfil'),
    path('inventario/', views.inventario, name='inventario'),
    path('estadisticas/', views.estadisticas, name='estadisticas'),
    path('gestion_usuarios/', views.gestion_usuarios, name='gestion_usuarios'),
    path('recuperacion/', views.recuperacion, name='recuperacion'),
]
