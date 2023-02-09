from django.core.management import base
from accounts.models import User


class Command(base.BaseCommand):
    help = "View group(s) on a user."

    def add_arguments(self, parser):
        parser.add_argument("user")

    def handle(self, *args, **options):
        user = User.objects.get(username=options["user"])

        print("User:", user.username)

        print("Has access to groups:")
        for group in user.groups.all():
            print(group.name)
