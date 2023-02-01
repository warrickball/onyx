from django.core.management import base
from django.db.utils import IntegrityError
from ...models import Project


class Command(base.BaseCommand):
    help = "Create a new project in the database."

    def add_arguments(self, parser):
        parser.add_argument("code")

    def handle(self, *args, **options):
        code = options["code"]

        exists = False
        try:
            project = Project.objects.create(code=code)
        except IntegrityError:
            exists = True
        
        if exists:
            project = Project.objects.get(code=code.lower())
            print("Project already existed.")
            print("Code:", project.code)
        else:
            project = Project.objects.get(code=code.lower())
            print("Project created successfully.")
            print("Code:", project.code)
