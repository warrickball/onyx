from django.db import models
import data.models as data_models
from datetime import date
import secrets


def generate_cid():
    cid = "C-" + "".join(secrets.token_hex(3).upper())
    if data_models.Pathogen.objects.filter(cid=cid).exists():
        cid = generate_cid()
    return cid


# TODO: Improve
class YearMonthField(models.DateField):
    '''
    Minimal override of DateField to support YYYY-MM format.
    '''
    def to_python(self, value):
        if isinstance(value, str):
            year, month = value.split("-")
            value = date(int(year), int(month), 1)
        return super().to_python(value)
