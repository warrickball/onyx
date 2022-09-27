from django.core.management import base
from ...models import User


class Command(base.BaseCommand):
    help = "Grant user the ability to approve other users within their institute."

    def add_arguments(self, parser):
        parser.add_argument("username")

    def handle(self, *args, **options):
        username = options["username"]
        user = User.objects.get(username=username)

        user.is_authority = True
        user.save(update_fields=["is_authority"])

        user = User.objects.get(username=options["username"])
        print("User:", user.username)
        print("is_authority:", user.is_authority)
