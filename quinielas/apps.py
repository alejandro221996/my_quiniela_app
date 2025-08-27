from django.apps import AppConfig


class QuinielasConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'quinielas'
    
    def ready(self):
        """Importar signals cuando la app esté lista"""
        import quinielas.signals
