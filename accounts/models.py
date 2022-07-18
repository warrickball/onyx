from django.contrib.auth.models import AbstractUser
from django.db import models

# Create your models here.

class User(AbstractUser):
    institute = models.CharField(max_length=10) # TODO: Make foreignkey. At the moment, there is no verification of this code
    is_approved = models.BooleanField(default=False)
    is_authority = models.BooleanField(default=False)


class Institute(models.Model):
    name = models.CharField(max_length=100, unique=True)
    code = models.CharField(max_length=10, unique=True)
