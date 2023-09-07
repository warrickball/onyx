from django.core.management import base
from ...models import Choice
import json


# TODO: Case insensitivity in handling


class Command(base.BaseCommand):
    help = "Set choice constraints in the database."

    def add_arguments(self, parser):
        action = parser.add_mutually_exclusive_group(required=True)
        action.add_argument("scheme", nargs="?")
        action.add_argument("--validate", action="store_true")
        parser.add_argument("--quiet", action="store_true")

    def print(self, *args, **kwargs):
        if not self.quiet:
            print(*args, **kwargs)

    def handle(self, *args, **options):
        self.quiet = options["quiet"]

        if options.get("scheme"):
            with open(options["scheme"]) as scheme:
                data = json.load(scheme)

                # For each project, set constraints for each choice
                for project, fields in data.items():
                    # Empty constraints for that project
                    for choice in Choice.objects.filter(project_id=project):
                        choice.constraints.clear()

                    for field, choices in fields.items():
                        for choice, constraint_fields in choices.items():
                            choice_instance = Choice.objects.get(
                                project_id=project, field=field, choice=choice
                            )

                            for (
                                constraint_field,
                                constraint_choices,
                            ) in constraint_fields.items():
                                # Get each constraint choice instance
                                constraint_instances = [
                                    Choice.objects.get(
                                        project_id=project,
                                        field=constraint_field,
                                        choice=constraint_choice,
                                    )
                                    for constraint_choice in constraint_choices
                                ]
                                # Set constraints
                                # This is set both ways: each constraint is added for the choice
                                # And the choice is added for each constraint
                                for constraint_instance in constraint_instances:
                                    choice_instance.constraints.add(constraint_instance)
                                    constraint_instance.constraints.add(choice_instance)
                                    self.print(
                                        f"Set constraint: {project} | ({choice_instance.field}, {choice_instance.choice}) | ({constraint_instance.field}, {constraint_instance.choice})",
                                    )
        else:
            # Check that each constraint in a choice's constraint set also has the choice itself as a constraint
            valid = True
            for choice in Choice.objects.all():
                for constraint in choice.constraints.all():
                    if choice not in constraint.constraints.all():
                        self.print(
                            f"Choice {(choice.field, choice.choice)} is not in the constraint set of Choice {(constraint.field, constraint.choice)}.",
                        )
                        valid = False
                        break

            if valid:
                self.print("Constraints are valid.")
            else:
                self.print("Constraints are invalid.")
