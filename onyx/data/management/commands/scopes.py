from django.core.management import base
from django.contrib.auth.models import Group, Permission
from ...models import Project, Scope
import json


class Command(base.BaseCommand):
    help = "Set scopes in the database."

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
            for project_code, scopes in data.items():
                project = Project.objects.get(code=project_code)
                content_type = project.content_type
                for scope_code, actions in scopes.items():
                    for action, fields in actions.items():
                        name = f"{action}.scope.{project_code}.{scope_code}"
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

                        scope, s_created = Scope.objects.update_or_create(
                            project=project,
                            code=scope_code,
                            action=action,
                            defaults={
                                "group": group,
                            },
                        )

                        if s_created:
                            print(
                                f"Created scope: {scope.action}.{project.code}.{scope.code}"
                            )
                        else:
                            print(
                                f"Updated scope: {scope.action}.{project.code}.{scope.code}"
                            )
