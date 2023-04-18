import collections
import json
import resource
import time
import uuid
from pathlib import Path
from queue import Queue
import av

from modules import attack, utils, worker
from modules.cli.input import parser, DEFAULT_ROUTES, DEFAULT_CREDENTIALS
from modules.rtsp import Target
from modules.utils import start_threads, wait_for
from sqlalchemy import MetaData
from modules.db import init_db, Result

metadata = MetaData()
args = parser.parse_args()

engine, session = init_db(args.db_url)
metadata.create_all(engine)


def main():
    attack.logger_is_enabled = args.debug
    av.logging.set_level(av.logging.FATAL)

    if args.targets_ip_port:
        targets_list = collections.deque(set(utils.load_txt(args.targets_ip_port, "targets")))
    else:
        targets_list = collections.deque(set(utils.load_txt(args.targets, "targets")))

    brute_id = str(uuid.uuid4())
    targets = []
    while targets_list:
        unpacked = targets_list.popleft().split(':')
        ip, port = unpacked
        targets.append({"host": ip.strip(), "port": int(port)})

    result = start_brute(
        brute_id,
        targets,
        args.check_threads,
        args.brute_threads,
        args.screenshot_threads,
        args.proxy,
        args.timeout
    )

    screenshots = list(attack.PICS_FOLDER.iterdir())

    print(json.dumps({
        "success": screenshots,
        "results": result,
    }))


def start_brute(brute_id: str, targets: [], check_threads_num=100, brute_threads_num=50, screenshot_thread_num=5,
                proxy=None, timeout=2):
    attack.DB_SESSION = session

    report_folder = Path.cwd() / "reports" / time.strftime("%Y.%m.%d-%H.%M.%S")

    attack.PICS_FOLDER = report_folder / "pics"
    attack.ROUTES = utils.load_txt(DEFAULT_ROUTES, "routes")
    attack.CREDENTIALS = utils.load_txt(DEFAULT_CREDENTIALS, "credentials")

    utils.create_folder(attack.PICS_FOLDER)

    _, _max = resource.getrlimit(resource.RLIMIT_NOFILE)
    resource.setrlimit(resource.RLIMIT_NOFILE, (_max, _max))

    check_queue = Queue()
    brute_queue = Queue()
    screenshot_queue = Queue()

    check_threads = start_threads(
        check_threads_num, worker.brute_routes, check_queue, brute_queue
    )
    brute_threads = start_threads(
        brute_threads_num, worker.brute_credentials, brute_queue, screenshot_queue
    )
    screenshot_threads = start_threads(
        screenshot_thread_num, worker.screenshot_targets, screenshot_queue
    )

    for target in targets:
        check_queue.put(Target(ip=target['host'], brute_id=brute_id, port=target['port'], timeout=timeout, proxy=proxy))

    wait_for(check_queue, check_threads)
    wait_for(brute_queue, brute_threads)
    wait_for(screenshot_queue, screenshot_threads)

    query = session().query(Result).filter(Result.brute_id.in_([brute_id]))
    return [record.get_state() for record in query.all()]


if __name__ == "__main__":
    main()
