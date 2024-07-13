import os
import json
from dfpyre.util import warn


ACTIONDUMP_PATH = os.path.join(os.path.dirname(__file__), 'data/actiondump_min.json')

CODEBLOCK_NAME_LOOKUP = {
    'PLAYER ACTION': 'player_action',
    'ENTITY ACTION': 'entity_action',
    'GAME ACTION': 'game_action',
    'SET VARIABLE': 'set_var',
    'IF PLAYER': 'if_player',
    'IF ENTITY': 'if_entity',
    'IF GAME': 'if_game',
    'IF VARIABLE': 'if_var',
    'REPEAT': 'repeat',
    'SELECT OBJECT': 'select_object',
    'CONTROL': 'control',
    'PLAYER EVENT': 'event',
    'ENTITY EVENT': 'entity_event',
    'FUNCTION': 'func',
    'CALL FUNCTION': 'call_func',
    'PROCESS': 'process',
    'START PROCESS': 'start_process',
}


def get_action_tags(action_data: dict) -> list[dict]:
    action_tags = []
    for tag_data in action_data['tags']:
        options = [o['name'] for o in tag_data['options']]
        converted_tag_data = {
            'tag': tag_data['name'],
            'options': options,
            'default': tag_data['defaultOption'],
            'slot': tag_data['slot']
        }
        action_tags.append(converted_tag_data)
    return action_tags


def parse_actiondump():
    codeblock_data = {n: {} for n in CODEBLOCK_NAME_LOOKUP.values()}
    codeblock_data['else'] = {'tags': []}

    if not os.path.exists(ACTIONDUMP_PATH):
        warn('data.json not found -- Item tags and error checking will not work.')
        return {}, set()
    
    with open(ACTIONDUMP_PATH, 'r', encoding='utf-8') as f:
        actiondump = json.loads(f.read())
    
    for action_data in actiondump['actions']:
        action_tags = get_action_tags(action_data)
        parsed_action_data = {'tags': action_tags}
        if dep_note := action_data['icon']['deprecatedNote']:
            parsed_action_data['deprecatedNote'] = ' '.join(dep_note)
        
        codeblock_name = CODEBLOCK_NAME_LOOKUP[action_data['codeblockName']]
        codeblock_data[codeblock_name][action_data['name']] = parsed_action_data
    
    return codeblock_data


CODEBLOCK_DATA = parse_actiondump()
