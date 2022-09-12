from django.core.management import base
from ...models import User


class Command(base.BaseCommand):
    help = "Grant user the abiltiy to approve other users within their institute."

    def add_arguments(self, parser):
        parser.add_argument("username")

    def handle(self, *args, **options):
        user = User.objects.get(username=options["username"])
        user.is_approved = True
        user.is_authority = True
        user.save()
        user = User.objects.get(username=options["username"])
        print("User:", user.username)
        print("is_approved:", user.is_approved)
        print("is_authority:", user.is_authority)
