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

class MovimientoInventarioInline(admin.TabularInline):
    """ Muestra el historial de movimientos dentro del producto """
    model = MovimientoInventario
    extra = 0
    fields = ('fecha_movimiento', 'tipo_movimiento', 'cantidad')
    readonly_fields = ('fecha_movimiento',)
    ordering = ('-fecha_movimiento',)
    can_delete = False
    def has_add_permission(self, request, obj=None):
        return False

@admin.register(Producto)
class ProductoAdmin(admin.ModelAdmin):
    list_display = ('nombre_producto', 'categoria', 'marca', 'stock_actual', 'stock_minimo')
    list_filter = ('categoria', 'marca')
    search_fields = ('nombre_producto',)
    ordering = ('nombre_producto',)
    
    # Bloquea la edición manual del stock
    readonly_fields = ('stock_actual',)
    
    # Añade el historial de movimientos
    inlines = [MovimientoInventarioInline]

@admin.register(MovimientoInventario)
class MovimientoInventarioAdmin(admin.ModelAdmin):
    list_display = ('producto', 'tipo_movimiento', 'cantidad', 'fecha_movimiento')
    list_filter = ('tipo_movimiento', 'fecha_movimiento')
    date_hierarchy = 'fecha_movimiento'
    autocomplete_fields = ['producto'] # Optimiza la búsqueda de productos