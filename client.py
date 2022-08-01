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


class Client:
    # Constants shared across every client
    CONFIG_DIR_ENV_VAR = "METADB_CONFIG_DIR"
    CONFIG_DIR_NAME = "config"
    CONFIG_FILE_NAME = "config.json"
    TOKENS_FILE_POSTFIX = "_tokens.json"
    CONFIG_FIELDS = ["host", "port", "users", "default_user"]
    USER_FIELDS = ["password", "tokens"]


    @classmethod
    def _format_response(cls, response, pretty_print=True):
        '''
        Make the response look nice
        '''
        if pretty_print:
            return f"<[{response.status_code}] {response.reason}>\n{json.dumps(response.json(), indent=4)}"
        else:
            return f"<[{response.status_code}] {response.reason}>\n{json.dumps(response.json())}"


    @classmethod
    def _get_input(cls, field, password=False, type=None, required=True):
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


    @classmethod
    def _locate_config(cls, config_dir_path=None):
        '''
        If a `config_dir` was provided, confirm this is a directory containing a config file.

        Otherwise, use `Client.CONFIG_DIR_ENV_VAR`, and confirm that this is a directory that contains a config file.
        '''
        if config_dir_path:
            # Check config dir path is a directory
            if not os.path.isdir(config_dir_path):
                raise FileNotFoundError(f"'{config_dir_path}' does not exist")
            
            # Check config file path is a file
            config_file_path = os.path.join(config_dir_path, Client.CONFIG_FILE_NAME)
            if not os.path.isfile(config_file_path):
                raise FileNotFoundError(f"Config file does not exist in directory '{config_dir_path}'")

        else:
            # Find the config directory
            config_dir_path = os.getenv(Client.CONFIG_DIR_ENV_VAR)
            if config_dir_path is None:
                raise KeyError(f"Environment variable '{Client.CONFIG_DIR_ENV_VAR}' is not set")
            
            # Check config dir path is a directory
            if not os.path.isdir(config_dir_path):
                raise FileNotFoundError(f"'{Client.CONFIG_DIR_ENV_VAR}' points to a directory that does not exist")
            
            # Check config file path is a file
            config_file_path = os.path.join(config_dir_path, Client.CONFIG_FILE_NAME)
            if not os.path.isfile(config_file_path):
                raise FileNotFoundError(f"Config file does not exist in directory '{config_dir_path}'")

        return config_dir_path, config_file_path


    @classmethod
    def _validate_config(cls, config):
        '''
        Avoid a million KeyErrors due to the config file.
        '''
        for field in Client.CONFIG_FIELDS:
            if field not in config:
                raise KeyError(f"'{field}' key is missing from the config file")

        for user, ufields in config["users"].items():
            for field in Client.USER_FIELDS:
                if field not in ufields:
                    raise KeyError(f"'{field}' key is missing from user '{user}' in the config file")



    @classmethod
    def makeconfig(cls):
        '''
        Generate the config directory and config file.
        '''
        host = cls._get_input("host")
        port = cls._get_input("port", type=int)
        config_dir_location = cls._get_input("location to create a config directory")
        config_dir_location = config_dir_location.replace("~", os.path.expanduser("~"))
        if not os.path.isdir(config_dir_location):
            raise FileNotFoundError(f"No such directory: {config_dir_location}")

        config_dir_path = os.path.join(config_dir_location, Client.CONFIG_DIR_NAME)
        if not os.path.isdir(config_dir_path):
            os.mkdir(config_dir_path)
        os.chmod(config_dir_path, stat.S_IRUSR | stat.S_IWUSR | stat.S_IXUSR)
        
        config_file_path = os.path.join(config_dir_path, Client.CONFIG_FILE_NAME)
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
        os.chmod(config_file_path, stat.S_IRUSR | stat.S_IWUSR)

        print("")
        print("Config directory and config file created successfully.")
        print(f"Please create the following environment variable by typing the following in your shell:") 
        print("")
        print(f"export METADB_CONFIG_DIR={config_dir_path}")
        print("")
        warning_message = [
            "Your config directory stores sensitive information such as user passwords and tokens.",
            "The config directory (and files within) have been created with the permissions needed to keep your information safe.",
            "DO NOT CHANGE THESE PERMISSIONS. Doing so may allow other users to read your passwords and tokens!"
        ]
        message_width = max([len(x) for x in warning_message])
        print("IMPORTANT: DO NOT CHANGE CONFIG DIRECTORY PERMISSIONS".center(message_width, "!"))
        for line in warning_message:
            print(line)
        print("!" * message_width)


    def __init__(self, config_dir_path=None):
        # Locate the config
        config_dir_path, config_file_path = Client._locate_config(config_dir_path=config_dir_path)

        # Load the config
        with open(config_file_path) as config_file:
            config = json.load(config_file)

        # Validate the config
        Client._validate_config(config)

        # Set up client object
        self.config = config
        self.config_dir_path = config_dir_path
        self.config_file_path = config_file_path
        self.url = f"http://{self.config['host']}:{self.config['port']}"

        self.endpoints = {
            "token-pair" : f"{self.url}/auth/token-pair/",
            "token-refresh" : f"{self.url}/auth/token-refresh/",
            "register" : f"{self.url}/accounts/register/",
            "data" : f"{self.url}/data/",
            "pathogen_codes" : f"{self.url}/data/pathogen_codes/",
        }


    def _request_token_pair(self, username, password):
        '''
        Request an access token and a refresh token.
        '''
        response = requests.post(
            self.endpoints["token-pair"],
            json={
                "username" : username,
                "password" : password
            }
        )
        return response


    def _request_access_token(self, refresh_token):
        '''
        Use the refresh token to request a new access token.
        '''
        response = requests.post(
            self.endpoints["token-refresh"], 
            json={
                "refresh" : refresh_token,
            }
        )
        return response


    def _handle_tokens_request(self, method, url, username, password, tokens, params=None, body=None):
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
            headers={"Authorization": "Bearer {}".format(tokens["access"])},
            params=params,
            json=body
        )

        # Handle token expiry
        if response.status_code == 401:
            # Get a new access token using the refresh token
            access_token_response = self._request_access_token(tokens["refresh"])

            if not access_token_response.ok:
                # Assume we have an expired refresh token, so get a new pair using username+password
                token_pair_response = self._request_token_pair(username, password)
                
                if not token_pair_response.ok:
                    # Who knows what is happening, return the issue with token pairs back to user
                    return token_pair_response, tokens
                else:
                    tokens = token_pair_response.json()
            else:
                tokens["access"] = access_token_response.json()["access"]
        
            # Now that we have our updated tokens, retry the request and return whatever response is given
            response = method(
                url=url,
                headers={"Authorization": "Bearer {}".format(tokens["access"])},
                params=params,
                json=body
            )

        return response, tokens 


    def prepare_login(self, username=None, password=None):
        '''
        Obtain username, password and tokens, and assign to the client.
        '''
        if username is not None:
            pass
        elif self.config["default_user"] is not None:
            username = self.config["default_user"]
        else:
            username = Client._get_input("username")

        if password is not None:
            pass
        elif username in self.config["users"]:
            password = self.config["users"][username]["password"]
        else:
            password = Client._get_input("password", password=True)

        if username in self.config["users"]:
            with open(self.config["users"][username]["tokens"]) as tokens_file:
                tokens = json.load(tokens_file) 
        else:
            tokens = self._request_token_pair(username, password)
            if not tokens.ok:
                # Something is wrong with the username + password 
                print(Client._format_response(tokens))
                tokens.raise_for_status()
            else:
                tokens = tokens.json()
        
        self.username = username
        self.password = password
        self.tokens = tokens


    def dump_tokens(self):
        '''
        Write user tokens to their tokens file.
        '''
        with open(self.config["users"][self.username]["tokens"], "w") as tokens_file:            
            json.dump(self.tokens, tokens_file, indent=4)


    def register(self):
        '''
        Create a new user. 
        
        If the account is created successfully, their details will be added to the config.
        '''
        username = Client._get_input("username")
        email = Client._get_input("email address", required=False) # TODO: should email be required?
        institute = Client._get_input("institute code").upper()
        
        match = False
        while not match:
            password = Client._get_input("password", password=True)
            password2 = Client._get_input("password (again)", password=True)
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

        print(Client._format_response(response))
        
        if response.ok:
            print("Account created successfully.")
            tokens_path = os.path.join(self.config_dir_path, f"{username}_tokens.json")
            self.config["users"][username] = {
                "password" : password, # type: ignore
                "tokens" : tokens_path
            }
            if len(self.config["users"]) == 1:
                self.config["default_user"] = username
            
            # TODO: Probably has issues if using the same client in multiple places
            with open(self.config_file_path, "w") as config:
                json.dump(self.config, config, indent=4)
            
            with open(tokens_path, "w") as tokens:
                json.dump({"access" : None, "refresh" : None}, tokens, indent=4)
            
            # User read-write only
            os.chmod(tokens_path, stat.S_IRUSR | stat.S_IWUSR)

            print("The user has been added to the config.")


    def create(self, pathogen_code, tsv_path):
        '''
        Post new records to the database.
        '''
        if tsv_path == '-':
            tsv = sys.stdin
        else:
            tsv = open(tsv_path)
        try:
            reader = csv.DictReader(tsv, delimiter='\t')
            response = None
            tokens = None
            for record in reader:
                response, tokens = self._handle_tokens_request(
                    method=requests.post,
                    url=os.path.join(self.endpoints["data"], pathogen_code + "/"),
                    body=record,
                    username=self.username,
                    password=self.password,
                    tokens=self.tokens
                )
                print(Client._format_response(response, pretty_print=False))
            if response and response.ok and tokens:
                self.tokens = tokens
        finally:
            if tsv is not sys.stdin:
                tsv.close()


    def get(self, pathogen_code, filters=None):
        '''
        Get records from the database. 
        '''        
        if filters is None:
            filters = {}

        response, tokens = self._handle_tokens_request(
            method=requests.get,
            url=os.path.join(self.endpoints["data"], pathogen_code + "/"),
            params=filters,
            username=self.username,
            password=self.password,
            tokens=self.tokens
        )
        if response.ok:
            self.tokens = tokens
            table = pd.json_normalize(response.json()["results"])
            print(table.to_csv(index=False, sep='\t'), end='')
            next = response.json()["next"]
            while next is not None:
                response, tokens = self._handle_tokens_request(
                    method=requests.get,
                    url=next,
                    username=self.username,
                    password=self.password,
                    tokens=tokens
                )            
                if response.ok:
                    self.tokens = tokens
                    table = pd.json_normalize(response.json()["results"])
                    print(table.to_csv(index=False, sep='\t', header=False), end='')
                    next = response.json()["next"]
                else:
                    print(Client._format_response(response))
        else:
            print(Client._format_response(response))


    def update(self, pathogen_code, cid, update_fields=None):
        '''
        Update a record in the database.
        '''        
        if update_fields is None:
            update_fields = {}

        response, tokens = self._handle_tokens_request(
            method=requests.patch,
            url=os.path.join(self.endpoints["data"], pathogen_code + "/", cid + "/"),
            body=update_fields,
            username=self.username,
            password=self.password,
            tokens=self.tokens
        )
        if response.ok:
            self.tokens = tokens
        print(Client._format_response(response))

    
    def delete(self, pathogen_code, cid):
        '''
        Delete a record in the database.
        '''        
        response, tokens = self._handle_tokens_request(
            method=requests.delete,
            url=os.path.join(self.endpoints["data"], pathogen_code + "/", cid + "/"),
            username=self.username,
            password=self.password,
            tokens=self.tokens
        )
        if response.ok:
            self.tokens = tokens
        print(Client._format_response(response))


    def pathogen_codes(self):
        '''
        Get the current pathogens within the database.
        '''        
        response, tokens = self._handle_tokens_request(
            method=requests.get,
            url=self.endpoints["pathogen_codes"],
            username=self.username,
            password=self.password,
            tokens=self.tokens
        )
        if response.ok:
            self.tokens = tokens
        print(Client._format_response(response))


def main():
    user_parser = argparse.ArgumentParser(add_help=False)
    user_parser.add_argument("-u", "--user")

    parser = argparse.ArgumentParser()
    parser.add_argument("-t", "--timeit", action="store_true")
    command = parser.add_subparsers(dest="command")

    makeconfig_parser = command.add_parser("makeconfig")
    
    register_parser = command.add_parser("register")
    
    create_parser = command.add_parser("create", parents=[user_parser])
    create_parser.add_argument("pathogen_code")
    create_parser.add_argument("tsv")

    get_parser = command.add_parser("get", parents=[user_parser])
    get_parser.add_argument("pathogen_code")
    get_parser.add_argument("-f", "--filter", nargs=2, action="append", metavar=("FIELD", "VALUE"))
    # TODO: How to filter by published_week?

    update_parser = command.add_parser("update", parents=[user_parser])
    update_parser.add_argument("pathogen_code")
    update_parser.add_argument("cid")
    update_parser.add_argument("-uf", "--update-field", nargs=2, action="append", metavar=("FIELD", "VALUE"))

    delete_parser = command.add_parser("delete", parents=[user_parser])
    delete_parser.add_argument("pathogen_code")
    delete_parser.add_argument("cid")

    pathogen_codes_parser = command.add_parser("pathogen_codes", parents=[user_parser])

    args = parser.parse_args()

    if args.command == "makeconfig":
        Client.makeconfig()
    else:
        client = Client()
        
        if args.command == "register":
            client.register()
        
        else:
            client.prepare_login(username=args.user)

            if args.command == "create":
                client.create(args.pathogen_code, args.tsv)
            
            elif args.command == "get":
                if args.filter is not None:
                    filters = {f : v for f, v in args.filter}
                else:
                    filters = {}
                client.get(args.pathogen_code, filters)
            
            elif args.command == "update":
                if args.update_field is not None:
                    update_fields = {f : v for f, v in args.update_field}
                else:
                    update_fields = {}
                client.update(args.pathogen_code, args.cid, update_fields)

            elif args.command == "delete":
                client.delete(args.pathogen_code, args.cid)
            
            elif args.command == "pathogen_codes":
                client.pathogen_codes()
            
            if client.username in client.config["users"]:
                client.dump_tokens()

if __name__ == "__main__":
    main()
