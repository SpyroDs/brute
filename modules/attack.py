import logging
from pathlib import Path
from typing import List

import av
from sqlalchemy.orm import Session

from modules.db import Result
from modules.rtsp import Target, Status
from modules.utils import escape_chars, append_request_log, append_error_brute_empty

ROUTES: List[str]
CREDENTIALS: List[str]
PORTS: List[int]
PICS_FOLDER: Path
DB_SESSION: Session

DUMMY_ROUTE = "/0x8b6c42"
MAX_SCREENSHOT_TRIES = 2

# 401, 403: credentials are wrong but the route might be okay.
# 404: route is incorrect but the credentials might be okay.
# 200: stream is accessed successfully.
ROUTE_OK_CODES = [
    "RTSP/1.0 200",
    "RTSP/1.0 401",
    "RTSP/1.0 403",
    "RTSP/2.0 200",
    "RTSP/2.0 401",
    "RTSP/2.0 403",
]
CREDENTIALS_OK_CODES = ["RTSP/1.0 200", "RTSP/1.0 404", "RTSP/2.0 200", "RTSP/2.0 404"]

logger = logging.getLogger()
logger_is_enabled = True


def attack(target: Target, result: Result, route=None, credentials=None) -> bool:
    if route is None:
        route = target.route
    if credentials is None:
        credentials = target.credentials

    target.connect(result)
    authorized = target.send_describe_request(target.port, route, credentials)

    return bool(authorized)


def get_result_record(target: Target) -> [Result, Session]:
    session = DB_SESSION()
    ip_address = target.ip
    port = target.port
    result = session.query(Result).filter_by(brute_id=target.brute_id, ip_address=ip_address, port=port).first()
    if not result:
        result = Result(brute_id=target.brute_id, ip_address=ip_address, port=port)
        session.add(result)
        session.commit()

    return result, session


def attack_route(target: Target, result: Result):
    # If the stream responds positively to the dummy route, it means
    # it doesn't require (or respect the RFC) a route and the attack
    # can be skipped.

    ok = attack(target, result, route=DUMMY_ROUTE)
    if ok and any(code in target.data for code in ROUTE_OK_CODES):
        target.routes.append("/")

        # Save results to db
        result.set('route', '/')
        result.set('is_route', True)

        return target

    # Otherwise, bruteforce the routes.
    trial = 0
    route_trial = result.route_trial
    for route in ROUTES:
        trial += 1
        result.set('route_trial', trial)
        if int(route_trial) > trial:
            continue

        ok = attack(target, result, route=route)
        if not ok:
            break
        if any(code in target.data for code in ROUTE_OK_CODES):
            target.routes.append(route)

            result.set('route', route)
            result.set('is_route', True)

            return target

    # target.disconnect()


def attack_credentials(target: Target, result: Result):
    def _log_working_stream():
        if logger_is_enabled:
            logger.debug(
                f"Working stream at {target} with {target.auth_method.name} auth"
            )

    if target.is_authorized:
        _log_working_stream()

        result.set('is_creds', True)
        result.set('creds', target.credentials)

        return target

    # If stream responds positively to no credentials, it means
    # it doesn't require them and the attack can be skipped.
    ok = attack(target, result, credentials=":")
    if ok and any(code in target.data for code in CREDENTIALS_OK_CODES):
        _log_working_stream()
        result.set('is_creds', True)
        result.set('creds', target.credentials)

        return target

    # Otherwise, bruteforce the routes.
    trial = 0
    creds_trial = result.creds_trial
    for cred in CREDENTIALS:
        trial += 1
        result.set('creds_trial', trial)
        if int(creds_trial) > trial:
            continue

        ok = attack(target, result, credentials=cred)
        if not ok:
            result.set('is_creds', False)
            break
        if any(code in target.data for code in CREDENTIALS_OK_CODES):
            target.credentials = cred
            _log_working_stream()

            result.set('is_creds', True)
            result.set('creds', cred)

            return target


def _is_video_stream(stream):
    return (
            stream.profile is not None
            and stream.start_time is not None
            and stream.codec_context.format is not None
    )


def get_screenshot(rtsp_url: str, tries=1):
    try:
        with av.open(
                rtsp_url,
                options={
                    "rtsp_transport": "tcp",
                    "rtsp_flags": "prefer_tcp",
                    "stimeout": "3000000",
                },
                timeout=60.0,
        ) as container:
            stream = container.streams.video[0]
            if _is_video_stream(stream):
                file_name = escape_chars(f"{rtsp_url.lstrip('rtsp://')}.jpg")
                file_path = PICS_FOLDER / file_name
                stream.thread_type = "AUTO"
                for frame in container.decode(video=0):
                    frame.to_image().save(file_path)
                    break
                if logger_is_enabled:
                    logger.debug(f"Captured screenshot for {rtsp_url}")
                return file_path
            else:
                # There's a high possibility that this video stream is broken
                # or something else, so we try again just to make sure.
                if tries < MAX_SCREENSHOT_TRIES:
                    container.close()
                    tries += 1
                    return get_screenshot(rtsp_url, tries)
                else:
                    if logger_is_enabled:
                        logger.debug(
                            f"Broken video stream or unknown issues with {rtsp_url}"
                        )
                    return
    except (MemoryError, PermissionError, av.InvalidDataError) as e:
        # These errors occur when there's too much SCREENSHOT_THREADS.
        if logger_is_enabled:
            logger.debug(f"Missed screenshot of {rtsp_url}: {repr(e)}")
        # Try one more time in hope for luck.
        if tries < MAX_SCREENSHOT_TRIES:
            tries += 1
            return get_screenshot(rtsp_url, tries)
        else:
            return
    except Exception as e:
        if logger_is_enabled:
            logger.debug(f"get_screenshot failed with {rtsp_url}: {repr(e)}")
        raise e
