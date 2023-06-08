from django.core.management import base
from ...models import Project, Scope
from utils.groups import read_groups, create_or_update_group


class Command(base.BaseCommand):
    help = "Create or update a scope in the database."

    def add_arguments(self, parser):
        parser.add_argument("code")
        parser.add_argument("scope")
        parser.add_argument("--groups", required=True)

    def handle(self, *args, **options):
        project_code = options["code"].lower()
        scope_code = options["scope"].lower()

        project = Project.objects.get(code=project_code)
        app = project.content_type.app_label
        model = project.content_type.model

        for gdef in read_groups(options["groups"]):
            group, created = create_or_update_group(app, model, gdef)
            action, _, _ = gdef.name.partition("_")

            if created:
                print(f"Created group: {gdef.name}")
            else:
                print(f"Updated group: {gdef.name}")

            print("Permissions:")
            for perm in group.permissions.all():
                print(f"\t{perm}")
            print("")

            scope, created = Scope.objects.update_or_create(
                project=project,
                code=scope_code,
                action=action,
                defaults={
                    "group": group,
                },
            )

            if created:
                print(f"Created scope: {scope.code}")
            else:
                print(f"Updated scope: {scope.code}")

            print("\tproject:", project.code)
            print("\taction:", scope.action)
            print("")
