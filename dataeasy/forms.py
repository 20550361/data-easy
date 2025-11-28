from django import forms
from django.contrib.auth.models import User, Group
from django.core.exceptions import ValidationError
from django.contrib.auth.hashers import make_password

# --- Crear usuario ---
class UserCreateForm(forms.ModelForm):
    username = forms.CharField(required=True, label="Nombre de usuario")
    email = forms.EmailField(required=True, label="Correo electrónico")
    first_name = forms.CharField(required=True, label="Nombre")
    last_name = forms.CharField(required=True, label="Apellido")

    password1 = forms.CharField(label="Contraseña", widget=forms.PasswordInput, required=True)
    password2 = forms.CharField(label="Confirmar contraseña", widget=forms.PasswordInput, required=True)

    groups = forms.ModelMultipleChoiceField(
        queryset=Group.objects.all(), required=False, label="Grupos",
        widget=forms.CheckboxSelectMultiple
    )
    is_active = forms.BooleanField(initial=True, required=False, label="Activo")
    is_staff = forms.BooleanField(initial=False, required=False, label="Staff (acceso admin)")
    # Si quieres permitir crear superusuarios, descomenta la línea de abajo:
    # is_superuser = forms.BooleanField(initial=False, required=False, label="Superusuario")

    class Meta:
        model = User
        fields = ["username", "email", "first_name", "last_name"]

    def clean_password2(self):
        p1 = self.cleaned_data.get("password1")
        p2 = self.cleaned_data.get("password2")
        if p1 != p2:
            raise ValidationError("Las contraseñas no coinciden.")
        return p2

    def clean(self):
        cleaned = super().clean()
        activo = cleaned.get("is_active")
        staff = cleaned.get("is_staff")

        if not activo and not staff:
            raise ValidationError("El usuario debe ser ACTIVO o STAFF (al menos uno).")

        return cleaned


    # GUARDADO SEGURO    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password1"])
        user.is_active = self.cleaned_data["is_active"]
        user.is_staff = self.cleaned_data["is_staff"]
        # user.is_superuser = self.cleaned_data.get("is_superuser", False)
        if commit:
            user.save()
            user.groups.set(self.cleaned_data["groups"])
        return user

# ============================================================
# EDITAR USUARIO
# ============================================================
class UserUpdateForm(forms.ModelForm):

    username = forms.CharField(required=True, label="Nombre de usuario")
    email = forms.EmailField(required=True, label="Correo electrónico")
    first_name = forms.CharField(required=True, label="Nombre")
    last_name = forms.CharField(required=True, label="Apellido")


    new_password1 = forms.CharField(
        label="Nueva contraseña", widget=forms.PasswordInput, required=False
    )
    new_password2 = forms.CharField(
        label="Confirmar nueva contraseña", widget=forms.PasswordInput, required=False
    )
    groups = forms.ModelMultipleChoiceField(
        queryset=Group.objects.all(), required=False,
        widget=forms.CheckboxSelectMultiple, label="Grupos"
    )
    is_active = forms.BooleanField(required=False, label="Activo")
    is_staff = forms.BooleanField(required=False, label="Staff (acceso admin)")


    class Meta:
        model = User
        fields = ["username", "email", "first_name", "last_name"]

    def clean(self):
        cleaned = super().clean()
        p1 = cleaned.get("new_password1")
        p2 = cleaned.get("new_password2")
        if p1 or p2:
            if p1 != p2:
                raise ValidationError("Las contraseñas no coinciden.")

        activo = cleaned.get("is_active")
        staff = cleaned.get("is_staff")

        if not activo and not staff:
            raise ValidationError("El usuario debe ser ACTIVO o STAFF (al menos uno).")

        return cleaned

    def save(self, commit=True):
        user = super().save(commit=False)
        user.is_active = self.cleaned_data.get("is_active", True)
        user.is_staff = self.cleaned_data.get("is_staff", False)

        if commit:
            user.save()
            user.groups.set(self.cleaned_data["groups"])
            newpass = self.cleaned_data.get("new_password1")
            if newpass:
                user.set_password(newpass)
        return user
