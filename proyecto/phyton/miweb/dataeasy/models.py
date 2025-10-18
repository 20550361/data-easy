from django.db import models

class Categoria(models.Model):
    id_categoria = models.AutoField(primary_key=True)
    nombre_categoria = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.nombre_categoria


class Marca(models.Model):
    id_marca = models.AutoField(primary_key=True)
    nombre_marca = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.nombre_marca


class Producto(models.Model):
    id_producto = models.AutoField(primary_key=True)
    nombre_producto = models.CharField(max_length=100, unique=True)
    descripcion = models.TextField(blank=True, null=True)
    categoria = models.ForeignKey(Categoria, on_delete=models.SET_NULL, null=True, blank=True)
    marca = models.ForeignKey(Marca, on_delete=models.SET_NULL, null=True, blank=True)
    stock_actual = models.IntegerField(default=0)
    stock_minimo = models.IntegerField(default=5)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.nombre_producto


class MovimientoInventario(models.Model):
    id_movimiento = models.AutoField(primary_key=True)
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE)
    tipo_movimiento = models.CharField(max_length=10, choices=[('entrada', 'Entrada'), ('salida', 'Salida')])
    cantidad = models.IntegerField()
    fecha_movimiento = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.tipo_movimiento.capitalize()} - {self.producto.nombre_producto}"
