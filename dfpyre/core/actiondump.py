import os
import json
from pathlib import Path
from typing import TypedDict, Literal
from dfpyre.util.util import warn


ACTIONDUMP_PATH = os.path.join(os.path.dirname(__file__), '../data/actiondump_min.json')
DEPRECATED_ACTIONS_PATH = os.path.join(os.path.dirname(__file__), '../data/deprecated_actions.json')

CODEBLOCK_TYPE_LOOKUP = {
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


VariableType = Literal['VARIABLE', 'NUMBER', 'TEXT', 'COMPONENT', 'ANY_TYPE', 'DICT', 'LIST', 'LOCATION', 'NONE', 'SOUND', 'PARTICLE', 'VECTOR', 'POTION', 'ITEM']


class TagOption(TypedDict):
    name: str
    description: str | None


class ActionTag(TypedDict):
    name: str
    options: list[TagOption]
    default: str
    slot: int


class ActionArgument(TypedDict):
    type: VariableType
    plural: bool
    optional: bool
    description: str | None
    notes: str | None


class ActionData(TypedDict):
    tags: list[ActionTag]
    required_rank = Literal['None', 'Noble', 'Emperor', 'Mythic', 'Overlord']
    arguments: list[tuple[ActionArgument, ...]]
    return_values: list[VariableType]
    description: str | None
    deprecated: bool
    deprecated_note: str | None


class ActiondumpResult(TypedDict):
    codeblock_data: dict[str, dict[str, ActionData]]
    game_values: dict[str, VariableType]
    sound_names: list[str]
    potion_names: list[str]


def get_action_tags(action_data: dict) -> list[ActionTag]:
    action_tags = []
    for tag_data in action_data['tags']:
        options: list[TagOption] = []
        for option in tag_data['options']:
            option_desc = option['icon']['description']
            if option_desc:
                option_desc = ' '.join(option_desc)
            else:
                option_desc = None
            options.append(TagOption(name=option['name'], description=option_desc))
        
        converted_tag = ActionTag(
            name=tag_data['name'],
            options=options,
            default=tag_data['defaultOption'],
            slot=tag_data['slot']
        )
        action_tags.append(converted_tag)
    return action_tags


def get_action_args(action_data: dict) -> list[ActionArgument]:
    icon = action_data['icon']
    if 'arguments' not in icon:
        return []
    
    parsed_arguments: list[ActionArgument] = []
    argument_union_list: list[ActionArgument] = []
    add_to_union = False
    arguments = icon['arguments']
    for arg_data in arguments:
        if 'type' not in arg_data:
            if arg_data.get('text') == 'OR':
                add_to_union = True
            continue

        if argument_union_list and not add_to_union:
            parsed_arguments.append(tuple(argument_union_list))
            argument_union_list = []
        
        arg_description = arg_data['description']
        if arg_description:
            arg_description = ' '.join(arg_description)
        else:
            arg_description = None
        
        arg_notes = arg_data['notes']
        if arg_notes:
            arg_notes = ' '.join(arg_notes[0])
        else:
            arg_notes = None

        argument_union_list.append(ActionArgument(
            type=arg_data['type'],
            plural=arg_data['plural'],
            optional=arg_data['optional'],
            description=arg_description,
            notes=arg_notes
        ))
        add_to_union = False
    
    if argument_union_list:
        parsed_arguments.append(tuple(argument_union_list))
    
    return parsed_arguments


def get_action_return_values(action_data: dict) -> list[VariableType]:
    icon = action_data['icon']
    if 'arguments' not in icon:
        return []
    
    parsed_return_values: list[VariableType] = []
    return_values = icon['returnValues']
    for value_data in return_values:
        if 'type' not in value_data:
            continue
        parsed_return_values.append(value_data['type'])

    return parsed_return_values


def parse_actiondump() -> ActiondumpResult:
    codeblock_data = {n: {} for n in CODEBLOCK_TYPE_LOOKUP.values()}
    codeblock_data['else'] = dict()

    if not os.path.exists(ACTIONDUMP_PATH):
        warn('Actiondump not found -- Item tags and error checking will not work.')
        return ActiondumpResult(codeblock_data={}, game_values=[], sound_names=[], potion_names=[])
    
    with open(ACTIONDUMP_PATH, 'r', encoding='utf-8') as f:
        actiondump: dict = json.loads(f.read())
    
    with open(DEPRECATED_ACTIONS_PATH, 'r', encoding='utf-8') as f:
        all_deprecated_actions: dict = json.loads(f.read())
    
    for action_data in actiondump['actions']:
        action_tags = get_action_tags(action_data)
        
        required_rank = action_data['icon']['requiredRank']
        
        action_arguments = get_action_args(action_data)
        action_return_values = get_action_return_values(action_data)

        action_description = action_data['icon']['description']
        if action_description:
            action_description = ' '.join(action_description)
        else:
            action_description = None
        
        dep_note = action_data['icon']['deprecatedNote']
        if dep_note:
            dep_note = ' '.join(dep_note)
        else:
            dep_note = None
        
        codeblock_type = CODEBLOCK_TYPE_LOOKUP[action_data['codeblockName']]

        deprecated_actions = all_deprecated_actions.get(codeblock_type) or {}
        action_name = action_data['name']
        deprecated = action_name in deprecated_actions
        
        parsed_action_data = ActionData(
            tags=action_tags,
            required_rank=required_rank,
            arguments=action_arguments,
            return_values=action_return_values,
            description=action_description,
            deprecated=deprecated,
            deprecated_note=dep_note
        )
        codeblock_data[codeblock_type][action_name] = parsed_action_data
        
    game_values: dict[str, VariableType] = {}
    for game_value in actiondump['gameValues']:
        icon = game_value['icon']
        game_values[icon['name']] = icon['returnType']

    sound_names: list[str] = []
    for sound in actiondump['sounds']:
        sound_names.append(sound['icon']['name'])
    
    potion_names: list[str] = []
    for potion in actiondump['potions']:
        potion_names.append(potion['icon']['name'])
    
    return ActiondumpResult(
        codeblock_data=codeblock_data,
        game_values=game_values,
        sound_names=sound_names,
        potion_names=potion_names
    )


def get_default_tags(codeblock_type: str|None, codeblock_action: str|None) -> dict[str, str]:
    if not codeblock_type or not codeblock_action:
        return {}
    if codeblock_type not in CODEBLOCK_DATA:
        return {}
    if codeblock_action not in CODEBLOCK_DATA[codeblock_type]:
        return {}
    
    return {t['name']: t['default'] for t in CODEBLOCK_DATA[codeblock_type][codeblock_action]['tags']}


ACTIONDUMP = parse_actiondump()

CODEBLOCK_DATA = ACTIONDUMP['codeblock_data']
