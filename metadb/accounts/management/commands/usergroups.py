from django.core.management import base
from django.contrib.auth.models import Group
from accounts.models import User


class Command(base.BaseCommand):
    help = "Alter group(s) on a user."

    def add_arguments(self, parser):
        parser.add_argument("user")
        action = parser.add_mutually_exclusive_group(required=True)
        action.add_argument("-g", "--grant", nargs="+")
        action.add_argument("-r", "--revoke", nargs="+")
        action.add_argument("-l", "--list", action="store_true")

    def handle(self, *args, **options):
        user = User.objects.get(username=options["user"])
        print("User:", user.username)

        if options.get("grant"):
            print("Granted access to groups:")
            for g in options["grant"]:
                group = Group.objects.get(name=g)
                user.groups.add(group)
                print(group)

        elif options.get("revoke"):
            print("Revoked access to groups:")
            for g in options["revoke"]:
                group = Group.objects.get(name=g)
                user.groups.remove(group)
                print(group)

        elif options.get("list"):
            print("Has access to groups:")
            for group in user.groups.all():
                print(group.name)
