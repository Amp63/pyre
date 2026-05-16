import base64
import gzip
import re
import warnings
from functools import wraps
from collections.abc import Iterable
import keyword


COL_WARN = '\x1b[33m'
COL_RESET = '\x1b[0m'
COL_SUCCESS = '\x1b[32m'
COL_ERROR = '\x1b[31m'

NUMBER_REGEX = re.compile(r'^-?\d*\.?\d+$')


class PyreException(Exception):
    pass


def warn(message: str):
    print(f'{COL_WARN}! WARNING ! {message}{COL_RESET}')


def deprecated(message="This function is deprecated"):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            warnings.warn(
                f"{func.__name__} is deprecated. {message}",
                category=DeprecationWarning,
                stacklevel=2
            )
            return func(*args, **kwargs)
        return wrapper
    return decorator


def is_number(s: str) -> bool:
    return bool(NUMBER_REGEX.match(s))


def df_encode(json_string: str) -> str:
    """
    Encodes a stringified json.
    """
    encoded_string = gzip.compress(json_string.encode('utf-8'))
    return base64.b64encode(encoded_string).decode('utf-8')


def df_decode(encoded_string: str) -> str:
    return gzip.decompress(base64.b64decode(encoded_string.encode('utf-8'))).decode('utf-8')


def flatten(nested_iterable):
    """
    Flattens a nested iterable.
    """
    for item in nested_iterable:
        if isinstance(item, Iterable) and not isinstance(item, (str, bytes)):
            yield from flatten(item)
        else:
            yield item


def to_valid_identifier(s: str):
    """
    Converts a string into a valid Python identifier.
    """
    if not s:
        return "_"
    
    s = re.sub(r'\s+', '_', s)   # Replace whitespace
    s = re.sub(r'[^\w]', '', s)  # Replace invalid characters
    s = re.sub(r'_+', '_', s)    # Condense spans of underscores
    
    s = s.strip("_")

    if s[0].isdigit():
        s = "_" + s
    
    if not s:
        return "_"
    
    if keyword.iskeyword(s):
        s += "_"
    
    return s


def to_valid_identifier_noparen(s: str):
    """
    Converts a string into a valid Python identifier, omitting anything in parentesis.
    """
    s = re.sub(r'\(.*\)', '', s)  # Remove anything in parenthesis
    return to_valid_identifier(s)
