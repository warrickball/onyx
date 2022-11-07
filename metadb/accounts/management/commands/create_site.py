from django.core.management import base
from ...models import Site


class Command(base.BaseCommand):
    help = "Create a new site in the database."

    def add_arguments(self, parser):
        parser.add_argument("-n", "--name", required=True)
        parser.add_argument("-c", "--code", required=True)

    def handle(self, *args, **options):
        name = options["name"]
        code = options["code"]
        site = Site.objects.create(name=name, code=code)

        site = Site.objects.get(code=code.lower())
        print("Site created successfully.")
        print("Site name:", site.name)
        print("Site code:", site.code)
