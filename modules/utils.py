import ipaddress
import logging
import threading
import re
import zipfile
import os
from pathlib import Path
from queue import Queue
from typing import Callable, List, Union, Any

RESULT_FILE: Path
HTML_FILE: Path

ERROR_FILE_BRUTE_ROUTES: Path
ERROR_FILE_SCREENSHOT: Path
ERROR_FILE_BRUTE_CREDS: Path
ERROR_FILE_BRUTE_CREDS_EMPTY: Path
REQUEST_LOG_FILE: Path

logger = logging.getLogger()
reg = {
    "realm": re.compile(r'realm="(.*?)"'),
    "nonce": re.compile(r'nonce="(.*?)"'),
}

def defined(name):
    try:
        eval(name)
    except NameError:
        return False
    return True

def generate_html(path: Path):
    html = (
        f"<!DOCTYPE html>\n<html>\n<head>\n<title>{path.parent.name}</title>\n"
        """<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<style>   
html{background-color: #141414}
p{text-align: center;color: white;font-family: monospace;}
img{cursor: pointer;border: 2px solid #707070;}
img:hover {border: 2px solid white;}
div.gallery img {width: 100%;height: auto;}
*{box-sizing: border-box;}
.responsive {padding: 6px 6px;float: left;width: 25%;}
@media only screen and (max-width: 700px){.responsive {width: 50%;margin: 1px 0;}}
@media only screen and (max-width: 500px){.responsive {width: 100%;}}
</style>
<link rel="shortcut icon" href="data:image/png;base64,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"/>
</head><body>
<script>window.onload = function () {
var totalNumberOfImages = document.querySelectorAll("div.responsive").length;
document.getElementById("total").innerHTML = ":: Total images: " + totalNumberOfImages + " ::";};
function f(img){
navigator.clipboard.writeText(img.alt);}
</script>
<p id="total"></p>
<p>:: With Javascript enabled: Click on the image to get the corresponding RTSP link ::</p>\n\n"""
    )
    if logger.isEnabledFor(logging.DEBUG):
        logger.debug(f"Generating {path}")
    path.write_text(html)


def create_folder(path: Path):
    if logger.isEnabledFor(logging.DEBUG):
        logger.debug(f"Creating {path}")
    path.mkdir(parents=True)


def create_file(path: Path):
    if logger.isEnabledFor(logging.DEBUG):
        logger.debug(f"Creating {path}")
    path.touch()


def append_request_log(msg: str):
    with REQUEST_LOG_FILE.open("a") as f:
        f.write(f"{msg}\n")


def append_error_brute_creds(ip_address: str):
    if defined('ERROR_FILE_BRUTE_CREDS'):
        with ERROR_FILE_BRUTE_CREDS.open("a") as f:
            f.write(f"{ip_address}\n")


def append_error_brute_empty(ip_address: str):
    if defined('ERROR_FILE_BRUTE_CREDS_EMPTY'):
        with ERROR_FILE_BRUTE_CREDS_EMPTY.open("a") as f:
            f.write(f"{ip_address}\n")


def append_error_brute_routes(ip_address: str):
    if defined('ERROR_FILE_BRUTE_ROUTES'):
        with ERROR_FILE_BRUTE_ROUTES.open("a") as f:
            f.write(f"{ip_address}\n")


def append_error_screenshot(ip_address: str):
    if defined('ERROR_FILE_SCREENSHOT'):
        with ERROR_FILE_SCREENSHOT.open("a") as f:
            f.write(f"{ip_address}\n")


def append_result(pic_file: Path, rtsp_url: str):
    # Append to .txt result file
    if defined('RESULT_FILE'):
        with RESULT_FILE.open("a") as f:
            f.write(f"{rtsp_url}\n")

    # Insert to .html gallery file
    if defined('HTML_FILE') and pic_file.exists():
        with HTML_FILE.open("a") as f:
            f.write(
                (
                    '<div class="responsive"><div class="gallery">\n'
                    f'<img src="{pic_file.parent.name}/{pic_file.name}" alt="{rtsp_url}" '
                    'width="600" height="400" onclick="f(this)"></div></div>\n\n'
                )
            )


def escape_chars(s: str):
    # Escape every character that's not a letter,
    # '_', '-', '.' or space with an '_'.
    return re.sub(r"[^\w\-_. ]", "_", s)


def find(var: str, response: str):
    """Searches for `var` in `response`."""
    match = reg[var].search(response)
    if match:
        return match.group(1)
    else:
        return ""


def load_txt(path: Path, name: str) -> List[str]:
    result = []
    if name == "credentials":
        result = [line.strip("\t\r") for line in get_lines(path)]
    elif name == "routes":
        result = get_lines(path)
    elif name == "targets":
        result = [
            target for line in get_lines(path) for target in parse_input_line(line)
        ]
    return result


def wait_for(queue: Queue, threads: List[threading.Thread]):
    """Waits for queue and then threads to finish."""
    queue.join()
    [queue.put(None) for _ in range(len(threads))]
    [t.join() for t in threads]


def get_lines(path: Path) -> List[str]:
    return path.read_text().splitlines()


def parse_input_line(input_line: str) -> Union[list[str], str, list[Any]]:
    """
    Parse input line and return list with IPs.

    Supported inputs:

        1) 1.2.3.4
        2) 192.168.0.0/24
        3) 1.2.3.4 - 5.6.7.8
    Any non-ip value will be ignored.
    """
    try:
        # Input is in range form ("1.2.3.4 - 5.6.7.8"):
        if "-" in input_line:
            input_ips = input_line.split("-")
            ranges = [
                ipaddr
                for ipaddr in ipaddress.summarize_address_range(
                    ipaddress.IPv4Address(input_ips[0].strip()),
                    ipaddress.IPv4Address(input_ips[1].strip()),
                )
            ]
            return [str(ip) for r in ranges for ip in r]

        # Input is in CIDR form ("192.168.0.0/24"):
        elif "/" in input_line:
            network = ipaddress.ip_network(input_line)
            return [str(ip) for ip in network]

        # IP:PORT
        elif ":" in input_line:
            ip, port = input_line.split(':')
            ipaddress.ip_network(ip)

            return [str(input_line).strip()]

        # Input is a single ip ("1.1.1.1"):
        else:
            ip = ipaddress.ip_address(input_line)
            return [str(ip)]
    except ValueError:
        # If we get any non-ip value just ignore it
        return []


def start_threads(number: int, target: Callable, *args) -> List[threading.Thread]:
    threads = []
    for _ in range(number):
        thread = threading.Thread(target=target, args=args)
        thread.daemon = True
        threads.append(thread)
        thread.start()
    return threads


def create_zip_archive(directory_name: str, zip_file_name: str) -> None:
    # Raise an error if the specified directory does not exist
    if not os.path.exists(directory_name):
        raise FileNotFoundError(f"The directory '{directory_name}' does not exist.")

    # Create a new zip file in write mode
    with zipfile.ZipFile(zip_file_name, "w") as zip_file:

        # Iterate over the files in the directory
        for root, dirs, files in os.walk(directory_name):
            for file in files:
                # Create the full path of the file to add
                file_path = os.path.join(root, file)

                # Add the file to the archive
                zip_file.write(file_path, os.path.relpath(file_path, directory_name))
