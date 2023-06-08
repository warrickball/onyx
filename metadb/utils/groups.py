from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
import csv


class GroupDefinition:
    def __init__(self, name, permissions):
        self.name = name
        self.permissions = permissions


def read_groups(scheme):
    with open(scheme) as scheme_fh:
        reader = csv.reader(scheme_fh)

        name = next(reader)
        if not name[0].startswith("#"):
            raise Exception("Could not read group name")

        name = name[0].removeprefix("#")
        group_permissions = []

        for entry in reader:
            if not entry:
                continue

            elif entry[0].startswith("#"):
                gdef = GroupDefinition(name=name, permissions=group_permissions)
                yield gdef

                name = entry[0].removeprefix("#")
                group_permissions = []

            else:
                group_permissions.append(entry)

    gdef = GroupDefinition(name=name, permissions=group_permissions)
    yield gdef


def create_or_update_group(app_label, model, gdef):
    group, created = Group.objects.get_or_create(name=gdef.name)
    permissions = []

    for perm in gdef.permissions:
        permission = perm[0]
        action, _, thing = permission.partition("_")
        project, _, field = thing.partition("__")

        content_type = ContentType.objects.get(app_label=app_label, model=model)
        permission, created = Permission.objects.get_or_create(
            content_type=content_type,
            codename=permission,
            name=f"Can {action} {project}{' ' + field if field else ''}",
        )
        if created:
            print("Created permission:", permission)
        permissions.append(permission)

    group.permissions.set(permissions)

    return group, created
