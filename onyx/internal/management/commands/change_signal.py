from django.core.management import base
from django.utils import timezone
from ...models import Signal


class Command(base.BaseCommand):
    help = "Alter a given signal."

    def add_arguments(self, parser):
        parser.add_argument("code")

    def handle(self, *args, **options):
        code = options["code"]
        signal, created = Signal.objects.get_or_create(code=code)
        signal.modified = timezone.now()
        signal.save(update_fields=["modified"])
