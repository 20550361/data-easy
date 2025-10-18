from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required

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

@login_required
def perfil(request):
    return render(request, 'perfil.html')

@login_required
def configuracion(request):
    return render(request, 'configuracion.html')

def recuperacion(request):
    return render(request, 'recuperacion.html')

def inventario(request):
    return render(request, 'inventario.html')

def estadisticas(request):
    return render(request, 'estadisticas.html')

def gestion_usuarios(request):
    return render(request, 'gestion_usuarios.html')

def recuperacion(request):
    return render(request, 'recuperacion.html')

def carga_datos(request):
    if request.method == 'POST' and request.FILES.get('archivo_excel'):
        archivo = request.FILES['archivo_excel']
        # Por ahora solo mostramos el nombre, luego podemos procesarlo con pandas
        return HttpResponse(f"Archivo recibido correctamente: {archivo.name}")
    return render(request, 'carga_datos.html')