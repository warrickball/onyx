from django.core.management import base
from ...models import User


class Command(base.BaseCommand):
    help = "Alter role(s) on a user."

    def add_arguments(self, parser):
        parser.add_argument("user")
        action = parser.add_mutually_exclusive_group(required=True)
        action.add_argument("-g", "--grant", nargs="+")
        action.add_argument("-r", "--revoke", nargs="+")
        action.add_argument("-l", "--list", action="store_true")

    def handle(self, *args, **options):
        user = User.objects.get(username=options["user"])
        print("User:", user.username)

        allowed = [
            "is_active",
            "is_site_approved",
            "is_admin_approved",
            "is_site_authority",
            "is_staff",
        ]

        if options.get("grant"):
            roles = []
            for role in options["grant"]:
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

        elif options.get("revoke"):
            roles = []
            for role in options["revoke"]:
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

        elif options.get("list"):
            print("Roles:")
            for role in allowed:
                print(f"\t{role}:", getattr(user, role))
