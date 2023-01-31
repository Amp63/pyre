COL_WARN = '\x1b[33m'
COL_RESET = '\x1b[0m'
COL_SUCCESS = '\x1b[32m'
COL_ERROR = '\x1b[31m'

def warn(message):
    print(f'{COL_WARN}! WARNING ! {message}{COL_RESET}')
