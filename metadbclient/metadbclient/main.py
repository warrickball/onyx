import os
import csv
import sys
import stat
import json
import time
import argparse
import requests
import pandas as pd
from datetime import datetime
from getpass import getpass
from metadbclient.version import __version__



def timefunc(func):
    '''
    Decorator for timing a function
    '''
    def timed_func(*args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)
        end = time.time()
        print(f"'{func.__name__}' took {round(end - start, 5)} seconds")
        return result
    return timed_func



def get_published_week_fields(published_week):
    '''
    Convert an ISO week of the format `YYYY-WW` into date filters that can be passed to the Django filter function
    '''
    fields = {
        "published_date__gte" : [],
        "published_date__lte" : []
    }
    try:
        for pub_week in published_week:
            year, week = pub_week.split("-")
            start_date = datetime.fromisocalendar(int(year), int(week), 1).date()
            end_date = datetime.fromisocalendar(int(year), int(week), 7).date()
            fields["published_date__gte"].append(start_date)
            fields["published_date__lte"].append(end_date)
    except ValueError:
        raise Exception("Invalid published week. Must be a possible week, provided in YYYY-WW format.")
    return fields



def get_published_week_range_fields(published_week_range):
    '''
    Convert an ISO week range of the format `[YYYY-WW, YYYY-WW]` into date filters that can be passed to the Django filter function
    '''
    fields = {
        "published_date__gte" : [],
        "published_date__lte" : []
    }
    try:
        for pub_week_range in published_week_range:
            s_year, s_week = pub_week_range[0].split("-")
            e_year, e_week = pub_week_range[1].split("-")
            start_date = datetime.fromisocalendar(int(s_year), int(s_week), 1).date()
            end_date = datetime.fromisocalendar(int(e_year), int(e_week), 7).date()
            fields["published_date__gte"].append(start_date)
            fields["published_date__lte"].append(end_date)
    except ValueError:
        raise Exception("Invalid published week. Must be a possible week, provided in YYYY-WW format.")
    return fields



def format_response(response, pretty_print=True):
    '''
    Make the response look lovely.
    '''
    if pretty_print:
        indent = 4
    else:
        indent = None
    status_code = f"<[{response.status_code}] {response.reason}>"
    try:
        return f"{status_code}\n{json.dumps(response.json(), indent=indent)}".center(METADBClient.MESSAGE_BAR_WIDTH, "=")
    except json.decoder.JSONDecodeError:
        return f"{status_code}\n{response.text}"



def get_input(field, password=False, type=None, required=True):
    '''
    Get user input/password, ensuring they enter something.
    '''
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
        value = None
    if required:
        while not value:
            try:
                value = type(input_func(f"Please enter a valid {field.lower()}: ").strip())
            except ValueError:
                value = None
    return value



class METADBClient:
    CONFIG_DIR_ENV_VAR = "METADB_CONFIG_DIR"
    CONFIG_DIR_NAME = "config"
    CONFIG_FILE_NAME = "config.json"
    PASSWORD_ENV_VAR_FIXES = ["METADB_", "_PASSWORD"]
    TOKENS_FILE_POSTFIX = "_tokens.json"
    CONFIG_FIELDS = ["host", "port", "users", "default_user"]
    USER_FIELDS = ["tokens"]
    MESSAGE_BAR_WIDTH = 100


    @classmethod
    def _locate_config(cls, config_dir_path=None):
        '''
        If a `config_dir` was provided, confirm this is a directory containing a config file.

        Otherwise, use `METADBClient.CONFIG_DIR_ENV_VAR`, and confirm that this is a directory that contains a config file.
        '''
        if config_dir_path:
            # Check config dir path is a directory
            if not os.path.isdir(config_dir_path):
                raise FileNotFoundError(f"'{config_dir_path}' does not exist")
            
            # Check config file path is a file
            config_file_path = os.path.join(config_dir_path, METADBClient.CONFIG_FILE_NAME)
            if not os.path.isfile(config_file_path):
                raise FileNotFoundError(f"Config file does not exist in directory '{config_dir_path}'")

        else:
            # Find the config directory
            config_dir_path = os.getenv(METADBClient.CONFIG_DIR_ENV_VAR)
            if config_dir_path is None:
                raise KeyError(f"Environment variable '{METADBClient.CONFIG_DIR_ENV_VAR}' is not set")
            
            # Check config dir path is a directory
            if not os.path.isdir(config_dir_path):
                raise FileNotFoundError(f"'{METADBClient.CONFIG_DIR_ENV_VAR}' points to a directory that does not exist")
            
            # Check config file path is a file
            config_file_path = os.path.join(config_dir_path, METADBClient.CONFIG_FILE_NAME)
            if not os.path.isfile(config_file_path):
                raise FileNotFoundError(f"Config file does not exist in directory '{config_dir_path}'")

        return config_dir_path, config_file_path


    @classmethod
    def _validate_config(cls, config):
        '''
        Avoid a million KeyErrors due to problems with the config file.
        '''
        for field in METADBClient.CONFIG_FIELDS:
            if field not in config:
                raise KeyError(f"'{field}' key is missing from the config file")

        for user, ufields in config["users"].items():
            for field in METADBClient.USER_FIELDS:
                if field not in ufields:
                    raise KeyError(f"'{field}' key is missing from user '{user}' in the config file")


    @classmethod
    def make_config(cls):
        '''
        Generate the config directory and config file.
        '''
        host = get_input("host")
        port = get_input("port", type=int)
        config_dir_location = get_input("location to create a config directory")
        config_dir_location = config_dir_location.replace("~", os.path.expanduser("~"))
        if not os.path.isdir(config_dir_location):
            raise FileNotFoundError(f"No such directory: {config_dir_location}")

        config_dir_path = os.path.join(config_dir_location, METADBClient.CONFIG_DIR_NAME)
        if not os.path.isdir(config_dir_path):
            os.mkdir(config_dir_path)
        
        # Read-write-execute for OS user only
        os.chmod(config_dir_path, stat.S_IRUSR | stat.S_IWUSR | stat.S_IXUSR)
        
        config_file_path = os.path.join(config_dir_path, METADBClient.CONFIG_FILE_NAME)
        with open(config_file_path, "w") as config_file:
            json.dump(
                {
                    "host" : host,
                    "port" : port,
                    "users" : {},
                    "default_user" : None
                },
                config_file, 
                indent=4
            )

        # Read-write for OS user only
        os.chmod(config_file_path, stat.S_IRUSR | stat.S_IWUSR)

        print("")
        print("Config directory and config file created successfully.")
        print(f"Please create the following environment variable by typing the following in your shell:") 
        print("")
        print(f"export METADB_CONFIG_DIR={config_dir_path}")
        print("")
        print("IMPORTANT: DO NOT CHANGE CONFIG DIRECTORY PERMISSIONS".center(METADBClient.MESSAGE_BAR_WIDTH, "!"))
        warning_message = [
            "Your config directory (and files within) store sensitive information such as tokens.",
            "They have been created with the permissions needed to keep your information safe.",
            "DO NOT CHANGE THESE PERMISSIONS. Doing so may allow other users to read your tokens!"
        ]
        for line in warning_message:
            print(line)
        print("".center(METADBClient.MESSAGE_BAR_WIDTH, "!"))


    def __init__(self, config_dir_path=None):
        # Locate the config
        config_dir_path, config_file_path = METADBClient._locate_config(config_dir_path=config_dir_path)

        # Load the config
        with open(config_file_path) as config_file:
            config = json.load(config_file)

        # Validate the config
        METADBClient._validate_config(config)

        # Set up client object
        self.config = config
        self.config_dir_path = config_dir_path
        self.config_file_path = config_file_path
        self.url = f"http://{self.config['host']}:{self.config['port']}"

        # Define endpoints
        self.endpoints = {
            "token-pair" : f"{self.url}/auth/token-pair/",
            "token-refresh" : f"{self.url}/auth/token-refresh/",
            "register" : f"{self.url}/accounts/register/",
            "data" : f"{self.url}/data/",
            "pathogen_codes" : f"{self.url}/data/pathogen_codes/",
        }


    def get_login(self, username=None):
        '''
        Assign username, tokens and (if stored in an env var) password to the client.

        If no username is provided, the `default_user` in the config is used.
        '''
        if username is None:
            # Attempt to use default_user if no username was provided
            if self.config["default_user"] is None:
                raise Exception("No username was provided and there is no default_user in the config. Either provide a username or set a default_user")
            else:
                # The default_user must be in the config
                if self.config["default_user"] not in self.config["users"]:
                    raise Exception(f"default_user '{self.config['default_user']}' is not in the users list for the config")
                username = self.config["default_user"]
        else:
            # The provided user must be in the config
            if username not in self.config["users"]:
                raise KeyError(f"User '{username}' is not in the config. Add them using the add-user command")    
        self.username = username

        # Grab a password from the env var, if it exists
        self.password = os.getenv(METADBClient.PASSWORD_ENV_VAR_FIXES[0] + self.username.upper() + METADBClient.PASSWORD_ENV_VAR_FIXES[1])
        
        # Open the tokens file for the user and assign their tokens
        with open(self.config["users"][username]["tokens"]) as tokens_file:
            self.tokens = json.load(tokens_file) 


    def _handle_tokens_request(self, method, url, params=None, body=None):
        '''
        Carry out a given request, refreshing tokens if required.
        '''
        if params is None:
            params = {}

        if body is None:
            body = {}
        
        # Make request with the current access token
        response = method(
            url=url,
            headers={"Authorization": "Bearer {}".format(self.tokens["access"])},
            params=params,
            json=body
        )

        # Handle token expiry
        if response.status_code == 401:
            # Get a new access token using the refresh token
            access_token_response = requests.post(
                self.endpoints["token-refresh"], 
                json={
                    "refresh" : self.tokens["refresh"],
                }
            )

            # Something went wrong with the refresh token
            if not access_token_response.ok:
                # Get the password if it doesn't already exist in the client
                if self.password is None:
                    print("Your refresh token is expired or invalid. Please enter your password to request new tokens.")
                    self.password = get_input("password", password=True)
                
                # Request a new access-refresh token pair
                token_pair_response = requests.post(
                    self.endpoints["token-pair"],
                    json={
                        "username" : self.username,
                        "password" : self.password
                    }
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
                json=body
            )

        return response


    def dump_tokens(self):
        '''
        Write user tokens to their tokens file.
        '''
        with open(self.config["users"][self.username]["tokens"], "w") as tokens_file:            
            json.dump(self.tokens, tokens_file, indent=4)


    def add_user(self, username=None):
        '''
        Add user to the config.
        '''
        if username is None:
            username = get_input("username")

        tokens_path = os.path.join(self.config_dir_path, f"{username}_tokens.json")
        self.config["users"][username] = {
            "tokens" : tokens_path
        }

        # If this is the only user in the config, make them the default_user
        if len(self.config["users"]) == 1:
            self.config["default_user"] = username
        
        # Write user details to the config file
        # NOTE: Probably has issues if using the same client in multiple places
        with open(self.config_file_path, "w") as config:
            json.dump(self.config, config, indent=4)
        
        # Create user tokens file
        with open(tokens_path, "w") as tokens:
            json.dump({"access" : None, "refresh" : None}, tokens, indent=4)
        
        # Read-write for OS user only
        os.chmod(tokens_path, stat.S_IRUSR | stat.S_IWUSR)

        print("The user has been added to the config.")  


    def register(self, add_to_config=False):
        '''
        Create a new user. 
        '''
        username = get_input("username")
        email = get_input("email address")
        institute = get_input("institute code").upper()
        
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
                "username" : username,
                "password" : password, # type: ignore
                "email" : email,
                "institute" : institute
            }
        )

        print(format_response(response))
        
        if response.ok:
            print("Account created successfully.")

            if add_to_config:
                self.add_user(username)
            else:
                check = ""
                while not check:
                    check = input("Would you like to add this account to the config? [y/n]: ").upper()
                
                if check == "Y":
                    self.add_user(username)


    def set_default_user(self, username=None):
        if username is None:
            username = get_input("username")

        if username not in self.config["users"]:
            raise KeyError(f"User '{username}' is not in the config. Add them using the add-user command")    

        self.config["default_user"] = username

        with open(self.config_file_path, "w") as config:
            json.dump(self.config, config, indent=4)
        
        print(f"'{username}' has been set as the default user.")


    def get_default_user(self):
        print(self.config["default_user"])
    

    def create(self, pathogen_code, tsv_path=None, fields=None):
        '''
        Post new records to the database.
        '''
        if (tsv_path is not None) and (fields is not None):
            raise Exception("Cannot provide both a tsv file and fields dict at the same time")

        if (tsv_path is None) and (fields is None):
            raise Exception("Must provide a tsv file or fields dict")

        if tsv_path is not None:
            if tsv_path == '-':
                tsv = sys.stdin
            else:
                tsv = open(tsv_path)
            try:
                reader = csv.DictReader(tsv, delimiter='\t')
                for record in reader:
                    response = self._handle_tokens_request(
                        method=requests.post,
                        url=os.path.join(self.endpoints["data"], pathogen_code + "/"),
                        body=record
                    )
                    print(format_response(response))
            finally:
                if tsv is not sys.stdin:
                    tsv.close()
        else:
            response = self._handle_tokens_request(
                method=requests.post,
                url=os.path.join(self.endpoints["data"], pathogen_code + "/"),
                body=fields
            )
            print(format_response(response))
            

    def get(self, pathogen_code, cid=None, fields=None, published_week=None, published_week_range=None, stats=None):
        '''
        Get records from the database. 
        '''        
        if fields is None:
            fields = {}
        
        if cid is not None:
            if fields.get("cid") is None:
                fields["cid"] = []
            fields["cid"].append(cid)
        
        if published_week:
            published_week_fields = get_published_week_fields(published_week)
            for f, v in published_week_fields.items():
                if fields.get(f) is None:
                    fields[f] = []
                fields[f].extend(v)
        
        if published_week_range:
            published_week_range_fields = get_published_week_range_fields(published_week_range)
            for f, v in published_week_range_fields.items():
                if fields.get(f) is None:
                    fields[f] = []
                fields[f].extend(v)
        
        if stats is not None:
            fields["stats"] = stats
        
        response = self._handle_tokens_request(
            method=requests.get,
            url=os.path.join(self.endpoints["data"], pathogen_code + "/"),
            params=fields
        )
        if response.ok:
            table = pd.json_normalize(response.json()["results"])
            print(table.to_csv(index=False, sep='\t'), end='')
            next = response.json()["next"]
            while next is not None:
                response = self._handle_tokens_request(
                    method=requests.get,
                    url=next
                )            
                if response.ok:
                    next = response.json()["next"]
                    table = pd.json_normalize(response.json()["results"])
                    print(table.to_csv(index=False, sep='\t', header=False), end='')
                else:
                    next = None
                    print(format_response(response))
        else:
            print(format_response(response))


    def update(self, pathogen_code, cid, fields=None):
        '''
        Update a record in the database.
        '''        
        if fields is None:
            fields = {}

        response = self._handle_tokens_request(
            method=requests.patch,
            url=os.path.join(self.endpoints["data"], pathogen_code + "/", cid + "/"),
            body=fields
        )
        print(format_response(response))

    
    def suppress(self, pathogen_code, cid):
        '''
        Suppress a record in the database.
        '''        
        response = self._handle_tokens_request(
            method=requests.delete,
            url=os.path.join(self.endpoints["data"], pathogen_code + "/", cid + "/")
        )
        print(format_response(response))


    def pathogen_codes(self):
        '''
        Get the current pathogens within the database.
        '''        
        response = self._handle_tokens_request(
            method=requests.get,
            url=self.endpoints["pathogen_codes"]
        )
        print(format_response(response))



def run():
    # TODO: Return metadata in tsv
    user_parser = argparse.ArgumentParser(add_help=False)
    user_parser.add_argument("-u", "--user")

    parser = argparse.ArgumentParser()
    parser.add_argument("-v", "--version", action="version", version=__version__)
    parser.add_argument("-t", "--timeit", action="store_true")
    command = parser.add_subparsers(dest="command")

    make_config_parser = command.add_parser("make-config")

    register_parser = command.add_parser("register")

    set_default_user_parser = command.add_parser("set-default-user")
    set_default_user_parser.add_argument("user", nargs="?")
    
    get_default_user_parser = command.add_parser("get-default-user")
    
    add_user_parser = command.add_parser("add-user")
    add_user_parser.add_argument("user", nargs="?")
    
    create_parser = command.add_parser("create", parents=[user_parser])
    create_type = create_parser.add_mutually_exclusive_group(required=True)
    create_parser.add_argument("pathogen_code")
    create_type.add_argument("-f", "--field", nargs=2, action="append", metavar=("FIELD", "VALUE"))
    create_type.add_argument("--tsv")

    get_parser = command.add_parser("get", parents=[user_parser])
    get_parser.add_argument("pathogen_code", help="required")
    get_parser.add_argument("cid", nargs="?", help="optional")
    get_parser.add_argument("-f", "--field", nargs=2, action="append", metavar=("FIELD", "VALUE"))
    get_parser.add_argument("--published-week", action="append", metavar="YYYY-WW")
    get_parser.add_argument("--published-week-range", nargs=2, action="append", metavar=("YYYY-WW", "YYYY-WW"))
    get_parser.add_argument("--stats", action="store_true")

    update_parser = command.add_parser("update", parents=[user_parser])
    update_parser.add_argument("pathogen_code")
    update_parser.add_argument("cid")
    update_parser.add_argument("-f", "--field", nargs=2, action="append", metavar=("FIELD", "VALUE"))

    suppress_parser = command.add_parser("suppress", parents=[user_parser])
    suppress_parser.add_argument("pathogen_code")
    suppress_parser.add_argument("cid")

    pathogen_codes_parser = command.add_parser("pathogen-codes", parents=[user_parser])

    args = parser.parse_args()

    if args.command == "make-config":
        METADBClient.make_config()
    else:
        client = METADBClient()

        if args.command == "register":
            client.register()
        
        elif args.command == "set-default-user":
            client.set_default_user(args.user)
        
        elif args.command == "get-default-user":
            client.get_default_user()

        elif args.command == "add-user":
            client.add_user(args.user)

        else:
            try:                
                client.get_login(username=args.user)

                if args.command == "create":
                    if args.field is not None:
                        fields = {f : v for f, v in args.field}
                        client.create(args.pathogen_code, fields=fields)
                    else:
                        client.create(args.pathogen_code, tsv_path=args.tsv)
                
                elif args.command == "get":
                    fields = {}
                    if args.field is not None:
                        for f, v in args.field:
                            if fields.get(f) is None:
                                fields[f] = []
                            fields[f].append(v)
                    client.get(args.pathogen_code, args.cid, fields, published_week=args.published_week, published_week_range=args.published_week_range, stats=args.stats)
                
                elif args.command == "update":
                    if args.field is not None:
                        fields = {f : v for f, v in args.field}
                    else:
                        fields = {}
                    client.update(args.pathogen_code, args.cid, fields)

                elif args.command == "suppress":
                    client.suppress(args.pathogen_code, args.cid)
                
                elif args.command == "pathogen-codes":
                    client.pathogen_codes()
                
            finally:
                client.dump_tokens()
