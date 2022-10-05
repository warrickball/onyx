import os
import sys
import csv
import stat
import json
import requests
from metadbclient import utils, settings


class METADBClient:
    def __init__(self, config_dir_path=None):
        """
        Initialise the client, and connect it to a config directory.

        If a `config_dir_path` was not provided, looks for the environment variable given by `settings.CONFIG_DIR_ENV_VAR`.
        """

        # Locate the config
        config_dir_path, config_file_path = utils.locate_config(
            config_dir_path=config_dir_path
        )

        # Load the config
        with open(config_file_path) as config_file:
            config = json.load(config_file)

        # Validate the config structure
        utils.validate_config(config)

        # Set up the client object
        self.config = config
        self.config_dir_path = config_dir_path
        self.config_file_path = config_file_path
        self.url = f"http://{self.config['host']}:{self.config['port']}"

        # Define API endpoints
        self.endpoints = {
            "token-pair": f"{self.url}/auth/token-pair/",
            "token-refresh": f"{self.url}/auth/token-refresh/",
            "register": f"{self.url}/accounts/register/",
            "approve": f"{self.url}/accounts/approve/",
            "institute-users": f"{self.url}/accounts/institute-users/",
            "all-users": f"{self.url}/accounts/all-users/",
            "data": f"{self.url}/data/",
            "pathogen-codes": f"{self.url}/data/pathogen-codes/",
        }

        # No user login details have been assigned to the client yet
        self.has_login_details = False

    def get_login(self, username=None, use_password_env_var=False):
        """
        Assign username, tokens and (if stored in an env var) password to the client.

        If no username is provided, the `default_user` in the config is used.
        """
        if username is None:
            # Attempt to use default_user if no username was provided
            if self.config["default_user"] is None:
                raise Exception(
                    "No username was provided and there is no default_user in the config. Either provide a username or set a default_user"
                )
            else:
                # The default_user must be in the config
                if self.config["default_user"] not in self.config["users"]:
                    raise Exception(
                        f"default_user '{self.config['default_user']}' is not in the users list for the config"
                    )
                username = self.config["default_user"]
        else:
            # Username is case-insensitive
            username = username.lower()

            # The provided user must be in the config
            if username not in self.config["users"]:
                raise KeyError(
                    f"User '{username}' is not in the config. Add them using the add-user command"
                )

        # Assign username to the client
        self.username = username

        # If the password is meant to be an env var, grab it. If its not there, this is unintended so raise an error
        if use_password_env_var:
            password_env_var = (
                settings.PASSWORD_ENV_VAR_PREFIX
                + self.username.upper()
                + settings.PASSWORD_ENV_VAR_POSTFIX
            )
            password = os.getenv(password_env_var)
            if password is None:
                raise KeyError(f"Environment variable '{password_env_var}' is not set")
            self.password = password
        else:
            self.password = None

        # Open the tokens file for the user and assign their tokens
        with open(self.config["users"][username]["tokens"]) as tokens_file:
            self.tokens = json.load(tokens_file)

        # The client now has details to log in with (correct or not)
        self.has_login_details = True

    def request(self, method, url, params=None, body=None):
        """
        Carry out a given request, refreshing tokens if required.
        """
        if params is None:
            params = {}

        if body is None:
            body = {}

        # Make request with the current access token
        response = method(
            url=url,
            headers={"Authorization": "Bearer {}".format(self.tokens["access"])},
            params=params,
            json=body,
        )

        # Handle token expiry
        if response.status_code == 401:
            # Get a new access token using the refresh token
            access_token_response = requests.post(
                self.endpoints["token-refresh"],
                json={
                    "refresh": self.tokens["refresh"],
                },
            )

            # Something went wrong with the refresh token
            if not access_token_response.ok:
                # Get the password if it doesn't already exist in the client
                if self.password is None:
                    print(
                        "Your refresh token has expired or is invalid. Please enter your password to request new tokens."
                    )
                    self.password = utils.get_input("password", password=True)

                # Request a new access-refresh token pair
                token_pair_response = requests.post(
                    self.endpoints["token-pair"],
                    json={"username": self.username, "password": self.password},
                )

                if token_pair_response.ok:
                    self.tokens = token_pair_response.json()
                else:
                    # Who knows what is happening, return the issue back to user
                    return token_pair_response
            else:
                self.tokens["access"] = access_token_response.json()["access"]

            # Now that we have our updated tokens, retry the request and return whatever response is given
            response = method(
                url=url,
                headers={"Authorization": "Bearer {}".format(self.tokens["access"])},
                params=params,
                json=body,
            )

        return response

    def add_user(self, username=None):
        """
        Add user to the config.
        """
        if username is None:
            username = utils.get_input("username")

        # Username is case-insensitive
        username = username.lower()

        tokens_path = os.path.join(self.config_dir_path, f"{username}_tokens.json")
        self.config["users"][username] = {"tokens": tokens_path}

        # Reload the config incase its changed
        # Not perfect but better than just blanket overwriting the file
        config_dir_path, config_file_path = utils.locate_config(
            config_dir_path=self.config_dir_path
        )
        self.config_dir_path = config_dir_path
        self.config_file_path = config_file_path

        # Load the config
        with open(self.config_file_path) as current_config_file:
            current_config = json.load(current_config_file)

        # Validate the config structure
        utils.validate_config(current_config)

        # Update the config
        self.config["host"] = current_config["host"]
        self.config["port"] = current_config["port"]
        self.config["users"].update(current_config["users"])

        # If there is only one user in the config, make them the default_user
        if len(self.config["users"]) == 1:
            self.config["default_user"] = username
        else:
            self.config["default_user"] = current_config["default_user"]

        # Write to the config file
        with open(self.config_file_path, "w") as config:
            json.dump(self.config, config, indent=4)

        # Create user tokens file
        with open(tokens_path, "w") as tokens:
            json.dump({"access": None, "refresh": None}, tokens, indent=4)

        # Read-write for OS user only
        os.chmod(tokens_path, stat.S_IRUSR | stat.S_IWUSR)

    def set_default_user(self, username=None):
        """
        Set the default user in the config.
        """
        if username is None:
            username = utils.get_input("username")

        # Username is case-insensitive
        username = username.lower()

        if username not in self.config["users"]:
            raise KeyError(
                f"User '{username}' is not in the config. Add them using the add-user command"
            )

        self.config["default_user"] = username

        with open(self.config_file_path, "w") as config:
            json.dump(self.config, config, indent=4)

    def get_default_user(self):
        """
        Get the default user in the config.
        """
        return self.config["default_user"]

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

    @utils.login_required
    def approve(self, username):
        """
        Approve another user on the server.
        """
        response = self.request(
            method=requests.patch,
            url=os.path.join(self.endpoints["approve"], username + "/"),
        )
        return response

    @utils.login_required
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
                        body=record,
                    )
                    yield response

            finally:
                if csv_file is not sys.stdin:
                    csv_file.close()

        else:
            response = self.request(
                method=requests.post,
                url=os.path.join(self.endpoints["data"], pathogen_code + "/"),
                body=fields,
            )
            yield response

    @utils.login_required
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
            response = self.request(method=requests.get, url=_next)
            yield response

            if response.ok:
                _next = response.json()["next"]
            else:
                _next = None

    @utils.login_required
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
                        body=fields,
                    )
                    yield response
            finally:
                if csv_file is not sys.stdin:
                    csv_file.close()

        else:
            response = self.request(
                method=requests.patch,
                url=os.path.join(self.endpoints["data"], pathogen_code + "/", cid + "/"),  # type: ignore
                body=fields,
            )
            yield response

    @utils.login_required
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

    @utils.login_required
    def institute_users(self):
        """
        Get the current users within the institute of the requesting user.
        """
        response = self.request(
            method=requests.get, url=self.endpoints["institute-users"]
        )
        return response

    @utils.login_required
    def all_users(self):
        """
        Get all users.
        """
        response = self.request(method=requests.get, url=self.endpoints["all-users"])
        return response

    @utils.login_required
    def pathogen_codes(self):
        """
        Get the current pathogens within the database.
        """
        response = self.request(
            method=requests.get, url=self.endpoints["pathogen-codes"]
        )
        return response
