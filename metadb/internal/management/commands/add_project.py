from django.core.management import base
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from ...models import Project

class Command(base.BaseCommand):
    help = "Create a new project in the database."

    def add_arguments(self, parser):
        parser.add_argument("code")
        parser.add_argument("model")
        parser.add_argument("--hidden", action="store_true")

    def handle(self, *args, **options):
        code = options["code"].lower()
        app, model = options["model"].split(".")
        content_type = ContentType.objects.get(app_label=app, model=model)
        
        add_group = Group.objects.get(name=f"add_{code}")
        view_group = Group.objects.get(name=f"view_{code}")
        change_group = Group.objects.get(name=f"change_{code}")
        suppress_group = Group.objects.get(name=f"suppress_{code}")
        delete_group = Group.objects.get(name=f"delete_{code}")
 
        project, created = Project.objects.get_or_create(
            code=code,
            hidden=options["hidden"],
            content_type=content_type,
            add_group=add_group,
            view_group=view_group,
            change_group=change_group,
            suppress_group=suppress_group,
            delete_group=delete_group,
        )

        project_content_type = ContentType.objects.get(app_label="internal", model="project")
        add, _ = Permission.objects.get_or_create(codename=f"add_project_{code}",name=f"Can add {code}",content_type=project_content_type)
        view, _ = Permission.objects.get_or_create(codename=f"view_project_{code}",name=f"Can view {code}",content_type=project_content_type)
        change, _ = Permission.objects.get_or_create(codename=f"change_project_{code}",name=f"Can change {code}",content_type=project_content_type)
        suppress, _ = Permission.objects.get_or_create(codename=f"suppress_project_{code}",name=f"Can suppress {code}",content_type=project_content_type)
        delete, _ = Permission.objects.get_or_create(codename=f"delete_project_{code}",name=f"Can delete {code}",content_type=project_content_type)

        add_group.permissions.add(add)
        view_group.permissions.add(view)
        change_group.permissions.add(change)
        suppress_group.permissions.add(suppress)
        delete_group.permissions.add(delete)

        if created:
            print("Project created.")
        else:
            print("Project updated.")
        print("Name:", code)
        print("Model:", content_type.model_class())
        