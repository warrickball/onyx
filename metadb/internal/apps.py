from django.apps import AppConfig
from django.db.models import Field
from django.db.models.fields.related import ForeignKey


class InternalConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "internal"

    def ready(self):
        from .models import NotEqual, NotEqualRelated, IsNull, IsNullRelated

        Field.register_lookup(NotEqual)
        ForeignKey.register_lookup(NotEqualRelated)
        Field.register_lookup(IsNull)
        ForeignKey.register_lookup(IsNullRelated)
