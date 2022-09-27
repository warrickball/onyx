from django.core.management import base
from ...models import User


# NOTE: Most cross-institute functionality has been torn out for the time being
# Will need implementing when/if users are granted ability to directly create/update/suppress data
class Command(base.BaseCommand):
    help = "Grant user the ability to perform actions on data of other institutes."

    def add_arguments(self, parser):
        parser.add_argument("username")

    def handle(self, *args, **options):
        username = options["username"]
        user = User.objects.get(username=username)

        user.is_staff = True
        user.save(update_fields=["is_staff"])

        user = User.objects.get(username=username)
        print("User:", user.username)
        print("is_staff:", user.is_staff)
