from django.core.management import base
from data.models import Uploader


class Command(base.BaseCommand):
    help = "Add a new uploader."

    def add_arguments(self, parser):
        parser.add_argument("uploader_code")

    def handle(self, *args, **options):
        Uploader.objects.create(uploader_code=options["uploader_code"])
