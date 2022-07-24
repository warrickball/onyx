import os
import csv
import sys
import stat
import json
import argparse
import requests
import pandas as pd
from getpass import getpass


class Client:
    # Constants shared across every client
    CONFIG_DIR_ENV_VAR = "METADB_CONFIG_DIR"
    CONFIG_DIR_NAME = "config"
    CONFIG_FILE_NAME = "config.json"
    TOKENS_FILE_POSTFIX = "_tokens.json"
    CONFIG_FIELDS = ["host", "port", "users", "default_user"]
    USER_FIELDS = ["password", "tokens"]

    def __init__(self, args):
        if args.command != "setup":
            # Locate the config
            config_dir_path, config_file_path = self.locate_config()

            # Load the config
            with open(config_file_path) as config_file:
                config = json.load(config_file)

            # Validate the config
            self.validate_config(config)

            # Set up client object
            self.config = config
            self.config_dir_path = config_dir_path
            self.config_file_path = config_file_path
            self.args = args
            self.url = f"http://{self.config['host']}:{self.config['port']}"
            self.endpoints = {
                "token-pair" : f"{self.url}/auth/token-pair/",
                "token-refresh" : f"{self.url}/auth/token-refresh/",
                "register" : f"{self.url}/accounts/register/",
                "create" : f"{self.url}/data/create/",
                "get" : f"{self.url}/data/get/"
            }

        # Execute the provided command
        getattr(self, args.command)()


    def locate_config(self):
        '''
        Finds and confirms that `Client.CONFIG_DIR_ENV_VAR` is a directory, and that the directory contains a config file.
        '''
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
            raise FileNotFoundError("Config file does not exist")

        return config_dir_path, config_file_path


    def validate_config(self, config):
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


    def format_response(self, response, pretty_print=True):
        if pretty_print:
            return f"<[{response.status_code}] {response.reason}>\n{json.dumps(response.json(), indent=4)}"
        else:
            return f"<[{response.status_code}] {response.reason}>\n{json.dumps(response.json())}"


    def get_input(self, field, password=False, type=None):
        '''
        Get user input/password, ensuring they do not enter nothing or only spaces.
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
        while not value:
            try:
                value = type(input_func(f"Please enter a valid {field.lower()}: ").strip())
            except ValueError:
                value = None
        return value


    def setup(self):
        '''
        Generate the config directory and config file.
        '''
        host = self.get_input("host")
        port = self.get_input("port", type=int)
        config_dir_location = self.get_input("location to create a config directory")
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


    def register(self):
        username = self.get_input("username")
        email = self.get_input("email address")
        institute = self.get_input("institute code")
        
        match = False
        while not match:
            password = self.get_input("password", password=True)
            password2 = self.get_input("password (again)", password=True)
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

        print(self.format_response(response))
        
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
            
            os.chmod(tokens_path, stat.S_IRUSR | stat.S_IWUSR)

            print("The user has been added to the config.")


    def request_token_pair(self, username, password):
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


    def request_access_token(self, refresh_token):
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


    def get_username(self):
        '''
        Locate a user to make requests with. 
        
        Checks for a `--user`, followed by `default_user` within the config, followed by asking for input.
        '''
        if self.args.user is not None:
            username = self.args.user
            if username not in self.config["users"]:
                print(f"Note: the user '{username}' is not present within the config.")
        elif self.config["default_user"] is not None:
            username = self.config["default_user"]
            if username not in self.config["users"]:
                print("Note: the default_user is not present in the config.")
        else:
            username = self.get_input("username")   
        
        return username


    def get_password(self, username):
        '''
        Locate the password for the provided user.
        '''
        if username in self.config["users"]:
            password = self.config["users"][username]["password"]
        else:
            # The user isn't in the config, so ask for the password
            password = self.get_input("password", password=True)
        return password

    
    def get_tokens(self, username, password):
        '''
        Locate/generate tokens for the provided user.
        '''
        if username in self.config["users"]:
            with open(self.config["users"][username]["tokens"]) as tokens_file:
                tokens = json.load(tokens_file) 
        else:
            tokens = self.request_token_pair(username, password)
            if not tokens.ok:
                # Something is wrong with the username + password 
                print(self.format_response(tokens))
                tokens = None
            else:
                tokens = tokens.json()
        return tokens


    def get_login_details(self):
        '''
        Obtain username, password and tokens.
        '''
        username = self.get_username()
        password = self.get_password(username)
        tokens = self.get_tokens(username, password)
        if tokens is None:
            # Try again as tokens couldn't be obtained with provided username + password
            self.get_login_details()
        return username, password, tokens


    def handle_tokens_request(self, method, url, username, password, tokens, params=None, body=None,):
        '''
        Carry out a given request, refreshing tokens if required.
        '''
        if params is None:
            params = {}

        if body is None:
            body = {}
        
        response = method(
            url=url,
            headers={"Authorization": "Bearer {}".format(tokens["access"])},
            params=params,
            json=body
        )

        # Handle potential token expiry
        if not response.ok:
            # Assume we have an expired access token, so get a new one using the refresh token
            access_token_response = self.request_access_token(tokens["refresh"])
            if not access_token_response.ok:
                # Assume we have an expired refresh token, so get a new pair using username+password
                token_pair_response = self.request_token_pair(username, password)
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


    def dump_tokens(self, username, tokens):
        '''
        Write user tokens to their tokens file.
        '''
        with open(self.config["users"][username]["tokens"], "w") as tokens_file:            
            json.dump(tokens, tokens_file, indent=4)


    def create(self):
        username, password, tokens = self.get_login_details()
        if self.args.tsv == '-':
            tsv = sys.stdin
        else:
            tsv = open(self.args.tsv)
        try:
            reader = csv.DictReader(tsv, delimiter='\t')
            for record in reader:
                response, tokens = self.handle_tokens_request(
                    method=requests.post,
                    url=self.endpoints["create"],
                    params={},
                    body=record,
                    username=username,
                    password=password,
                    tokens=tokens
                )
                print(self.format_response(response, pretty_print=False))
        finally:
            if tsv is not sys.stdin:
                tsv.close()
            if username in self.config["users"]:
                self.dump_tokens(username, tokens)


    def get(self):
        username, password, tokens = self.get_login_details()
        
        if self.args.filter is not None:
            params = {f : v for f, v in self.args.filter}
        else:
            params = {}
        
        response, tokens = self.handle_tokens_request(
            method=requests.get,
            url=self.endpoints["get"] + f"{self.args.pathogen_code}/",
            params=params,
            body={},
            username=username,
            password=password,
            tokens=tokens
        )
        table = pd.json_normalize(response.json()["results"])
        print(table.to_csv(index=False, sep='\t'), end='')

        next = response.json()["next"]
        while next is not None:
            response, tokens = self.handle_tokens_request(
                method=requests.get,
                url=next,
                body={},
                username=username,
                password=password,
                tokens=tokens
            )            
            table = pd.json_normalize(response.json()["results"])
            print(table.to_csv(index=False, sep='\t', header=False), end='')
            next = response.json()["next"]

        if username in self.config["users"]:
            self.dump_tokens(username, tokens)


def main():
    # Arguments shared by all commands that require a user to login
    user_parser = argparse.ArgumentParser(add_help=False)
    user_parser.add_argument("-u", "--user")

    parser = argparse.ArgumentParser()
    command = parser.add_subparsers(dest="command")
    setup_parser = command.add_parser("makeconfig")
    register_parser = command.add_parser("register")
    create_parser = command.add_parser("create", parents=[user_parser])
    create_parser.add_argument("tsv")
    get_parser = command.add_parser("get", parents=[user_parser])
    get_parser.add_argument("pathogen_code")
    get_parser.add_argument("-f", "--filter", nargs=2, action="append", metavar=("FIELD", "VALUE"))

    args = parser.parse_args()
    Client(args)


if __name__ == "__main__":
    main()
