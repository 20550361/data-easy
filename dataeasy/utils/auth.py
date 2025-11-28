from django.contrib.auth.decorators import user_passes_test

def groups_required(*group_names, login_url='index'):
    """
    Permite acceso si el usuario es superuser o pertenece a alguno de los grupos indicados.
    Uso:
    @groups_required('Auditor', 'Administrador')
    def mi_vista(request):
        ...
    """
    def in_groups(u):
        if not u.is_authenticated:
            return False
        if u.is_superuser:
            return True
        return u.groups.filter(name__in=group_names).exists()
    return user_passes_test(in_groups, login_url=login_url)


def validar_rut(rut):
    """
    Valida un RUT chileno según el dígito verificador.
    Acepta formato con o sin puntos y guión (ej: 12.345.678-9 o 123456789).
    Retorna True si es válido, False en caso contrario.
    """
    rut = rut.replace(".", "").replace("-", "")
    if len(rut) < 8:
        return False

    cuerpo = rut[:-1]
    dv = rut[-1].upper()

    suma = 0
    multiplo = 2

    for c in reversed(cuerpo):
        suma += int(c) * multiplo
        multiplo = 2 if multiplo == 7 else multiplo + 1

    dv_esperado = 11 - (suma % 11)
    dv_esperado = "0" if dv_esperado == 11 else "K" if dv_esperado == 10 else str(dv_esperado)

    return dv == dv_esperado
