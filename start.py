import collections
import logging
import resource
import time
import json
from pathlib import Path
from queue import Queue
import av

from modules import attack, utils, worker
from modules.cli.input import parser
from modules.cli.output import console, progress_bar
from modules.rtsp import Target
from modules.utils import start_threads, wait_for, create_zip_archive
from sqlalchemy import MetaData
from modules.db import init_db

metadata = MetaData()

args = parser.parse_args()
engine, Session = init_db(args.keep_database)

metadata.create_all(engine)


def main():
    _, _max = resource.getrlimit(resource.RLIMIT_NOFILE)
    resource.setrlimit(resource.RLIMIT_NOFILE, (_max, _max))

    # Folders and files set up
    report_folder = Path.cwd() / "reports" / time.strftime("%Y.%m.%d-%H.%M.%S")
    log_folder = report_folder / "log"

    attack.DB_SESSION = Session
    attack.PICS_FOLDER = report_folder / "pics"
    utils.RESULT_FILE = report_folder / "result.txt"
    utils.HTML_FILE = report_folder / "index.html"

    utils.ERROR_FILE_BRUTE_ROUTES = log_folder / "routes_error.txt"
    utils.ERROR_FILE_BRUTE_CREDS = log_folder / "creds_fail_error.txt"
    utils.ERROR_FILE_BRUTE_CREDS_EMPTY = log_folder / "creds_empty_error.txt"
    utils.ERROR_FILE_SCREENSHOT = log_folder / "screenshots_error.txt"
    utils.REQUEST_LOG_FILE = log_folder / "request_log.txt"

    utils.create_folder(attack.PICS_FOLDER)

    # Errors
    utils.create_folder(log_folder)
    utils.create_file(utils.RESULT_FILE)
    utils.create_file(utils.ERROR_FILE_BRUTE_ROUTES)
    utils.create_file(utils.ERROR_FILE_BRUTE_CREDS)
    utils.create_file(utils.ERROR_FILE_BRUTE_CREDS_EMPTY)
    utils.create_file(utils.ERROR_FILE_SCREENSHOT)
    utils.create_file(utils.REQUEST_LOG_FILE)

    utils.generate_html(utils.HTML_FILE)

    # Logging module set up
    logger = logging.getLogger()
    attack.logger_is_enabled = args.debug
    if args.debug:
        logger.setLevel(logging.DEBUG)
        file_handler = logging.FileHandler(report_folder / "debug.log")
        file_handler.setFormatter(
            logging.Formatter(
                "[%(asctime)s] [%(levelname)s] [%(threadName)s] [%(funcName)s] %(message)s"
            )
        )
        logger.addHandler(file_handler)

    av.logging.set_level(av.logging.FATAL)

    # Progress output set up
    worker.PROGRESS_BAR = progress_bar
    worker.CHECK_PROGRESS = progress_bar.add_task("[bright_red]Checking...", total=0)
    worker.BRUTE_PROGRESS = progress_bar.add_task("[bright_yellow]Bruting...", total=0)
    worker.SCREENSHOT_PROGRESS = progress_bar.add_task(
        "[bright_green]Screenshoting...", total=0
    )

    targets = collections.deque(set(utils.load_comma_separated(args.targets_comma)))

    # Prepare attack
    attack.ROUTES = utils.load_txt(args.routes, "routes")
    attack.CREDENTIALS = utils.load_txt(args.credentials, "credentials")
    attack.PORTS = args.ports

    check_queue = Queue()
    brute_queue = Queue()
    screenshot_queue = Queue()

    check_threads = start_threads(
        args.check_threads, worker.brute_routes, check_queue, brute_queue
    )
    brute_threads = start_threads(
        args.brute_threads, worker.brute_credentials, brute_queue, screenshot_queue
    )
    screenshot_threads = start_threads(
        args.screenshot_threads, worker.screenshot_targets, screenshot_queue
    )

    while targets:
        check_queue.put(Target(ip=targets.popleft(), timeout=args.timeout, proxy=args.proxy))

    wait_for(check_queue, check_threads)
    wait_for(brute_queue, brute_threads)
    wait_for(screenshot_queue, screenshot_threads)

    screenshots = list(attack.PICS_FOLDER.iterdir())
    folder_name = str(report_folder)
    zip_file_name = folder_name + '.zip'

    create_zip_archive(folder_name, zip_file_name)

    print(json.dumps({
        "archive": zip_file_name,
        "screenshots": len(screenshots),
    }))


if __name__ == "__main__":
    main()
