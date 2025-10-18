from django.db import models
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.db.models import Sum

# --- Modelo 1: Categoria ---
class Categoria(models.Model):
    # Django crea un 'id' automáticamente.
    nombre_categoria = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.nombre_categoria

# --- Modelo 2: Marca ---
class Marca(models.Model):
    # Django crea un 'id' automáticamente.
    nombre_marca = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.nombre_marca

# --- Modelo 3: Producto ---
class Producto(models.Model):
    # Django crea un 'id' automáticamente. Usaremos 'id' en lugar de 'id_producto'.
    nombre_producto = models.CharField(max_length=100, unique=True)
    descripcion = models.TextField(blank=True, null=True)
    
    categoria = models.ForeignKey(Categoria, on_delete=models.SET_NULL, null=True, blank=True)
    marca = models.ForeignKey(Marca, on_delete=models.SET_NULL, null=True, blank=True)
    
    # Este campo se actualizará automáticamente por los signals.
    stock_actual = models.IntegerField(default=0) 
    stock_minimo = models.IntegerField(default=5)
    
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.nombre_producto
    
    @property
    def en_alerta_stock(self):
        """
        Propiedad para saber si el stock está por debajo del mínimo.
        (Movida desde MovimientoInventario a Producto, que es donde pertenece).
        """
        return self.stock_actual <= self.stock_minimo

# --- Modelo 4: MovimientoInventario ---
class MovimientoInventario(models.Model):
    # Django crea un 'id' automáticamente.
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE, related_name="movimientos")
    
    TIPO_MOVIMIENTO_CHOICES = [
        ('entrada', 'Entrada'), 
        ('salida', 'Salida')
    ]
    
    tipo_movimiento = models.CharField(
        max_length=10,
        choices=TIPO_MOVIMIENTO_CHOICES
    )
    
    # Usamos PositiveIntegerField para asegurar que la cantidad nunca sea negativa.
    cantidad = models.PositiveIntegerField()
    fecha_movimiento = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.tipo_movimiento.capitalize()} - {self.producto.nombre_producto}"