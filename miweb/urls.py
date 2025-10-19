from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # Conecta todas las URLs de tu app 'dataeasy' a la raíz del sitio
    path('', include('dataeasy.urls')),
]