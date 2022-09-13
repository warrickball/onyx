import argparse
from metadbclient import version, METADBClient, utils


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

    return args


def execute_command(args):
    if args.command == "make-config":
        utils.make_config()
    else:
        client = METADBClient()

        # Commands that require a config, but no user login details
        if args.command == "register":
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

            print(utils.format_response(registration))

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

        elif args.command == "set-default-user":
            client.set_default_user(args.username)
            print(f"The user has been set as the default user.")

        elif args.command == "get-default-user":
            default_user = client.get_default_user()
            print(default_user)

        elif args.command == "add-user":
            client.add_user(args.username)
            print("The user has been added to the config.")

        else:
            # Commands that require a config and user login details
            client.get_login(
                username=args.user, use_password_env_var=args.use_password_env_var
            )

            if args.command == "approve":
                approval = client.approve(args.username)
                print(utils.format_response(approval))

            elif args.command == "create":
                if args.field is not None:
                    fields = {f: v for f, v in args.field}
                    results = client.create(args.pathogen_code, fields=fields)
                else:
                    if args.csv:
                        results = client.create(args.pathogen_code, csv_path=args.csv)
                    else:
                        results = client.create(
                            args.pathogen_code, csv_path=args.tsv, delimiter="\t"
                        )

                for result in results:
                    print(utils.format_response(result))

            elif args.command == "get":
                fields = {}
                if args.field is not None:
                    for f, v in args.field:
                        if fields.get(f) is None:
                            fields[f] = []
                        fields[f].append(v)

                results = client.get(args.pathogen_code, args.cid, fields)

                result, ok = next(results)
                if ok:
                    print(result.to_csv(index=False, sep="\t"), end="")  # type: ignore
                else:
                    print(utils.format_response(result))

                for result, ok in results:
                    if ok:
                        print(
                            result.to_csv(index=False, sep="\t", header=False), end=""  # type: ignore
                        )
                    else:
                        print(utils.format_response(result))

            elif args.command == "update":
                if args.field is not None:
                    fields = {f: v for f, v in args.field}
                else:
                    fields = {}

                updates = client.update(args.pathogen_code, args.cid, fields)
                print(utils.format_response(updates))

            elif args.command == "suppress":
                suppressions = client.suppress(args.pathogen_code, args.cid)
                print(utils.format_response(suppressions))

            elif args.command == "list-pathogen-codes":
                pathogen_codes = client.pathogen_codes()
                print(utils.format_response(pathogen_codes))

            elif args.command == "list-institute-users":
                institute_users = client.institute_users()
                print(utils.format_response(institute_users))

            elif args.command == "list-all-users":
                all_users = client.all_users()
                print(utils.format_response(all_users))


def run():
    args = get_args()

    if args.timeit:
        utils.timefunc(execute_command)(args)
    else:
        execute_command(args)
