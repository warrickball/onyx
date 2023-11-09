from django.utils.translation import gettext_lazy as _
from rest_framework.validators import UniqueTogetherValidator


class OnyxUniqueTogetherValidator(UniqueTogetherValidator):
    message = _("This combination of {field_names} already exists.")
