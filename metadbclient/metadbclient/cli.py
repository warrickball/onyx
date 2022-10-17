import os
import stat
import json
import argparse
import pandas as pd
from metadbclient import version, Client, Config, utils, settings


def create_config():
    """
    Generate the config directory and config file.
    """
    host = utils.get_input("host")
    port = utils.get_input("port", type=int)

    config_dir_location = utils.get_input("location to create a config directory")
    config_dir_location = config_dir_location.replace("~", os.path.expanduser("~"))
    if not os.path.isdir(config_dir_location):
        raise FileNotFoundError(f"No such directory: {config_dir_location}")

    config_dir_path = os.path.join(config_dir_location, settings.CONFIG_DIR_NAME)
    if os.path.isdir(config_dir_path):
        raise FileExistsError(f"Config directory already exists: {config_dir_path}")

    os.mkdir(config_dir_path)

    # Read-write-execute for OS user only
    os.chmod(config_dir_path, stat.S_IRUSR | stat.S_IWUSR | stat.S_IXUSR)

    config_file_path = os.path.join(config_dir_path, settings.CONFIG_FILE_NAME)
    if os.path.isfile(config_file_path):
        raise FileExistsError(f"Config file already exists: {config_file_path}")

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


def add_user(config, username):
    """
    Add user to the config.
    """
    config.add_user(username)
    print("The user has been added to the config.")


def set_default_user(config, username):
    """
    Set the default user in the config.
    """
    config.set_default_user(username)
    print(f"The user has been set as the default user.")


def get_default_user(config):
    """
    Get the default user in the config.
    """
    default_user = config.get_default_user()
    print(default_user)


def list_users(config):
    """
    List all users in the config.
    """
    users = config.list_users()
    for user in users:
        print(user)


def register(client):
    """
    Create a new user.
    """
    first_name = utils.get_input("first name")
    last_name = utils.get_input("last name")
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

    registration = client.register(
        first_name=first_name,
        last_name=last_name,
        email=email,
        institute=institute,
        password=password,  # type: ignore
    )

    utils.print_response(registration)

    if registration.ok:
        print("Account created successfully.")
        check = ""
        while not check:
            check = input(
                "Would you like to add this account to the config? [y/n]: "
            ).upper()

        if check == "Y":
            results = registration.json()["results"]
            if len(results) != 1:
                raise Exception("Expected only one result in response")

            username = results[0]["username"]
            client.add_user(username)
            print("The user has been added to the config.")


def login(client, username, env_password):
    """
    Log in as a user.
    """
    response = client.login(
        username=username,
        env_password=env_password,
    )
    utils.print_response(response, status_only=True)


def logout(client):
    """
    Log out the current user.
    """
    response = client.logout()
    utils.print_response(response, status_only=True)


def approve(client, username):
    """
    Approve another user on the server.
    """
    approval = client.approve(username)
    utils.print_response(approval)


def create(client, pathogen_code, fields):
    """
    Post a new pathogen record to the database.
    """
    fields = utils.construct_unique_fields_dict(fields)
    creations = client.create(pathogen_code, fields=fields)
    utils.execute_uploads(creations)


def csv_create(client, pathogen_code, csv_path):
    """
    Post new pathogen records to the database, using a csv.
    """
    creations = client.create(pathogen_code, csv_path=csv_path)
    utils.execute_uploads(creations)


def tsv_create(client, pathogen_code, tsv_path):
    """
    Post new pathogen records to the database, using a tsv.
    """
    creations = client.create(pathogen_code, csv_path=tsv_path, delimiter="\t")
    utils.execute_uploads(creations)


def get(client, pathogen_code, cid, fields):
    """
    Get pathogen records from the database.
    """
    fields = utils.construct_fields_dict(fields)

    results = client.get(pathogen_code, cid, fields)

    result = next(results)
    if result.ok:
        table = pd.json_normalize(result.json()["results"])
        print(table.to_csv(index=False, sep="\t"), end="")
    else:
        utils.print_response(result)

    for result in results:
        if result.ok:
            table = pd.json_normalize(result.json()["results"])
            print(table.to_csv(index=False, sep="\t", header=False), end="")
        else:
            utils.print_response(result)


def update(client, pathogen_code, cid, fields):
    """
    Update a pathogen record in the database.
    """
    fields = utils.construct_unique_fields_dict(fields)
    updates = client.update(pathogen_code, cid=cid, fields=fields)
    utils.execute_uploads(updates)


def csv_update(client, pathogen_code, csv_path):
    """
    Update pathogen records in the database, using a csv.
    """
    updates = client.update(pathogen_code, csv_path=csv_path)
    utils.execute_uploads(updates)


def tsv_update(client, pathogen_code, tsv_path):
    """
    Update pathogen records in the database, using a tsv.
    """
    updates = client.update(pathogen_code, csv_path=tsv_path, delimiter="\t")
    utils.execute_uploads(updates)


def suppress(client, pathogen_code, cid):
    """
    Suppress a pathogen record in the database.
    """
    suppressions = client.suppress(pathogen_code, cid=cid)
    utils.execute_uploads(suppressions)


def csv_suppress(client, pathogen_code, csv_path):
    """
    Suppress pathogen records in the database, using a csv.
    """
    suppressions = client.suppress(pathogen_code, csv_path=csv_path)
    utils.execute_uploads(suppressions)


def tsv_suppress(client, pathogen_code, tsv_path):
    """
    Suppress pathogen records in the database, using a tsv.
    """
    suppressions = client.suppress(pathogen_code, csv_path=tsv_path, delimiter="\t")
    utils.execute_uploads(suppressions)


def list_pathogen_codes(client):
    """
    Get the current pathogens within the database.
    """
    pathogen_codes = client.pathogen_codes()
    utils.print_response(pathogen_codes)


def list_institute_users(client):
    """
    Get the current users within the institute of the requesting user.
    """
    institute_users = client.institute_users()
    utils.print_response(institute_users)


def admin_list_users(client):
    """
    Get all users.
    """
    all_users = client.all_users()
    utils.print_response(all_users)


def run(args):
    if args.command == "config":

        if args.config_command == "create":
            create_config()

        else:
            config = Config()

            if args.config_command == "set-default-user":
                set_default_user(config, args.username)

            elif args.config_command == "get-default-user":
                get_default_user(config)

            elif args.config_command == "add-user":
                add_user(config, args.username)

            elif args.config_command == "list-users":
                list_users(config)

    else:
        config = Config()
        client = Client(config)

        if args.command == "register":
            register(client)

        elif args.command == "login":
            login(client, args.user, args.env_password)

        else:
            client.continue_session(username=args.user, env_password=args.env_password)

            if args.command == "admin":
                if args.admin_command == "approve":
                    pass  # TODO

                elif args.admin_command == "list-users":
                    admin_list_users(client)

            elif args.command == "logout":
                logout(client)

            elif args.command == "approve":
                approve(client, args.username)

            elif args.command == "create":
                create(client, args.pathogen_code, args.field)

            elif args.command == "csv-create":
                csv_create(client, args.pathogen_code, args.csv)

            elif args.command == "tsv-create":
                tsv_create(client, args.pathogen_code, args.tsv)

            elif args.command == "get":
                get(client, args.pathogen_code, args.cid, args.field)

            elif args.command == "update":
                update(client, args.pathogen_code, args.cid, args.field)

            elif args.command == "csv-update":
                csv_update(client, args.pathogen_code, args.csv)

            elif args.command == "tsv-update":
                tsv_update(client, args.pathogen_code, args.tsv)

            elif args.command == "suppress":
                suppress(client, args.pathogen_code, args.cid)

            elif args.command == "csv-suppress":
                csv_suppress(client, args.pathogen_code, args.csv)

            elif args.command == "tsv-suppress":
                tsv_suppress(client, args.pathogen_code, args.tsv)

            elif args.command == "list-pathogen-codes":
                list_pathogen_codes(client)

            elif args.command == "list-institute-users":
                list_institute_users(client)


def get_args():
    user_parser = argparse.ArgumentParser(add_help=False)
    user_parser.add_argument("-u", "--user")
    user_parser.add_argument("-p", "--env-password", action="store_true")

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-v", "--version", action="version", version=version.__version__
    )

    command = parser.add_subparsers(dest="command", metavar="{command}")

    # Commands involving creation/altering of the config
    config_parser = command.add_parser(
        "config", help="Commands for creating/interacting with the config."
    )

    config_commands_parser = config_parser.add_subparsers(
        dest="config_command", metavar="{config-command}"
    )

    # Create the config directory and config file
    create_config_parser = config_commands_parser.add_parser(
        "create", help="Create a config for the client."
    )

    # Set the default user in the config
    set_default_user_parser = config_commands_parser.add_parser(
        "set-default-user", help="Set the default user in the config of the client."
    )
    set_default_user_parser.add_argument("username", nargs="?")

    # List the default user in the config
    get_default_user_parser = config_commands_parser.add_parser(
        "get-default-user", help="Get the default user in the config of the client."
    )

    # Add a pre-existing user to the config
    add_user_parser = config_commands_parser.add_parser(
        "add-user", help="Add a pre-existing metadb user to the config of the client."
    )
    add_user_parser.add_argument("username", nargs="?")

    # List all users in the config
    list_config_users_parser = config_commands_parser.add_parser(
        "list-users", help="List all users in the config of the client."
    )

    # Admin specific commands
    admin_parser = command.add_parser("admin", help="Commands for admins only.")

    admin_commands_parser = admin_parser.add_subparsers(
        dest="admin_command", metavar="{admin-command}"
    )

    # Admin-approve a user
    admin_approve_parser = admin_commands_parser.add_parser(
        "approve", parents=[user_parser], help="Admin-approve another user in metadb."
    )
    admin_approve_parser.add_argument("username")

    # List all users
    list_all_users_parser = admin_commands_parser.add_parser(
        "list-users", parents=[user_parser], help="List all users in metadb."
    )

    # Create a user on the server
    register_parser = command.add_parser(
        "register", help="Create a new user in metadb."
    )

    # Log in to metadb
    login_parser = command.add_parser(
        "login", parents=[user_parser], help="Log in to metadb."
    )

    # Log out of metadb
    logout_parser = command.add_parser(
        "logout",
        parents=[user_parser],
        help="Log out of metadb.",
    )

    # Institute approval of another user on the server
    approve_parser = command.add_parser(
        "approve", parents=[user_parser], help="Approve another user in metadb."
    )
    approve_parser.add_argument("username")

    # List users within institute of the requesting user
    list_institute_users_parser = command.add_parser(
        "list-institute-users",
        parents=[user_parser],
        help="List all users within the institute of the requesting user.",
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
    create_parser.add_argument(
        "-f", "--field", nargs=2, action="append", metavar=("FIELD", "VALUE")
    )

    csv_create_parser = command.add_parser(
        "csv-create",
        parents=[user_parser],
        help="Upload pathogen metadata to metadb via a .csv file.",
    )
    csv_create_parser.add_argument("pathogen_code")
    csv_create_parser.add_argument("csv")

    tsv_create_parser = command.add_parser(
        "tsv-create",
        parents=[user_parser],
        help="Upload pathogen metadata to metadb via a .tsv file.",
    )
    tsv_create_parser.add_argument("pathogen_code")
    tsv_create_parser.add_argument("tsv")

    # Get pathogen metadata from the database
    get_parser = command.add_parser(
        "get", parents=[user_parser], help="Get pathogen metadata from metadb."
    )
    get_parser.add_argument("pathogen_code")
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

    csv_update_parser = command.add_parser(
        "csv-update",
        parents=[user_parser],
        help="Update pathogen metadata within metadb via a .csv file.",
    )
    csv_update_parser.add_argument("pathogen_code")
    csv_update_parser.add_argument("csv")

    tsv_update_parser = command.add_parser(
        "tsv-update",
        parents=[user_parser],
        help="Update pathogen metadata within metadb via a .tsv file.",
    )
    tsv_update_parser.add_argument("pathogen_code")
    tsv_update_parser.add_argument("tsv")

    # Suppress pathogen metadata within the database
    # Suppression means that the data will not be deleted, but will be hidden from users
    suppress_parser = command.add_parser(
        "suppress",
        parents=[user_parser],
        help="Suppress pathogen metadata within metadb.",
    )
    suppress_parser.add_argument("pathogen_code")
    suppress_parser.add_argument("cid")
    suppress_parser.add_argument(
        "-f", "--field", nargs=2, action="append", metavar=("FIELD", "VALUE")
    )

    csv_suppress_parser = command.add_parser(
        "csv-suppress",
        parents=[user_parser],
        help="Suppress pathogen metadata within metadb via a .csv file.",
    )
    csv_suppress_parser.add_argument("pathogen_code")
    csv_suppress_parser.add_argument("csv")

    tsv_suppress_parser = command.add_parser(
        "tsv-suppress",
        parents=[user_parser],
        help="Suppress pathogen metadata within metadb via a .tsv file.",
    )
    tsv_suppress_parser.add_argument("pathogen_code")
    tsv_suppress_parser.add_argument("tsv")

    args = parser.parse_args()

    return args


def main():
    args = get_args()
    run(args)
