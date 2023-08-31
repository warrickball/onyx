from django.utils.translation import gettext_lazy as _
from rest_framework import exceptions


class CIDNotFound(exceptions.NotFound):
    default_detail = _("CID not found.")
