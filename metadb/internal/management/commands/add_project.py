from django.core.management import base
from django.contrib.auth.models import Group
from django.contrib.contenttypes.models import ContentType
from ...models import Project

class Command(base.BaseCommand):
    help = "Create a new project in the database."

    def add_arguments(self, parser):
        parser.add_argument("code")
        parser.add_argument("model")
        parser.add_argument("--hidden", action="store_true")

    def handle(self, *args, **options):
        app, model = options["model"].split(".")
        content_type = ContentType.objects.get(app_label=app, model=model)
        
        add_group = Group.objects.get(name=f"add_{options['code']}")
        view_group = Group.objects.get(name=f"view_{options['code']}")
        change_group = Group.objects.get(name=f"change_{options['code']}")
        suppress_group = Group.objects.get(name=f"suppress_{options['code']}")
        delete_group = Group.objects.get(name=f"delete_{options['code']}")
 
        project, created = Project.objects.get_or_create(
            code=options["code"],
            hidden=options["hidden"],
            content_type=content_type,
            add_group=add_group,
            view_group=view_group,
            change_group=change_group,
            suppress_group=suppress_group,
            delete_group=delete_group,
        )

        if created:
            print("Project created.")
        else:
            print("Project updated.")
        print("Name:", options["code"])
        print("Model:", content_type.model_class())
        