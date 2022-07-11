from django.core.management import base
from ...models import Uploader


class Command(base.BaseCommand):
    help = "Add a new uploader."

    def add_arguments(self, parser):
        parser.add_argument("-n", "--name")
        parser.add_argument("-c", "--code")

    def handle(self, *args, **options):
        Uploader.objects.create(
            name=options["name"],
            code=options["code"]
        )
