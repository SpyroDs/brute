import base64
from queue import Queue
from threading import RLock

from rich.progress import TaskID

from modules.attack import attack_credentials, attack_route, get_screenshot, get_result_record
from modules.cli.output import ProgressBar
from modules.rtsp import Target
from modules.utils import append_result, append_error_brute_creds, append_error_brute_routes, append_error_screenshot

PROGRESS_BAR: ProgressBar
CHECK_PROGRESS: TaskID
BRUTE_PROGRESS: TaskID
SCREENSHOT_PROGRESS: TaskID
LOCK = RLock()
DO_NOT_SAVE_SCREENSHOTS = False


def brute_routes(input_queue: Queue, output_queue: Queue) -> None:
    while True:
        target: Target = input_queue.get()
        if target is None:
            break
        db_result, session = get_result_record(target)

        if not db_result.is_final:
            try:
                result = attack_route(target, db_result)
                if result:
                    output_queue.put(result)
                else:
                    append_error_brute_routes(target.ip)
                    db_result.set('is_final', True)
            except Exception as e:
                append_error_brute_routes(target.ip)
                db_result.set('is_final', False)

            db_result.set_target_common_values(target)
            session.commit()

        input_queue.task_done()


def brute_credentials(input_queue: Queue, output_queue: Queue) -> None:
    while True:
        target: Target = input_queue.get()
        if target is None:
            break

        db_result, session = get_result_record(target)
        if not db_result.is_final:
            try:
                res = attack_credentials(target, db_result)
                if res:
                    output_queue.put(res)
                else:
                    append_error_brute_creds(target.ip)
                    db_result.set('is_final', True)
            except Exception:
                append_error_brute_creds(target.ip)
                db_result.set('is_final', False)

            db_result.set_target_common_values(target)
            session.commit()
        input_queue.task_done()


def screenshot_targets(input_queue: Queue) -> None:
    while True:
        target: Target = input_queue.get()
        if target is None:
            break

        db_result, session = get_result_record(target)
        target_url: str = str(target)

        try:
            image = get_screenshot(target_url)

            if image:
                with open(image, 'rb') as image_file:
                    if not DO_NOT_SAVE_SCREENSHOTS:
                        screenshot = base64.b64encode(image_file.read())
                        db_result.set('screen', screenshot)
                    db_result.set('is_screen', True)
                with LOCK:
                    append_result(image, target_url)
            else:
                db_result.set('is_screen', False)
                append_error_screenshot(target_url)
            db_result.set('is_final', True)
        except Exception as e:
            db_result.set('is_screen', False)
            db_result.set('is_final', False)

        db_result.set_target_common_values(target)
        session.commit()
        input_queue.task_done()
