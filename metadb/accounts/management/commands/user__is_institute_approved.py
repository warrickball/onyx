from django.core.management import base
from ...models import User


class Command(base.BaseCommand):
    help = "Grant/revoke a user's membership to the institute they claim to be from."

    def add_arguments(self, parser):
        parser.add_argument("username")
        action = parser.add_mutually_exclusive_group(required=True)
        action.add_argument("--grant", action="store_true", dest="action")
        action.add_argument("--revoke", action="store_false", dest="action")

    def handle(self, *args, **options):
        username = options["username"]
        action = options["action"]

        user = User.objects.get(username=username)
        user.is_institute_approved = action
        user.save(update_fields=["is_institute_approved"])

        user = User.objects.get(username=username)
        print("User:", user.username)
        print("is_institute_approved:", user.is_institute_approved)
