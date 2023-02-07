from django.core.management import base
from ...models import User


class Command(base.BaseCommand):
    help = "Grant/revoke a user's ability to approve other users within their site."

    def add_arguments(self, parser):
        parser.add_argument("username")
        action = parser.add_mutually_exclusive_group(required=True)
        action.add_argument("--grant", action="store_true", dest="action")
        action.add_argument("--revoke", action="store_false", dest="action")

    def handle(self, *args, **options):
        username = options["username"]
        action = options["action"]

        user = User.objects.get(username=username)
        user.site_authority = action
        user.save(update_fields=["site_authority"])

        user = User.objects.get(username=options["username"])
        print("User:", user.username)
        print("site_authority:", user.site_authority)
