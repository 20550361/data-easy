# --- 1. IMPORTACIONES ---

# Python Standard Library
import json
from datetime import datetime, timedelta

# Third-Party Libraries
import pandas as pd  # Asegúrate de tenerlo instalado (pip install pandas openpyxl)

# Django Core
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.serializers.json import DjangoJSONEncoder
from django.core.paginator import Paginator
from django.db.models import Sum, Count, F, Q
from django.db.models.functions import TruncMonth
from django.utils import timezone

# Django Models
from django.contrib.auth.models import User

# Local App Imports
from .models import Producto, Categoria, Marca, MovimientoInventario
# (Aquí importarás tus Forms cuando los creemos)
# from .forms import ProductoForm, MovimientoForm 


# --- 2. VISTAS DE AUTENTICACIÓN Y NÚCLEO 🌐 ---

def index(request):
    """ Vista de Login """
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect("home")  # si es correcto, ir al home
        else:
            messages.error(request, "Usuario o contraseña incorrectos")
            return render(request, "index.html")
    return render(request, "index.html")

@login_required
def home(request):
    """ Vista Home / Dashboard """
    # Obtener los 5 productos con stock por debajo del mínimo
    productos_bajo_stock = Producto.objects.filter(
        stock_actual__lt=F('stock_minimo')
    ).order_by('stock_actual')[:5]

    # Obtener los 5 movimientos más recientes
    movimientos_recientes = MovimientoInventario.objects.select_related(
        'producto'
    ).order_by('-fecha_movimiento')[:5]

    context = {
        'productos_bajo_stock': productos_bajo_stock,
        'movimientos_recientes': movimientos_recientes,
    }
    return render(request, 'home.html', context)

@login_required
def perfil(request):
    """ Vista de Perfil de Usuario """
    return render(request, 'perfil.html')

@login_required
def configuracion(request):
    """ Vista de Configuración """
    return render(request, 'configuracion.html')


# --- 3. VISTAS DE GESTIÓN DE INVENTARIO 📦 ---

@login_required
def lista_inventario(request):
    """ Vista principal para listar, buscar y paginar el inventario. """
    
    # 1. Lógica de Búsqueda
    query = request.GET.get('q', '') 
    
    if query:
        productos_list = Producto.objects.filter(
            Q(nombre_producto__icontains=query) |
            Q(categoria__nombre_categoria__icontains=query) |
            Q(marca__nombre_marca__icontains=query)
        ).select_related('categoria', 'marca').order_by('nombre_producto')
    else:
        productos_list = Producto.objects.select_related('categoria', 'marca').all().order_by('nombre_producto')

    # 2. Conteo de Alertas
    total_alertas = productos_list.filter(stock_actual__lte=F('stock_minimo')).count()

    # 3. Lógica de Paginación
    paginator = Paginator(productos_list, 20) # 20 productos por página
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'total_alertas': total_alertas,
        'search_query': query,
        'total_productos': productos_list.count(),
    }
    return render(request, 'inventario.html', context)

@login_required
def editar_producto(request, id_producto):
    """ (POR HACER) Lógica para editar un producto y ver/añadir movimientos. """
    # (Aquí irá la lógica de ProductoForm y MovimientoForm)
    messages.info(request, "Función 'Editar Producto' pendiente de implementar.")
    return redirect('inventario_lista') # De momento, solo redirige

@login_required
def eliminar_producto(request, id_producto):
    """ (POR HACER) Lógica para eliminar un producto. """
    # (Aquí irá la lógica de confirmación)
    messages.info(request, "Función 'Eliminar Producto' pendiente de implementar.")
    return redirect('inventario_lista') # De momento, solo redirige


# --- 4. VISTAS DE GESTIÓN DE USUARIOS 👥 ---

@login_required
def lista_usuarios(request):
    """ Vista para la página de 'gestión de usuarios'. """
    usuarios = User.objects.all().order_by('username')
    context = {
        'lista_usuarios': usuarios
    }
    return render(request, 'gestion_usuarios.html', context)

@login_required
def crear_usuario(request):
    """ (POR HACER) Lógica para crear nuevos usuarios. """
    # (Aquí irá la lógica del formulario de creación de usuarios)
    messages.info(request, "Función 'Crear Usuario' pendiente de implementar.")
    return redirect('lista_usuarios') # De momento, solo redirige

@login_required
def editar_usuario(request, pk):
    """ (POR HACER) Lógica para editar roles/datos de usuarios. """
    # (Aquí irá la lógica del formulario de edición de usuarios)
    messages.info(request, "Función 'Editar Usuario' pendiente de implementar.")
    return redirect('lista_usuarios') # De momento, solo redirige


# --- 5. VISTAS DE DATOS Y ANALÍTICAS 📊 ---

@login_required
def estadisticas(request):
    """ Vista para mostrar gráficos y métricas del inventario. """
    fecha_inicio = request.GET.get('fecha_inicio')
    fecha_fin = request.GET.get('fecha_fin')
    hoy = timezone.now().date()

    try:
        fecha_inicio = datetime.strptime(fecha_inicio, "%Y-%m-%d").date() if fecha_inicio else (hoy - timedelta(days=180))
        fecha_fin = datetime.strptime(fecha_fin, "%Y-%m-%d").date() if fecha_fin else hoy
    except:
        fecha_inicio, fecha_fin = hoy - timedelta(days=180), hoy

    # --- Métricas generales ---
    total_productos = Producto.objects.count()
    stock_total = Producto.objects.aggregate(total_stock=Sum('stock_actual'))['total_stock'] or 0
    total_categorias = Categoria.objects.count()
    total_marcas = Marca.objects.count()
    total_movimientos = MovimientoInventario.objects.count()

    # --- Productos críticos ---
    productos_bajo_stock = Producto.objects.filter(stock_actual__lt=F('stock_minimo')).order_by('stock_actual')
    productos_sin_stock = Producto.objects.filter(stock_actual=0)

    # --- Stock por categoría ---
    stock_por_categoria_qs = (
        Producto.objects.values('categoria__nombre_categoria')
        .annotate(total=Sum('stock_actual'))
        .order_by('-total')
    )
    stock_por_categoria = [
        {'categoria': r['categoria__nombre_categoria'] or 'Sin categoría', 'total': r['total'] or 0}
        for r in stock_por_categoria_qs
    ]

    # --- Marcas con más productos en stock crítico ---
    stock_critico_marca_qs = (
        Producto.objects.filter(stock_actual__lt=F('stock_minimo'), marca__isnull=False)
        .values('marca__nombre_marca')
        .annotate(cantidad=Count('id_producto'))
        .order_by('-cantidad')
    )
    stock_critico_marca = [{'marca': r['marca__nombre_marca'], 'cantidad': r['cantidad']} for r in stock_critico_marca_qs]

    # --- Movimientos por mes (para gráfico) ---
    movimientos = MovimientoInventario.objects.filter(fecha_movimiento__date__range=[fecha_inicio, fecha_fin])
    movimientos_por_mes = movimientos.annotate(mes=TruncMonth('fecha_movimiento')) \
        .values('mes', 'tipo_movimiento') \
        .annotate(total=Sum('cantidad')) \
        .order_by('mes')

    # --- Generación de listas para gráficos ---
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


@login_required
def carga_datos(request):
    """ Vista para la carga masiva de datos desde Excel. """
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

                # Preparamos los datos del producto
                defaults_producto = {
                    'descripcion': row.get('descripcion'),
                    'categoria': categoria,
                    'marca': marca,
                    'stock_minimo': int(row.get('stock_minimo', 5)),
                }

                # Intenta crear el producto o actualiza si ya existe
                producto, created = Producto.objects.update_or_create(
                    nombre_producto=nombre,
                    defaults=defaults_producto
                )

                # SI ES UN PRODUCTO NUEVO, registrar su stock inicial
                if created:
                    stock_inicial = int(row.get('stock_actual', 0))
                    if stock_inicial > 0:
                        MovimientoInventario.objects.create(
                            producto=producto,
                            tipo_movimiento='entrada',
                            cantidad=stock_inicial
                        )

            messages.success(request, "✅ Archivo Excel cargado correctamente.")
        except Exception as e:
            messages.error(request, f"❌ Error al procesar el archivo: {e}")

        return redirect('carga_datos')
    
    # Renderiza la página de carga
    return render(request, 'dataeasy/carga_datos.html')