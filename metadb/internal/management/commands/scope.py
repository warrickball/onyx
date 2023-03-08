from django.core.management import base
from django.contrib.auth.models import Permission
from ...models import Project, Scope
from utils.groups import read_groups, create_or_update_group


class Command(base.BaseCommand):
    help = "Create a new scope in the database."

    def add_arguments(self, parser):
        parser.add_argument("code")
        parser.add_argument("--groups")
        visibility = parser.add_mutually_exclusive_group(required=False)
        visibility.add_argument(
            "--public", action="store_false", default=None, dest="hidden"
        )
        visibility.add_argument(
            "--private", action="store_true", default=None, dest="hidden"
        )

    def handle(self, *args, **options):
        code = options["code"].lower()
        project_code, _, scope_code = code.partition("-")
        project = Project.objects.get(code=project_code)
        hidden = options.get("hidden")
        groups = {}

        for gdef in read_groups(options["groups"]):
            group, created = create_or_update_group(gdef)

            action, _, _ = gdef.name.partition("_")
            action_perm, _ = Permission.objects.get_or_create(
                codename=f"{action}_{code}",
                name=f"Can {action} {code}",
                content_type=project.content_type,
            )
            group.permissions.add(action_perm)

            groups[action] = group

            if created:
                print(f"Group created: {gdef.name}")
            else:
                print(f"Group updated: {gdef.name}")

            print("Permissions:")
            for perm in group.permissions.all():
                print(perm)

        scope, created = Scope.objects.update_or_create(
            project=project,
            code=scope_code,
            defaults={
                "hidden": hidden,
                "add_group": groups.get("add"),
                "view_group": groups.get("view"),
                "change_group": groups.get("change"),
                "suppress_group": groups.get("suppress"),
                "delete_group": groups.get("delete"),
            },
        )

        if created:
            print("Scope created.")
        else:
            print("Scope updated.")

        print("Project code:", project.code)
        print("Scope code:", scope.code)
        print("Hidden:", scope.hidden)
