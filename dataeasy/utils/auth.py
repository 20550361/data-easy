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
