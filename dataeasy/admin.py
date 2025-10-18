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

# --- 2. Configuración de Producto (con mejoras) ---

class MovimientoInventarioInline(admin.TabularInline):
    """
    Esto permite ver el historial de movimientos 
    DENTRO de la página de detalle de cada Producto.
    """
    model = MovimientoInventario
    extra = 0  # No mostrar formularios vacíos
    fields = ('fecha_movimiento', 'tipo_movimiento', 'cantidad')
    readonly_fields = ('fecha_movimiento',) # La fecha no se debe editar
    ordering = ('-fecha_movimiento',) # Mostrar los más recientes primero
    can_delete = False # No permitir borrar movimientos desde aquí

    def has_add_permission(self, request, obj=None):
        return False # No permitir añadir movimientos desde aquí (debe hacerse en la app)

@admin.register(Producto)
class ProductoAdmin(admin.ModelAdmin):
    list_display = ('nombre_producto', 'categoria', 'marca', 'stock_actual', 'stock_minimo')
    list_filter = ('categoria', 'marca')
    search_fields = ('nombre_producto',) # Necesario para el autocomplete
    ordering = ('nombre_producto',)
    
    # --- MEJORA DE LÓGICA ---
    # El stock_actual se calcula automáticamente con los 'signals'
    # que programamos. Hacemos que sea de "solo lectura" en el 
    # admin para evitar que alguien lo edite manualmente y 
    # rompa la consistencia de los datos.
    readonly_fields = ('stock_actual',)
    
    # --- MEJORA DE UI ---
    # Muestra la tabla de movimientos (el Inline de arriba)
    # en la parte inferior de la página de edición del producto.
    inlines = [MovimientoInventarioInline]


# --- 3. Configuración de Movimiento (con mejoras) ---

@admin.register(MovimientoInventario)
class MovimientoInventarioAdmin(admin.ModelAdmin):
    list_display = ('producto', 'tipo_movimiento', 'cantidad', 'fecha_movimiento')
    list_filter = ('tipo_movimiento', 'fecha_movimiento')
    date_hierarchy = 'fecha_movimiento' # Navegación rápida por fechas
    
    # --- MEJORA DE RENDIMIENTO ---
    # Si tienes miles de productos, un menú desplegable es muy lento.
    # 'autocomplete_fields' lo reemplaza con un buscador dinámico
    # (requiere 'search_fields' en ProductoAdmin, que ya lo tiene).
    autocomplete_fields = ['producto']