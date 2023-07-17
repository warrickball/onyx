from django.core.management import base
from django.contrib.contenttypes.models import ContentType
from data.models import Choice
import csv


def _print(*args, quiet=False, **kwargs):
    if not quiet:
        print(*args, **kwargs)


class Command(base.BaseCommand):
    help = "Set choice constraints in the database."

    def add_arguments(self, parser):
        action = parser.add_mutually_exclusive_group(required=True)
        action.add_argument("scheme", nargs="?")
        action.add_argument("--validate", action="store_true")
        parser.add_argument("--quiet")

    def handle(self, *args, **options):
        if options.get("scheme"):
            with open(options["scheme"]) as scheme:
                reader = csv.DictReader(scheme, skipinitialspace=True)

                # Empty constraints
                for choice in Choice.objects.all():
                    choice.constraints.clear()

                for row in reader:
                    app_label, model = row["content_type"].strip().split(".")
                    content_type = ContentType.objects.get(
                        app_label=app_label, model=model
                    )
                    field = row["field"].strip()
                    choice = row["choice"].strip()
                    constraint_field = row["constraint_field"].strip()
                    constraint_choices = [
                        x.strip() for x in row["constraint_choices"].split(":")
                    ]
                    choice_instance = Choice.objects.get(
                        content_type=content_type, field=field, choice=choice
                    )
                    constraint_instances = [
                        Choice.objects.get(
                            content_type=content_type,
                            field=constraint_field,
                            choice=constraint_choice,
                        )
                        for constraint_choice in constraint_choices
                    ]
                    # Set constraints
                    for constraint_instance in constraint_instances:
                        choice_instance.constraints.add(constraint_instance)
                        constraint_instance.constraints.add(choice_instance)
                        _print(
                            f"Set constraint: {content_type.app_label} | {content_type.model_class()} | ({choice_instance.field}, {choice_instance.choice}) | ({constraint_instance.field}, {constraint_instance.choice})",
                            quiet=options["quiet"],
                        )
        else:
            valid = True
            for choice in Choice.objects.all():
                for constraint in choice.constraints.all():
                    if choice not in constraint.constraints.all():
                        _print(
                            f"Choice {(choice.field, choice.choice)} is not in the constraint set of Choice {(constraint.field, constraint.choice)}.",
                            quiet=options["quiet"],
                        )
                        valid = False
                        break

            if valid:
                _print("Constraints are valid.", quiet=options["quiet"])
            else:
                _print("Constraints are invalid.", quiet=options["quiet"])
