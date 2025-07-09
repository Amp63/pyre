import os
import json
from typing import TypedDict
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
    'SELECT OBJECT': 'select_obj',
    'CONTROL': 'control',
    'PLAYER EVENT': 'event',
    'ENTITY EVENT': 'entity_event',
    'FUNCTION': 'func',
    'CALL FUNCTION': 'call_func',
    'PROCESS': 'process',
    'START PROCESS': 'start_process',
}


class ActiondumpResult(TypedDict):
    codeblock_data: dict[str, dict]
    game_value_names: list[str]
    sound_names: list[str]
    potion_names: list[str]


def get_action_tags(action_data: dict) -> list[dict]:
    action_tags = []
    for tag_data in action_data['tags']:
        options = [o['name'] for o in tag_data['options']]
        converted_tag_data = {
            'name': tag_data['name'],
            'options': options,
            'default': tag_data['defaultOption'],
            'slot': tag_data['slot']
        }
        action_tags.append(converted_tag_data)
    return action_tags


def parse_actiondump() -> ActiondumpResult:
    codeblock_data = {n: {} for n in CODEBLOCK_NAME_LOOKUP.values()}
    codeblock_data['else'] = {'tags': []}

    if not os.path.exists(ACTIONDUMP_PATH):
        warn('data.json not found -- Item tags and error checking will not work.')
        return {}, set()
    
    with open(ACTIONDUMP_PATH, 'r', encoding='utf-8') as f:
        actiondump = json.loads(f.read())
    for action_data in actiondump['actions']:
        action_tags = get_action_tags(action_data)
        parsed_action_data = {'tags': action_tags, 'required_rank': 'None'}
        if dep_note := action_data['icon']['deprecatedNote']:
            parsed_action_data['deprecatedNote'] = ' '.join(dep_note)
        
        required_rank = action_data['icon']['requiredRank']
        if required_rank:
            parsed_action_data['required_rank'] = required_rank
        
        codeblock_name = CODEBLOCK_NAME_LOOKUP[action_data['codeblockName']]
        codeblock_data[codeblock_name][action_data['name']] = parsed_action_data
        if aliases := action_data['aliases']:
            alias_data = parsed_action_data.copy()
            alias_data['alias'] = action_data['name']
            for alias in aliases:
                codeblock_data[codeblock_name][alias] = alias_data
    
    game_value_names: list[str] = []
    for game_value in actiondump['gameValues']:
        game_value_names.append(game_value['icon']['name'])

    sound_names: list[str] = []
    for sound in actiondump['sounds']:
        sound_names.append(sound['icon']['name'])
    
    potion_names: list[str] = []
    for potion in actiondump['potions']:
        potion_names.append(potion['icon']['name'])
    
    return ActiondumpResult(
        codeblock_data=codeblock_data,
        game_value_names=game_value_names,
        sound_names=sound_names,
        potion_names=potion_names
    )


def get_default_tags(codeblock_type: str|None, codeblock_action: str|None) -> dict[str, str]:
    if codeblock_type is None or codeblock_action is None:
        return {}
    return {t['name']: t['default'] for t in CODEBLOCK_DATA[codeblock_type][codeblock_action]['tags']}


ACTIONDUMP = parse_actiondump()

CODEBLOCK_DATA = ACTIONDUMP['codeblock_data']
