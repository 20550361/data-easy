import os
import django
import random
from datetime import timedelta
from django.utils import timezone

# 1. Configurar Django para que funcione en este script suelto
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'miweb.settings')
django.setup()

from dataeasy.models import Producto, MovimientoInventario

def poblar_datos():
    print("🧹 1. Borrando historial antiguo...")
    MovimientoInventario.objects.all().delete()

    productos = list(Producto.objects.all())
    
    if not productos:
        print("❌ ERROR: No hay productos. Carga el Excel primero.")
        return

    print(f"📦 2. Generando movimientos para {len(productos)} productos...")
    
    # Generamos 200 movimientos distribuidos en los últimos 6 meses
    cantidad_movimientos = 200
    
    for i in range(cantidad_movimientos):
        producto = random.choice(productos)
        tipo = random.choice(['entrada', 'salida'])
        cantidad = random.randint(1, 15)
        
        # Fecha aleatoria entre hoy y hace 180 días
        dias_atras = random.randint(0, 180)