import json
import pandas as pd
from datetime import datetime, timedelta
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Count, F
from django.db.models.functions import TruncMonth
from django.utils import timezone
from django.core.serializers.json import DjangoJSONEncoder
from django.contrib import messages
from .models import Producto, Categoria, Marca, MovimientoInventario


# Vista de Login
def index(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect("home")  # si es correcto, ir al home
        else:
            return render(request, "index.html", {"error": "Usuario o contraseña incorrectos"})
    return render(request, "index.html")

# Vista Home
@login_required
def home(request):
    return render(request, 'home.html')

# Vista Perfil
@login_required
def perfil(request):
    return render(request, 'perfil.html')

# Vista Configuración
@login_required
def configuracion(request):
    return render(request, 'configuracion.html')


def estadisticas(request):
    fecha_inicio = request.GET.get('fecha_inicio')
    fecha_fin = request.GET.get('fecha_fin')
    hoy = timezone.now().date()

    try:
        fecha_inicio = datetime.strptime(fecha_inicio, "%Y-%m-%d").date() if fecha_inicio else (hoy - timedelta(days=180))
        fecha_fin = datetime.strptime(fecha_fin, "%Y-%m-%d").date() if fecha_fin else hoy
    except:
        fecha_inicio, fecha_fin = hoy - timedelta(days=180), hoy

    total_productos = Producto.objects.count()
    stock_total = Producto.objects.aggregate(total_stock=Sum('stock_actual'))['total_stock'] or 0
    total_categorias = Categoria.objects.count()
    total_marcas = Marca.objects.count()
    total_movimientos = MovimientoInventario.objects.count()

    productos_bajo_stock = Producto.objects.filter(stock_actual__lt=F('stock_minimo')).order_by('stock_actual')
    productos_sin_stock = Producto.objects.filter(stock_actual=0)

    stock_por_categoria_qs = Producto.objects.values('categoria__nombre_categoria').annotate(total=Sum('stock_actual')).order_by('-total')
    stock_por_categoria = [
        {'categoria': r['categoria__nombre_categoria'] or 'Sin categoría', 'total': r['total'] or 0}
        for r in stock_por_categoria_qs
    ]

    stock_critico_marca_qs = (
        Producto.objects.filter(stock_actual__lt=F('stock_minimo'), marca__isnull=False)
        .values('marca__nombre_marca')
        .annotate(cantidad=Count('id_producto'))
        .order_by('-cantidad')
    )
    stock_critico_marca = [{'marca': r['marca__nombre_marca'], 'cantidad': r['cantidad']} for r in stock_critico_marca_qs]

    movimientos = MovimientoInventario.objects.filter(fecha_movimiento__date__range=[fecha_inicio, fecha_fin])
    movimientos_por_mes = movimientos.annotate(mes=TruncMonth('fecha_movimiento')) \
        .values('mes', 'tipo_movimiento') \
        .annotate(total=Sum('cantidad')) \
        .order_by('mes')

    meses, entradas, salidas = [], {}, {}
    curr = fecha_inicio.replace(day=1)
    while curr <= fecha_fin:
        key = curr.strftime('%Y-%m')
        meses.append(key)
        entradas[key], salidas[key] = 0, 0
        curr = (curr + timedelta(days=32)).replace(day=1)

    for row in movimientos_por_mes:
        m = row['mes'].strftime('%Y-%m')
        if row['tipo_movimiento'] == 'entrada':
            entradas[m] = row['total'] or 0
        else:
            salidas[m] = row['total'] or 0

    chart_data = {
        'meses': meses,
        'entradas': [entradas[m] for m in meses],
        'salidas': [salidas[m] for m in meses],
        'stock_por_categoria_labels': [r['categoria'] for r in stock_por_categoria],
        'stock_por_categoria_values': [r['total'] for r in stock_por_categoria],
        'stock_critico_marca_labels': [r['marca'] for r in stock_critico_marca],
        'stock_critico_marca_values': [r['cantidad'] for r in stock_critico_marca],
    }

    context = {
        'total_productos': total_productos,
        'stock_total': stock_total,
        'total_categorias': total_categorias,
        'total_marcas': total_marcas,
        'total_movimientos': total_movimientos,
        'productos_bajo_stock': productos_bajo_stock,
        'productos_sin_stock': productos_sin_stock,
        'chart_data_json': json.dumps(chart_data, cls=DjangoJSONEncoder),
        'fecha_inicio': fecha_inicio,
        'fecha_fin': fecha_fin,
    }
    return render(request, 'inventario/estadisticas.html', context)


def carga_datos(request):
    if request.method == 'POST' and request.FILES.get('archivo_excel'):
        archivo = request.FILES['archivo_excel']
        try:
            df = pd.read_excel(archivo)
            for _, row in df.iterrows():
                nombre = str(row.get('nombre_producto')).strip()
                categoria_nombre = str(row.get('categoria')).strip() if row.get('categoria') else None
                marca_nombre = str(row.get('marca')).strip() if row.get('marca') else None

                categoria = Categoria.objects.get_or_create(nombre_categoria=categoria_nombre)[0] if categoria_nombre else None
                marca = Marca.objects.get_or_create(nombre_marca=marca_nombre)[0] if marca_nombre else None

                producto, _ = Producto.objects.get_or_create(nombre_producto=nombre)
                producto.descripcion = row.get('descripcion', producto.descripcion)
                producto.categoria = categoria
                producto.marca = marca
                producto.stock_actual = int(row.get('stock_actual', producto.stock_actual or 0))
                producto.stock_minimo = int(row.get('stock_minimo', producto.stock_minimo or 5))
                producto.save()

            messages.success(request, "✅ Archivo Excel cargado correctamente.")
        except Exception as e:
            messages.error(request, f"❌ Error al procesar el archivo: {e}")

        return redirect('carga_datos')

    return render(request, 'inventario/carga_datos.html')