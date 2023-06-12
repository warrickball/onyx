from django.core.management import base
from django.contrib.contenttypes.models import ContentType
from ...models import Project
from utils.groups import read_groups, create_or_update_group


class Command(base.BaseCommand):
    help = "Create or update a project in the database."

    def add_arguments(self, parser):
        parser.add_argument("code")
        parser.add_argument("--groups", required=True)
        parser.add_argument("--content-type")

    def handle(self, *args, **options):
        code = options["code"].lower()

        if options["content_type"]:
            app, model = options["content_type"].split(".")
        else:
            app, model = "data", code

        content_type = ContentType.objects.get(app_label=app, model=model)
        groups = {}

        for gdef in read_groups(options["groups"]):
            group, created = create_or_update_group(app, model, gdef)
            action, _, _ = gdef.name.partition("_")
            groups[action] = group

            if created:
                print(f"Created group: {gdef.name}")
            else:
                print(f"Updated group: {gdef.name}")

            print("Permissions:")
            for perm in group.permissions.all():
                print(f"\t{perm}")
            print("")

        project, created = Project.objects.update_or_create(
            code=code,
            defaults={
                "content_type": content_type,
                "add_group": groups["add"],
                "view_group": groups["view"],
                "change_group": groups["change"],
                "suppress_group": groups["suppress"],
                "delete_group": groups["delete"],
            },
        )

        if created:
            print(f"Created project: {project.code}")
        else:
            print(f"Updated project: {project.code}")

        print("\tmodel:", project.content_type.model_class())
