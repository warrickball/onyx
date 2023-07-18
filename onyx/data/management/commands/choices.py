from django.core.management import base
from data.models import Choice
import csv


def _print(*args, quiet=False, **kwargs):
    if not quiet:
        print(*args, **kwargs)


class Command(base.BaseCommand):
    help = "Set choice groups in the database."

    def add_arguments(self, parser):
        parser.add_argument("scheme")
        parser.add_argument("--quiet")

    def handle(self, *args, **options):
        with open(options["scheme"]) as scheme:
            reader = csv.DictReader(scheme, skipinitialspace=True)

            for row in reader:
                project = row["project"].strip()
                field = row["field"].strip()
                choices = [x.strip() for x in row["choices"].split(":")]

                # Create new choices if required
                for choice in choices:
                    db_choice, created = Choice.objects.get_or_create(
                        project_id=project,
                        field=field,
                        choice=choice,
                    )

                    if created:
                        _print(
                            f"Created choice: {project} | {db_choice.field} | {db_choice.choice}",
                            quiet=options["quiet"],
                        )
                    elif not db_choice.is_active:
                        db_choice.is_active = True
                        db_choice.save()
                        _print(
                            f"Reactivated choice: {project} | {db_choice.field} | {db_choice.choice}",
                            quiet=options["quiet"],
                        )
                    else:
                        _print(
                            f"Active choice: {project} | {db_choice.field} | {db_choice.choice}",
                            quiet=options["quiet"],
                        )

                # Deactivate choices no longer in the set
                db_choices = Choice.objects.filter(
                    project_id=project,
                    field=field,
                    is_active=True,
                )

                for db_choice in db_choices:
                    if db_choice.choice not in choices:
                        db_choice.is_active = False
                        db_choice.save()
                        _print(
                            f"Deactivated choice: {project} | {db_choice.field} | {db_choice.choice}",
                            quiet=options["quiet"],
                        )
