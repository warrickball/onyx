from django.core.management import base
from ...models import Site


class Command(base.BaseCommand):
    help = "Grant/revoke an site's status as a public health agency."

    def add_arguments(self, parser):
        parser.add_argument("code")
        action = parser.add_mutually_exclusive_group(required=True)
        action.add_argument("--grant", action="store_true", dest="action")
        action.add_argument("--revoke", action="store_false", dest="action")

    def handle(self, *args, **options):
        code = options["code"]
        action = options["action"]

        site = Site.objects.get(code=code)
        site.is_pha = action
        site.save(update_fields=["is_pha"])

        site = Site.objects.get(code=code)
        print("Site:", site.code)
        print("is_pha:", site.is_pha)
