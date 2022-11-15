from django.db.models.signals import post_save
from django.dispatch import receiver
from data.models import Mpx, Signal
from django.utils import timezone

# from data.tasks import generate_fasta_statistics


@receiver(post_save, sender=Mpx)
def post_save_mpx(sender, instance, **kwargs):
    signal, created = Signal.objects.get_or_create(code="mpx")
    signal.modified = timezone.now()
    signal.save(update_fields=["modified"])

    # if not instance.fasta_statistics:
    #     generate_fasta_statistics.delay(
    #         cid=instance.cid, fasta_path=instance.fasta_path
    #     )
