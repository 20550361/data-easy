from django.apps import AppConfig


class DataeasyConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'dataeasy'

    def ready(self):
        """
        Esta función se ejecuta cuando la app está lista.
        La usamos para importar los signals.
        """
        
        # --- SOLUCIÓN DE DEBUGGING ---
        # Tuvimos que comentar esta línea temporalmente
        # porque 'signals.py' (o 'views.py') tenía un error
        # que impedía que la app cargara, causando el NoReverseMatch.
        
        # import dataeasy.signals 
        pass