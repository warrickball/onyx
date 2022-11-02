from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.validators import validate_email, MinLengthValidator
from model_utils.fields import MonitorField
from utils.fields import LowerCharField


class Institute(models.Model):
    code = LowerCharField(max_length=10, unique=True)
    name = models.CharField(max_length=100, unique=True)

    is_active = models.BooleanField(default=True)
    is_pha = models.BooleanField(default=False)


class User(AbstractUser):
    username = LowerCharField(
        _("username"),
        max_length=100,
        unique=True,
        help_text=_(
            "Required. 100 characters or fewer. Letters, digits and @/./+/-/_ only."
        ),
        validators=[AbstractUser.username_validator, MinLengthValidator(5)],
        error_messages={
            "unique": _("A user with that username already exists."),
        },
    )
    email = LowerCharField(
        _("email address"),
        max_length=100,
        unique=True,
        validators=[validate_email],
        error_messages={
            "unique": _("A user with that email already exists."),
        },
    )
    institute = models.ForeignKey("Institute", on_delete=models.CASCADE)
    is_institute_approved = models.BooleanField(default=False)
    date_institute_approved = models.DateTimeField(null=True)
    is_admin_approved = models.BooleanField(default=False)
    is_institute_authority = models.BooleanField(default=False)
