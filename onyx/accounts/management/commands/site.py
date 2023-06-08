from django.core.management import base
from django.db.utils import IntegrityError
from ...models import Site


class Command(base.BaseCommand):
    help = "Create a site in the database."

    def add_arguments(self, parser):
        parser.add_argument("code")
        parser.add_argument("-n", "--name", required=True)

    def handle(self, *args, **options):
        code = options["code"].lower()
        name = options["name"]

        exists = False
        try:
            site = Site.objects.create(name=name, code=code)
        except IntegrityError:
            exists = True

        if exists:
            site = Site.objects.get(code=code)
            print(f"Existing site: {site.code}")
            print("\tname:", site.name)
        else:
            site = Site.objects.get(code=code)
            print(f"Created site: {site.code}")
            print("\tname:", site.name)
