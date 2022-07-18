from django.db.utils import OperationalError


def get_choices(model, field):
    try:
        choices = list(model.objects.values_list(field, flat=True))
    except OperationalError:
        choices = []
    return choices
