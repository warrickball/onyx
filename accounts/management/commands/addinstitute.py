from django.core.management import base
from ...models import Institute


class Command(base.BaseCommand):
    help = "Add a new institute."

    def add_arguments(self, parser):
        parser.add_argument("-n", "--name")
        parser.add_argument("-c", "--code")

    def handle(self, *args, **options):
        Institute.objects.create(
            name=options["name"],
            code=options["code"]
        )
