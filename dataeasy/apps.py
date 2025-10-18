from django.apps import AppConfig

class DataeasyConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'dataeasy'

    def ready(self):
        # Importa los signals para que se conecten cuando arranque Django
        import dataeasy.signals