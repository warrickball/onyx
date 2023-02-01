from django.core.management import base
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
import csv


class Command(base.BaseCommand):
    help = "Create groups in the database"

    def add_arguments(self, parser):
        parser.add_argument("scheme")

    def handle(self, *args, **options):
        with open(options["scheme"]) as scheme:
            reader = csv.reader(scheme)

            name = next(reader)
            if not name[0].startswith("#"):
                raise Exception("Could not read group name")

            name = name[0].removeprefix("#")
            group_permissions = []

            for entry in reader:
                if not entry:
                    continue

                elif entry[0].startswith("#"):
                    group, created = Group.objects.get_or_create(name=name)
                    group.permissions.set(group_permissions)

                    if created:
                        print(f"Created group: {name}")
                    else:
                        print(f"Updated group: {name}")

                    print("Permissions:")
                    for perm in group_permissions:
                        print(perm)

                    name = entry[0].removeprefix("#")
                    group_permissions = []

                elif entry[0].startswith("@"):
                    g_name = entry[0].removeprefix("@")
                    try:
                        g = Group.objects.get(name=g_name)
                        g_perms = g.permissions.all()
                        group_permissions.extend(g_perms)
                    except Group.DoesNotExist:
                        raise Exception(
                            f"Tried to include permissions from non-existent group '{g_name}'"
                        )

                else:
                    app_label, model, permission = entry

                    content_type = ContentType.objects.get(
                        app_label=app_label, model=model
                    )

                    permission = Permission.objects.get(
                        content_type=content_type, codename=permission
                    )
                    group_permissions.append(permission)

        group, created = Group.objects.get_or_create(name=name)
        group.permissions.set(group_permissions)

        if created:
            print(f"Created group: {name}")
        else:
            print(f"Updated group: {name}")

        print("Permissions:")
        for perm in group_permissions:
            print(perm)
