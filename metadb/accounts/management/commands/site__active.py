from django.core.management import base
from ...models import Site


class Command(base.BaseCommand):
    help = "Activate/deactivate an site."

    def add_arguments(self, parser):
        parser.add_argument("code")
        action = parser.add_mutually_exclusive_group(required=True)
        action.add_argument("--grant", action="store_true", dest="action")
        action.add_argument("--revoke", action="store_false", dest="action")

    def handle(self, *args, **options):
        code = options["code"]
        action = options["action"]

        site = Site.objects.get(code=code)
        site.is_active = action
        site.save(update_fields=["is_active"])

        site = Site.objects.get(code=code)
        print("Site:", site.code)
        print("is_active:", site.is_active)
