import base64
import functools
import hashlib


@functools.lru_cache(maxsize=15)
def _basic_auth(credentials):
    encoded_cred = base64.b64encode(credentials.encode("utf-8"))
    return f"Authorization: Basic {str(encoded_cred, 'utf-8')}"


@functools.lru_cache()
def _ha1(username, realm, password):
    return hashlib.md5(f"{username}:{realm}:{password}".encode("utf-8")).hexdigest()


def _digest_auth(option, ip, port, path, credentials, realm, nonce):
    username, password = credentials.split(":")
    uri = f"rtsp://{ip}:{port}{path}"
    HA1 = _ha1(username, realm, password)
    HA2 = hashlib.md5(f"{option}:{uri}".encode("utf-8")).hexdigest()
    response = hashlib.md5(f"{HA1}:{nonce}:{HA2}".encode("utf-8")).hexdigest()

    return (
        "Authorization: Digest "
        f'username="{username}", '
        f'realm="{realm}", '
        f'nonce="{nonce}", '
        f'uri="{uri}", '
        f'response="{response}"'
    )


def describe(ip, port, path, cseq, credentials, realm=None, nonce=None):
    if credentials == ":":
        auth_str = ""
    elif realm:
        auth_str = (
            f"{_digest_auth('DESCRIBE', ip, port, path, credentials, realm, nonce)}\r\n"
        )
    else:
        auth_str = f"{_basic_auth(credentials)}\r\n"

    return (
        f"DESCRIBE rtsp://{ip}:{port}{path} RTSP/1.0\r\n"
        f"CSeq: {cseq}\r\n"
        f"{auth_str}"
        "LibVLC/3.0.17.3 (LIVE555 Streaming Media v2016.11.28)\r\n"
        "Accept: application/sdp\r\n"
        "\r\n"
    )
