import base64
import gzip


COL_WARN = '\x1b[33m'
COL_RESET = '\x1b[0m'
COL_SUCCESS = '\x1b[32m'
COL_ERROR = '\x1b[31m'


class PyreException(Exception):
    pass


def warn(message: str):
    print(f'{COL_WARN}! WARNING ! {message}{COL_RESET}')


def df_encode(json_string: str) -> str:
    """
    Encodes a stringified json.
    """
    encoded_string = gzip.compress(json_string.encode('utf-8'))
    return base64.b64encode(encoded_string).decode('utf-8')


def df_decode(encoded_string: str) -> str:
    return gzip.decompress(base64.b64decode(encoded_string.encode('utf-8'))).decode('utf-8')


def flatten(nested_list: list):
    """
    Flattens a list.
    """
    for item in nested_list:
        if isinstance(item, list):
            yield from flatten(item)
        else:
            yield item
