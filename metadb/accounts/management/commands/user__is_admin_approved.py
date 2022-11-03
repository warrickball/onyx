from django.core.management import base
from ...models import User


class Command(base.BaseCommand):
    help = "Grant/revoke admin approval of a user."

    def add_arguments(self, parser):
        parser.add_argument("username")
        action = parser.add_mutually_exclusive_group(required=True)
        action.add_argument("--grant", action="store_true", dest="action")
        action.add_argument("--revoke", action="store_false", dest="action")

    def handle(self, *args, **options):
        username = options["username"]
        action = options["action"]

        user = User.objects.get(username=username)
        user.is_admin_approved = action
        user.save(update_fields=["is_admin_approved"])

        user = User.objects.get(username=username)
        print("User:", user.username)
        print("is_admin_approved:", user.is_admin_approved)
