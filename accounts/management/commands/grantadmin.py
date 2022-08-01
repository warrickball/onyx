from django.core.management import base
from ...models import User


class Command(base.BaseCommand):
    help = "Make user an admin."

    def add_arguments(self, parser):
        parser.add_argument("username")

    def handle(self, *args, **options):
        print("NOTE: This makes a user an admin, not an authority of their institute.")
        
        check = ""
        while not check:
            check = input("Are you sure you want to do this? [y/n]: ").upper()
        if check == "Y":
            user = User.objects.get(username=options["username"])
            user.is_staff = True
            user.save()
            user = User.objects.get(username=options["username"])
            print("User:", user.username)
            print("is_staff:", user.is_staff)
