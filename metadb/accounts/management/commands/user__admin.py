from django.core.management import base
from ...models import User


class Command(base.BaseCommand):
    help = "Grant/revoke a user's ability to perform actions on data of other sites."

    def add_arguments(self, parser):
        parser.add_argument("username")
        action = parser.add_mutually_exclusive_group(required=True)
        action.add_argument("--grant", action="store_true", dest="action")
        action.add_argument("--revoke", action="store_false", dest="action")

    def handle(self, *args, **options):
        username = options["username"]
        action = options["action"]

        user = User.objects.get(username=username)
        user.is_staff = action
        user.save(update_fields=["is_staff"])

        user = User.objects.get(username=username)
        print("User:", user.username)
        print("is_staff:", user.is_staff)
