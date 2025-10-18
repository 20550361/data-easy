from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.db.models import Sum, F
from .models import MovimientoInventario, Producto

def actualizar_stock_producto(producto_id):
    """
    Calcula el stock total sumando todas las entradas y restando 
    todas las salidas para un producto específico.
    """
    
    # 1. Suma todas las 'entradas'
    total_entradas = MovimientoInventario.objects.filter(
        producto_id=producto_id,
        tipo_movimiento='entrada'
    ).aggregate(total=Sum('cantidad'))['total'] or 0

    # 2. Suma todas las 'salidas'
    total_salidas = MovimientoInventario.objects.filter(
        producto_id=producto_id,
        tipo_movimiento='salida'
    ).aggregate(total=Sum('cantidad'))['total'] or 0

    # 3. Calcula el stock final
    stock_calculado = total_entradas - total_salidas
    
    # 4. Actualiza el campo 'stock_actual' en el modelo Producto
    # Usamos .update() en lugar de .save() para evitar un bucle infinito
    # (ya que .save() volvería a disparar el signal).
    Producto.objects.filter(id=producto_id).update(stock_actual=stock_calculado)

@receiver(post_save, sender=MovimientoInventario)
def gestionar_movimiento_guardado(sender, instance, **kwargs):
    """
    Se activa CADA VEZ que un MovimientoInventario se guarda 
    (ya sea nuevo o editado).
    """
    actualizar_stock_producto(instance.producto.id)

@receiver(post_delete, sender=MovimientoInventario)
def gestionar_movimiento_eliminado(sender, instance, **kwargs):
    """
    Se activa CADA VEZ que un MovimientoInventario se elimina.
    """
    actualizar_stock_producto(instance.producto.id)