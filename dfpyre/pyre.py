"""
A package for externally creating code templates for the DiamondFire Minecraft server.

By Amp
2/24/2024
"""

import base64
import gzip
import json
import os
from difflib import get_close_matches
import datetime
from typing import Tuple, List, Dict
from enum import Enum
from mcitemlib.itemlib import Item as NbtItem
from dfpyre.items import *

COL_WARN = '\x1b[33m'
COL_RESET = '\x1b[0m'
COL_SUCCESS = '\x1b[32m'
COL_ERROR = '\x1b[31m'

CODEBLOCK_DATA_PATH = os.path.join(os.path.dirname(__file__), 'data/data.json')

VARIABLE_TYPES = {'txt', 'comp', 'num', 'item', 'loc', 'var', 'snd', 'part', 'pot', 'g_val', 'vec', 'pn_el'}
TEMPLATE_STARTERS = {'event', 'entity_event', 'func', 'process'}

TARGETS = ['Selection', 'Default', 'Killer', 'Damager', 'Shooter', 'Victim', 'AllPlayers', 'Projectile', 'AllEntities', 'AllMobs', 'LastEntity']
TARGET_CODEBLOCKS = {'player_action', 'entity_action', 'if_player', 'if_entity'}

VAR_SHORTHAND_CHAR = '$'
VAR_SCOPES = {'g': 'unsaved', 's': 'saved', 'l': 'local', 'i': 'line'}

CODECLIENT_URL = 'ws://localhost:31375'


class Target(Enum):
    SELECTION = 0
    DEFAULT = 1
    KILLER = 2
    DAMAGER = 3
    SHOOTER = 4
    VICTIM = 5
    ALL_PLAYERS = 6
    PROJECTILE = 7
    ALL_ENTITIES = 8
    ALL_MOBS = 9
    LAST_ENTITY = 10

    def get_string_value(self):
        return TARGETS[self.value]

DEFAULT_TARGET = Target.SELECTION


class CodeBlock:
    def __init__(self, name: str, args: Tuple=(), target: Target=DEFAULT_TARGET, data: Dict={}):
        self.name = name
        self.args = args
        self.target = target
        self.data = data


def _warn(message):
    print(f'{COL_WARN}! WARNING ! {message}{COL_RESET}')


def _warn_unrecognized_name(codeblock_type: str, codeblock_name: str):
    close = get_close_matches(codeblock_name, TAGDATA[codeblock_type].keys())
    if close:
        _warn(f'Code block name "{codeblock_name}" not recognized. Did you mean "{close[0]}"?')
    else:
        _warn(f'Code block name "{codeblock_name}" not recognized. Try spell checking or retyping without spaces.')


def _load_codeblock_data() -> Tuple:
    tag_data = {}
    if os.path.exists(CODEBLOCK_DATA_PATH):
        with open(CODEBLOCK_DATA_PATH, 'r') as f:
            tag_data = json.load(f)
    else:
        _warn('data.json not found -- Item tags and error checking will not work.')
        return ({}, set(), set())
    
    del tag_data['meta']

    all_names = [x for l in [d.keys() for d in tag_data.values()] for x in l]  # flatten list
    return (
        tag_data,
        set(tag_data['extras'].keys()),
        set(all_names)
    )

TAGDATA, TAGDATA_EXTRAS_KEYS, ALL_CODEBLOCK_NAMES = _load_codeblock_data()

def _add_inverted(data, inverted):
    """
    If inverted is true, add 'inverted': 'NOT' to data.
    """
    if inverted:
        data['inverted'] = 'NOT'


def _convert_data_types(args):
    converted_args = []
    for value in args:
        if type(value) in {int, float}:
            converted_args.append(num(value))
        elif type(value) is str:
            if value[0] == VAR_SHORTHAND_CHAR and value[1] in VAR_SCOPES:
                var_object = var(value[2:], VAR_SCOPES[value[1]])
                converted_args.append(var_object)
            else:
                converted_args.append(text(value))
        else:
            converted_args.append(value)
    return tuple(converted_args)


def _reformat_codeblock_tags(tags, codeblock_type: str, codeblock_name: str):
    """
    Turns data.json tag items into DiamondFire formatted tag items
    """
    reformatted_tags = []
    for tag_item in tags:
        action_value = codeblock_name if 'action' not in tag_item else tag_item['action']
        new_tag_item = {
            'item': {
                'id': 'bl_tag',
                'data': {
                    'option': tag_item['option'],
                    'tag': tag_item['tag'],
                    'action': action_value,
                    'block': codeblock_type
                }
            },
            'slot': tag_item['slot']
        }
        reformatted_tags.append(new_tag_item)
    return reformatted_tags


def _get_codeblock_tags(codeblock_type: str, codeblock_name: str):
    """
    Get tags for the specified codeblock type and name
    """
    tags = None
    if codeblock_type in TAGDATA_EXTRAS_KEYS:
        tags = TAGDATA['extras'][codeblock_type]
    else:
        tags = TAGDATA[codeblock_type].get(codeblock_name)
    return _reformat_codeblock_tags(tags, codeblock_type, codeblock_name)


def _build_block(codeblock: CodeBlock, include_tags: bool):
    """
    Builds a properly formatted block from a CodeBlock object.
    """
    final_block = codeblock.data.copy()
    codeblock_type = codeblock.data.get('block')
    
    # add target if necessary ('Selection' is the default when 'target' is blank)
    if codeblock_type in TARGET_CODEBLOCKS and codeblock.target != DEFAULT_TARGET:
        final_block['target'] = codeblock.target.get_string_value()
    
    # add items into args
    final_args = [arg.format(slot) for slot, arg in enumerate(codeblock.args) if arg.type in VARIABLE_TYPES]
    
    # check for unrecognized name, add tags
    if codeblock_type is not None:  # for brackets
        if codeblock_type not in TAGDATA_EXTRAS_KEYS and codeblock.name not in ALL_CODEBLOCK_NAMES:
            _warn_unrecognized_name(codeblock_type, codeblock.name)
        elif include_tags:
            tags = _get_codeblock_tags(codeblock_type, codeblock.name)
            if len(final_args) + len(tags) > 27:
                final_args = final_args[:(27-len(tags))]  # trim list if over 27 elements
            final_args.extend(tags)  # add tags to end
    
    final_block['args'] = {'items': final_args}
    return final_block


def _df_encode(jsonString: str) -> str:
    """
    Encodes a stringified json.
    """
    encodedString = gzip.compress(jsonString.encode('utf-8'))
    return base64.b64encode(encodedString).decode('utf-8')


def _get_template_item(template_code: str, name: str, author: str) -> NbtItem:
    now = datetime.datetime.now()

    template_item = NbtItem('yellow_shulker_box')
    template_item.set_name(f'&x&f&f&5&c&0&0>> &x&f&f&c&7&0&0{name}')
    template_item.set_lore([
        f'&8Author: {author}',
        f'&8Date: {now.strftime("%Y-%m-%d")}',
        '',
        '&7This template was generated by &6pyre&7.',
        '&7https://github.com/Amp63/pyre'
    ])
    
    pbv_tag = {
        'hypercube:codetemplatedata': f'{{"author":"{author}","name":"{name}","version": 1,"code":"{template_code}"}}',
        'hypercube:pyre_creation_timestamp': now.timestamp()
    }
    template_item.set_tag('PublicBukkitValues', pbv_tag, raw=True)

    return template_item


class DFTemplate:
    """
    Represents a DiamondFire code template.
    """
    def __init__(self, name: str=None, author: str='pyre'):
        self.codeblocks: List[CodeBlock] = []
        self.closebracket = None
        self.name = name
        self.author = author


    def _set_template_name(self, first_block):
        if self.name is not None:
            return
        if 'data' in first_block:
            self.name = first_block['data']
            if not self.name:
                self.name = 'Unnamed Template'
        else:
            self.name = first_block['block'] + '_' + first_block['action']


    def build(self, include_tags: bool=True) -> str:
        """
        Build this template.

        :param bool includeTags: If True, include item tags in code blocks. Otherwise omit them.
        :return: String containing encoded template data.
        """
        template_dict_blocks = [_build_block(codeblock, include_tags) for codeblock in self.codeblocks]
        template_dict = {'blocks': template_dict_blocks}
        first_block = template_dict_blocks[0]
        if first_block['block'] not in TEMPLATE_STARTERS:
            _warn('Template does not start with an event, function, or process.')

        self._set_template_name(first_block)

        print(f'{COL_SUCCESS}Template built successfully.{COL_RESET}')

        json_string = json.dumps(template_dict, separators=(',', ':'))
        return _df_encode(json_string)
    

    def build_and_send(self, method: Literal['recode', 'codeclient'], includeTags: bool=True) -> int:
        """
        Builds this template and sends it to DiamondFire automatically.
        
        :param bool includeTags: If True, include item tags in code blocks. Otherwise omit them.
        """
        templateCode = self.build(includeTags)
        templateItem = _get_template_item(templateCode, self.name, self.author)
        return templateItem.send_to_minecraft(method)
    

    def clear(self):
        """
        Clears this template's data.
        """
        self.__init__()
    

    def _openbracket(self, btype: Literal['norm', 'repeat']='norm'):
        bracket = CodeBlock('Bracket', data={'id': 'bracket', 'direct': 'open', 'type': btype})
        self.codeblocks.append(bracket)
        self.closebracket = btype
    

    # command methods
    def player_event(self, name: str):
        cmd = CodeBlock(name, data={'id': 'block', 'block': 'event', 'action': name})
        self.codeblocks.append(cmd)
    

    def entity_event(self, name: str):
        cmd = CodeBlock(name, data={'id': 'block', 'block': 'entity_event', 'action': name})
        self.codeblocks.append(cmd)
    

    def function(self, name: str, *args):
        args = _convert_data_types(args)
        cmd = CodeBlock('function', args, data={'id': 'block', 'block': 'func', 'data': name})
        self.codeblocks.append(cmd)
    

    def process(self, name: str):
        cmd = CodeBlock('process', data={'id': 'block', 'block': 'process', 'data': name})
        self.codeblocks.append(cmd)
    

    def call_function(self, name: str, *args):
        args = _convert_data_types(args)
        cmd = CodeBlock('call_func', args, data={'id': 'block', 'block': 'call_func', 'data': name})
        self.codeblocks.append(cmd)
    

    def start_process(self, name: str):
        cmd = CodeBlock('start_process', data={'id': 'block', 'block': 'start_process', 'data': name})
        self.codeblocks.append(cmd)


    def player_action(self, name: str, *args, target: Target=DEFAULT_TARGET):
        args = _convert_data_types(args)
        cmd = CodeBlock(name, args, target=target, data={'id': 'block', 'block': 'player_action', 'action': name})
        self.codeblocks.append(cmd)
    

    def game_action(self, name: str, *args):
        args = _convert_data_types(args)
        cmd = CodeBlock(name, args, data={'id': 'block', 'block': 'game_action', 'action': name})
        self.codeblocks.append(cmd)
    

    def entity_action(self, name: str, *args, target: Target=DEFAULT_TARGET):
        args = _convert_data_types(args)
        cmd = CodeBlock(name, args, target=target, data={'id': 'block', 'block': 'entity_action', 'action': name})
        self.codeblocks.append(cmd)
    

    def if_player(self, name: str, *args, target: Target=DEFAULT_TARGET, inverted: bool=False):
        args = _convert_data_types(args)
        data = {'id': 'block', 'block': 'if_player', 'action': name}
        _add_inverted(data, inverted)
        cmd = CodeBlock(name, args, target=target, data=data)
        self.codeblocks.append(cmd)
        self._openbracket()
    

    def if_variable(self, name: str, *args, inverted: bool=False):
        args = _convert_data_types(args)
        data = {'id': 'block', 'block': 'if_var', 'action': name}
        _add_inverted(data, inverted)
        cmd = CodeBlock(name, args, data=data)
        self.codeblocks.append(cmd)
        self._openbracket()
    

    def if_game(self, name: str, *args, inverted: bool=False):
        args = _convert_data_types(args)
        data = {'id': 'block', 'block': 'if_game', 'action': name}
        _add_inverted(data, inverted)
        cmd = CodeBlock(name, args, data=data)
        self.codeblocks.append(cmd)
        self._openbracket()
    

    def if_entity(self, name: str, *args, target: Target=DEFAULT_TARGET, inverted: bool=False):
        args = _convert_data_types(args)
        data = {'id': 'block', 'block': 'if_entity', 'action': name}
        _add_inverted(data, inverted)
        cmd = CodeBlock(name, args, target=target, data=data)
        self.codeblocks.append(cmd)
        self._openbracket()


    def else_(self):
        cmd = CodeBlock('else', data={'id': 'block', 'block': 'else'})
        self.codeblocks.append(cmd)
        self._openbracket()
    

    def repeat(self, name: str, *args, sub_action: str=None):
        args = _convert_data_types(args)
        data = {'id': 'block', 'block': 'repeat', 'action': name}
        if sub_action is not None:
            data['subAction'] = sub_action
        cmd = CodeBlock(name, args, data=data)
        self.codeblocks.append(cmd)
        self._openbracket('repeat')


    def bracket(self, *args):
        args = _convert_data_types(args)
        cmd = CodeBlock('Bracket', data={'id': 'bracket', 'direct': 'close', 'type': self.closebracket})
        self.codeblocks.append(cmd)
    

    def control(self, name: str, *args):
        args = _convert_data_types(args)
        cmd = CodeBlock(name, args, data={'id': 'block', 'block': 'control', 'action': name})
        self.codeblocks.append(cmd)
    

    def select_object(self, name: str, *args):
        args = _convert_data_types(args)
        cmd = CodeBlock(name, args, data={'id': 'block', 'block': 'select_obj', 'action': name})
        self.codeblocks.append(cmd)
    

    def set_variable(self, name: str, *args):
        args = _convert_data_types(args)
        cmd = CodeBlock(name, args, data={'id': 'block', 'block': 'set_var', 'action': name})
        self.codeblocks.append(cmd)