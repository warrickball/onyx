from django.core.management import base
from ...models import Institute


class Command(base.BaseCommand):
    help = "Grant/revoke an institute's status as a public health agency."

    def add_arguments(self, parser):
        parser.add_argument("code")
        action = parser.add_mutually_exclusive_group(required=True)
        action.add_argument("--grant", action="store_true", dest="action")
        action.add_argument("--revoke", action="store_false", dest="action")

    def handle(self, *args, **options):
        code = options["code"]
        action = options["action"]

        institute = Institute.objects.get(code=code)
        institute.is_pha = action
        institute.save(update_fields=["is_pha"])

        institute = Institute.objects.get(code=code)
        print("Institute:", institute.code)
        print("is_pha:", institute.is_pha)
