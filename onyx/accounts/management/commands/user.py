from typing import Optional, List
from django.core.management import base
from django.contrib.auth.models import Group
from ...models import User, Site


ROLES = [
    "is_active",
    "is_approved",
    "is_staff",
]


def create_user(
    username: str,
    password: str,
    site: str,
    email: str,
    first_name: str,
    last_name: str,
):
    if User.objects.filter(username=username).exists():
        print(f"User with username '{username}' already exists.")
        exit()

    user = User.objects.create_user(  # type: ignore
        username=username,
        password=password,
        site=Site.objects.get(code=site),
        email=email,
        first_name=first_name,
        last_name=last_name,
    )
    print("Created user:", user.username)
    print("\tsite:", user.site.code)
    print("\temail:", user.email)


def manage_user_roles(
    username: str,
    granted: Optional[List[str]],
    revoked: Optional[List[str]],
):
    user = User.objects.get(username=username)
    print("User:", user.username)

    if granted:
        roles = []
        for role in granted:
            if not hasattr(user, role):
                raise Exception("Role is unknown")

            if role not in ROLES:
                raise Exception("Role cannot be changed")

            setattr(user, role, True)
            roles.append(role)

        user.save(update_fields=roles)
        print("Granted roles:")
        for role in roles:
            print(f"\t{role}")

    elif revoked:
        roles = []
        for role in revoked:
            if not hasattr(user, role):
                raise Exception("Role is unknown")

            if role not in ROLES:
                raise Exception("Role cannot be changed")

            setattr(user, role, False)
            roles.append(role)

        user.save(update_fields=roles)
        print("Revoked roles:")
        for role in roles:
            print(f"\t{role}")

    else:
        print("Roles:")
        for role in ROLES:
            print(f"\t{role}:", getattr(user, role))


def manage_user_groups(
    username: str,
    granted: Optional[List[str]],
    revoked: Optional[List[str]],
):
    user = User.objects.get(username=username)
    print("User:", user.username)

    if granted:
        print("Granted groups:")
        for g in granted:
            group = Group.objects.get(name=g)
            user.groups.add(group)
            print(f"\t{group}")

    elif revoked:
        print("Revoked groups:")
        for g in revoked:
            group = Group.objects.get(name=g)
            user.groups.remove(group)
            print(f"\t{group}")

    else:
        print("Groups:")
        for group in user.groups.all():
            print(f"\t{group}")


def list_users():
    for user in User.objects.all():
        attrs = {
            "username": user.username,
            "email": user.email if user.email else "-----",
        }
        for role in ROLES:
            value = getattr(user, role)
            if value:
                attrs[role] = role.lower()
            else:
                attrs[role] = ("NOT_" + role.removeprefix("is_")).lower()

        groups = []

        # Filter user groups to determine all distinct (code, action, scope) pairs
        for project_action_scope in (
            user.groups.filter(projectgroup__isnull=False)
            .values(
                "projectgroup__project__code",
                "projectgroup__action",
                "projectgroup__scope",
            )
            .distinct()
        ):
            groups.append(
                f"{project_action_scope['projectgroup__project__code']}[{project_action_scope['projectgroup__action']}][{project_action_scope['projectgroup__scope']}]",
            )

        print(
            *attrs.values(),
            f":".join(groups),
            sep="\t",
        )


class Command(base.BaseCommand):
    help = "Manage users."

    def add_arguments(self, parser):
        command = parser.add_subparsers(
            dest="command", metavar="{command}", required=True
        )

        # CREATE A USER
        create_parser = command.add_parser("create", help="Create a user.")
        create_parser.add_argument("--username", required=True)
        create_parser.add_argument("--password", required=True)
        create_parser.add_argument("--site", required=True)
        create_parser.add_argument("--email", default="")
        create_parser.add_argument("--first-name", default="")
        create_parser.add_argument("--last-name", default="")

        # MANAGE USER ROLES
        roles_parser = command.add_parser("roles", help="Manage roles for a user.")
        roles_parser.add_argument("user")
        roles_action = roles_parser.add_mutually_exclusive_group()
        roles_action.add_argument("-g", "--grant", nargs="+")
        roles_action.add_argument("-r", "--revoke", nargs="+")

        # MANAGE USER GROUPS
        groups_parser = command.add_parser("groups", help="Manage groups for a user.")
        groups_parser.add_argument("user")
        groups_action = groups_parser.add_mutually_exclusive_group()
        groups_action.add_argument("-g", "--grant", nargs="+")
        groups_action.add_argument("-r", "--revoke", nargs="+")

        # LIST USERS
        list_parser = command.add_parser(
            "list",
            help="Print a table of all users, with their roles and project groups.",
        )

    def handle(self, *args, **options):
        if options["command"] == "create":
            create_user(
                username=options["username"],
                password=options["password"],
                site=options["site"],
                email=options["email"],
                first_name=options["first_name"],
                last_name=options["last_name"],
            )

        elif options["command"] == "roles":
            manage_user_roles(
                username=options["user"],
                granted=options.get("grant"),
                revoked=options.get("revoke"),
            )

        elif options["command"] == "groups":
            manage_user_groups(
                username=options["user"],
                granted=options.get("grant"),
                revoked=options.get("revoke"),
            )

        elif options["command"] == "list":
            list_users()
