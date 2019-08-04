from argparse import ArgumentParser
import getpass
from app.database import init_db

parser = ArgumentParser("Initialise DB for Flask app")
parser.add_argument('--password', '-p', default=None,
                    help="The password for the admin account")
args = parser.parse_args()

if args.password is None:
    password = getpass.getpass(
        "Please enter password for admin account "
        "('manager.mbi@monash.edu'): ")
else:
    password = args.password

init_db(password)
