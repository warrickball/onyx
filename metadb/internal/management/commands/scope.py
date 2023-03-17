from django.core.management import base
from ...models import Project, Scope
from utils.groups import read_groups, create_or_update_group


class Command(base.BaseCommand):
    help = "Create or update a scope in the database."

    def add_arguments(self, parser):
        parser.add_argument("code")
        parser.add_argument("--groups")

    def handle(self, *args, **options):
        code = options["code"].lower()
        project_code, _, scope_code = code.partition("-")
        project = Project.objects.get(code=project_code)

        for gdef in read_groups(options["groups"]):
            group, created = create_or_update_group(gdef)
            action, _, _ = gdef.name.partition("_")

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
                action=action,
                defaults={
                    "group": group,
                },
            )

            if created:
                print("Scope created.")
            else:
                print("Scope updated.")

            print("Project code:", project.code)
            print("Scope code:", scope.code)
            print("Action:", scope.action)
