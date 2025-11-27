
from .models import Producto
from django.db.models import F

def alertas_sidebar(request):
    if request.user.is_authenticated:
        alertas = Producto.objects.filter(
            stock_actual__lte=F("stock_minimo")
        ).order_by('stock_actual')
        
        return {
            'sidebar_alertas': alertas,
            'hay_alertas_sidebar': alertas.exists()
        }
    return {}