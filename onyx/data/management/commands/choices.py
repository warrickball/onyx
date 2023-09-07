from django.core.management import base
from ...models import Choice
import json


# TODO: Issue with reactivate/deactivate choices if you provide them in uppercase in the json
# Upgrade Choices management command to DELETE inactive choices if a new one comes in with the same characters but a different case
# E.g. if a new choice Swab comes in, DELETE the old choice swab
# TL:DR we need case insensitivity in handling


class Command(base.BaseCommand):
    help = "Set choice groups in the database."

    def add_arguments(self, parser):
        parser.add_argument("scheme")
        parser.add_argument("--quiet", action="store_true")

    def print(self, *args, **kwargs):
        if not self.quiet:
            print(*args, **kwargs)

    def handle(self, *args, **options):
        self.quiet = options["quiet"]

        with open(options["scheme"]) as scheme:
            data = json.load(scheme)

            for project, fields in data.items():
                for field, choices in fields.items():
                    # Create new choices if required
                    for choice in choices:
                        instance, created = Choice.objects.get_or_create(
                            project_id=project,
                            field=field,
                            choice=choice,
                        )

                        if created:
                            self.print(
                                f"Created choice: {project} | {instance.field} | {instance.choice}",
                            )
                        elif not instance.is_active:
                            instance.is_active = True
                            instance.save()
                            self.print(
                                f"Reactivated choice: {project} | {instance.field} | {instance.choice}",
                            )
                        else:
                            self.print(
                                f"Active choice: {project} | {instance.field} | {instance.choice}",
                            )

                    # Deactivate choices no longer in the set
                    instances = Choice.objects.filter(
                        project_id=project,
                        field=field,
                        is_active=True,
                    )

                    for instance in instances:
                        if instance.choice not in choices:
                            instance.is_active = False
                            instance.save()
                            self.print(
                                f"Deactivated choice: {project} | {instance.field} | {instance.choice}",
                            )
