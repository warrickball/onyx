from django.core.management import base
from accounts.models import User, Site
import os


class Command(base.BaseCommand):
    help = "Create a user in the database."

    def add_arguments(self, parser):
        parser.add_argument("--username", required=True)
        parser.add_argument("--email", required=True)
        parser.add_argument("--site", required=True)
        password_group = parser.add_mutually_exclusive_group(required=True)
        password_group.add_argument("--password")
        password_group.add_argument(
            "--password-env-var",
            help="Name of environment variable containing password.",
        )
        parser.add_argument("--first-name", default="")
        parser.add_argument("--last-name", default="")

    def handle(self, *args, **options):
        username = options["username"]
        email = options["email"]

        if options["password"]:
            password = options["password"]
        else:
            password = os.environ[options["password_env_var"]]

        if User.objects.filter(username=username).exists():
            print(f"User with username '{username}' already exists.")
            exit()

        if User.objects.filter(email=email).exists():
            print(f"User with email '{email}' already exists.")
            exit()

        site = Site.objects.get(code=options["site"])

        user = User.objects.create_user(
            username=options["username"],
            email=options["email"],
            password=password,
            site=site,
            first_name=options["first_name"],
            last_name=options["last_name"],
        )
        print("Created user:", user.username)
        print("\temail:", user.email)
        print("\tsite:", user.site.code)
