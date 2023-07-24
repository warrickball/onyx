from django.core.management import base
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from ...models import Project
import json


class Command(base.BaseCommand):
    help = "Set projects in the database."

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

            for project_code, project_info in data.items():
                # If a {app}.{model} was provided, use it to get the content_type
                # Otherwise, assume that app = data and that the model has the same
                # name as the project
                if project_info.get("content_type"):
                    app, _, model = project_info["content_type"].partition(".")
                else:
                    app, model = "data", project_code
                content_type = ContentType.objects.get(app_label=app, model=model)

                # Create / update each group for the project
                groups = {}
                for action, fields in project_info.get("groups").items():
                    name = f"{action}.project.{project_code}"
                    group, g_created = Group.objects.get_or_create(name=name)
                    permissions = []

                    for field in fields:
                        codename = f"{action}_{project_code}__{field}"
                        permission, p_created = Permission.objects.get_or_create(
                            content_type=content_type,
                            codename=codename,
                            name=f"Can {action} {project_code}{' ' + field if field else ''}",
                        )
                        if p_created:
                            self.print("Created permission:", permission)

                        permissions.append(permission)

                    group.permissions.set(permissions)

                    if g_created:
                        self.print(f"Created group: {name}")
                    else:
                        self.print(f"Updated group: {name}")

                    self.print("Permissions:")
                    for perm in group.permissions.all():
                        self.print(f"\t{perm}")
                    self.print("")

                    groups[action] = group

                project, p_created = Project.objects.update_or_create(
                    code=project_code,
                    defaults={
                        "content_type": content_type,
                        "add_group": groups["add"],
                        "view_group": groups["view"],
                        "change_group": groups["change"],
                        "suppress_group": groups["suppress"],
                        "delete_group": groups["delete"],
                    },
                )

                if p_created:
                    self.print(f"Created project: {project.code}")
                else:
                    self.print(f"Updated project: {project.code}")

                self.print("\tmodel:", project.content_type.model_class())
