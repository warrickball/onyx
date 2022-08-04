from django.contrib.auth.models import AbstractUser
from django.db import models


class Institute(models.Model):
    code = models.CharField(max_length=10, unique=True)
    name = models.CharField(max_length=100, unique=True)


class User(AbstractUser):
    institute = models.ForeignKey("Institute", on_delete=models.CASCADE) 
    is_approved = models.BooleanField(default=False)
    is_authority = models.BooleanField(default=False)
