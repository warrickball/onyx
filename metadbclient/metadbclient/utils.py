import os
import json
import time
import stat
from getpass import getpass
from metadbclient import settings


def timefunc(func):
    """
    Decorator for timing a function.
    """

    def timed_func(*args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)
        end = time.time()
        print(f"Time taken: {round(end - start, 5)} seconds")
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

    Otherwise, use `settings.CONFIG_DIR_ENV_VAR`, and confirm that this is a directory that contains a config file.
    """
    if config_dir_path:
        # Check config dir path is a directory
        if not os.path.isdir(config_dir_path):
            raise FileNotFoundError(f"'{config_dir_path}' does not exist")

        # Check config file path is a file
        config_file_path = os.path.join(config_dir_path, settings.CONFIG_FILE_NAME)
        if not os.path.isfile(config_file_path):
            raise FileNotFoundError(
                f"Config file does not exist in directory '{config_dir_path}'"
            )

    else:
        # Find the config directory
        config_dir_path = os.getenv(settings.CONFIG_DIR_ENV_VAR)
        if config_dir_path is None:
            raise KeyError(
                f"Environment variable '{settings.CONFIG_DIR_ENV_VAR}' is not set"
            )

        # Check config dir path is a directory
        if not os.path.isdir(config_dir_path):
            raise FileNotFoundError(
                f"'{settings.CONFIG_DIR_ENV_VAR}' points to a directory that does not exist"
            )

        # Check config file path is a file
        config_file_path = os.path.join(config_dir_path, settings.CONFIG_FILE_NAME)
        if not os.path.isfile(config_file_path):
            raise FileNotFoundError(
                f"Config file does not exist in directory '{config_dir_path}'"
            )

    return config_dir_path, config_file_path


def validate_config(config):
    """
    Avoid a million KeyErrors due to problems with the config file.
    """
    for field in settings.CONFIG_FIELDS:
        if field not in config:
            raise KeyError(f"'{field}' key is missing from the config file")

    for user, ufields in config["users"].items():
        for field in settings.USER_FIELDS:
            if field not in ufields:
                raise KeyError(
                    f"'{field}' key is missing from user '{user}' in the config file"
                )


def make_config():
    """
    Generate the config directory and config file.
    """
    host = get_input("host")
    port = get_input("port", type=int)
    config_dir_location = get_input("location to create a config directory")
    config_dir_location = config_dir_location.replace("~", os.path.expanduser("~"))
    if not os.path.isdir(config_dir_location):
        raise FileNotFoundError(f"No such directory: {config_dir_location}")

    config_dir_path = os.path.join(config_dir_location, settings.CONFIG_DIR_NAME)
    if not os.path.isdir(config_dir_path):
        os.mkdir(config_dir_path)

    # Read-write-execute for OS user only
    os.chmod(config_dir_path, stat.S_IRUSR | stat.S_IWUSR | stat.S_IXUSR)

    config_file_path = os.path.join(config_dir_path, settings.CONFIG_FILE_NAME)
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
            settings.MESSAGE_BAR_WIDTH, "!"
        )
    )
    warning_message = [
        "Your config directory (and files within) store sensitive information such as tokens.",
        "They have been created with the permissions needed to keep your information safe.",
        "DO NOT CHANGE THESE PERMISSIONS. Doing so may allow other users to read your tokens!",
    ]
    for line in warning_message:
        print(line)
    print("".center(settings.MESSAGE_BAR_WIDTH, "!"))


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
                "The client has no details to log in with. If you are using the client as a python import, please first provide details with the 'get_login' command."
            )
        try:
            output = method(obj, *args, **kwargs)
        finally:
            with open(obj.config["users"][obj.username]["tokens"], "w") as tokens_file:
                json.dump(obj.tokens, tokens_file, indent=4)
        return output

    return wrapped_method
