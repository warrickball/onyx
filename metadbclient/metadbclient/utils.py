import os
import json
import time
import inspect
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


def check_for_login_details(obj):
    if not obj.has_login_details:
        raise Exception("The client has no details to log in with")


def write_tokens(obj):
    with open(obj.config["users"][obj.username]["tokens"], "w") as tokens_file:
        json.dump(obj.tokens, tokens_file, indent=4)


def login_required(method):
    """
    Decorator that does the following:

    * Checks the client object has user login details.
    * Runs the provided method and returns the output.
    * Writes user tokens to their tokens file, after running the provided method.
    """

    # If the method is a generator we have to use 'yield from'
    # Meddling with forces I don't fully understand here, but it works
    if inspect.isgeneratorfunction(method):

        def wrapped_generator_method(obj, *args, **kwargs):
            check_for_login_details(obj)
            try:
                # Run the method and yield the output
                output = yield from method(obj, *args, **kwargs)
            finally:
                # ONLY when the method has finished yielding do we reach this point
                # After everything is done, write the user tokens to their tokens file
                write_tokens(obj)
            return output

        return wrapped_generator_method

    else:

        def wrapped_method(obj, *args, **kwargs):
            check_for_login_details(obj)
            try:
                # Run the method and get the output
                output = method(obj, *args, **kwargs)
            finally:
                # After everything is done, write the user tokens to their tokens file
                write_tokens(obj)
            return output

        return wrapped_method
