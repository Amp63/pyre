import os

INDENT = ' ' * 4

DATA_PATH = os.path.join(os.path.dirname(__file__), '../data')


def load_data_file(file_name: str):
    path = DATA_PATH + '/' + file_name
    with open(path, 'r') as f:
        return f.read()
