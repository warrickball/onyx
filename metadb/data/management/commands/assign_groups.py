from django.core.management import base
from django.contrib.auth.models import Group
from accounts.models import User


class Command(base.BaseCommand):
    help = "Assign a group to a user"

    def add_arguments(self, parser):
        parser.add_argument("user")
        parser.add_argument("group", nargs="+")

    def handle(self, *args, **options):
        user = User.objects.get(username=options["user"])

        for g in options["group"]:
            group = Group.objects.get(name=g)
            user.groups.add(group)
