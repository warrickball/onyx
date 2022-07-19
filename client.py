import os
import csv
import sys
import stat
import json
import argparse
import requests
import pandas as pd
from getpass import getpass


class ConfigError(Exception):
    pass


class Client:
    CONFIG_DIR_ENV_VAR = "METADB_CONFIG_DIR"
    CONFIG_DIR_NAME = "config"
    CONFIG_FILE_NAME = "config.json"
    TOKENS_FILE_POSTFIX = "_tokens.json"
    CONFIG_FIELDS = ["host", "port", "users", "default_user"]
    USER_FIELDS = ["password", "tokens"]

    def __init__(self, args):
        if args.command != "setup":
            # If the user is not setting up the client, find the config file
            config_dir_path = os.getenv(Client.CONFIG_DIR_ENV_VAR)
            if config_dir_path is None:
                print(f"Environment variable '{Client.CONFIG_DIR_ENV_VAR}' is not set.")
                print("Please set this variable to be the path to your config directory.")
                print("If you do not have a config directory, run the 'setup' command to create one.")
                sys.exit()

            if not os.path.isdir(config_dir_path):
                raise FileNotFoundError(f"'{Client.CONFIG_DIR_ENV_VAR}' points to a directory that does not exist")
            
            config_file_path = os.path.join(config_dir_path, Client.CONFIG_FILE_NAME)
            if not os.path.isfile(config_file_path):
                raise FileNotFoundError("Config file does not exist")

            # Read the config file and validate it
            with open(config_file_path) as config_file:
                config = json.load(config_file)

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


    def validate_config(self, config):
        for field in Client.CONFIG_FIELDS:
            if field not in config:
                raise ConfigError(f"'{field}' is missing from the config file")

        for user, ufields in config["users"].items():
            for field in Client.USER_FIELDS:
                if field not in ufields:
                    raise ConfigError(f"'{field}' is missing from user '{user}' in the config file")


    def format_response(self, response):
        return f"<[{response.status_code}] {response.reason}>\n{response.json()}"


    def get_input(self, field, password=False):
        if password:
            # User input is not displayed to the terminal
            input_func = getpass
        else:
            input_func = input
        value = input_func(f"{field[0].upper()}{field[1:].lower()}: ").strip()
        while not value:
            value = input_func(f"Please enter a valid {field.lower()}: ").strip()
        return value


    def setup(self):
        host = self.get_input("host")
        port = int(self.get_input("port"))
        data = {
            "host" : host,
            "port" : port,
            "users" : {},
            "default_user" : None
        }
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
            json.dump(data, config_file, indent=4)
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
        else:
            print(self.format_response(response))


    def get_username(self):
        if self.args.user != None:
            if self.args.user not in self.config["users"]:
                username = None
                print("The user provided by --user is not present within the config.")
            else:
                username = self.args.user
        else:
            if (self.config["default_user"] is None) or (self.config["default_user"] not in self.config["users"]):
                username = None
                print("The default_user is not present in the config.")
            else:
                username = self.config["default_user"]
        if username is None:
            # We do not yet have a username, so ask for input
            username = self.get_input("username")
        return username


    # def get_login_details(self):
    #     username = self.config["default_user"]
    #     if username is None:
    #         username = input("Username: ").strip()
    #     password = self.config["users"].get(username, {}).get("password") # TODO: Bit of a hacky way
    #     if password is None:
    #         password = getpass().strip()
    #     return username, password


    def get_token_pair(self, username, password):
        response = requests.post(
            self.endpoints["token-pair"],
            json={
                "username" : username,
                "password" : password
            }
        )
        return response


    def get_access_token(self, refresh_token):
        response = requests.post(
            self.endpoints["token-refresh"], 
            json={
                "refresh" : refresh_token,
            }
        )
        return response


    def get_login_details(self):
        username = self.get_username()
        if username not in self.config["users"]:
            user_config = None
            # The user isn't in the config
            # So ask for password and get some tokenz
            password = self.get_input("password", password=True)
            token_pair_response = self.get_token_pair(username, password)
            if token_pair_response.ok:
                tokens = token_pair_response.json()
            else:
                # TODO
                print("Failed to obtain token pair.")
                sys.exit()
        else:
            # The user is in the config
            # So (attempt to) open tokens file and use these
            user_config = self.config["users"][username]
            password = user_config["password"]
            with open(user_config["tokens"]) as tokens_file:
                tokens = json.load(tokens_file)
        return username, password, tokens


    def handle_tokens_request(self, method, url, params, body, username, password, tokens):
        response = method(
            url=url,
            headers={"Authorization": "Bearer {}".format(tokens["access"])},
            params=params,
            json=body
        )

        if not response.ok:
            # Likely to be an expired access token
            access_token_response = self.get_access_token(tokens["refresh"])
            if not access_token_response.ok:
                # Likely to be expired refresh token
                token_pair_response = self.get_token_pair(username, password)
                if not token_pair_response.ok:
                    # TODO
                    print("Failed to obtain token pair.")
                    sys.exit()
                else:
                    tokens = token_pair_response.json()
            else:
                tokens["access"] = access_token_response.json()["access"]

            response = method(
                url=url,
                headers={"Authorization": "Bearer {}".format(tokens["access"])},
                params=params,
                json=body
            )

        return response, tokens    


    def dump_tokens(self, username, tokens):
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
                print(self.format_response(response))
        finally:
            if tsv is not sys.stdin:
                tsv.close()
            if username in self.config["users"]:
                self.dump_tokens(username, tokens)


    def get(self):
        username, password, tokens = self.get_login_details()
        params = {f : v for f, v in self.args.filter}
        page = 1
        params["page"] = page # type: ignore
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

        while response.json()["next"] is not None:
            page += 1
            params["page"] = page # type: ignore
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
            print(table.to_csv(index=False, sep='\t', header=False), end='')

        if username in self.config["users"]:
            self.dump_tokens(username, tokens)


def main():
    parser = argparse.ArgumentParser()
    command = parser.add_subparsers(dest="command")

    setup_parser = command.add_parser("setup")

    register_parser = command.add_parser("register")

    create_parser = command.add_parser("create")
    create_parser.add_argument("tsv")
    create_parser.add_argument("-u", "--user")

    get_parser = command.add_parser("get")
    get_parser.add_argument("pathogen_code")
    get_parser.add_argument("-f", "--filter", nargs=2, action="append", metavar=("ARGUMENT" "VALUE"))
    get_parser.add_argument("-u", "--user")

    args = parser.parse_args()
    Client(args)


if __name__ == "__main__":
    main()
