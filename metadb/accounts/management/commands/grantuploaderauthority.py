from django.core.management import base
from ...models import User


class Command(base.BaseCommand):
    help = "Grant user permission to uploader approve other users."

    def add_arguments(self, parser):
        parser.add_argument("username")

    def handle(self, *args, **options):
        user = User.objects.get(username=options["username"])
        user.is_uploader_approved = True
        user.is_uploader_authority = True
        user.save()
