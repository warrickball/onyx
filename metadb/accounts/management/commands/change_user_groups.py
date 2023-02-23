from django.core.management import base
from django.contrib.auth.models import Group
from accounts.models import User


class Command(base.BaseCommand):
    help = "Alter group(s) on a user."

    def add_arguments(self, parser):
        parser.add_argument("user")
        parser.add_argument("group", nargs="+")
        action = parser.add_mutually_exclusive_group(required=True)
        action.add_argument("--grant", action="store_true", dest="action")
        action.add_argument("--revoke", action="store_false", dest="action")

    def handle(self, *args, **options):
        user = User.objects.get(username=options["user"])
        grant = options["action"]

        print("User:", user.username)

        if grant:
            print("Granted access to groups:")
            for g in options["group"]:
                group = Group.objects.get(name=g)
                user.groups.add(group)
                print(group)

        else:
            print("Revoked access to groups:")
            for g in options["group"]:
                group = Group.objects.get(name=g)
                user.groups.remove(group)
                print(group)
