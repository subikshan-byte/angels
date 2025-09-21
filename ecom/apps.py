from django.apps import AppConfig

class EcomConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'ecom'
    def ready(self):
        import ecom.signals  # 👈 this ensures signals are registered
