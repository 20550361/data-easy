from django.urls import path
from . import views
from django.contrib.auth.views import LogoutView

urlpatterns = [
    # --- Autenticación y Páginas Principales ---
    path('', views.index, name='index'), 
    path('home/', views.home, name='home'),
    path('recuperacion/', views.recuperacion, name='recuperacion'),
    path('logout/', LogoutView.as_view(template_name='logout.html'), name='logout'),
    
    # --- Páginas Estáticas de Usuario ---
    path('perfil/', views.perfil, name='perfil'),
    path('configuracion/', views.configuracion, name='configuracion'),

    # --- Gestión de Inventario ---
    path('inventario/', views.lista_inventario, name='inventario_lista'),
    path('inventario/nuevo/', views.crear_producto, name='inventario_nuevo'),
    path('inventario/editar/<int:id_producto>/', views.editar_producto, name='inventario_editar'),
    path('inventario/eliminar/<int:id_producto>/', views.eliminar_producto, name='inventario_eliminar'),
    path('inventario/exportar/', views.exportar_excel, name='exportar_excel'),


        
    
    # NUEVO: crear producto
    path('inventario/nuevo/', views.crear_producto, name='inventario_nuevo'),


    # --- Gestión de Usuarios ---vene

    path('usuarios/', views.lista_usuarios, name='lista_usuarios'),
    path('usuarios/crear/', views.crear_usuario, name='usuario_crear'),
    path('usuarios/editar/<int:pk>/', views.editar_usuario, name='usuario_editar'),
    path('usuarios/eliminar/<int:pk>/', views.eliminar_usuario, name='usuario_eliminar'),

    
    # --- Datos y Analíticas ---
    path('estadisticas/', views.estadisticas, name='estadisticas'),
    path('carga_datos/', views.carga_datos, name='carga_datos'),
    path('api/chart-data/', views.chart_data_api, name='chart_data_api'),

    # --- FACTURACIÓN ---
    path('facturacion/', views.facturacion, name='facturacion'),
    path('facturacion/registrar/', views.registrar_factura, name='registrar_factura'),
    path('facturacion/pdf/<int:id>/', views.factura_pdf, name='factura_pdf'),







    path('acceso-denegado/', views.acceso_denegado, name='acceso_denegado'),


]