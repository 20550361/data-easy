import os
import django
import random
from datetime import timedelta
from django.utils import timezone

# 1. Configuración de Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'miweb.settings')
django.setup()

# 2. Importar tus modelos
from dataeasy.models import Producto, MovimientoInventario

def poblar_datos():
    print("🧹 1. Borrando historial antiguo...")
    MovimientoInventario.objects.all().delete()

    productos = list(Producto.objects.all())
    
    if not productos:
        print("❌ ERROR: No hay productos. Carga productos primero.")
        return

    print(f"📦 2. Generando movimientos para {len(productos)} productos...")
    
    cantidad_movimientos = 200
    
    for i in range(cantidad_movimientos):
        producto = random.choice(productos)
        tipo = random.choice(['entrada', 'salida'])
        cantidad = random.randint(1, 15)
        
        # Generar fecha aleatoria (hasta 6 meses atrás)
        dias_atras = random.randint(0, 180)
        fecha_real = timezone.now() - timedelta(days=dias_atras)

        # PASO A: Crear el movimiento (Django pondrá la fecha de HOY automáticamente)
        mov = MovimientoInventario.objects.create(
            producto=producto,
            tipo_movimiento=tipo,
            cantidad=cantidad
        )

        # PASO B: Sobrescribir la fecha manualmente y guardar de nuevo
        # Esto es obligatorio porque 'auto_now_add=True' impide poner fechas pasadas al crear
        mov.fecha_movimiento = fecha_real
        mov.save()

    print(f"✅ ¡Listo! Se crearon {cantidad_movimientos} movimientos con fechas antiguas.")

if __name__ == '__main__':
    poblar_datos()