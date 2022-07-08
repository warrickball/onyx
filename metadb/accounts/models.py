from django.contrib.auth.models import AbstractUser
from django.db import models

# Create your models here.

class User(AbstractUser):
    uploader = models.CharField(max_length=8) # TODO: Was somehow able to make blank despite not being so..?
