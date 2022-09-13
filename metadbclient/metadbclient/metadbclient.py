import os
import sys
import csv
import stat
import json
import requests
import pandas as pd
from metadbclient import utils, settings


class METADBClient:
    def __init__(self, config_dir_path=None, cli=False):
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

        # Enables the class to be used as either an importable package or part of a CLI
        self.cli = cli

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
            # The provided user must be in the config
            if username not in self.config["users"]:
                raise KeyError(
                    f"User '{username}' is not in the config. Add them using the add-user command"
                )
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

        tokens_path = os.path.join(self.config_dir_path, f"{username}_tokens.json")
        self.config["users"][username] = {"tokens": tokens_path}

        # If this is the only user in the config, make them the default_user
        if len(self.config["users"]) == 1:
            self.config["default_user"] = username

        # Write user details to the config file
        # NOTE: Probably has issues if using the same client in multiple places
        with open(self.config_file_path, "w") as config:
            json.dump(self.config, config, indent=4)

        # Create user tokens file
        with open(tokens_path, "w") as tokens:
            json.dump({"access": None, "refresh": None}, tokens, indent=4)

        # Read-write for OS user only
        os.chmod(tokens_path, stat.S_IRUSR | stat.S_IWUSR)

        print("The user has been added to the config.")

    def set_default_user(self, username=None):
        if username is None:
            username = utils.get_input("username")

        if username not in self.config["users"]:
            raise KeyError(
                f"User '{username}' is not in the config. Add them using the add-user command"
            )

        self.config["default_user"] = username

        with open(self.config_file_path, "w") as config:
            json.dump(self.config, config, indent=4)

        print(f"'{username}' has been set as the default user.")

    def get_default_user(self):
        print(self.config["default_user"])

    def register(self, add_to_config=False):
        """
        Create a new user.
        """
        username = utils.get_input("username")
        email = utils.get_input("email address")
        institute = utils.get_input("institute code")

        match = False
        while not match:
            password = utils.get_input("password", password=True)
            password2 = utils.get_input("password (again)", password=True)
            if password == password2:
                match = True
            else:
                print("Passwords do not match. Please try again.")

        response = requests.post(
            self.endpoints["register"],
            json={
                "username": username,
                "password": password,  # type: ignore
                "email": email,
                "institute": institute,
            },
        )

        print(utils.format_response(response))

        if response.ok:
            print("Account created successfully.")

            if add_to_config:
                self.add_user(username)
            else:
                check = ""
                while not check:
                    check = input(
                        "Would you like to add this account to the config? [y/n]: "
                    ).upper()

                if check == "Y":
                    self.add_user(username)

    @utils.login_required
    def approve(self, username):
        """
        Approve another user on the server.
        """
        response = self.request(
            method=requests.patch,
            url=os.path.join(self.endpoints["approve"], username + "/"),
        )
        if self.cli:
            print(utils.format_response(response))
        else:
            try:
                return response.json()
            except json.decoder.JSONDecodeError:
                return response.text

    @utils.login_required
    def create(self, pathogen_code, csv_path=None, fields=None, delimiter=None):
        """
        Post new records to the database.
        """
        if (csv_path is not None) and (fields is not None):
            raise Exception(
                "Cannot provide both a csv file and fields dict at the same time"
            )

        if (csv_path is None) and (fields is None):
            raise Exception("Must provide a csv file or fields dict")

        responses = []

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
                    if self.cli:
                        print(utils.format_response(response))
                    else:
                        responses.append(response)
            finally:
                if csv_file is not sys.stdin:
                    csv_file.close()

        else:
            response = self.request(
                method=requests.post,
                url=os.path.join(self.endpoints["data"], pathogen_code + "/"),
                body=fields,
            )
            if self.cli:
                print(utils.format_response(response))
            else:
                responses.append(response)

        if self.cli:
            pass
        else:
            return responses

    @utils.login_required
    def get(self, pathogen_code, cid=None, fields=None):
        """
        Get records from the database.
        """
        if fields is None:
            fields = {}

        if cid is not None:
            if fields.get("cid") is None:
                fields["cid"] = []
            fields["cid"].append(cid)

        data = []

        response = self.request(
            method=requests.get,
            url=os.path.join(self.endpoints["data"], pathogen_code + "/"),
            params=fields,
        )
        if response.ok:
            table = pd.json_normalize(response.json()["results"])

            if self.cli:
                print(table.to_csv(index=False, sep="\t"), end="")
            else:
                data.extend(table.to_dict("records"))

            next = response.json()["next"]
            while next is not None:
                response = self.request(method=requests.get, url=next)
                if response.ok:
                    next = response.json()["next"]
                    table = pd.json_normalize(response.json()["results"])

                    if self.cli:
                        print(table.to_csv(index=False, sep="\t", header=False), end="")
                    else:
                        data.extend(table.to_dict("records"))
                else:
                    next = None
                    if self.cli:
                        print(utils.format_response(response))
                    else:
                        data.append(response)
        else:
            if self.cli:
                print(utils.format_response(response))
            else:
                data.append(response)

        if self.cli:
            pass
        else:
            return data

    # TODO: Update from a csv
    @utils.login_required
    def update(self, pathogen_code, cid, fields=None):
        """
        Update a record in the database.
        """
        if fields is None:
            fields = {}

        responses = []

        response = self.request(
            method=requests.patch,
            url=os.path.join(self.endpoints["data"], pathogen_code + "/", cid + "/"),
            body=fields,
        )
        if self.cli:
            print(utils.format_response(response))
        else:
            responses.append(response)
            return responses

    # TODO: Suppress from a csv
    @utils.login_required
    def suppress(self, pathogen_code, cid):
        """
        Suppress a record in the database.
        """
        responses = []

        response = self.request(
            method=requests.delete,
            url=os.path.join(self.endpoints["data"], pathogen_code + "/", cid + "/"),
        )
        if self.cli:
            print(utils.format_response(response))
        else:
            responses.append(response)
            return responses

    @utils.login_required
    def institute_users(self):
        """
        Get the current users within the institute of the requesting user.
        """
        response = self.request(
            method=requests.get, url=self.endpoints["institute-users"]
        )
        if self.cli:
            print(utils.format_response(response))
        else:
            try:
                return response.json()
            except json.decoder.JSONDecodeError:
                return response.text

    @utils.login_required
    def all_users(self):
        """
        Get all users.
        """
        response = self.request(method=requests.get, url=self.endpoints["all-users"])
        if self.cli:
            print(utils.format_response(response))
        else:
            try:
                return response.json()
            except json.decoder.JSONDecodeError:
                return response.text

    @utils.login_required
    def pathogen_codes(self):
        """
        Get the current pathogens within the database.
        """
        response = self.request(
            method=requests.get, url=self.endpoints["pathogen-codes"]
        )
        if self.cli:
            print(utils.format_response(response))
        else:
            try:
                return response.json()
            except json.decoder.JSONDecodeError:
                return response.text
