from django.contrib import admin
from .models import Categoria, Marca, Producto, MovimientoInventario

@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    list_display = ('nombre_categoria',)
    search_fields = ('nombre_categoria',)

@admin.register(Marca)
class MarcaAdmin(admin.ModelAdmin):
    list_display = ('nombre_marca',)
    search_fields = ('nombre_marca',)

@admin.register(Producto)
class ProductoAdmin(admin.ModelAdmin):
    list_display = ('nombre_producto', 'categoria', 'marca', 'stock_actual', 'stock_minimo')
    list_filter = ('categoria', 'marca')
    search_fields = ('nombre_producto',)
    ordering = ('nombre_producto',)

@admin.register(MovimientoInventario)
class MovimientoInventarioAdmin(admin.ModelAdmin):
    list_display = ('producto', 'tipo_movimiento', 'cantidad', 'fecha_movimiento')
    list_filter = ('tipo_movimiento', 'fecha_movimiento')
    date_hierarchy = 'fecha_movimiento'