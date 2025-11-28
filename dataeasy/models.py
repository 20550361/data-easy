from django.db import models
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.db.models import Sum
from django.contrib.auth.models import User  # <-- NUEVO
from django.core.files.base import ContentFile

# --- Modelo 1: Categoria ---
class Categoria(models.Model):
    nombre_categoria = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.nombre_categoria

# --- Modelo 2: Marca ---
class Marca(models.Model):
    nombre_marca = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.nombre_marca

# --- Modelo 3: Producto ---
class Producto(models.Model):
    nombre_producto = models.CharField(max_length=100, unique=True)
    descripcion = models.TextField(blank=True, null=True)

    categoria = models.ForeignKey(Categoria, on_delete=models.SET_NULL, null=True, blank=True)
    marca = models.ForeignKey(Marca, on_delete=models.SET_NULL, null=True, blank=True)

    stock_actual = models.IntegerField(default=0)
    stock_minimo = models.IntegerField(default=5)

    fecha_actualizacion = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.nombre_producto

    @property
    def en_alerta_stock(self):
        """ True si el stock está por debajo (o igual) del mínimo. """
        return self.stock_actual <= self.stock_minimo

# --- Modelo 4: MovimientoInventario ---
class MovimientoInventario(models.Model):
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE, related_name="movimientos")

    TIPO_MOVIMIENTO_CHOICES = [
        ('entrada', 'Entrada'),
        ('salida', 'Salida')
    ]

    tipo_movimiento = models.CharField(max_length=10, choices=TIPO_MOVIMIENTO_CHOICES)
    cantidad = models.PositiveIntegerField()
    fecha_movimiento = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.tipo_movimiento.capitalize()} - {self.producto.nombre_producto}"

# --- Modelo 5: Preguntas de Seguridad por Usuario ---
class SeguridadUsuario(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='seguridad')

    # Puedes personalizar el catálogo de preguntas o dejarlas libres
    pregunta1 = models.CharField(max_length=255, blank=True)
    respuesta1 = models.CharField(max_length=255, blank=True)

    pregunta2 = models.CharField(max_length=255, blank=True)
    respuesta2 = models.CharField(max_length=255, blank=True)

    class Meta:
        verbose_name = "Seguridad de Usuario"
        verbose_name_plural = "Seguridad de Usuarios"

    def __str__(self):
        return f"Seguridad de {self.user.username}"

    @property
    def has_preguntas(self):
        return bool(self.pregunta1 and self.respuesta1 and self.pregunta2 and self.respuesta2)

    def verify_answers(self, r1: str, r2: str) -> bool:
        """
        Verifica respuestas de forma case-insensitive y sin espacios extra.
        """
        norm = lambda s: (s or "").strip().casefold()
        return norm(r1) == norm(self.respuesta1) and norm(r2) == norm(self.respuesta2)
    
# ============================
# MODELOS DE FACTURACIÓN
# ============================
class Factura(models.Model):
    cliente_nombre = models.CharField(max_length=100)
    cliente_apellido = models.CharField(max_length=100)
    cliente_rut = models.CharField(max_length=15)
    fecha = models.DateTimeField(auto_now_add=True)

    # Nuevo: total de la factura
    total = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    # Nuevo: archivo PDF generado
    archivo_pdf = models.FileField(upload_to="facturas_pdfs/", null=True, blank=True)

    def __str__(self):
        return f"Factura #{self.id} - {self.cliente_nombre} {self.cliente_apellido}"


class DetalleFactura(models.Model):
    factura = models.ForeignKey(Factura, related_name="detalles", on_delete=models.CASCADE)
    producto = models.ForeignKey("Producto", on_delete=models.CASCADE)

    cantidad = models.PositiveIntegerField()

    # No usamos precios por ahora, pero se dejan
    precio = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    subtotal = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    # Nuevos datos informativos:
    categoria = models.CharField(max_length=255, null=True, blank=True)
    marca = models.CharField(max_length=255, null=True, blank=True)

    def __str__(self):
        return f"{self.producto.nombre_producto} (x{self.cantidad})"