from django.core.management import base
from ...models import Site


class Command(base.BaseCommand):
    help = "Alter role(s) on a site."

    def add_arguments(self, parser):
        parser.add_argument("code")
        action = parser.add_mutually_exclusive_group(required=True)
        action.add_argument("-g", "--grant", nargs="+")
        action.add_argument("-r", "--revoke", nargs="+")
        action.add_argument("-l", "--list", action="store_true")

    def handle(self, *args, **options):
        site = Site.objects.get(code=options["code"])

        print("Site:", site.code)

        allowed = ["is_active"]

        if options.get("grant"):
            roles = []
            for role in options["grant"]:
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

        elif options.get("revoke"):
            roles = []
            for role in options["revoke"]:
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

        elif options.get("list"):
            print("Has access to roles:")
            for role in allowed:
                if getattr(site, role):
                    print(role)
