from django.core.management import base
from ...models import User


class Command(base.BaseCommand):
    help = "Alter a property on a user."

    def add_arguments(self, parser):
        parser.add_argument("username")
        parser.add_argument("property")
        action = parser.add_mutually_exclusive_group(required=True)
        action.add_argument("--grant", action="store_true", dest="action")
        action.add_argument("--revoke", action="store_false", dest="action")

    def handle(self, *args, **options):
        username = options["username"]
        property = options["property"]
        action = options["action"]

        user = User.objects.get(username=username)

        if not hasattr(user, property):
            raise Exception("Property is unknown")

        if property not in [
            "is_active",
            "is_site_approved",
            "is_admin_approved",
            "is_site_authority",
            "is_staff",
        ]:
            raise Exception("Property cannot be changed")

        setattr(user, property, action)
        user.save(update_fields=[property])

        user = User.objects.get(username=username)
        print("User:", user.username)
        print(f"{property}:", getattr(user, property))
