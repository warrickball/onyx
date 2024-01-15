from django.utils.translation import gettext_lazy as _
from rest_framework import exceptions


class ClimbIDNotFound(exceptions.NotFound):
    default_detail = _("CLIMB ID not found.")
