from django.apps import AppConfig


class CoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'core'
    
    def ready(self):
        print('scheduler ready')
        from .scheduler import start_scheduler, schedule_carga_empleados
        start_scheduler()
        schedule_carga_empleados()
    