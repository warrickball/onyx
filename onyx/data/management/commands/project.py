from django.core.management import base
from django.contrib.contenttypes.models import ContentType
from ...models import Project
from utils.groups import read_groups, create_or_update_group


def _print(*args, quiet=False, **kwargs):
    if not quiet:
        print(*args, **kwargs)


class Command(base.BaseCommand):
    help = "Create or update a project in the database."

    def add_arguments(self, parser):
        parser.add_argument("code")
        parser.add_argument("--groups", required=True)
        parser.add_argument("--content-type")
        parser.add_argument("--quiet", default=False)

    def handle(self, *args, **options):
        code = options["code"].lower()

        if options["content_type"]:
            app, model = options["content_type"].split(".")
        else:
            app, model = "data", code

        content_type = ContentType.objects.get(app_label=app, model=model)
        groups = {}

        for gdef in read_groups(options["groups"]):
            group, created = create_or_update_group(
                app, model, gdef, quiet=options["quiet"]
            )
            action, _, _ = gdef.name.partition(".")
            groups[action] = group

            if created:
                _print(f"Created group: {gdef.name}", quiet=options["quiet"])
            else:
                _print(f"Updated group: {gdef.name}", quiet=options["quiet"])

            _print("Permissions:", quiet=options["quiet"])
            for perm in group.permissions.all():
                _print(f"\t{perm}", quiet=options["quiet"])
            _print("", quiet=options["quiet"])

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
            _print(f"Created project: {project.code}", quiet=options["quiet"])
        else:
            _print(f"Updated project: {project.code}", quiet=options["quiet"])

        _print("\tmodel:", project.content_type.model_class(), quiet=options["quiet"])
