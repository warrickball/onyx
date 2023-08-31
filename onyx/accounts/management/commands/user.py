import os
from django.core.management import base
from django.contrib.auth.models import Group
from ...models import User, Site


def create_user(
    username, email, site, password, password_env_var, first_name, last_name
):
    if not password:
        password = os.environ[password_env_var]

    if User.objects.filter(username=username).exists():
        print(f"User with username '{username}' already exists.")
        exit()

    if User.objects.filter(email=email).exists():
        print(f"User with email '{email}' already exists.")
        exit()

    user = User.objects.create_user(  # type: ignore
        username=username,
        email=email,
        password=password,
        site=Site.objects.get(code=site),
        first_name=first_name,
        last_name=last_name,
    )
    print("Created user:", user.username)
    print("\temail:", user.email)
    print("\tsite:", user.site.code)


def manage_user_roles(username, granted, revoked):
    user = User.objects.get(username=username)
    print("User:", user.username)

    allowed = [
        "is_active",
        "is_site_approved",
        "is_admin_approved",
        "is_site_authority",
        "is_staff",
    ]

    if granted:
        roles = []
        for role in granted:
            if not hasattr(user, role):
                raise Exception("Role is unknown")

            if role not in allowed:
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

            if role not in allowed:
                raise Exception("Role cannot be changed")

            setattr(user, role, False)
            roles.append(role)

        user.save(update_fields=roles)
        print("Revoked roles:")
        for role in roles:
            print(f"\t{role}")

    else:
        print("Roles:")
        for role in allowed:
            print(f"\t{role}:", getattr(user, role))


def manage_user_groups(username, granted, revoked):
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


class Command(base.BaseCommand):
    help = "Create/manage users."

    def add_arguments(self, parser):
        command = parser.add_subparsers(
            dest="command", metavar="{command}", required=True
        )

        # CREATE A USER
        create_parser = command.add_parser("create", help="Create a user.")
        create_parser.add_argument("--username", required=True)
        create_parser.add_argument("--email", required=True)
        create_parser.add_argument("--site", required=True)
        password_group = create_parser.add_mutually_exclusive_group(required=True)
        password_group.add_argument("--password")
        password_group.add_argument(
            "--password-env-var",
            help="Name of environment variable containing password.",
        )
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

    def handle(self, *args, **options):
        if options["command"] == "create":
            create_user(
                username=options["username"],
                email=options["email"],
                site=options["site"],
                password=options["password"],
                password_env_var=options["password_env_var"],
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
