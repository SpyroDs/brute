import collections
import logging
import platform
import time
from pathlib import Path
from queue import Queue

import av
from rich.panel import Panel

from modules import attack, utils, worker
from modules.cli.input import parser
from modules.cli.output import console, progress_bar
from modules.rtsp import Target
from modules.utils import start_threads, wait_for


def main():
    args = parser.parse_args()

    # Folders and files set up
    start_datetime = time.strftime("%Y.%m.%d-%H.%M.%S")
    report_folder = Path.cwd() / "reports" / start_datetime

    attack.PICS_FOLDER = report_folder / "pics"
    utils.RESULT_FILE = report_folder / "result.txt"

    utils.HTML_FILE = report_folder / "index.html"

    log_folder = report_folder / "log"

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
    # This disables ValueError from av module printing to console, but this also
    # means we won't get any logs from av, if they aren't FATAL or PANIC level.
    av.logging.set_level(av.logging.FATAL)

    # Progress output set up
    worker.PROGRESS_BAR = progress_bar
    worker.CHECK_PROGRESS = progress_bar.add_task("[bright_red]Checking...", total=0)
    worker.BRUTE_PROGRESS = progress_bar.add_task("[bright_yellow]Bruting...", total=0)
    worker.SCREENSHOT_PROGRESS = progress_bar.add_task(
        "[bright_green]Screenshoting...", total=0
    )

    # Targets, routes, credentials and ports set up
    targets = collections.deque(set(utils.load_txt(args.targets, "targets")))
    attack.ROUTES = utils.load_txt(args.routes, "routes")
    attack.CREDENTIALS = utils.load_txt(args.credentials, "credentials")
    attack.PORTS = args.ports

    check_queue = Queue()
    brute_queue = Queue()
    screenshot_queue = Queue()

    if platform.system() == "Linux":
        import resource

        _, _max = resource.getrlimit(resource.RLIMIT_NOFILE)
        resource.setrlimit(resource.RLIMIT_NOFILE, (_max, _max))
        console.print(f"[yellow]Temporary ulimit -n set to {_max}")

    if args.debug:
        logger.debug(f"Starting {args.check_threads} threads of worker.brute_routes")

    check_threads = start_threads(
        args.check_threads, worker.brute_routes, check_queue, brute_queue
    )

    print("check threads")

    if args.debug:
        logger.debug(
            f"Starting {args.brute_threads} threads of worker.brute_credentials"
        )

    brute_threads = start_threads(
        args.brute_threads, worker.brute_credentials, brute_queue, screenshot_queue
    )

    print("brute threads")

    if args.debug:
        logger.debug(
            f"Starting {args.screenshot_threads} threads of worker.screenshot_targets"
        )

    screenshot_threads = start_threads(
        args.screenshot_threads, worker.screenshot_targets, screenshot_queue
    )

    print("screen threads")

    console.print("[green]Starting...\n")

    progress_bar.update(worker.CHECK_PROGRESS, total=len(targets))
    progress_bar.start()
    while targets:
        check_queue.put(Target(ip=targets.popleft(), timeout=args.timeout))

    wait_for(check_queue, check_threads)

    print("Finish check threads ============================")
    if args.debug:
        logger.debug("Check queue and threads finished")
    wait_for(brute_queue, brute_threads)

    print("Finish brute threads ============================")
    if args.debug:
        logger.debug("Brute queue and threads finished")
    wait_for(screenshot_queue, screenshot_threads)

    print("Finish screen threads ============================")
    if args.debug:
        logger.debug("Screenshot queue and threads finished")

    progress_bar.stop()

    print()
    screenshots = list(attack.PICS_FOLDER.iterdir())
    console.print(f"[green]Saved {len(screenshots)} screenshots")
    console.print(
        Panel(f"[bright_green]{str(report_folder)}", title="Report", expand=False),
        justify="center",
    )


if __name__ == "__main__":
    main()
