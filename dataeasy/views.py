# --- 1. IMPORTACIONES ---

# Python Standard Library
import json
from datetime import datetime, timedelta

# Third-Party Libraries
import pandas as pd  # pip install pandas openpyxl

# Django Core
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required, user_passes_test
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


# --- 1.1 Helper de grupos ---
def groups_required(*group_names, login_url='index'):
    def in_groups(u):
        if not u.is_authenticated:
            return False
        if u.is_superuser:
            return True
        return u.groups.filter(name__in=group_names).exists()
    return user_passes_test(in_groups, login_url=login_url)


# --- 2. VISTAS DE AUTENTICACIÓN Y NÚCLEO 🌐 ---

def index(request):
    """ Vista de Login """
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            if user.groups.filter(name='Auditor').exists() and not user.is_superuser:
                return redirect("auditor_home")
            return redirect("home")
        else:
            messages.error(request, "Usuario o contraseña incorrectos")
            return render(request, "index.html")
    return render(request, "index.html")


@login_required
def home(request):
    productos_bajo_stock = Producto.objects.filter(stock_actual__lt=F('stock_minimo')).order_by('stock_actual')[:5]
    movimientos_recientes = MovimientoInventario.objects.select_related('producto').order_by('-fecha_movimiento')[:5]
    context = {
        'productos_bajo_stock': productos_bajo_stock,
        'movimientos_recientes': movimientos_recientes,
    }
    return render(request, 'home.html', context)


@login_required
def perfil(request):
    return render(request, 'perfil.html')


@login_required
def configuracion(request):
    return render(request, 'configuracion.html')


def recuperacion(request):
    return render(request, 'recuperacion.html')


# --- 3. VISTAS DE INVENTARIO 📦 ---

@login_required
def lista_inventario(request):
    query = request.GET.get('q', '') 
    if query:
        productos_list = Producto.objects.filter(
            Q(nombre_producto__icontains=query) |
            Q(categoria__nombre_categoria__icontains=query) |
            Q(marca__nombre_marca__icontains=query)
        ).select_related('categoria', 'marca').order_by('nombre_producto')
    else:
        productos_list = Producto.objects.select_related('categoria', 'marca').all().order_by('nombre_producto')

    total_alertas = productos_list.filter(stock_actual__lte=F('stock_minimo')).count()
    paginator = Paginator(productos_list, 20)
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
    return redirect('inventario_lista')


@login_required
def eliminar_producto(request, id_producto):
    return redirect('inventario_lista')


# --- 4. USUARIOS 👥 ---

@login_required
@groups_required('Auditor', 'Administrador')
def lista_usuarios(request):
    usuarios = User.objects.all().order_by('username')
    context = {'lista_usuarios': usuarios}
    return render(request, 'gestion_usuarios.html', context)


@login_required
@groups_required('Administrador')
def crear_usuario(request):
    return redirect('lista_usuarios')


@login_required
@groups_required('Administrador')
def editar_usuario(request, pk):
    return redirect('lista_usuarios')


# --- 5. DATOS Y ANALÍTICAS 📊 ---
# Helper compartido para reutilizar el mismo contexto entre auditor y admin
def _build_estadisticas_context(request):
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

    stock_por_categoria_qs = (
        Producto.objects.values('categoria__nombre_categoria')
        .annotate(total=Sum('stock_actual'))
        .order_by('-total')
    )
    stock_por_categoria = [
        {'categoria': r['categoria__nombre_categoria'] or 'Sin categoría', 'total': r['total'] or 0}
        for r in stock_por_categoria_qs
    ]

    stock_critico_marca_qs = (
        Producto.objects.filter(stock_actual__lt=F('stock_minimo'), marca__isnull=False)
        .values('marca__nombre_marca')
        .annotate(cantidad=Count('id'))
        .order_by('-cantidad')
    )
    stock_critico_marca = [{'marca': r['marca__nombre_marca'], 'cantidad': r['cantidad']} for r in stock_critico_marca_qs]

    movimientos = MovimientoInventario.objects.filter(fecha_movimiento__date__range=[fecha_inicio, fecha_fin])
    movimientos_por_mes = (movimientos
        .annotate(mes=TruncMonth('fecha_movimiento'))
        .values('mes', 'tipo_movimiento')
        .annotate(total=Sum('cantidad'))
        .order_by('mes')
    )

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
    return {
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

@login_required
@groups_required('Auditor', 'Administrador')
def estadisticas(request):
    context = _build_estadisticas_context(request)
    context['base_template'] = 'base.html'
    return render(request, 'estadisticas.html', context)

@login_required
@groups_required('Auditor')
def auditor_estadisticas(request):
    context = _build_estadisticas_context(request)
    context['base_template'] = 'base_auditor.html'
    return render(request, 'estadisticas.html', context)

# --- 6. CARGA DE DATOS (Excel) 📁 ---
@login_required
def carga_datos(request):
    if request.method == 'POST' and request.FILES.get('archivo_excel'):
        archivo = request.FILES['archivo_excel']
        columnas_esperadas = ['nombre_producto', 'categoria', 'marca', 'descripcion', 'stock_actual', 'stock_minimo']
        try:
            df = pd.read_excel(archivo)
            columnas_archivo = [col.strip().lower().replace(' ', '_') for col in df.columns]
            df.columns = columnas_archivo
            columnas_faltantes = [c for c in columnas_esperadas if c not in columnas_archivo]
            if columnas_faltantes:
                messages.error(request, f"❌ Faltan columnas: {', '.join(columnas_faltantes)}")
                return redirect('carga_datos')
            productos_creados = 0
            productos_actualizados = 0
            for _, row in df.iterrows():
                nombre = str(row.get('nombre_producto', '')).strip()
                if not nombre: continue
                categoria_nombre = str(row.get('categoria', '')).strip() if pd.notna(row.get('categoria')) else None
                marca_nombre = str(row.get('marca', '')).strip() if pd.notna(row.get('marca')) else None
                descripcion_val = str(row.get('descripcion', '')).strip() if pd.notna(row.get('descripcion')) else None
                stock_minimo_val = int(row.get('stock_minimo', 5)) if pd.notna(row.get('stock_minimo')) else 5
                stock_actual_val = int(row.get('stock_actual', 0)) if pd.notna(row.get('stock_actual')) else 0
                categoria = Categoria.objects.get_or_create(nombre_categoria=categoria_nombre)[0] if categoria_nombre else None
                marca = Marca.objects.get_or_create(nombre_marca=marca_nombre)[0] if marca_nombre else None
                defaults_producto = {
                    'descripcion': descripcion_val,
                    'categoria': categoria,
                    'marca': marca,
                    'stock_minimo': stock_minimo_val,
                }
                producto, created = Producto.objects.update_or_create(
                    nombre_producto=nombre,
                    defaults=defaults_producto
                )
                if created:
                    productos_creados += 1
                    if stock_actual_val > 0:
                        MovimientoInventario.objects.create(
                            producto=producto,
                            tipo_movimiento='entrada',
                            cantidad=stock_actual_val
                        )
                else:
                    productos_actualizados += 1
            messages.success(request, f"✅ {productos_creados} nuevos, {productos_actualizados} actualizados.")
        except Exception as e:
            messages.error(request, f"❌ Error al procesar archivo: {e}")
        return redirect('carga_datos')
    return render(request, 'carga_datos.html')


# --- 7. AUDITOR ---
@login_required
@groups_required('Auditor')
def auditor_home(request):
    return render(request, 'auditor/auditor_home.html')

@login_required
@groups_required('Auditor')
def auditor_perfil(request):
    return render(request, 'auditor/auditor_perfil.html')

@login_required
@groups_required('Auditor')
def auditor_usuarios(request):
    usuarios = User.objects.all().order_by('username')
    return render(request, 'auditor/auditor_usuarios.html', {'lista_usuarios': usuarios})

@login_required
@groups_required('Auditor')
def auditor_estadisticas(request):
    context = _build_estadisticas_context(request)
    context['base_template'] = 'auditor/base_auditor.html'   # <-- CAMBIO AQUÍ
    return render(request, 'estadisticas.html', context)
