from django.db.models.signals import post_save
from django.dispatch import receiver
from data.models import Mpx
from internal.models import Signal
from django.utils import timezone


@receiver(post_save, sender=Mpx)
def post_save_mpx(sender, instance, **kwargs):
    Signal.objects.update_or_create(code="mpx", defaults={"modified": timezone.now()})
