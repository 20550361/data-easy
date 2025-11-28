from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.db.models import Sum
from .models import MovimientoInventario, Producto

def actualizar_stock_producto(producto_id):
    """
    Recalcula el stock de un producto sumando entradas y restando salidas.
    
    LÓGICA:
    - Suma todas las ENTRADAS (compras/devoluciones)
    - Resta todas las SALIDAS (ventas)
    - stock_actual = total_entradas - total_salidas
    
    Nota: La validación de stock insuficiente se hace en la vista ANTES de crear movimientos.
    """
    # Obtener total de todas las entradas (compras, devoluciones, etc.)
    total_entradas = MovimientoInventario.objects.filter(
        producto_id=producto_id,
        tipo_movimiento='entrada'
    ).aggregate(total=Sum('cantidad'))['total'] or 0

    # Obtener total de todas las salidas (ventas, pérdidas, etc.)
    total_salidas = MovimientoInventario.objects.filter(
        producto_id=producto_id,
        tipo_movimiento='salida'
    ).aggregate(total=Sum('cantidad'))['total'] or 0

    # Calcular stock: entradas - salidas
    stock_calculado = total_entradas - total_salidas
    
    # Actualizar el stock del producto
    # Usamos update() para evitar disparar signals infinitamente
    Producto.objects.filter(id=producto_id).update(stock_actual=stock_calculado)

@receiver(post_save, sender=MovimientoInventario)
def gestionar_movimiento_guardado(sender, instance, **kwargs):
    """
    Signal que se dispara DESPUÉS de crear o editar un MovimientoInventario.
    Recalcula el stock del producto afectado automáticamente.
    """
    actualizar_stock_producto(instance.producto.id)

@receiver(post_delete, sender=MovimientoInventario)
def gestionar_movimiento_eliminado(sender, instance, **kwargs):
    """
    Signal que se dispara DESPUÉS de eliminar un MovimientoInventario.
    Recalcula el stock del producto afectado automáticamente.
    """
    actualizar_stock_producto(instance.producto.id)