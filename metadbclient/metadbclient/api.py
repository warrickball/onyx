import os
import sys
import csv
import json
import requests
from metadbclient import utils, settings
from metadbclient.field import Field
from metadbclient.config import Config


class Client:
    def __init__(self, config):
        """
        Initialise the client with a given config.
        """
        self.config = config
        self.url = f"http://{self.config.host}:{self.config.port}"
        self.endpoints = {
            # accounts
            "register": f"{self.url}/accounts/register/",
            "login": f"{self.url}/accounts/login/",
            "logout": f"{self.url}/accounts/logout/",
            "logoutall": f"{self.url}/accounts/logoutall/",
            "institute_approve": f"{self.url}/accounts/institute/approve/",
            "institute_waiting": f"{self.url}/accounts/institute/waiting/",
            "institute_users": f"{self.url}/accounts/institute/users/",
            "admin_approve": f"{self.url}/accounts/admin/approve/",
            "admin_waiting": f"{self.url}/accounts/admin/waiting/",
            "admin_users": f"{self.url}/accounts/admin/users/",
            # data
            "data": f"{self.url}/data/",
        }

    def request(self, method, **kwargs):
        kwargs.setdefault("headers", {}).update(
            {"Authorization": f"Token {self.token}"}
        )
        method_response = method(**kwargs)
        if method_response.status_code == 401:
            password = self.get_password()
            login_response = requests.post(
                self.endpoints["login"],
                auth=(self.username, password),
            )
            if login_response.ok:
                self.token = login_response.json().get("token")
                self.expiry = login_response.json().get("expiry")
                self.config.write_token(self.username, self.token, self.expiry)

                kwargs.setdefault("headers", {}).update(
                    {"Authorization": f"Token {self.token}"}
                )
                method_response = method(**kwargs)

            else:
                return login_response

        return method_response

    def register(self, first_name, last_name, email, institute, password):
        """
        Create a new user.
        """
        response = requests.post(
            self.endpoints["register"],
            json={
                "first_name": first_name,
                "last_name": last_name,
                "password": password,
                "email": email,
                "institute": institute,
            },
        )
        return response

    def continue_session(self, username=None, env_password=False):
        if username is None:
            # Attempt to use default_user if no username was provided
            if self.config.default_user is None:
                raise Exception(
                    "No username was provided and there is no default_user in the config. Either provide a username or set a default_user"
                )
            else:
                # The default_user must be in the config
                if self.config.default_user not in self.config.users:
                    raise Exception(
                        f"default_user '{self.config.default_user}' is not in the users list for the config"
                    )
                username = self.config.default_user
        else:
            # Username is case-insensitive
            username = username.lower()

            # The provided user must be in the config
            if username not in self.config.users:
                raise KeyError(
                    f"User '{username}' is not in the config. Add them using the add-user config command"
                )

        # Assign username to the client
        self.username = username

        # Assign flag indicating whether to look for user's password to the client
        self.env_password = env_password

        # Open the token file for the user and assign the current token, and its expiry, to the client
        with open(self.config.users[username]["token"]) as token_file:
            token_data = json.load(token_file)
            self.token = token_data.get("token")
            self.expiry = token_data.get("expiry")

        return username

    def get_password(self):
        if self.env_password:
            # If the password is meant to be an env var, grab it. If its not there, this is unintended so raise an error
            password_env_var = (
                settings.PASSWORD_ENV_VAR_PREFIX
                + self.username.upper()
                + settings.PASSWORD_ENV_VAR_POSTFIX
            )
            password = os.getenv(password_env_var)
            if password is None:
                raise KeyError(f"Environment variable '{password_env_var}' is not set")
        else:
            # Otherwise, prompt for the password
            print("Please enter your password.")
            password = utils.get_input("password", password=True)
        return password

    def login(self, username=None, env_password=False):
        """
        Log in as a particular user, get a new token and store the token in the client.

        If no user is provided, the `default_user` in the config is used.
        """

        # Load previous session
        # If no user was provided, the previous session of the default_user is used
        self.continue_session(username, env_password=env_password)

        if isinstance(self.token, str):
            # Log out the current token just in case
            # Is cleaner this way, I think so at least
            # Helps ensure each user of the config is tied to only one token at a particular time
            # Of course this is not a hard enforcement but slows users from spam creating new tokens they don't use
            # If a user needs logins on different machines, this is still possible via multiple configs
            response = self.request(
                method=requests.post,
                url=self.endpoints["logout"],
            )

        # Get the password
        password = self.get_password()

        # Log in
        response = requests.post(
            self.endpoints["login"], auth=(self.username, password)
        )
        if response.ok:
            self.token = response.json().get("token")
            self.expiry = response.json().get("expiry")
            self.config.write_token(self.username, self.token, self.expiry)

        return response

    @utils.session_required
    def logout(self):
        """
        Log out the user.
        """
        response = self.request(
            method=requests.post,
            url=self.endpoints["logout"],
        )
        if response.ok:
            self.token = None
            self.expiry = None
            self.config.write_token(self.username, self.token, self.expiry)

        return response

    @utils.session_required
    def logoutall(self):
        """
        Log out the user everywhere.
        """
        response = self.request(
            method=requests.post,
            url=self.endpoints["logoutall"],
        )
        if response.ok:
            self.token = None
            self.expiry = None
            self.config.write_token(self.username, self.token, self.expiry)

        return response

    @utils.session_required
    def institute_approve(self, username):
        """
        Institute-approve another user.
        """
        response = self.request(
            method=requests.patch,
            url=os.path.join(self.endpoints["institute_approve"], username + "/"),
        )
        return response

    @utils.session_required
    def institute_list_waiting(self):
        """
        List users waiting for institute approval.
        """
        response = self.request(
            method=requests.get, url=self.endpoints["institute_waiting"]
        )
        return response

    @utils.session_required
    def institute_list_users(self):
        """
        Get the current users within the institute of the requesting user.
        """
        response = self.request(
            method=requests.get, url=self.endpoints["institute_users"]
        )
        return response

    @utils.session_required
    def admin_approve(self, username):
        """
        Admin-approve another user.
        """
        response = self.request(
            method=requests.patch,
            url=os.path.join(self.endpoints["admin_approve"], username + "/"),
        )
        return response

    @utils.session_required
    def admin_list_waiting(self):
        """
        List users waiting for admin approval.
        """
        response = self.request(
            method=requests.get, url=self.endpoints["admin_waiting"]
        )
        return response

    @utils.session_required
    def admin_list_users(self):
        """
        List all users.
        """
        response = self.request(method=requests.get, url=self.endpoints["admin_users"])
        return response

    @utils.session_required
    def list_pathogen_codes(self):
        """
        List the current pathogens within the database.
        """
        response = self.request(
            method=requests.get, url=os.path.join(self.endpoints["data"], "pathogens/")
        )
        return response

    @utils.session_required
    def create(self, pathogen_code, fields=None, csv_path=None, delimiter=None):
        """
        Post new pathogen records to the database.
        """
        if (csv_path is not None) and (fields is not None):
            raise Exception("Cannot provide both fields and csv_path")

        if (csv_path is None) and (fields is None):
            raise Exception("Must provide either fields or csv_path")

        if csv_path is not None:
            if csv_path == "-":
                csv_file = sys.stdin
            else:
                csv_file = open(csv_path)
            try:
                if delimiter is None:
                    reader = csv.DictReader(csv_file)
                else:
                    reader = csv.DictReader(csv_file, delimiter=delimiter)

                for record in reader:
                    response = self.request(
                        method=requests.post,
                        url=os.path.join(self.endpoints["data"], pathogen_code + "/"),
                        json=record,
                    )
                    yield response

            finally:
                if csv_file is not sys.stdin:
                    csv_file.close()

        else:
            response = self.request(
                method=requests.post,
                url=os.path.join(self.endpoints["data"], pathogen_code + "/"),
                json=fields,
            )
            yield response

    @utils.session_required
    def get(self, pathogen_code, cid=None, fields=None, **kwargs):
        """
        Get records from the database.
        """
        if fields is None:
            fields = {}

        if cid is not None:
            fields.setdefault("cid", []).append(cid)

        for field, values in kwargs.items():
            if isinstance(values, list):
                for v in values:
                    if isinstance(v, tuple):
                        v = ",".join(str(x) for x in v)

                    fields.setdefault(field, []).append(v)
            else:
                if isinstance(values, tuple):
                    values = ",".join(str(x) for x in values)

                fields.setdefault(field, []).append(values)

        response = self.request(
            method=requests.get,
            url=os.path.join(self.endpoints["data"], pathogen_code + "/"),
            params=fields,
        )
        yield response

        if response.ok:
            _next = response.json()["next"]
        else:
            _next = None

        while _next is not None:
            response = self.request(
                method=requests.get,
                url=_next,
            )
            yield response

            if response.ok:
                _next = response.json()["next"]
            else:
                _next = None

    @utils.session_required
    def query(self, pathogen_code, query):
        """
        Get records from the database.
        """
        if not isinstance(query, Field):
            raise Exception("Query must be of type Field")

        response = self.request(
            method=requests.post,
            url=os.path.join(self.endpoints["data"], pathogen_code + "/query/"),
            json=query.query,
        )

        return response

    @utils.session_required
    def update(
        self, pathogen_code, cid=None, fields=None, csv_path=None, delimiter=None
    ):
        """
        Update pathogen records in the database.
        """
        if ((cid is not None) or (fields is not None)) and (csv_path is not None):
            raise Exception("Cannot provide both cid/fields and csv_path")

        if ((cid is None) or (fields is None)) and (csv_path is None):
            raise Exception("Must provide either cid and fields, or csv_path")

        if csv_path is not None:
            if csv_path == "-":
                csv_file = sys.stdin
            else:
                csv_file = open(csv_path)
            try:
                if delimiter is None:
                    reader = csv.DictReader(csv_file)
                else:
                    reader = csv.DictReader(csv_file, delimiter=delimiter)

                for record in reader:
                    cid = record.pop("cid", None)
                    if cid is None:
                        raise KeyError("cid column must be provided")

                    fields = record

                    response = self.request(
                        method=requests.patch,
                        url=os.path.join(self.endpoints["data"], pathogen_code + "/", cid + "/"),  # type: ignore
                        json=fields,
                    )
                    yield response
            finally:
                if csv_file is not sys.stdin:
                    csv_file.close()

        else:
            response = self.request(
                method=requests.patch,
                url=os.path.join(self.endpoints["data"], pathogen_code + "/", cid + "/"),  # type: ignore
                json=fields,
            )
            yield response

    @utils.session_required
    def suppress(self, pathogen_code, cid=None, csv_path=None, delimiter=None):
        """
        Suppress pathogen records in the database.
        """
        if (cid is not None) and (csv_path is not None):
            raise Exception("Cannot provide both cid and csv_path")

        if (cid is None) and (csv_path is None):
            raise Exception("Must provide either cid or csv_path")

        if csv_path is not None:
            if csv_path == "-":
                csv_file = sys.stdin
            else:
                csv_file = open(csv_path)
            try:
                if delimiter is None:
                    reader = csv.DictReader(csv_file)
                else:
                    reader = csv.DictReader(csv_file, delimiter=delimiter)

                for record in reader:
                    cid = record.get("cid")

                    if cid is None:
                        raise KeyError("cid column must be provided")

                    response = self.request(
                        method=requests.delete,
                        url=os.path.join(
                            self.endpoints["data"], pathogen_code + "/", cid + "/"
                        ),
                    )
                    yield response
            finally:
                if csv_file is not sys.stdin:
                    csv_file.close()

        else:
            response = self.request(
                method=requests.delete,
                url=os.path.join(
                    self.endpoints["data"], pathogen_code + "/", cid + "/"  # type: ignore
                ),
            )
            yield response


class Session:
    def __init__(self, username, env_password=False, login=False, logout=False):
        self.config = Config()
        self.client = Client(self.config)
        self.username = username
        self.env_password = env_password
        self.login = login
        self.logout = logout

    def __enter__(self):
        if self.login:
            response = self.client.login(self.username, env_password=self.env_password)
            response.raise_for_status()
        else:
            self.client.continue_session(self.username, env_password=self.env_password)
        return self.client

    def __exit__(self, type, value, traceback):
        if self.logout:
            self.client.logout()
