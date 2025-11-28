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

from io import BytesIO

from .models import Producto, Categoria, Marca, MovimientoInventario, Factura, DetalleFactura
from .forms import UserCreateForm, UserUpdateForm
from .utils.auth import validar_rut


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
# 7. CARGA MASIVA DE PRODUCTOS
# ============================================================
@login_required(login_url="index")
def carga_datos(request):

    if request.method == "POST":
        if not request.FILES.get("archivo_excel"):
            return JsonResponse({"status": "error", "message": "No seleccionaste ningún archivo."})

        try:
            archivo = request.FILES["archivo_excel"]
            

            df = pd.read_excel(archivo)


            def limpiar(txt):
                return str(txt).strip().lower().replace(" ", "_").replace("á","a").replace("é","e").replace("í","i").replace("ó","o").replace("ú","u")


            df.columns = [limpiar(c) for c in df.columns]

 
            cols_ok = ["nombre_producto", "categoria", "marca", "stock_actual"]
            faltan = [c for c in cols_ok if c not in df.columns]

            if faltan:
                return JsonResponse({"status": "error", "message": f"Faltan columnas en el Excel: {', '.join(faltan)}"})

           
            count = 0
            nuevos = 0
            for _, row in df.iterrows():
                if pd.isna(row.get("nombre_producto")): continue
                

                cat_obj = None
                if pd.notna(row.get("categoria")):
                    cat_obj, _ = Categoria.objects.get_or_create(nombre_categoria=str(row["categoria"]).strip())
                
                marca_obj = None
                if pd.notna(row.get("marca")):
                    marca_obj, _ = Marca.objects.get_or_create(nombre_marca=str(row["marca"]).strip())

                
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
            
            
            return JsonResponse({
                "status": "success", 
                "message": f"¡Proceso finalizado! {count} productos procesados ({nuevos} nuevos)."
            })

        except Exception as e:
           
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


# ============================================================
# REGISTRAR FACTURA (AJAX / JSON)
# ============================================================
# REGISTRAR FACTURA (AJAX / JSON)
# ============================================================
@login_required(login_url="index")
def registrar_factura(request):
    """
    Endpoint AJAX para crear una factura y descontar stock.
    
    FLUJO:
    1. Valida RUT del cliente (validar_rut)
    2. Crea registro de Factura
    3. Valida que hay SUFICIENTE stock para TODOS los items
    4. Si hay error de stock → Cancela y devuelve error
    5. Si hay stock → Crea DetalleFactura y MovimientoInventario (salida)
    6. Signal automático recalcula stock: stock = entradas - salidas
    
    NOTA: El descuento de stock ocurre automáticamente por el signal,
          no se descuenta manualmente.
    """
    if request.method == "POST":
        datos = json.loads(request.body)

        # Datos del cliente
        cliente_nombre = datos.get("cliente_nombre", "")
        cliente_apellido = datos.get("cliente_apellido", "")
        cliente_rut = datos.get("cliente_rut", "")

        # VALIDACIÓN 1: Validar RUT chileno
        if not validar_rut(cliente_rut):
            return JsonResponse({"status": "error", "message": "RUT inválido. Verifica el formato y el dígito verificador."})

        # PASO 1: Crear factura
        factura = Factura.objects.create(
            cliente_nombre=cliente_nombre,
            cliente_apellido=cliente_apellido,
            cliente_rut=cliente_rut
        )

        items = datos.get("items", [])

        # VALIDACIÓN 2: Verificar stock ANTES de procesar
        # Recorre todos los items y valida que haya cantidad suficiente
        for item in items:
            producto = Producto.objects.get(id=item["id"])
            cantidad = int(item["cantidad"])
            
            if producto.stock_actual < cantidad:
                # Si no hay stock, elimina la factura y devuelve error
                factura.delete()
                return JsonResponse({
                    "status": "error", 
                    "message": f"Stock insuficiente para '{producto.nombre_producto}'. Disponible: {producto.stock_actual}, Solicitado: {cantidad}"
                })

        # PASO 2: Crear detalles y movimientos de inventario
        for item in items:
            producto = Producto.objects.get(id=item["id"])
            cantidad = int(item["cantidad"])

            # Crear registro de detalle de factura
            DetalleFactura.objects.create(
                factura=factura,
                producto=producto,
                cantidad=cantidad
            )

            # Crear movimiento de SALIDA (esto dispara el signal automáticamente)
            # El signal recalculará: stock = entradas - salidas
            MovimientoInventario.objects.create(
                producto=producto,
                tipo_movimiento='salida',
                cantidad=cantidad,
                fecha_movimiento=timezone.now()
            )

        return JsonResponse({"status": "ok", "factura_id": factura.id})

    return JsonResponse({"status": "error"})


# ============================================================
# GENERAR PDF
# ============================================================
@login_required(login_url="index")
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

    # Devolver PDF como respuesta HTTP
    response = HttpResponse(buffer_pdf.getvalue(), content_type='application/pdf')
    response["Content-Disposition"] = f'attachment; filename="factura_{factura.id}.pdf"'
    return response

<<<<<<< Updated upstream
=======

# ============================================================
# API NUEVA: GRÁFICO COMPARATIVO POR PRODUCTOS ESPECÍFICOS
# ============================================================
@login_required
def chart_productos_api(request):
    """
    Devuelve el total de Entradas vs Salidas por PRODUCTO (no por tiempo),
    filtrado por el rango de fechas global.
    """
    ids_str = request.GET.get('ids', '')
    fecha_inicio = request.GET.get('fecha_inicio')
    fecha_fin = request.GET.get('fecha_fin')

    # 1. Validar IDs
    if not ids_str:
        return JsonResponse({"labels": [], "entradas": [], "salidas": []})

    try:
        id_list = [int(x) for x in ids_str.split(',') if x.strip().isdigit()]
    except ValueError:
        return JsonResponse({"labels": [], "entradas": [], "salidas": []})

    # 2. Configurar Fechas
    hoy = timezone.now().date()
    if not fecha_inicio:
        fecha_inicio = hoy - timedelta(days=180)
    else:
        try:
            fecha_inicio = datetime.strptime(fecha_inicio, "%Y-%m-%d").date()
        except ValueError:
            fecha_inicio = hoy - timedelta(days=180)
        
    if not fecha_fin:
        fecha_fin = hoy
    else:
        try:
            fecha_fin = datetime.strptime(fecha_fin, "%Y-%m-%d").date()
        except ValueError:
            fecha_fin = hoy

    # 3. CONSULTA AGRUPADA POR PRODUCTO
    # Filtramos por fecha y productos, pero agrupamos por NOMBRE del producto
    qs = MovimientoInventario.objects.filter(
        fecha_movimiento__date__range=[fecha_inicio, fecha_fin],
        producto_id__in=id_list
    ).values(
        'producto__nombre_producto', 'tipo_movimiento'
    ).annotate(
        total=Sum('cantidad')
    ).order_by('producto__nombre_producto')

    # 4. Procesar Datos
    data_map = {}
    
    # (Opcional) Si quisieras mostrar productos con 0 movimientos,
    # podrías iterar id_list aquí para inicializar data_map.
    # Por ahora solo mostramos los que tienen actividad en el rango.

    for row in qs:
        nombre = row['producto__nombre_producto']
        if nombre not in data_map:
            data_map[nombre] = {'entradas': 0, 'salidas': 0}
        
        if row['tipo_movimiento'] == 'entrada':
            data_map[nombre]['entradas'] += row['total']
        else:
            data_map[nombre]['salidas'] += row['total']

    # Separar en listas para Chart.js
    labels = list(data_map.keys())
    return JsonResponse({
        "labels": labels, # Nombres de productos
        "entradas": [data_map[k]['entradas'] for k in labels],
        "salidas": [data_map[k]['salidas'] for k in labels]
    })

# ============================================================
# API NUEVA: VALIDAR RUT CHILENO
>>>>>>> Stashed changes
