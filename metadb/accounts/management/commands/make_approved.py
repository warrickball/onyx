from django.core.management import base
from ...models import User


class Command(base.BaseCommand):
    help = "Grant user membership to the institute they claim to be from."

    def add_arguments(self, parser):
        parser.add_argument("username")

    def handle(self, *args, **options):
        username = options["username"]
        user = User.objects.get(username=username)

        user.is_approved = True
        user.save(update_fields=["is_approved"])

        user = User.objects.get(username=username)
        print("User:", user.username)
        print("is_approved:", user.is_approved)
