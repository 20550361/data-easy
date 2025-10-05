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

# Vista Perfil
@login_required
def perfil(request):
    return render(request, 'perfil.html')

# Vista Configuración
@login_required
def configuracion(request):
    return render(request, 'configuracion.html')

def recuperacion(request):
    return render(request, 'recuperacion.html')
