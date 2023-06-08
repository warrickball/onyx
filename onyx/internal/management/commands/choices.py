from django.core.management import base
from django.contrib.contenttypes.models import ContentType
from internal.models import Choice
import csv


class Command(base.BaseCommand):
    help = "Create choices in the database."

    def add_arguments(self, parser):
        parser.add_argument("scheme")

    def handle(self, *args, **options):
        with open(options["scheme"]) as scheme:
            reader = csv.reader(scheme)

            for row in reader:
                app_label = row[0]
                model = row[1]
                field = row[2]
                choices = row[3:]
                content_type = ContentType.objects.get(app_label=app_label, model=model)

                for c in choices:
                    choice, created = Choice.objects.get_or_create(
                        content_type=content_type,
                        field=field,
                        choice=c,
                    )

                    if created:
                        print(f"Created choice: {app_label} | {model} | {field} | {c}")
                    else:
                        print(f"Existing choice: {app_label} | {model} | {field} | {c}")
