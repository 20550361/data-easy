# --- 1. IMPORTACIONES ---
import json
import csv
from datetime import datetime, timedelta
import pandas as pd

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.serializers.json import DjangoJSONEncoder
from django.core.paginator import Paginator
from django.db.models import Sum, Count, F, Q
from django.db.models.functions import TruncMonth
from django.utils import timezone
from django.contrib.auth.models import User
from django.http import HttpResponse, JsonResponse
from xhtml2pdf import pisa 
from django.template.loader import render_to_string
from django.db.models.functions import TruncWeek, TruncDay

from .models import Producto, Categoria, Marca, MovimientoInventario, Factura, DetalleFactura
from django.contrib.auth.decorators import login_required
from .forms import UserCreateForm, UserUpdateForm
from io import BytesIO
from django.core.files.base import ContentFile

# ============================================================
# 2. LOGIN
# ============================================================
def index(request):
    """Login único (ya no hay roles)."""
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            return redirect("home")

        messages.error(request, "Usuario o contraseña incorrectos")

    return render(request, "index.html")


# ============================================================
# 3. HOME (Admin único)
# ============================================================
@login_required
def home(request):

    # Construimos contexto general
    context = _build_estadisticas_context(request)

    # ALERTA si hay productos en mal estado
    total_alertas = (
        context["productos_sin_stock"].count() +
        context["productos_bajo_stock"].count()
    )

    return render(request, "home.html", context)


@login_required
def perfil(request):
    return render(request, "perfil.html")


@login_required
def configuracion(request):
    return render(request, "configuracion.html")


def recuperacion(request):
    return render(request, "recuperacion.html")
# ============================================================
# INVENTARIO
# ============================================================

@login_required
def lista_inventario(request):
    query = request.GET.get("q", "")
    solo_alertas = request.GET.get("solo_alertas") == "1"

    productos = Producto.objects.select_related("categoria", "marca").all()

    if query:
        productos = productos.filter(
            Q(nombre_producto__icontains=query) |
            Q(categoria__nombre_categoria__icontains=query) |
            Q(marca__nombre_marca__icontains=query)
        )

    if solo_alertas:
        productos = productos.filter(
            Q(stock_actual=0) |
            Q(stock_actual__gt=0, stock_actual__lte=F("stock_minimo"))
        )

    alertas_qs = Producto.objects.filter(
        Q(stock_actual=0) | Q(stock_actual__gt=0, stock_actual__lte=F("stock_minimo"))
    )

    paginator = Paginator(productos.order_by("nombre_producto"), 20)
    page_obj = paginator.get_page(request.GET.get("page"))

    context = {
        "page_obj": page_obj,
        "categorias": Categoria.objects.all(),
        "marcas": Marca.objects.all(),
        "search_query": query,
        "solo_alertas": solo_alertas,
        "total_alertas": alertas_qs.count(),
        "total_productos": Producto.objects.count(),
        "sin_stock_items": alertas_qs.filter(stock_actual=0),
        "bajo_stock_items": alertas_qs.filter(stock_actual__gt=0),
    }

    return render(request, "inventario.html", context)


# ============================================================
# CREAR PRODUCTO
# ============================================================

@login_required
def crear_producto(request):
    if request.method == "POST":
        categoria = Categoria.objects.filter(id=request.POST.get("categoria")).first()
        marca = Marca.objects.filter(id=request.POST.get("marca")).first()

        Producto.objects.create(
            nombre_producto=request.POST.get("nombre_producto"),
            descripcion=request.POST.get("descripcion"),
            categoria=categoria,
            marca=marca,
            stock_actual=int(request.POST.get("stock_actual", 0)),
            stock_minimo=int(request.POST.get("stock_minimo", 0)),
        )

        messages.success(request, "Producto creado correctamente.")
        return redirect("inventario_lista")

    return redirect("inventario_lista")


# ============================================================
# EDITAR PRODUCTO
# ============================================================

@login_required
def editar_producto(request, id_producto):
    producto = get_object_or_404(Producto, id=id_producto)

    if request.method == "POST":
        producto.nombre_producto = request.POST.get("nombre_producto")
        producto.descripcion = request.POST.get("descripcion")
        producto.categoria = Categoria.objects.filter(id=request.POST.get("categoria")).first()
        producto.marca = Marca.objects.filter(id=request.POST.get("marca")).first()
        producto.stock_actual = int(request.POST.get("stock_actual", 0))
        producto.stock_minimo = int(request.POST.get("stock_minimo", 0))

        producto.save()
        messages.success(request, "Producto actualizado.")
        return redirect("inventario_lista")

    return redirect("inventario_lista")


# ============================================================
# ELIMINAR PRODUCTO
# ============================================================

@login_required
def eliminar_producto(request, id_producto):
    producto = get_object_or_404(Producto, id=id_producto)
    producto.delete()
    messages.success(request, "Producto eliminado.")
    return redirect("inventario_lista")



# ============================================================
# 5. USUARIOS (ADMIN)
# ============================================================
def admin_required(view_func):
    return login_required(view_func)


@login_required
@admin_required
def lista_usuarios(request):
    return render(request, "gestion_usuarios.html", {
        "lista_usuarios": User.objects.all()
    })


@login_required
@admin_required
def crear_usuario(request):
    if request.method == "POST":
        form = UserCreateForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Usuario creado.")
            return redirect("lista_usuarios")
        messages.error(request, "Corrige los errores.")
    else:
        form = UserCreateForm()

    return render(request, "usuario_form.html", {"form": form})


@login_required
@admin_required
def editar_usuario(request, pk):
    usuario = get_object_or_404(User, pk=pk)
    form = UserUpdateForm(request.POST or None, instance=usuario)

    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Usuario actualizado.")
        return redirect("lista_usuarios")

    return render(request, "usuario_form.html", {"form": form})


@login_required
@admin_required
def eliminar_usuario(request, pk):
    usuario = get_object_or_404(User, pk=pk)
    if usuario.is_superuser:
        messages.error(request, "No puedes eliminar al superusuario.")
        return redirect("lista_usuarios")

    usuario.delete()
    messages.success(request, "Usuario eliminado.")
    return redirect("lista_usuarios")


# ============================================================
# 6. ESTADÍSTICAS
# ============================================================
def _build_estadisticas_context(request):
    fecha_inicio = request.GET.get("fecha_inicio")
    fecha_fin = request.GET.get("fecha_fin")
    hoy = timezone.now().date()

    if fecha_inicio:
        fecha_inicio = datetime.strptime(fecha_inicio, "%Y-%m-%d").date()
    else:
        fecha_inicio = hoy - timedelta(days=180)

    if fecha_fin:
        fecha_fin = datetime.strptime(fecha_fin, "%Y-%m-%d").date()
    else:
        fecha_fin = hoy

    # 1. PRODUCTOS CRÍTICOS (Para los gráficos de barras)
    productos_criticos = Producto.objects.filter(
        stock_actual__lte=F("stock_minimo")
    ).select_related('categoria', 'marca')

    
    critico_cat_map = {}
    critico_cat_tooltips = {}
    for p in productos_criticos:
        cat = p.categoria.nombre_categoria if p.categoria else "Sin categoría"
        if cat not in critico_cat_map:
            critico_cat_map[cat] = 0
            critico_cat_tooltips[cat] = []
        critico_cat_map[cat] += 1
        critico_cat_tooltips[cat].append(f"{p.nombre_producto} ({p.stock_actual})")

    
    critico_marca_map = {}
    critico_marca_tooltips = {}
    for p in productos_criticos:
        marca = p.marca.nombre_marca if p.marca else "Sin marca"
        if marca not in critico_marca_map:
            critico_marca_map[marca] = 0
            critico_marca_tooltips[marca] = []
        critico_marca_map[marca] += 1
        critico_marca_tooltips[marca].append(f"{p.nombre_producto} ({p.stock_actual})")

    
    def formatear_tooltips(diccionario):
        lista_final = []
        for key in diccionario: 
            items = diccionario[key][:5]
            if len(diccionario[key]) > 5:
                items.append(f"... y {len(diccionario[key])-5} más")
            lista_final.append(items)
        return lista_final

    # 2. CONSTRUCCIÓN DEL JSON COMPLETO
    chart_data = {
       
        "stock_por_categoria_labels": [
            x["categoria__nombre_categoria"] or "Sin categoría"
            for x in Producto.objects.values("categoria__nombre_categoria").annotate(t=Sum("stock_actual"))
        ],
        "stock_por_categoria_values": [
            x["t"] for x in Producto.objects.values("categoria__nombre_categoria").annotate(t=Sum("stock_actual"))
        ],
        
        "stock_por_marca_labels": [
            x["marca__nombre_marca"] or "Sin marca"
            for x in Producto.objects.values("marca__nombre_marca").annotate(t=Sum("stock_actual"))
        ],
        "stock_por_marca_values": [
            x["t"] for x in Producto.objects.values("marca__nombre_marca").annotate(t=Sum("stock_actual"))
        ],

        
        "stock_critico_categoria_labels": list(critico_cat_map.keys()),
        "stock_critico_categoria_values": list(critico_cat_map.values()),
        "stock_critico_categoria_tooltips": formatear_tooltips(critico_cat_tooltips),

        "stock_critico_marca_labels": list(critico_marca_map.keys()),
        "stock_critico_marca_values": list(critico_marca_map.values()),
        "stock_critico_marca_tooltips": formatear_tooltips(critico_marca_tooltips),
    }

    
    productos_sin = productos_criticos.filter(stock_actual=0)
    productos_bajo = productos_criticos.filter(stock_actual__gt=0)

    return {
        "fecha_inicio": fecha_inicio,
        "fecha_fin": fecha_fin,
        "productos_bajo_stock": productos_bajo,
        "productos_sin_stock": productos_sin,
        "total_categorias": Categoria.objects.count(),
        "total_marcas": Marca.objects.count(),
        "total_productos": Producto.objects.count(),
        "stock_total": Producto.objects.aggregate(t=Sum("stock_actual"))["t"] or 0,
        "chart_data_json": json.dumps(chart_data, cls=DjangoJSONEncoder),
    }

@login_required
def estadisticas(request):
    return render(request, "estadisticas.html", _build_estadisticas_context(request))


# ============================================================
# 7. CARGA MASIVA DE PRODUCTOS
# ============================================================
@login_required
def carga_datos(request):

    if request.method == "POST" and request.FILES.get("archivo_excel"):

        next_url = request.POST.get("next") or "home"
        archivo = request.FILES["archivo_excel"]

        columnas = ["nombre_producto", "categoria", "marca", "descripcion", "stock_actual", "stock_minimo"]

        try:
            df = pd.read_excel(archivo)
            df.columns = [c.strip().lower().replace(" ", "_") for c in df.columns]

            faltantes = [c for c in columnas if c not in df.columns]
            if faltantes:
                messages.error(request, "Faltan columnas: " + ", ".join(faltantes))
                return redirect(next_url)

            nuevos = 0
            actualizados = 0

            for _, row in df.iterrows():

                nombre = row.get("nombre_producto")
                if not nombre:
                    continue

                categoria = Categoria.objects.get_or_create(
                    nombre_categoria=row.get("categoria")
                )[0] if row.get("categoria") else None

                marca = Marca.objects.get_or_create(
                    nombre_marca=row.get("marca")
                )[0] if row.get("marca") else None

                producto, creado = Producto.objects.update_or_create(
                    nombre_producto=nombre,
                    defaults={
                        "descripcion": row.get("descripcion", ""),
                        "categoria": categoria,
                        "marca": marca,
                        "stock_minimo": int(row.get("stock_minimo", 0)),
                        "stock_actual": int(row.get("stock_actual", 0)),
                    }
                )

                if creado:
                    nuevos += 1
                else:
                    actualizados += 1

            messages.success(request, f"Carga completada: {nuevos} nuevos, {actualizados} actualizados.")

        except Exception as e:
            messages.error(request, f"Error procesando archivo: {e}")

        return redirect(next_url)

    return render(request, "carga_datos.html")


# ============================================================
# 8. EXPORTAR EXCEL
# ============================================================
@login_required
def exportar_excel(request):

    productos = Producto.objects.select_related("categoria", "marca")

    solo_alertas = request.GET.get("solo_alertas") == "1"
    if solo_alertas:
        productos = productos.filter(Q(stock_actual=0) | Q(stock_actual__lte=F("stock_minimo")))

    query = request.GET.get("q")
    if query:
        productos = productos.filter(
            Q(nombre_producto__icontains=query) |
            Q(marca__nombre_marca__icontains=query) |
            Q(categoria__nombre_categoria__icontains=query)
        )

    data = [{
        "Producto": p.nombre_producto,
        "Categoría": p.categoria.nombre_categoria if p.categoria else "N/A",
        "Marca": p.marca.nombre_marca if p.marca else "N/A",
        "Stock actual": p.stock_actual,
        "Stock mínimo": p.stock_minimo,
        "Estado": (
            "Sin stock" if p.stock_actual == 0 else
            "Bajo stock" if p.stock_actual <= p.stock_minimo else
            "Normal"
        )
    } for p in productos]

    df = pd.DataFrame(data)

    response = HttpResponse(content_type="application/vnd.ms-excel")
    response["Content-Disposition"] = 'attachment; filename="inventario.xlsx"'
    df.to_excel(response, index=False)

    return response

@login_required
def facturacion(request):
    productos = Producto.objects.all().order_by("nombre_producto")
    return render(request, "facturacion.html", {"productos": productos})

@login_required
def registrar_factura(request):
    if request.method == "POST":
        datos = json.loads(request.body)

        # Datos del cliente
        cliente_nombre = datos.get("cliente_nombre", "")
        cliente_apellido = datos.get("cliente_apellido", "")
        cliente_rut = datos.get("cliente_rut", "")

        # Productos enviados desde JS
        items = datos.get("items", [])

        # Crear la factura (SIN TOTAL)
        factura = Factura.objects.create(
            cliente_nombre=cliente_nombre,
            cliente_apellido=cliente_apellido,
            cliente_rut=cliente_rut
        )

        # Procesar items
        for item in items:
            producto = Producto.objects.get(id=item["id"])
            cantidad = int(item["cantidad"])

            # Actualizar stock
            producto.stock_actual -= cantidad
           
            producto.save()

            # Crear detalle
            DetalleFactura.objects.create(
                factura=factura,
                producto=producto,
                cantidad=cantidad
            )

            # Registrar movimiento
            MovimientoInventario.objects.create(
                producto=producto,
                cantidad=cantidad
            )

        return JsonResponse({"status": "ok", "factura_id": factura.id})

    return JsonResponse({"status": "error"})

@login_required
def factura_pdf(request, id):
    factura = Factura.objects.get(id=id)
    detalles = factura.detalles.all()

    # 1) GENERAR PDF EN MEMORIA
    html = render_to_string("factura_pdf.html", {
        "factura": factura,
        "detalles": detalles,
    })

    buffer_pdf = BytesIO()
    pisa_status = pisa.CreatePDF(html, dest=buffer_pdf)

    if pisa_status.err:
        return HttpResponse("Error generando el PDF", status=500)

    # 2) GUARDAR PDF EN EL MODELO
    nombre_archivo = f"factura_{factura.id}.pdf"
    factura.archivo_pdf.save(nombre_archivo, ContentFile(buffer_pdf.getvalue()))
    factura.save()

    # 3) ENTREGAR PDF AL NAVEGADOR (DESCARGA)
    response = HttpResponse(buffer_pdf.getvalue(), content_type="application/pdf")
    response["Content-Disposition"] = f'attachment; filename="{nombre_archivo}"'
    return response      





@login_required
def chart_data_api(request):
    """ API para alimentar el gráfico dinámico de movimientos (Mes/Semana/Día) """
    rango = request.GET.get('rango', 'mes')
    fecha_inicio = request.GET.get('fecha_inicio')
    fecha_fin = request.GET.get('fecha_fin')
    
    hoy = timezone.now().date()
    if not fecha_inicio:
        fecha_inicio = hoy - timedelta(days=180)
    else:
        fecha_inicio = datetime.strptime(fecha_inicio, "%Y-%m-%d").date()
        
    if not fecha_fin:
        fecha_fin = hoy
    else:
        fecha_fin = datetime.strptime(fecha_fin, "%Y-%m-%d").date()

    if rango == 'semana':
        trunc_func = TruncWeek('fecha_movimiento')
        fmt = '%W-%Y'
    elif rango == 'dia':
        trunc_func = TruncDay('fecha_movimiento')
        fmt = '%d/%m' 
    else:
        trunc_func = TruncMonth('fecha_movimiento')
        fmt = '%Y-%m'

    qs = MovimientoInventario.objects.filter(
        fecha_movimiento__date__range=[fecha_inicio, fecha_fin]
    ).annotate(
        periodo=trunc_func
    ).values(
        'periodo', 'tipo_movimiento'
    ).annotate(
        total=Sum('cantidad')
    ).order_by('periodo')

    data_map = {}
    for row in qs:
        if not row['periodo']: continue
        label = row['periodo'].strftime(fmt)
        
        if label not in data_map:
            data_map[label] = {'entradas': 0, 'salidas': 0}
        
        if row['tipo_movimiento'] == 'entrada':
            data_map[label]['entradas'] += row['total']
        else:
            data_map[label]['salidas'] += row['total']

    labels = list(data_map.keys())
    return JsonResponse({
        "labels": labels,
        "entradas": [data_map[k]['entradas'] for k in labels],
        "salidas": [data_map[k]['salidas'] for k in labels]
    })