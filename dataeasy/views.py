# --- 1. IMPORTACIONES ---
import json
from datetime import datetime, timedelta
import pandas as pd
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.serializers.json import DjangoJSONEncoder
from django.core.paginator import Paginator
from django.db.models import Sum, Count, F, Q
from django.db.models.functions import TruncMonth
from django.utils import timezone
from django.contrib.auth.models import User
from .models import Producto, Categoria, Marca, MovimientoInventario

# --- 2. VISTAS DE AUTENTICACIÓN Y NÚCLEO ---
def index(request):
    """ Vista de Login """
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect("home")
        else:
            messages.error(request, "Usuario o contraseña incorrectos")
            return render(request, "index.html")
    return render(request, "index.html")

def recuperacion(request):
    """
    Vista (POR HACER) para la página de recuperación de contraseña.
    """
    # (Aquí irá la lógica para enviar el email de recuperación)
    
    # Renderiza el template que ya tienes en tu carpeta
    return render(request, 'recuperacion.html')

@login_required
def home(request):
    """ Vista Home / Dashboard """
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


# --- 3. VISTAS DE GESTIÓN DE INVENTARIO ---
@login_required
def lista_inventario(request):
    """ Lista, busca y pagina el inventario. """
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
    messages.info(request, "Función 'Editar Producto' pendiente de implementar.")
    return redirect('inventario_lista')

@login_required
def eliminar_producto(request, id_producto):
    messages.info(request, "Función 'Eliminar Producto' pendiente de implementar.")
    return redirect('inventario_lista')

# --- 4. VISTAS DE GESTIÓN DE USUARIOS ---
@login_required
def lista_usuarios(request):
    """ Vista para 'gestión de usuarios'. """
    usuarios = User.objects.all().order_by('username')
    context = {'lista_usuarios': usuarios}
    return render(request, 'gestion_usuarios.html', context)

@login_required
def crear_usuario(request):
    messages.info(request, "Función 'Crear Usuario' pendiente de implementar.")
    return redirect('lista_usuarios')

@login_required
def editar_usuario(request, pk):
    messages.info(request, "Función 'Editar Usuario' pendiente de implementar.")
    return redirect('lista_usuarios')

# --- 5. VISTAS DE DATOS Y ANALÍTICAS ---
@login_required
def estadisticas(request):
    """ Vista para mostrar gráficos y métricas. """
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
    # ... (Toda la lógica de estadísticas que ya tenías) ...
    
    # (El resto de tu lógica de estadísticas...)
    context = {
        'total_productos': total_productos,
        'stock_total': stock_total,
        # ... (El resto de tu contexto) ...
    }
    return render(request, 'estadisticas.html', context) # (Asegúrate que el template sea 'estadisticas.html')

@login_required
def carga_datos(request):
    """ Vista para la carga masiva de datos desde Excel. """
    if request.method == 'POST' and request.FILES.get('archivo_excel'):
        archivo = request.FILES['archivo_excel']
        try:
            df = pd.read_excel(archivo)
            for _, row in df.iterrows():
                # ... (Toda la lógica de carga de Pandas que ya tenías) ...
                nombre = str(row.get('nombre_producto')).strip()
                categoria_nombre = str(row.get('categoria')).strip() if row.get('categoria') else None
                marca_nombre = str(row.get('marca')).strip() if row.get('marca') else None

                categoria = Categoria.objects.get_or_create(nombre_categoria=categoria_nombre)[0] if categoria_nombre else None
                marca = Marca.objects.get_or_create(nombre_marca=marca_nombre)[0] if marca_nombre else None

                defaults_producto = {
                    'descripcion': row.get('descripcion'),
                    'categoria': categoria,
                    'marca': marca,
                    'stock_minimo': int(row.get('stock_minimo', 5)),
                }
                producto, created = Producto.objects.update_or_create(
                    nombre_producto=nombre,
                    defaults=defaults_producto
                )
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
    
    return render(request, 'carga_datos.html') # (Asegúrate que el template sea 'carga_datos.html')