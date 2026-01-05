import os
import json
from typing import Literal
from dataclasses import dataclass
from dfpyre.util.util import warn


ACTIONDUMP_PATH = os.path.join(os.path.dirname(__file__), '../data/actiondump_min.json')
DEPRECATED_ACTIONS_PATH = os.path.join(os.path.dirname(__file__), '../data/deprecated_actions.json')

CODEBLOCK_ID_LOOKUP = {
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


@dataclass
class CodeblockDataEntry:
    name: str
    id: str
    description: str
    examples: list[str]


@dataclass
class TagOption:
    name: str
    description: str | None


@dataclass
class ActionTag:
    name: str
    options: list[TagOption]
    default: str
    slot: int


@dataclass
class ActionArgument:
    type: VariableType
    plural: bool
    optional: bool
    description: str | None
    notes: str | None


@dataclass
class ActionDataEntry:
    tags: list[ActionTag]
    required_rank: Literal['None', 'Noble', 'Emperor', 'Mythic', 'Overlord']
    arguments: list[tuple[ActionArgument, ...]]
    return_values: list[VariableType]
    description: str | None
    is_deprecated: bool
    deprecated_note: str | None


@dataclass
class ParticleEntry:
    id: str
    name: str
    category: str
    fields: list[str]
    additional_info: str | None
    icon_material: str
    icon_color: tuple[int, int, int] | None = None
    icon_head_data: str | None = None


@dataclass
class ActiondumpResult:
    codeblock_data: dict[str, CodeblockDataEntry]
    action_data: dict[str, dict[str, ActionDataEntry]]
    particle_data: list[ParticleEntry]
    game_values: dict[str, VariableType]
    sound_names: list[str]
    potion_names: list[str]


def parse_action_tags(action_data: dict):
    action_tags: list[ActionTag] = []

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


def parse_action_args(action_data: dict) -> list[ActionArgument]:
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


def parse_codeblock_data(raw_codeblock_data: list[dict]) -> dict[str, CodeblockDataEntry]:
    parsed_data: dict[str, CodeblockDataEntry] = {}
    for raw_data in raw_codeblock_data:
        identifier = raw_data['identifier']
        description = ' '.join(raw_data['item']['description'])
        parsed_codeblock = CodeblockDataEntry(
            name=raw_data['name'],
            id=identifier,
            description=description,
            examples=raw_data['item']['example']
        )
        parsed_data[identifier] = parsed_codeblock
    
    return parsed_data


def parse_action_data(raw_action_data: list[dict]):
    all_action_data = {n: {} for n in CODEBLOCK_ID_LOOKUP.values()}
    all_action_data['else'] = dict()

    with open(DEPRECATED_ACTIONS_PATH, 'r', encoding='utf-8') as f:
        all_deprecated_actions: dict = json.loads(f.read())

    for action_data in raw_action_data:
        action_tags = parse_action_tags(action_data)
        
        required_rank = action_data['icon']['requiredRank']
        
        action_arguments = parse_action_args(action_data)
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
        
        codeblock_type = CODEBLOCK_ID_LOOKUP[action_data['codeblockName']]

        deprecated_actions = all_deprecated_actions.get(codeblock_type) or {}
        action_name = action_data['name']
        is_deprecated = action_name in deprecated_actions
        
        parsed_action_data = ActionDataEntry(
            tags=action_tags,
            required_rank=required_rank,
            arguments=action_arguments,
            return_values=action_return_values,
            description=action_description,
            is_deprecated=is_deprecated,
            deprecated_note=dep_note
        )
        all_action_data[codeblock_type][action_name] = parsed_action_data
    
    return all_action_data


def parse_particle_data(raw_particle_data: list[dict]):
    particle_entries: list[ParticleEntry] = []

    for par_data in raw_particle_data:
        category = par_data['category']
        if category is None:
            continue  # Probably deprecated, skip

        icon: dict = par_data['icon']

        additional_info = icon['additionalInfo']
        if additional_info:
            additional_info = ' '.join(additional_info[0])
        else:
            additional_info = None
        
        icon_color: dict | None = icon.get('color')
        if icon_color is not None:
            icon_color = tuple(icon_color.values())
        
        icon_head_data: str | None = icon.get('head')

        par_entry = ParticleEntry(
            par_data['particle'],
            icon['name'],
            category,
            par_data['fields'],
            additional_info,
            icon['material'],
            icon_color,
            icon_head_data
        )
        particle_entries.append(par_entry)
    
    return particle_entries


def parse_actiondump() -> ActiondumpResult:
    if not os.path.isfile(ACTIONDUMP_PATH):
        warn('Actiondump not found -- Item tags and error checking will not work.')
        return ActiondumpResult(codeblock_data={}, action_data={}, game_values=[], sound_names=[], potion_names=[])
    
    with open(ACTIONDUMP_PATH, 'r', encoding='utf-8') as f:
        actiondump: dict = json.loads(f.read())

    codeblock_data = parse_codeblock_data(actiondump['codeblocks'])
    all_action_data = parse_action_data(actiondump['actions'])
    particle_data = parse_particle_data(actiondump['particles'])
        
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
        action_data=all_action_data,
        particle_data=particle_data,
        game_values=game_values,
        sound_names=sound_names,
        potion_names=potion_names
    )


ACTIONDUMP = parse_actiondump()
ACTION_DATA = ACTIONDUMP.action_data


def get_default_tags(codeblock_type: str|None, codeblock_action: str|None) -> dict[str, str]:
    if not codeblock_type or not codeblock_action:
        return {}
    if codeblock_type not in ACTION_DATA:
        return {}
    if codeblock_action not in ACTION_DATA[codeblock_type]:
        return {}
    
    return {t.name: t.default for t in ACTION_DATA[codeblock_type][codeblock_action].tags}
