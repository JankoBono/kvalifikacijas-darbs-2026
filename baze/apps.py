from django.apps import AppConfig


class BazeConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'baze'

    def ready(self):
        from . import signals