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
# LOGIN
# ============================================================
def index(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            return redirect("home")

        messages.error(request, "Usuario o contraseña incorrectos")

    return render(request, "index.html")


def acceso_denegado(request):
    return render(request, "acceso_denegado.html")


# ============================================================
# HOME
# ============================================================
@login_required(login_url="index")
def home(request):
    context = _build_estadisticas_context(request)

    total_alertas = (
        context["productos_sin_stock"].count() +
        context["productos_bajo_stock"].count()
    )

    context["total_alertas"] = total_alertas

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

    # 1️⃣ Búsqueda
    query = request.GET.get("q", "")

    # 2️⃣ Filtros multiselección
    categorias_sel = [c for c in request.GET.getlist("f_categoria") if c.isdigit()]
    marcas_sel = [m for m in request.GET.getlist("f_marca") if m.isdigit()]


    # 3️⃣ Mostrar solo productos en alerta
    solo_alertas = request.GET.get("solo_alertas") == "1"

    # 4️⃣ Base queryset
    productos = Producto.objects.select_related("categoria", "marca").all()

    # ============================================
    # 🔍 FILTRO: busqueda por texto
    # ============================================
    if query:
        productos = productos.filter(
            Q(nombre_producto__icontains=query) |
            Q(categoria__nombre_categoria__icontains=query) |
            Q(marca__nombre_marca__icontains=query)
        )

    # ============================================
    # ⛏ FILTRO: MULTISELECT Categoría
    # ============================================
    if categorias_sel:
        productos = productos.filter(categoria_id__in=categorias_sel)

    # ============================================
    # 🔧 FILTRO: MULTISELECT Marca
    # ============================================
    if marcas_sel:
        productos = productos.filter(marca_id__in=marcas_sel)

    # ============================================
    # ⚠ FILTRO: Solo alertas (stock bajo + 0)
    # ============================================
    if solo_alertas:
        productos = productos.filter(
            Q(stock_actual=0) |
            Q(stock_actual__gt=0, stock_actual__lte=F("stock_minimo"))
        )

    # ============================================
    # ⚠ Queryset para el modal de alertas global
    # ============================================
    alertas_qs = Producto.objects.filter(
        Q(stock_actual=0) |
        Q(stock_actual__gt=0, stock_actual__lte=F("stock_minimo"))
    )

    # ============================================
    # 📄 PAGINACIÓN
    # ============================================
    paginator = Paginator(productos.order_by("nombre_producto"), 20)
    page_obj = paginator.get_page(request.GET.get("page"))

    # ============================================
    # CONTEXTO FINAL
    # ============================================
    context = {
        "page_obj": page_obj,
        "categorias": Categoria.objects.all(),
        "marcas": Marca.objects.all(),

        # Conservamos filtros usados
        "search_query": query,
        "solo_alertas": solo_alertas,
        "categorias_sel": categorias_sel,
        "marcas_sel": marcas_sel,

        # Datos alertas
        "total_alertas": alertas_qs.count(),
        "sin_stock_items": alertas_qs.filter(stock_actual=0),
        "bajo_stock_items": alertas_qs.filter(stock_actual__gt=0),

        # Totales
        "total_productos": Producto.objects.count(),
    }

    return render(request, "inventario.html", context)
# ============================================================
# CREAR PRODUCTO
# ============================================================
@login_required(login_url="index")
def crear_producto(request):
    if request.method == "POST":
        nombre = request.POST.get("nombre_producto").strip()
        descripcion = request.POST.get("descripcion")
        categoria_id = request.POST.get("categoria")
        marca_id = request.POST.get("marca")
        stock_actual = int(request.POST.get("stock_actual", 0))
        stock_minimo = int(request.POST.get("stock_minimo", 0))

        # 🔍 VALIDACIÓN: evitar productos duplicados
        if Producto.objects.filter(nombre_producto__iexact=nombre).exists():
            messages.error(request, f"❌ Ya existe un producto con el nombre '{nombre}'.")
            return redirect("inventario_lista")

        categoria = Categoria.objects.filter(id=categoria_id).first()
        marca = Marca.objects.filter(id=marca_id).first()

        Producto.objects.create(
            nombre_producto=nombre,
            descripcion=descripcion,
            categoria=categoria,
            marca=marca,
            stock_actual=stock_actual,
            stock_minimo=stock_minimo,
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
# USUARIOS (ADMIN)
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
# ESTADÍSTICAS
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

    productos_criticos_total = Producto.objects.filter(
        stock_actual__lte=F("stock_minimo")
    ).select_related('categoria', 'marca')


    productos_sin = productos_criticos_total.filter(stock_actual=0)
    productos_bajo = productos_criticos_total.filter(stock_actual__gt=0)

    critico_cat_map = {}
    critico_cat_nombres = {}

    for p in productos_criticos_total:
        cat_name = p.categoria.nombre_categoria if p.categoria else "Sin categoría"
        
        if cat_name not in critico_cat_map:
            critico_cat_map[cat_name] = 0
            critico_cat_nombres[cat_name] = []
        
        critico_cat_map[cat_name] += 1
        estado = "(0)" if p.stock_actual == 0 else f"({p.stock_actual}/{p.stock_minimo})"
        critico_cat_nombres[cat_name].append(f"{p.nombre_producto} {estado}")


    critico_marca_map = {}
    critico_marca_nombres = {}

    for p in productos_criticos_total:
        marca_name = p.marca.nombre_marca if p.marca else "Sin marca"
        
        if marca_name not in critico_marca_map:
            critico_marca_map[marca_name] = 0
            critico_marca_nombres[marca_name] = []
            
        critico_marca_map[marca_name] += 1
        estado = "(0)" if p.stock_actual == 0 else f"({p.stock_actual}/{p.stock_minimo})"
        critico_marca_nombres[marca_name].append(f"{p.nombre_producto} {estado}")


    def preparar_tooltip(lista_nombres):
        resultado = []
        for nombres in lista_nombres:
            recorte = nombres[:5]
            if len(nombres) > 5:
                recorte.append(f"... y {len(nombres)-5} más")
            resultado.append(recorte)
        return resultado


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

        next_month = curr.replace(day=28) + timedelta(days=4)
        curr = next_month.replace(day=1)


    for row in movimientos_por_mes:
        if row["mes"]:
            m = row["mes"].strftime("%Y-%m")
            if m in meses:
                idx = meses.index(m)
                if row["tipo_movimiento"] == "entrada":
                    entradas[idx] = row["total"]
                else:
                    salidas[idx] = row["total"]


    chart_data = {
        "meses": meses,
        "entradas": entradas,
        "salidas": salidas,
        
        # --- GRAFICOS DE PASTEL (DISTRIBUCIÓN) ---
        "stock_por_categoria_labels": [
            c["categoria__nombre_categoria"] or "Sin categoría"
            for c in Producto.objects.values("categoria__nombre_categoria").annotate(total=Sum("stock_actual"))
        ],
        "stock_por_categoria_values": [
            c["total"]
            for c in Producto.objects.values("categoria__nombre_categoria").annotate(total=Sum("stock_actual"))
        ],
        "stock_por_marca_labels": [
            m["marca__nombre_marca"] or "Sin marca"
            for m in Producto.objects.values("marca__nombre_marca").annotate(total=Sum("stock_actual"))
        ],
        "stock_por_marca_values": [
            m["total"]
            for m in Producto.objects.values("marca__nombre_marca").annotate(total=Sum("stock_actual"))
        ],

        # --- GRAFICOS DE BARRAS (CRÍTICOS) ---
        "stock_critico_categoria_labels": list(critico_cat_map.keys()),
        "stock_critico_categoria_values": list(critico_cat_map.values()),
        "stock_critico_categoria_tooltips": preparar_tooltip(list(critico_cat_nombres.values())),

        "stock_critico_marca_labels": list(critico_marca_map.keys()),
        "stock_critico_marca_values": list(critico_marca_map.values()),
        "stock_critico_marca_tooltips": preparar_tooltip(list(critico_marca_nombres.values())),
    }


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


@login_required(login_url="index")
def estadisticas(request):
    return render(request, "estadisticas.html", _build_estadisticas_context(request))


@login_required(login_url="index")
def chart_data_api(request):
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
    elif rango == 'dia':
        trunc_func = TruncDay('fecha_movimiento')
        if (fecha_fin - fecha_inicio).days > 60: 
            fecha_inicio = fecha_fin - timedelta(days=30)
    else:
        trunc_func = TruncMonth('fecha_movimiento')


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
# CARGA MASIVA DE PRODUCTOS
# ============================================================
@login_required(login_url="index")
def carga_datos(request):

    if request.method == "POST":
        if not request.FILES.get("archivo_excel"):
            return JsonResponse({"status": "error", "message": "No seleccionaste ningún archivo."})

        try:
            archivo = request.FILES["archivo_excel"]

            df = pd.read_excel(archivo)

            # Normalizar nombres de columnas
            def limpiar(txt):
                return (
                    str(txt)
                    .strip()
                    .lower()
                    .replace(" ", "_")
                    .replace("á", "a")
                    .replace("é", "e")
                    .replace("í", "i")
                    .replace("ó", "o")
                    .replace("ú", "u")
                )

            df.columns = [limpiar(c) for c in df.columns]

            # Columnas obligatorias
            cols_ok = ["nombre_producto", "categoria", "marca", "stock_actual"]
            faltan = [c for c in cols_ok if c not in df.columns]

            if faltan:
                return JsonResponse({
                    "status": "error",
                    "message": f"Faltan columnas en el Excel: {', '.join(faltan)}"
                })

            count = 0
            nuevos = 0

            for _, row in df.iterrows():
                if pd.isna(row.get("nombre_producto")):
                    continue

                # --- Categoría ---
                cat_obj = None
                if pd.notna(row.get("categoria")):
                    cat_obj, _ = Categoria.objects.get_or_create(
                        nombre_categoria=str(row["categoria"]).strip()
                    )

                # --- Marca ---
                marca_obj = None
                if pd.notna(row.get("marca")):
                    marca_obj, _ = Marca.objects.get_or_create(
                        nombre_marca=str(row["marca"]).strip()
                    )

                # =====================================================
                # VALIDACIÓN NUMÉRICA PARA stock_actual Y stock_minimo
                # =====================================================

                # Validar stock_actual
                try:
                    stock_actual_val = int(row.get("stock_actual", 0))
                except:
                    return JsonResponse({
                        "status": "error",
                        "message": f"❌ El valor de stock_actual debe ser numérico. Revisa el producto: {row.get('nombre_producto')}"
                    })

                if stock_actual_val < 0:
                    return JsonResponse({
                        "status": "error",
                        "message": f"❌ No se permiten números negativos en stock_actual. Producto: {row.get('nombre_producto')}"
                    })

                # Validar stock_minimo
                try:
                    stock_minimo_val = int(row.get("stock_minimo", 5))
                except:
                    return JsonResponse({
                        "status": "error",
                        "message": f"❌ El valor de stock_minimo debe ser numérico. Revisa el producto: {row.get('nombre_producto')}"
                    })

                if stock_minimo_val < 0:
                    return JsonResponse({
                        "status": "error",
                        "message": f"❌ No se permiten números negativos en stock_minimo. Producto: {row.get('nombre_producto')}"
                    })

                # =====================================================
                # GUARDADO FINAL
                # =====================================================
                _, created = Producto.objects.update_or_create(
                    nombre_producto=row["nombre_producto"],
                    defaults={
                        "categoria": cat_obj,
                        "marca": marca_obj,
                        "stock_actual": stock_actual_val,
                        "stock_minimo": stock_minimo_val,
                        "descripcion": row.get("descripcion", "")
                    }
                )

                count += 1
                if created:
                    nuevos += 1

            return JsonResponse({
                "status": "success",
                "message": f"¡Proceso finalizado! {count} productos procesados ({nuevos} nuevos)."
            })

        except Exception as e:
            return JsonResponse({
                "status": "error",
                "message": f"Error interno: {str(e)}"
            })

    # Si entran por URL directa, mostramos el HTML normal
    return render(request, "carga_datos.html")

# ============================================================
# EXPORTAR EXCEL
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


# ============================================================
# REGISTRAR FACTURA (AJAX / JSON)
# ============================================================
@login_required(login_url="index")
def registrar_factura(request):
    if request.method == "POST":
        datos = json.loads(request.body)

        cliente = datos.get("cliente")
        items = datos.get("items")
        total = datos.get("total")

        # Crear factura
        factura = Factura.objects.create(
            cliente=cliente,
            total=total
        )

        # Crear detalle + actualizar stock
        for item in items:
            producto = Producto.objects.get(id=item["id"])
            cantidad = int(item["cantidad"])

            
            producto.stock_actual -= cantidad
            producto.en_alerta_stock = producto.stock_actual <= producto.stock_minimo
            producto.save()

            
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


# ============================================================
# GENERAR PDF
# ============================================================
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
