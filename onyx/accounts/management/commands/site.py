from django.core.management import base
from ...models import Site


class Command(base.BaseCommand):
    help = "Create or update a site in the database."

    def add_arguments(self, parser):
        parser.add_argument("code")
        parser.add_argument("-d", "--description")

    def handle(self, *args, **options):
        code = options["code"].lower()
        description = options["description"]

        site, created = Site.objects.update_or_create(
            code=code, defaults={"description": description}
        )

        if created:
            print(f"Created site: {site.code}")
        else:
            print(f"Updated site: {site.code}")

        print("\tdescription:", site.description)
