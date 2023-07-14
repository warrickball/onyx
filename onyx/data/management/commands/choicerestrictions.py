from django.core.management import base
from django.contrib.contenttypes.models import ContentType
from data.models import Choice
import csv


def _print(*args, quiet=False, **kwargs):
    if not quiet:
        print(*args, **kwargs)


class Command(base.BaseCommand):
    help = "Set choice restrictions in the database."

    def add_arguments(self, parser):
        parser.add_argument("scheme")
        parser.add_argument("--quiet")

    def handle(self, *args, **options):
        with open(options["scheme"]) as scheme:
            reader = csv.DictReader(scheme, skipinitialspace=True)

            for row in reader:
                app_label, model = row["content_type"].strip().split(".")
                content_type = ContentType.objects.get(app_label=app_label, model=model)
                field = row["field"].strip()
                choice = row["choice"].strip()
                restricted_to_field = row["restricted_to_field"].strip()
                restricted_to_choices = [
                    x.strip() for x in row["restricted_to_choices"].split(":")
                ]
                choice_instance = Choice.objects.get(
                    content_type=content_type, field=field, choice=choice
                )
                restricted_instances = [
                    Choice.objects.get(
                        content_type=content_type,
                        field=restricted_to_field,
                        choice=restricted_to_choice,
                    )
                    for restricted_to_choice in restricted_to_choices
                ]
                for restricted_instance in restricted_instances:
                    choice_instance.restricted_to.add(restricted_instance)
                    restricted_instance.restricted_to.add(choice_instance)
                    _print(
                        f"Created restriction: {content_type.app_label} | {content_type.model_class()} | ({choice_instance.field}, {choice_instance.choice}) | ({restricted_instance.field}, {restricted_instance.choice})",
                        quiet=options["quiet"],
                    )
