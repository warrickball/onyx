from django.db import models
from django.utils.translation import gettext_lazy as _


class ModelChoiceField(models.ForeignKey):
    def __init__(self, *args, **kwargs):
        name = kwargs.pop("name", None)
        kwargs["to"] = "data.Choice"
        kwargs["on_delete"] = models.CASCADE
        kwargs["related_name"] = f"%(app_label)s_%(class)s_{name}"
        super().__init__(*args, **kwargs)


class StrippedCharField(models.CharField):
    def to_python(self, value):
        if value is None:
            return value

        if not isinstance(value, str):
            value = str(value)

        value = value.strip()
        return super().to_python(value)


class LowerCharField(StrippedCharField):
    def to_python(self, value):
        if value is None:
            return value

        if not isinstance(value, str):
            value = str(value)

        value = value.lower()
        return super().to_python(value)


class UpperCharField(StrippedCharField):
    def to_python(self, value):
        if value is None:
            return value

        if not isinstance(value, str):
            value = str(value)

        value = value.upper()
        return super().to_python(value)


class YearMonthField(models.DateField):
    pass


class ChoiceField(models.TextField):
    pass


class HashField(models.TextField):
    pass


# All text field types
TEXT_FIELDS = [
    models.CharField,
    models.TextField,
    StrippedCharField,
    LowerCharField,
    UpperCharField,
]
