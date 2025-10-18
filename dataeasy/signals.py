from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.db.models import Sum
from .models import MovimientoInventario, Producto

def actualizar_stock_producto(producto_id):
    """
    Recalcula el stock de un producto sumando entradas y restando salidas.
    """
    total_entradas = MovimientoInventario.objects.filter(
        producto_id=producto_id,
        tipo_movimiento='entrada'
    ).aggregate(total=Sum('cantidad'))['total'] or 0

    total_salidas = MovimientoInventario.objects.filter(
        producto_id=producto_id,
        tipo_movimiento='salida'
    ).aggregate(total=Sum('cantidad'))['total'] or 0

    stock_calculado = total_entradas - total_salidas
    
    # Actualiza el producto sin disparar el signal de nuevo
    Producto.objects.filter(id=producto_id).update(stock_actual=stock_calculado)

@receiver(post_save, sender=MovimientoInventario)
def gestionar_movimiento_guardado(sender, instance, **kwargs):
    """ Se activa cuando se crea o edita un movimiento. """
    actualizar_stock_producto(instance.producto.id)

@receiver(post_delete, sender=MovimientoInventario)
def gestionar_movimiento_eliminado(sender, instance, **kwargs):
    """ Se activa cuando se elimina un movimiento. """
    actualizar_stock_producto(instance.producto.id)