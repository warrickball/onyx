from django.core.management import base
from ...models import PathogenCode


class Command(base.BaseCommand):
    help = "Create a new pathogen code in the database."

    def add_arguments(self, parser):
        parser.add_argument("code")

    def handle(self, *args, **options):
        code = options["code"]
        pathogen_code = PathogenCode.objects.create(code=code)

        pathogen_code = PathogenCode.objects.get(code=code.lower())
        print("PathogenCode created successfully.")
        print("Code:", pathogen_code.code)
