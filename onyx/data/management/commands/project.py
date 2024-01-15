from typing import Optional, Dict, List
from django.core.management import base
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from ...models import Project, ProjectGroup, Choice
import json


class Command(base.BaseCommand):
    help = "Create/manage projects."

    def add_arguments(self, parser):
        parser.add_argument("project_config")
        parser.add_argument("--quiet", action="store_true")

    def print(self, *args, **kwargs):
        if not self.quiet:
            print(*args, **kwargs)

    def handle(self, *args, **options):
        self.quiet = options["quiet"]

        with open(options["project_config"]) as project_config_file:
            project_config = json.load(project_config_file)

            self.set_project(
                code=project_config["code"],
                name=project_config.get("name"),
                description=project_config.get("description"),
                content_type_name=project_config.get("content_type"),
            )

            if project_config.get("groups"):
                self.set_groups(project_config["groups"])

            if project_config.get("choices"):
                self.set_choices(project_config["choices"])

            if project_config.get("choice_constraints"):
                self.set_choice_constraints(project_config["choice_constraints"])

    def set_project(
        self,
        code: str,
        name: Optional[str] = None,
        description: Optional[str] = None,
        content_type_name: Optional[str] = None,
    ):
        """
        Create/update the project details.
        """

        # If no name was provided, use the code
        if not name:
            name = code

        # If no description was provided, set as empty
        if not description:
            description = ""

        # If a {app}.{model} was provided, use it to get the content_type
        # Otherwise, assume that app = data and that the model has the same name as the project
        if content_type_name:
            app, _, model = content_type_name.partition(".")
        else:
            app, model = "data", code

        content_type = ContentType.objects.get(app_label=app, model=model)

        self.project, p_created = Project.objects.update_or_create(
            code=code,
            defaults={
                "name": name,
                "description": description,
                "content_type": content_type,
            },
        )

        if p_created:
            self.print(f"Created project: {self.project.code}")
        else:
            self.print(f"Updated project: {self.project.code}")

        self.print("Name:", self.project.name)
        self.print("Description:", self.project.description)
        self.print("Model:", self.project.content_type.model_class())

    def set_groups(self, data: Dict[str, Dict[str, List[str]]]):
        """
        Create/update the groups for the project.
        """

        groups = {}
        for action, scopes in data.items():
            for scope, fields in scopes.items():
                name = f"{self.project.code}.{action}.{scope}"
                group, g_created = Group.objects.get_or_create(name=name)

                if g_created:
                    self.print(f"Created group: {name}")
                else:
                    self.print(f"Updated group: {name}")

                permissions = []

                for field in fields:
                    codename = f"{action}_{self.project.code}__{field}"
                    permission, p_created = Permission.objects.get_or_create(
                        content_type=self.project.content_type,
                        codename=codename,
                        name=f"Can {action} {self.project.code}{' ' + field if field else ''}",
                    )
                    if p_created:
                        self.print("Created permission:", permission)

                    permissions.append(permission)

                group.permissions.set(permissions)

                if permissions:
                    self.print(f"Permissions for {name}:")
                    for perm in group.permissions.all():
                        self.print(f"\t{perm}")
                else:
                    self.print(f"Group {name} has no permissions.")

                groups[(action, scope)] = group

        for (action, scope), group in groups.items():
            projectgroup, pg_created = ProjectGroup.objects.update_or_create(
                group=group,
                defaults={"project": self.project, "action": action, "scope": scope},
            )
            if pg_created:
                self.print(
                    f"Created project group: {self.project.code} | {projectgroup.action} | {projectgroup.scope}"
                )
            else:
                self.print(
                    f"Updated project group: {self.project.code} | {projectgroup.action} | {projectgroup.scope}"
                )

    def set_choices(self, data: Dict[str, List[str]]):
        """
        Create/update the choices for the project.
        """

        # TODO: Issue with reactivate/deactivate choices if you provide them in uppercase in the json
        # Upgrade Choices management command to DELETE inactive choices if a new one comes in with the same characters but a different case
        # E.g. if a new choice Swab comes in, DELETE the old choice swab
        # TL:DR we need case insensitivity in handling

        for field, choices in data.items():
            # Create new choices if required
            for choice in choices:
                instance, created = Choice.objects.get_or_create(
                    project_id=self.project.code,
                    field=field,
                    choice=choice,
                )

                if created:
                    self.print(
                        f"Created choice: {self.project.code} | {instance.field} | {instance.choice}",
                    )
                elif not instance.is_active:
                    instance.is_active = True
                    instance.save()
                    self.print(
                        f"Reactivated choice: {self.project.code} | {instance.field} | {instance.choice}",
                    )
                else:
                    self.print(
                        f"Active choice: {self.project.code} | {instance.field} | {instance.choice}",
                    )

            # Deactivate choices no longer in the set
            instances = Choice.objects.filter(
                project_id=self.project.code,
                field=field,
                is_active=True,
            )

            for instance in instances:
                if instance.choice not in choices:
                    instance.is_active = False
                    instance.save()
                    self.print(
                        f"Deactivated choice: {self.project.code} | {instance.field} | {instance.choice}",
                    )

    def set_choice_constraints(self, data: Dict[str, Dict[str, Dict[str, List[str]]]]):
        """
        Create/update the choice constraints for the project.
        """

        # TODO: Case insensitivity in constraint handling

        # Empty constraints for the project
        for choice in Choice.objects.filter(project_id=self.project.code):
            choice.constraints.clear()

        for field, choices in data.items():
            for choice, constraint_fields in choices.items():
                choice_instance = Choice.objects.get(
                    project_id=self.project.code, field=field, choice=choice
                )

                for (
                    constraint_field,
                    constraint_choices,
                ) in constraint_fields.items():
                    # Get each constraint choice instance
                    constraint_instances = [
                        Choice.objects.get(
                            project_id=self.project.code,
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
                            f"Set constraint: {self.project.code} | ({choice_instance.field}, {choice_instance.choice}) | ({constraint_instance.field}, {constraint_instance.choice})",
                        )

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
