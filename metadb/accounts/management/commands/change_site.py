from django.core.management import base
from ...models import Site


class Command(base.BaseCommand):
    help = "Alter a property on a site."

    def add_arguments(self, parser):
        parser.add_argument("code")
        parser.add_argument("property")
        action = parser.add_mutually_exclusive_group(required=True)
        action.add_argument("--grant", action="store_true", dest="action")
        action.add_argument("--revoke", action="store_false", dest="action")

    def handle(self, *args, **options):
        code = options["code"]
        property = options["property"]
        action = options["action"]

        site = Site.objects.get(code=code)

        if not hasattr(site, property):
            raise Exception("Property is unknown")

        if property not in [
            "is_active",
        ]:
            raise Exception("Property cannot be changed")

        setattr(site, property, action)
        site.save(update_fields=[property])

        site = Site.objects.get(code=code)
        print("Site:", site.code)
        print(f"{property}:", getattr(site, property))
