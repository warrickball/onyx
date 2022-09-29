import os
import stat
import json
import argparse
import pandas as pd
from metadbclient import version, METADBClient, utils, settings


def make_config():
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


def register(client):
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

    registration = client.register(
        username=username, email=email, institute=institute, password=password  # type: ignore
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
            username = registration.json()["username"]
            client.add_user(username)
            print("The user has been added to the config.")


def set_default_user(client, args):
    """
    Set the default user in the config.
    """
    client.set_default_user(args.username)
    print(f"The user has been set as the default user.")


def get_default_user(client):
    """
    Get the default user in the config.
    """
    default_user = client.get_default_user()
    print(default_user)


def add_user(client, args):
    """
    Add user to the config.
    """
    client.add_user(args.username)
    print("The user has been added to the config.")


def approve(client, args):
    """
    Approve another user on the server.
    """
    approval = client.approve(args.username)
    utils.print_response(approval)


def create(client, args):
    """
    Post a new pathogen record to the database.
    """
    fields = utils.construct_unique_fields_dict(args.field)
    creations = client.create(args.pathogen_code, fields=fields)
    utils.execute_uploads(creations)


def csv_create(client, args):
    """
    Post new pathogen records to the database, using a csv.
    """
    creations = client.create(args.pathogen_code, csv_path=args.csv)
    utils.execute_uploads(creations)


def tsv_create(client, args):
    """
    Post new pathogen records to the database, using a tsv.
    """
    creations = client.create(args.pathogen_code, csv_path=args.tsv, delimiter="\t")
    utils.execute_uploads(creations)


def get(client, args):
    """
    Get pathogen records from the database.
    """
    fields = utils.construct_fields_dict(args.field)

    results = client.get(args.pathogen_code, args.cid, fields)

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


def update(client, args):
    """
    Update a pathogen record in the database.
    """
    fields = utils.construct_unique_fields_dict(args.field)
    updates = client.update(args.pathogen_code, cid=args.cid, fields=fields)
    utils.execute_uploads(updates)


def csv_update(client, args):
    """
    Update pathogen records in the database, using a csv.
    """
    updates = client.update(args.pathogen_code, csv_path=args.csv)
    utils.execute_uploads(updates)


def tsv_update(client, args):
    """
    Update pathogen records in the database, using a tsv.
    """
    updates = client.update(args.pathogen_code, csv_path=args.tsv, delimiter="\t")
    utils.execute_uploads(updates)


def suppress(client, args):
    """
    Suppress a pathogen record in the database.
    """
    suppressions = client.suppress(args.pathogen_code, cid=args.cid)
    utils.execute_uploads(suppressions)


def csv_suppress(client, args):
    """
    Suppress pathogen records in the database, using a csv.
    """
    suppressions = client.suppress(args.pathogen_code, csv_path=args.csv)
    utils.execute_uploads(suppressions)


def tsv_suppress(client, args):
    """
    Suppress pathogen records in the database, using a tsv.
    """
    suppressions = client.suppress(
        args.pathogen_code, csv_path=args.tsv, delimiter="\t"
    )
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


def list_all_users(client):
    """
    Get all users.
    """
    all_users = client.all_users()
    utils.print_response(all_users)


def run(args):
    if args.command == "make-config":
        make_config()
    else:
        client = METADBClient()

        # Commands that require a config, but no user login details
        if args.command == "register":
            register(client)

        elif args.command == "set-default-user":
            set_default_user(client, args)

        elif args.command == "get-default-user":
            get_default_user(client)

        elif args.command == "add-user":
            add_user(client, args)

        else:
            # Commands that require a config and user login details
            client.get_login(
                username=args.user, use_password_env_var=args.use_password_env_var
            )

            if args.command == "approve":
                approve(client, args)

            elif args.command == "create":
                create(client, args)

            elif args.command == "csv-create":
                csv_create(client, args)

            elif args.command == "tsv-create":
                tsv_create(client, args)

            elif args.command == "get":
                get(client, args)

            elif args.command == "update":
                update(client, args)

            elif args.command == "csv-update":
                csv_update(client, args)

            elif args.command == "tsv-update":
                tsv_update(client, args)

            elif args.command == "suppress":
                suppress(client, args)

            elif args.command == "csv-suppress":
                csv_suppress(client, args)

            elif args.command == "tsv-suppress":
                tsv_suppress(client, args)

            elif args.command == "list-pathogen-codes":
                list_pathogen_codes(client)

            elif args.command == "list-institute-users":
                list_institute_users(client)

            elif args.command == "list-all-users":
                list_all_users(client)


def get_args():
    user_parser = argparse.ArgumentParser(add_help=False)
    user_parser.add_argument("-u", "--user")
    user_parser.add_argument("-p", "--use-password-env-var", action="store_true")

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-v", "--version", action="version", version=version.__version__
    )
    parser.add_argument(
        "-t",
        "--timeit",
        action="store_true",
        help="output the time taken to run a command",
    )
    command = parser.add_subparsers(dest="command", metavar="{command}")

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

    if args.timeit:
        utils.timefunc(run)(args)
    else:
        run(args)
