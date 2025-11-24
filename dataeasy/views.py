# --- 1. IMPORTACIONES ---
import json
import csv
from datetime import datetime, timedelta
import pandas as pd
import unicodedata

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required, user_passes_test
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
from django.db.models.functions import TruncMonth, TruncWeek, TruncDay
import locale
from django.http import JsonResponse

from .models import Producto, Categoria, Marca, MovimientoInventario
from .forms import UserCreateForm, UserUpdateForm


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
# 3. ACCESO DENEGADO
# ============================================================
def acceso_denegado(request):
    return render(request, "acceso_denegado.html")


# ============================================================
# 4. HOME (Admin único)
# ============================================================
@login_required(login_url="index")
def home(request):

    # Construimos contexto general
    context = _build_estadisticas_context(request)

    # ALERTA si hay productos en mal estado
    total_alertas = (
        context["productos_sin_stock"].count() +
        context["productos_bajo_stock"].count()
    )

    return render(request, "home.html", context)


@login_required(login_url="index")
def perfil(request):
    return render(request, "perfil.html")


@login_required(login_url="index")
def configuracion(request):
    return render(request, "configuracion.html")


def recuperacion(request):
    return render(request, "recuperacion.html")


# ============================================================
# INVENTARIO
# ============================================================
@login_required(login_url="index")
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
@login_required(login_url="index")
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
@login_required(login_url="index")
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
@login_required(login_url="index")
def eliminar_producto(request, id_producto):
    producto = get_object_or_404(Producto, id=id_producto)
    producto.delete()
    messages.success(request, "Producto eliminado.")
    return redirect("inventario_lista")


# ============================================================
# 5. USUARIOS (ADMIN)
# ============================================================
def es_admin(user):
    return user.is_superuser


@login_required(login_url="index")
@user_passes_test(es_admin, login_url="acceso_denegado")
def lista_usuarios(request):
    return render(request, "gestion_usuarios.html", {
        "lista_usuarios": User.objects.all()
    })


@login_required(login_url="index")
@user_passes_test(es_admin, login_url="acceso_denegado")
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


@login_required(login_url="index")
@user_passes_test(es_admin, login_url="acceso_denegado")
def editar_usuario(request, pk):
    usuario = get_object_or_404(User, pk=pk)
    form = UserUpdateForm(request.POST or None, instance=usuario)

    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Usuario actualizado.")
        return redirect("lista_usuarios")

    return render(request, "usuario_form.html", {"form": form})


@login_required(login_url="index")
@user_passes_test(es_admin, login_url="acceso_denegado")
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

    movimientos = MovimientoInventario.objects.filter(
        fecha_movimiento__date__range=[fecha_inicio, fecha_fin]
    )

    # ========== Datos generales ==========
    productos_bajo = Producto.objects.filter(stock_actual__gt=0, stock_actual__lte=F("stock_minimo"))
    productos_sin = Producto.objects.filter(stock_actual=0)

    # ========== Gráficos ==========
    movimientos_por_mes = (
        movimientos.annotate(mes=TruncMonth("fecha_movimiento"))
        .values("mes", "tipo_movimiento")
        .annotate(total=Sum("cantidad"))
        .order_by("mes")
    )

    meses = []
    entradas = []
    salidas = []

    curr = fecha_inicio.replace(day=1)
    while curr <= fecha_fin:
        key = curr.strftime("%Y-%m")
        meses.append(key)
        entradas.append(0)
        salidas.append(0)
        curr = (curr + timedelta(days=32)).replace(day=1)

    for row in movimientos_por_mes:
        m = row["mes"].strftime("%Y-%m")
        idx = meses.index(m)

        if row["tipo_movimiento"] == "entrada":
            entradas[idx] = row["total"]
        else:
            salidas[idx] = row["total"]
            

    # Diccionario categorias
    cat_map = {}
    for p in productos_bajo:
        cat_name = p.categoria.nombre_categoria if p.categoria else "Sin categoría"
        if cat_name not in cat_map:
            cat_map[cat_name] = []
        cat_map[cat_name].append(p.nombre_producto)


    cat_labels = list(cat_map.keys())
    cat_values = [len(prods) for prods in cat_map.values()]
    cat_tooltips = [] 
    
    for prods in cat_map.values():
        lista_formateada = prods[:5] 
        if len(prods) > 5:
            lista_formateada.append(f"... y {len(prods)-5} más")
        cat_tooltips.append(lista_formateada)

    marca_map = {}
    for p in productos_bajo:
        marca_name = p.marca.nombre_marca if p.marca else "Sin marca"
        if marca_name not in marca_map:
            marca_map[marca_name] = []
        marca_map[marca_name].append(p.nombre_producto)

    marca_labels = list(marca_map.keys())
    marca_values = [len(prods) for prods in marca_map.values()]
    marca_tooltips = []

    for prods in marca_map.values():
        lista_formateada = prods[:5]
        if len(prods) > 5:
            lista_formateada.append(f"... y {len(prods)-5} más")
        marca_tooltips.append(lista_formateada)


    chart_data = {
        "meses": meses,
        "entradas": entradas,
        "salidas": salidas,
        "stock_por_categoria_labels": [
            c["categoria__nombre_categoria"] or "Sin categoría"
            for c in Producto.objects.values("categoria__nombre_categoria")
            .annotate(total=Sum("stock_actual"))
        ],
        "stock_por_categoria_values": [
            c["total"]
            for c in Producto.objects.values("categoria__nombre_categoria")
            .annotate(total=Sum("stock_actual"))
        ],
        
        "stock_critico_categoria_labels": [
            r["categoria__nombre_categoria"] or "Sin categoría"
            for r in productos_bajo.values("categoria__nombre_categoria").annotate(cantidad=Count("id")).order_by("-cantidad")
        ],
        "stock_critico_categoria_values": [
            r["cantidad"]
            for r in productos_bajo.values("categoria__nombre_categoria").annotate(cantidad=Count("id")).order_by("-cantidad")
        ],
        # Datos para Gráfico de Barras (Crítico por MARCA)
        "stock_critico_marca_labels": [
            r["marca__nombre_marca"] or "Sin marca"
            for r in productos_bajo.values("marca__nombre_marca").annotate(cantidad=Count("id")).order_by("-cantidad")
        ],
        "stock_critico_marca_values": [
            r["cantidad"]
            for r in productos_bajo.values("marca__nombre_marca").annotate(cantidad=Count("id")).order_by("-cantidad")
        ],
        #  Datos para Gráfico de Torta (Marcas) 
        "stock_por_marca_labels": [
            m["marca__nombre_marca"] or "Sin marca"
            for m in Producto.objects.values("marca__nombre_marca").annotate(total=Sum("stock_actual"))
        ],
        "stock_por_marca_values": [
            m["total"]
            for m in Producto.objects.values("marca__nombre_marca").annotate(total=Sum("stock_actual"))
        ],
 # --- DATOS NUEVOS CON DETALLE ---
        "stock_critico_categoria_labels": cat_labels,
        "stock_critico_categoria_values": cat_values,
        "stock_critico_categoria_tooltips": cat_tooltips,

        "stock_critico_marca_labels": marca_labels,
        "stock_critico_marca_values": marca_values,
        "stock_critico_marca_tooltips": marca_tooltips, 
    }


    return {
        "fecha_inicio": fecha_inicio,
        "fecha_fin": fecha_fin,
        "productos_bajo_stock": productos_bajo,
        "productos_sin_stock": productos_sin,
        "total_categorias": Categoria.objects.count(),
        "total_marcas": Marca.objects.count(),
        "total_productos": Producto.objects.count(),
        "stock_total": Producto.objects.aggregate(total_stock=Sum("stock_actual"))["total_stock"],
        "total_movimientos": movimientos.count(),
        "chart_data_json": json.dumps(chart_data, cls=DjangoJSONEncoder),
    }


@login_required(login_url="index")
def estadisticas(request):
    return render(request, "estadisticas.html", _build_estadisticas_context(request))


@login_required(login_url="index")
def chart_data_api(request):
    rango = request.GET.get('rango', 'mes') # mes, semana, dia
    fecha_inicio = request.GET.get('fecha_inicio')
    fecha_fin = request.GET.get('fecha_fin')
    
    # 1. Fechas por defecto (últimos 6 meses)
    hoy = timezone.now().date()
    if not fecha_inicio:
        fecha_inicio = hoy - timedelta(days=180)
    else:
        fecha_inicio = datetime.strptime(fecha_inicio, "%Y-%m-%d").date()
        
    if not fecha_fin:
        fecha_fin = hoy
    else:
        fecha_fin = datetime.strptime(fecha_fin, "%Y-%m-%d").date()

    # 2. Definir agrupación según el rango seleccionado
    if rango == 'semana':
        trunc_func = TruncWeek('fecha_movimiento')
    elif rango == 'dia':
        trunc_func = TruncDay('fecha_movimiento')
        if (fecha_fin - fecha_inicio).days > 60: 
            fecha_inicio = fecha_fin - timedelta(days=30)
    else:
        trunc_func = TruncMonth('fecha_movimiento')

    # 3. Consulta a la BD
    qs = MovimientoInventario.objects.filter(
        fecha_movimiento__date__range=[fecha_inicio, fecha_fin]
    ).annotate(
        periodo=trunc_func
    ).values(
        'periodo', 'tipo_movimiento'
    ).annotate(
        total=Sum('cantidad')
    ).order_by('periodo')

    # 4. Procesar datos en Python
    data_map = {}

    for row in qs:
        fecha_obj = row['periodo']
        
        if rango == 'semana':
            label = f"Semana {fecha_obj.strftime('%W')}"
        elif rango == 'dia':
            label = fecha_obj.strftime('%d/%m')
        else:
            label = fecha_obj.strftime('%b-%Y')

        if label not in data_map:
            data_map[label] = {'entradas': 0, 'salidas': 0}
        
        if row['tipo_movimiento'] == 'entrada':
            data_map[label]['entradas'] += row['total']
        elif row['tipo_movimiento'] == 'salida':
            data_map[label]['salidas'] += row['total']

    labels = list(data_map.keys())
    entradas = [data_map[k]['entradas'] for k in labels]
    salidas = [data_map[k]['salidas'] for k in labels]

    return JsonResponse({
        "labels": labels,
        "entradas": entradas,
        "salidas": salidas
    })

# ============================================================
# 7. CARGA MASIVA DE PRODUCTOS
# ============================================================
@login_required(login_url="index")
def carga_datos(request):

    if request.method == "POST":
        if not request.FILES.get("archivo_excel"):
            return JsonResponse({"status": "error", "message": "No seleccionaste ningún archivo."})

        try:
            archivo = request.FILES["archivo_excel"]
            
            # Leemos el Excel
            df = pd.read_excel(archivo)

            # Función de limpieza rápida
            def limpiar(txt):
                return str(txt).strip().lower().replace(" ", "_").replace("á","a").replace("é","e").replace("í","i").replace("ó","o").replace("ú","u")

            # Normalizar columnas
            df.columns = [limpiar(c) for c in df.columns]

            # Validar columnas mínimas
            cols_ok = ["nombre_producto", "categoria", "marca", "stock_actual"]
            faltan = [c for c in cols_ok if c not in df.columns]

            if faltan:
                return JsonResponse({"status": "error", "message": f"Faltan columnas en el Excel: {', '.join(faltan)}"})

            # Procesar filas
            count = 0
            nuevos = 0
            for _, row in df.iterrows():
                if pd.isna(row.get("nombre_producto")): continue
                
                # Crear/Buscar Categoria y Marca
                cat_obj = None
                if pd.notna(row.get("categoria")):
                    cat_obj, _ = Categoria.objects.get_or_create(nombre_categoria=str(row["categoria"]).strip())
                
                marca_obj = None
                if pd.notna(row.get("marca")):
                    marca_obj, _ = Marca.objects.get_or_create(nombre_marca=str(row["marca"]).strip())

                # Crear/Actualizar Producto
                _, created = Producto.objects.update_or_create(
                    nombre_producto=row["nombre_producto"],
                    defaults={
                        "categoria": cat_obj,
                        "marca": marca_obj,
                        "stock_actual": int(row.get("stock_actual", 0)),
                        "stock_minimo": int(row.get("stock_minimo", 5)),
                        "descripcion": row.get("descripcion", "")
                    }
                )
                count += 1
                if created: nuevos += 1
            
            # --- RESPUESTA DE ÉXITO ---
            return JsonResponse({
                "status": "success", 
                "message": f"¡Proceso finalizado! {count} productos procesados ({nuevos} nuevos)."
            })

        except Exception as e:
            # --- RESPUESTA DE ERROR ---
            return JsonResponse({"status": "error", "message": f"Error interno: {str(e)}"})

    # Si entran por URL directa, mostramos el HTML normal
    return render(request, "carga_datos.html")


# ============================================================
# 8. EXPORTAR EXCEL
# ============================================================
@login_required(login_url="index")
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


# ============================================================
# 9. FACTURACIÓN
# ===============================   =============================
@login_required(login_url="index")
def facturacion(request):
    productos = Producto.objects.all().order_by("nombre_producto")
    return render(request, "facturacion.html", {"productos": productos})


@login_required(login_url="index")
def registrar_factura(request):
    if request.method == "POST":
        datos = json.loads(request.body)

        cliente = datos.get("cliente")
        items = datos.get("items")
        total = datos.get("total")

        factura = Factura.objects.create(
            cliente=cliente,
            total=total
        )

        for item in items:
            producto = Producto.objects.get(id=item["id"])
            cantidad = int(item["cantidad"])

            # descontar stock
            producto.stock_actual -= cantidad
            producto.en_alerta_stock = producto.stock_actual <= producto.stock_minimo
            producto.save()

            # crear detalle
            DetalleFactura.objects.create(
                factura=factura,
                producto=producto,
                cantidad=cantidad,
                precio=item["precio"],
                subtotal=item["subtotal"]
            )

        return JsonResponse({
            "status": "ok",
            "factura_id": factura.id
        })

    return JsonResponse({"status": "error"})


@login_required(login_url="index")
def factura_pdf(request, id):
    factura = Factura.objects.get(id=id)
    detalles = factura.detalles.all()

    html = render_to_string("factura_pdf.html", {
        "factura": factura,
        "detalles": detalles
    })

    response = HttpResponse(content_type="application/pdf")
    response['Content-Disposition'] = f'attachment; filename="factura_{id}.pdf"'
    pisa_status = pisa.CreatePDF(html, dest=response)

    return response
