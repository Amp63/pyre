import json
import os
from util import warn

# edit this to change where code block data is
DATA_PATH = 'data.json'

tagData = {}
if os.path.exists(DATA_PATH):
    with open(DATA_PATH, 'r') as f:
        tagData = json.load(f)
else:
    warn('data.json not found -- Item tags and error checking will not work.')

TAGDATA_KEYS = set(tagData.keys())
TAGDATA_EXTRAS_KEYS = set(tagData['extras'].keys())
