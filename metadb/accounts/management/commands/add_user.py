from django.core.management import base
from accounts.serializers import UserSerializer
import json
import os


class Command(base.BaseCommand):
    help = "Create a new user in the database."

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

    def handle(self, *args, **options):
        username = options["username"]
        email = options["email"]
        site = options["site"]

        if options["password"]:
            password = options["password"]
        else:
            password = os.environ[options["password_env_var"]]

        data = {
            "username": username,
            "email": email,
            "site": site,
            "password": password,
        }
        serializer = UserSerializer(data=data)  # type: ignore

        if serializer.is_valid():
            serializer.save()
            print(f"Created user: {username}")
        else:
            print(json.dumps(serializer.errors, indent=4))
