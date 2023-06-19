from django.core.management import base
from django.contrib.contenttypes.models import ContentType
from data.models import Choice
import csv


class Command(base.BaseCommand):
    help = "Set choice groups in the database."

    def add_arguments(self, parser):
        parser.add_argument("scheme")

    def handle(self, *args, **options):
        with open(options["scheme"]) as scheme:
            reader = csv.DictReader(scheme, skipinitialspace=True)

            for row in reader:
                app_label, model = row["content_type"].strip().split(".")
                content_type = ContentType.objects.get(app_label=app_label, model=model)
                field = row["field"].strip()
                choices = [x.strip() for x in row["choices"].split(":")]

                # Create new choices if required
                for choice in choices:
                    db_choice, created = Choice.objects.get_or_create(
                        content_type=content_type,
                        field=field,
                        choice=choice,
                    )

                    if created:
                        print(
                            f"Created choice: {db_choice.content_type.app_label} | {db_choice.content_type.model_class()} | {db_choice.field} | {db_choice.choice}"
                        )
                    elif not db_choice.is_active:
                        db_choice.is_active = True
                        db_choice.save()
                        print(
                            f"Reactivated choice: {db_choice.content_type.app_label} | {db_choice.content_type.model_class()} | {db_choice.field} | {db_choice.choice}"
                        )
                    else:
                        print(
                            f"Active choice: {db_choice.content_type.app_label} | {db_choice.content_type.model_class()} | {db_choice.field} | {db_choice.choice}"
                        )

                # Deactivate choices no longer in the set
                db_choices = Choice.objects.filter(
                    content_type=content_type,
                    field=field,
                    is_active=True,
                )

                for db_choice in db_choices:
                    if db_choice.choice not in choices:
                        db_choice.is_active = False
                        db_choice.save()
                        print(
                            f"Deactivated choice: {db_choice.content_type.app_label} | {db_choice.content_type.model_class()} | {db_choice.field} | {db_choice.choice}"
                        )
