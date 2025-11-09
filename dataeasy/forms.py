from django import forms
from django.contrib.auth.models import User, Group
from django.core.exceptions import ValidationError

# --- Crear usuario ---
class UserCreateForm(forms.ModelForm):
    password1 = forms.CharField(label="Contraseña", widget=forms.PasswordInput)
    password2 = forms.CharField(label="Confirmar contraseña", widget=forms.PasswordInput)
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


# --- Editar usuario ---
class UserUpdateForm(forms.ModelForm):
    # Campos opcionales de cambio de contraseña
    new_password1 = forms.CharField(
        label="Nueva contraseña", widget=forms.PasswordInput, required=False
    )
    new_password2 = forms.CharField(
        label="Confirmar nueva contraseña", widget=forms.PasswordInput, required=False
    )
    groups = forms.ModelMultipleChoiceField(
        queryset=Group.objects.all(), required=False, label="Grupos",
        widget=forms.CheckboxSelectMultiple
    )
    is_active = forms.BooleanField(required=False, label="Activo")
    is_staff = forms.BooleanField(required=False, label="Staff (acceso admin)")
    # is_superuser = forms.BooleanField(required=False, label="Superusuario")

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
        return cleaned

    def save(self, commit=True):
        user = super().save(commit=False)
        user.is_active = self.cleaned_data.get("is_active", True)
        user.is_staff = self.cleaned_data.get("is_staff", False)
        # user.is_superuser = self.cleaned_data.get("is_superuser", False)
        if commit:
            user.save()
            user.groups.set(self.cleaned_data["groups"])
            p1 = self.cleaned_data.get("new_password1")
            if p1:
                user.set_password(p1)
                user.save()
        return user
