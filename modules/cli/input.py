import argparse
from pathlib import Path
from typing import Any

DEFAULT_ROUTES = Path(__file__).parent / "../../routes.txt"
DEFAULT_CREDENTIALS = Path(__file__).parent / "../../cred_short.txt"


class CustomHelpFormatter(argparse.HelpFormatter):
    def __init__(self, prog):
        super().__init__(prog, max_help_position=40, width=99)

    def _format_action_invocation(self, action):
        if not action.option_strings or action.nargs == 0:
            return super()._format_action_invocation(action)

        default = self._get_default_metavar_for_optional(action)
        args_string = self._format_args(action, default)
        return ", ".join(action.option_strings) + " " + args_string


def file_path(value: Any):
    if Path(value).exists():
        return Path(value)
    # else:
    #     raise argparse.ArgumentTypeError(f"{value} is not a valid path")


def port(value: Any):
    if int(value) in range(65536):
        return int(value)
    else:
        raise argparse.ArgumentTypeError(f"{value} is not a valid port")


fmt = lambda prog: CustomHelpFormatter(prog)
parser = argparse.ArgumentParser(
    prog="rtspbrute",
    description="Tool for RTSP that brute-forces routes and credentials, makes screenshots!",
    formatter_class=fmt,
)
parser.add_argument(
    "-ip",
    "--targets-ip-port",
    type=file_path,
    help="IP and port targets, separated by :",
)
parser.add_argument(
    "-du",
    "--db-url",
    type=str,
    default="sqlite:///bruter.db",
    help="Database url",
)
parser.add_argument(
    "-id",
    "--brute-id",
    type=str,
    help="Brute id to finish stopped or broken brute",
)
parser.add_argument(
    "-pr",
    "--proxy",
    type=str,
    help="Proxy url i.e. socks5://user:password@192.168.0.1:2000",
)
parser.add_argument(
    "-r",
    "--routes",
    type=file_path,
    default=DEFAULT_ROUTES,
    help="the path on which to load a custom routes",
)
parser.add_argument(
    "-c",
    "--credentials",
    type=file_path,
    default=DEFAULT_CREDENTIALS,
    help="the path on which to load a custom credentials",
)
parser.add_argument(
    "-ct",
    "--check-threads",
    default=100,
    type=int,
    help="the number of threads to brute-force the routes",
    metavar="N",
)
parser.add_argument(
    "-bt",
    "--brute-threads",
    default=50,
    type=int,
    help="the number of threads to brute-force the credentials",
    metavar="N",
)
parser.add_argument(
    "-st",
    "--screenshot-threads",
    default=20,
    type=int,
    help="the number of threads to screenshot the streams",
    metavar="N",
)
parser.add_argument(
    "-T", "--timeout", default=2, type=int, help="the timeout to use for sockets"
)
parser.add_argument(
    "-d",
    "--debug",
    action="store_true",
    help="enable the debug logs"
)
parser.add_argument(
    "-ns",
    "--not-save-screenshots",
    action="store_true",
    help="Do not save screenshots to database"
)

