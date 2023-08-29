from django.core.management import base
from ...models import Site


def create_site(code, description):
    site, created = Site.objects.update_or_create(
        code=code.lower(), defaults={"description": description}
    )

    if created:
        print(f"Created site: {site.code}")
    else:
        print(f"Updated site: {site.code}")

    print("\tdescription:", site.description)


def manage_site_roles(code, granted, revoked):
    site = Site.objects.get(code=code)

    print("Site:", site.code)

    allowed = [
        "is_active",
    ]

    if granted:
        roles = []
        for role in granted:
            if not hasattr(site, role):
                raise Exception("Role is unknown")

            if role not in allowed:
                raise Exception("Role cannot be changed")

            setattr(site, role, True)
            roles.append(role)

        site.save(update_fields=roles)
        print("Granted access to roles:")
        for role in roles:
            print(role)

    elif revoked:
        roles = []
        for role in revoked:
            if not hasattr(site, role):
                raise Exception("Role is unknown")

            if role not in allowed:
                raise Exception("Role cannot be changed")

            setattr(site, role, False)
            roles.append(role)

        site.save(update_fields=roles)
        print("Revoked access to roles:")
        for role in roles:
            print(role)

    else:
        print("Has access to roles:")
        for role in allowed:
            if getattr(site, role):
                print(role)


class Command(base.BaseCommand):
    help = "Create/manage sites."

    def add_arguments(self, parser):
        command = parser.add_subparsers(
            dest="command", metavar="{command}", required=True
        )

        # CREATE A SITE
        create_parser = command.add_parser("create", help="Create a site.")
        create_parser.add_argument("code")
        create_parser.add_argument("-d", "--description")

        # MANAGE SITE ROLES
        roles_parser = command.add_parser("roles", help="Manage roles for a site.")
        roles_parser.add_argument("code")
        roles_action = roles_parser.add_mutually_exclusive_group()
        roles_action.add_argument("-g", "--grant", nargs="+")
        roles_action.add_argument("-r", "--revoke", nargs="+")

    def handle(self, *args, **options):
        if options["command"] == "create":
            create_site(
                code=options["code"],
                description=options["description"],
            )

        elif options["command"] == "roles":
            manage_site_roles(
                code=options["code"],
                granted=options.get("grant"),
                revoked=options.get("revoke"),
            )
