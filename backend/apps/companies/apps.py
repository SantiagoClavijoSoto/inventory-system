from django.apps import AppConfig


class CompaniesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.companies'
    verbose_name = 'Empresas'

    def ready(self):
        import apps.companies.signals  # noqa: F401
