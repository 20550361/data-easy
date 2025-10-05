from django.urls import path
from . import views
from django.contrib.auth.views import LogoutView

urlpatterns = [
    path('', views.index, name='index'),  # login
    path('home/', views.home, name='home'),
    path('perfil/', views.perfil, name='perfil'),
    path('configuracion/', views.configuracion, name='configuracion'),
    path('logout/', LogoutView.as_view(next_page='index'), name='logout'),
    path('recuperacion/', views.recuperacion, name='recuperacion'),

]
