from django.core.management import base
from ...models import Institute


class Command(base.BaseCommand):
    help = "Create a new institute in the database."

    def add_arguments(self, parser):
        parser.add_argument("-n", "--name")
        parser.add_argument("-c", "--code")

    def handle(self, *args, **options):
        name = options["name"]
        code = options["code"]
        institute = Institute.objects.create(name=name, code=code)

        institute = Institute.objects.get(code=code.lower())
        print("Institute created successfully.")
        print("Institute name:", institute.name)
        print("Institute code:", institute.code)
