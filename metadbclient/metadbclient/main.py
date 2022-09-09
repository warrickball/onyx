import os
import csv
import sys
import stat
import json
import time
import argparse
import requests
import pandas as pd
from getpass import getpass
from metadbclient.version import __version__


def timefunc(func):
    """
    Decorator for timing a function.
    """

    def timed_func(*args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)
        end = time.time()
        print(f"'{func.__name__}' took {round(end - start, 5)} seconds")
        return result

    return timed_func


def format_response(response, pretty_print=True):
    """
    Make the response look lovely.
    """
    if pretty_print:
        indent = 4
    else:
        indent = None
    status_code = f"<[{response.status_code}] {response.reason}>"
    try:
        return f"{status_code}\n{json.dumps(response.json(), indent=indent)}"
    except json.decoder.JSONDecodeError:
        return f"{status_code}\n{response.text}"


def get_input(field, password=False, type=None, required=True):
    """
    Get user input/password, ensuring they enter something.
    """
    if type is None:
        type = str
    if password:
        # User input is not displayed to the terminal with getpass
        input_func = getpass
    else:
        input_func = input
    try:
        # Take user input, strip it and convert to required type
        value = type(input_func(f"{field[0].upper()}{field[1:].lower()}: ").strip())
    except ValueError:
        value = ""
    if required:
        while not value:
            try:
                value = type(
                    input_func(f"Please enter a valid {field.lower()}: ").strip()
                )
            except ValueError:
                value = ""
    return value


def locate_config(config_dir_path=None):
    """
    If a `config_dir` was provided, confirm this is a directory containing a config file.

    Otherwise, use `METADBClient.CONFIG_DIR_ENV_VAR`, and confirm that this is a directory that contains a config file.
    """
    if config_dir_path:
        # Check config dir path is a directory
        if not os.path.isdir(config_dir_path):
            raise FileNotFoundError(f"'{config_dir_path}' does not exist")

        # Check config file path is a file
        config_file_path = os.path.join(config_dir_path, METADBClient.CONFIG_FILE_NAME)
        if not os.path.isfile(config_file_path):
            raise FileNotFoundError(
                f"Config file does not exist in directory '{config_dir_path}'"
            )

    else:
        # Find the config directory
        config_dir_path = os.getenv(METADBClient.CONFIG_DIR_ENV_VAR)
        if config_dir_path is None:
            raise KeyError(
                f"Environment variable '{METADBClient.CONFIG_DIR_ENV_VAR}' is not set"
            )

        # Check config dir path is a directory
        if not os.path.isdir(config_dir_path):
            raise FileNotFoundError(
                f"'{METADBClient.CONFIG_DIR_ENV_VAR}' points to a directory that does not exist"
            )

        # Check config file path is a file
        config_file_path = os.path.join(config_dir_path, METADBClient.CONFIG_FILE_NAME)
        if not os.path.isfile(config_file_path):
            raise FileNotFoundError(
                f"Config file does not exist in directory '{config_dir_path}'"
            )

    return config_dir_path, config_file_path


def validate_config(config):
    """
    Avoid a million KeyErrors due to problems with the config file.
    """
    for field in METADBClient.CONFIG_FIELDS:
        if field not in config:
            raise KeyError(f"'{field}' key is missing from the config file")

    for user, ufields in config["users"].items():
        for field in METADBClient.USER_FIELDS:
            if field not in ufields:
                raise KeyError(
                    f"'{field}' key is missing from user '{user}' in the config file"
                )


def login_required(method):
    """
    Decorator that does the following:

    * Checks the client object has user login details.
    * Runs the provided method and returns the output.
    * Writes user tokens to their tokens file, after running the provided method.
    """

    def wrapped_method(obj, *args, **kwargs):
        if not obj.has_login_details:
            raise Exception(
                "The client has no details to log in with. If you are using the client as a python import, please first log in with the 'get_login' command."
            )
        try:
            output = method(obj, *args, **kwargs)
        finally:
            with open(obj.config["users"][obj.username]["tokens"], "w") as tokens_file:
                json.dump(obj.tokens, tokens_file, indent=4)
        return output

    return wrapped_method


class METADBClient:
    CONFIG_DIR_NAME = "config"
    CONFIG_FILE_NAME = "config.json"
    CONFIG_DIR_ENV_VAR = "METADB_CONFIG_DIR"
    PASSWORD_ENV_VAR_PREFIX = "METADB_"
    PASSWORD_ENV_VAR_POSTFIX = "_PASSWORD"
    TOKENS_FILE_POSTFIX = "_tokens.json"
    CONFIG_FIELDS = ["host", "port", "users", "default_user"]
    USER_FIELDS = ["tokens"]
    MESSAGE_BAR_WIDTH = 100

    def __init__(self, config_dir_path=None, cli=False):
        # Locate the config
        config_dir_path, config_file_path = locate_config(
            config_dir_path=config_dir_path
        )

        # Load the config
        with open(config_file_path) as config_file:
            config = json.load(config_file)

        # Validate the config structure
        validate_config(config)

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

    @classmethod
    def make_config(cls):
        """
        Generate the config directory and config file.
        """
        host = get_input("host")
        port = get_input("port", type=int)
        config_dir_location = get_input("location to create a config directory")
        config_dir_location = config_dir_location.replace("~", os.path.expanduser("~"))
        if not os.path.isdir(config_dir_location):
            raise FileNotFoundError(f"No such directory: {config_dir_location}")

        config_dir_path = os.path.join(
            config_dir_location, METADBClient.CONFIG_DIR_NAME
        )
        if not os.path.isdir(config_dir_path):
            os.mkdir(config_dir_path)

        # Read-write-execute for OS user only
        os.chmod(config_dir_path, stat.S_IRUSR | stat.S_IWUSR | stat.S_IXUSR)

        config_file_path = os.path.join(config_dir_path, METADBClient.CONFIG_FILE_NAME)
        with open(config_file_path, "w") as config_file:
            json.dump(
                {"host": host, "port": port, "users": {}, "default_user": None},
                config_file,
                indent=4,
            )

        # Read-write for OS user only
        os.chmod(config_file_path, stat.S_IRUSR | stat.S_IWUSR)

        print("")
        print("Config directory and config file created successfully.")
        print(
            f"Please create the following environment variable by typing the following in your shell:"
        )
        print("")
        print(f"export METADB_CONFIG_DIR={config_dir_path}")
        print("")
        print(
            "IMPORTANT: DO NOT CHANGE CONFIG DIRECTORY PERMISSIONS".center(
                METADBClient.MESSAGE_BAR_WIDTH, "!"
            )
        )
        warning_message = [
            "Your config directory (and files within) store sensitive information such as tokens.",
            "They have been created with the permissions needed to keep your information safe.",
            "DO NOT CHANGE THESE PERMISSIONS. Doing so may allow other users to read your tokens!",
        ]
        for line in warning_message:
            print(line)
        print("".center(METADBClient.MESSAGE_BAR_WIDTH, "!"))

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
                METADBClient.PASSWORD_ENV_VAR_PREFIX
                + self.username.upper()
                + METADBClient.PASSWORD_ENV_VAR_POSTFIX
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
                    self.password = get_input("password", password=True)

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
            username = get_input("username")

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
            username = get_input("username")

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
        username = get_input("username")
        email = get_input("email address")
        institute = get_input("institute code")

        match = False
        while not match:
            password = get_input("password", password=True)
            password2 = get_input("password (again)", password=True)
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

        print(format_response(response))

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

    @login_required
    def approve(self, username):
        """
        Approve another user on the server.
        """
        response = self.request(
            method=requests.patch,
            url=os.path.join(self.endpoints["approve"], username + "/"),
        )
        if self.cli:
            print(format_response(response))
        else:
            try:
                return response.json()
            except json.decoder.JSONDecodeError:
                return response.text

    @login_required
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
                        print(format_response(response))
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
                print(format_response(response))
            else:
                responses.append(response)

        if self.cli:
            pass
        else:
            return responses

    @login_required
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
                        print(format_response(response))
                    else:
                        data.append(response)
        else:
            if self.cli:
                print(format_response(response))
            else:
                data.append(response)

        if self.cli:
            pass
        else:
            return data

    # TODO: Update from a csv
    @login_required
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
            print(format_response(response))
        else:
            responses.append(response)
            return responses

    # TODO: Suppress from a csv
    @login_required
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
            print(format_response(response))
        else:
            responses.append(response)
            return responses

    @login_required
    def institute_users(self):
        """
        Get the current users within the institute of the requesting user.
        """
        response = self.request(
            method=requests.get, url=self.endpoints["institute-users"]
        )
        if self.cli:
            print(format_response(response))
        else:
            try:
                return response.json()
            except json.decoder.JSONDecodeError:
                return response.text

    @login_required
    def all_users(self):
        """
        Get all users.
        """
        response = self.request(method=requests.get, url=self.endpoints["all-users"])
        if self.cli:
            print(format_response(response))
        else:
            try:
                return response.json()
            except json.decoder.JSONDecodeError:
                return response.text

    @login_required
    def pathogen_codes(self):
        """
        Get the current pathogens within the database.
        """
        response = self.request(
            method=requests.get, url=self.endpoints["pathogen-codes"]
        )
        if self.cli:
            print(format_response(response))
        else:
            try:
                return response.json()
            except json.decoder.JSONDecodeError:
                return response.text


def run():
    user_parser = argparse.ArgumentParser(add_help=False)
    user_parser.add_argument("-u", "--user")
    user_parser.add_argument("-p", "--use-password-env-var", action="store_true")

    parser = argparse.ArgumentParser()
    parser.add_argument("-v", "--version", action="version", version=__version__)
    parser.add_argument("-t", "--timeit", action="store_true")
    command = parser.add_subparsers(dest="command")

    # Create the config directory and config file
    make_config_parser = command.add_parser(
        "make-config", help="Make a config for the client."
    )

    # Create a user on the server
    register_parser = command.add_parser(
        "register", help="Create a new user in metadb."
    )

    # Approve another user on the server
    approve_parser = command.add_parser(
        "approve", parents=[user_parser], help="Approve another user in metadb."
    )
    approve_parser.add_argument("username")

    # Set default user in the config
    set_default_user_parser = command.add_parser(
        "set-default-user", help="Set the default user in the config of the client."
    )
    set_default_user_parser.add_argument("username", nargs="?")

    # List the default user in the config
    get_default_user_parser = command.add_parser(
        "get-default-user", help="Get the default user in the config of the client."
    )

    # Add a pre-existing user to the config
    add_user_parser = command.add_parser(
        "add-user", help="Add a pre-existing metadb user to the config of the client."
    )
    add_user_parser.add_argument("username", nargs="?")

    # List users within institute of the requesting user
    list_institute_users_parser = command.add_parser(
        "list-institute-users",
        parents=[user_parser],
        help="List all users within the institute of the requesting user.",
    )

    # List all users
    list_all_users_parser = command.add_parser(
        "list-all-users", parents=[user_parser], help="List all users in metadb."
    )

    # List all pathogen codes
    pathogen_codes_parser = command.add_parser(
        "list-pathogen-codes",
        parents=[user_parser],
        help="List all pathogen codes in metadb.",
    )

    # Upload pathogen metadata to the database
    create_parser = command.add_parser(
        "create", parents=[user_parser], help="Upload pathogen metadata to metadb."
    )
    create_parser.add_argument("pathogen_code")
    create_type = create_parser.add_mutually_exclusive_group(required=True)
    create_type.add_argument(
        "-f", "--field", nargs=2, action="append", metavar=("FIELD", "VALUE")
    )
    file_type = create_type.add_mutually_exclusive_group()
    file_type.add_argument("--csv")
    file_type.add_argument("--tsv")

    # Get pathogen metadata from the database
    get_parser = command.add_parser(
        "get", parents=[user_parser], help="Get pathogen metadata from metadb."
    )
    get_parser.add_argument("pathogen_code", help="required")
    get_parser.add_argument("cid", nargs="?", help="optional")
    get_parser.add_argument(
        "-f", "--field", nargs=2, action="append", metavar=("FIELD", "VALUE")
    )

    # Update pathogen metadata within the database
    update_parser = command.add_parser(
        "update", parents=[user_parser], help="Update pathogen metadata within metadb."
    )
    update_parser.add_argument("pathogen_code")
    update_parser.add_argument("cid")
    update_parser.add_argument(
        "-f", "--field", nargs=2, action="append", metavar=("FIELD", "VALUE")
    )

    # Suppress pathogen metadata within the database
    # Suppression means that the data will not be deleted, but will be hidden from users
    suppress_parser = command.add_parser(
        "suppress",
        parents=[user_parser],
        help="Suppress pathogen metadata within metadb.",
    )
    suppress_parser.add_argument("pathogen_code")
    suppress_parser.add_argument("cid")

    args = parser.parse_args()

    if args.command == "make-config":
        METADBClient.make_config()
    else:
        client = METADBClient(cli=True)

        # Commands that require a config, but no user login details
        if args.command == "register":
            client.register()

        elif args.command == "set-default-user":
            client.set_default_user(args.username)

        elif args.command == "get-default-user":
            client.get_default_user()

        elif args.command == "add-user":
            client.add_user(args.username)

        else:
            # Commands that require a config and user login details
            client.get_login(
                username=args.user, use_password_env_var=args.use_password_env_var
            )

            if args.command == "approve":
                client.approve(args.username)

            elif args.command == "create":
                if args.field is not None:
                    fields = {f: v for f, v in args.field}
                    client.create(args.pathogen_code, fields=fields)
                else:
                    if args.csv:
                        client.create(args.pathogen_code, csv_path=args.csv)
                    else:
                        client.create(
                            args.pathogen_code, csv_path=args.tsv, delimiter="\t"
                        )

            elif args.command == "get":
                fields = {}
                if args.field is not None:
                    for f, v in args.field:
                        if fields.get(f) is None:
                            fields[f] = []
                        fields[f].append(v)

                client.get(args.pathogen_code, args.cid, fields)

            elif args.command == "update":
                if args.field is not None:
                    fields = {f: v for f, v in args.field}
                else:
                    fields = {}

                client.update(args.pathogen_code, args.cid, fields)

            elif args.command == "suppress":
                client.suppress(args.pathogen_code, args.cid)

            elif args.command == "list-pathogen-codes":
                client.pathogen_codes()

            elif args.command == "list-institute-users":
                client.institute_users()

            elif args.command == "list-all-users":
                client.all_users()
