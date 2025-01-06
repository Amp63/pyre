"""
A package for externally creating code templates for the DiamondFire Minecraft server.

By Amp
"""

import json
from difflib import get_close_matches
import datetime
from typing import Tuple
from enum import Enum
import socket
from mcitemlib.itemlib import Item as NbtItem
from dfpyre.util import *
from dfpyre.items import *
from dfpyre.scriptgen import generate_script, GeneratorFlags
from dfpyre.actiondump import CODEBLOCK_DATA, get_default_tags


VARIABLE_TYPES = {'txt', 'comp', 'num', 'item', 'loc', 'var', 'snd', 'part', 'pot', 'g_val', 'vec', 'pn_el'}
TEMPLATE_STARTERS = {'event', 'entity_event', 'func', 'process'}
DYNAMIC_CODEBLOCKS = {'func', 'process', 'call_func', 'start_process'}

TARGETS = ['Selection', 'Default', 'Killer', 'Damager', 'Shooter', 'Victim', 'AllPlayers', 'Projectile', 'AllEntities', 'AllMobs', 'LastEntity']
TARGET_CODEBLOCKS = {'player_action', 'entity_action', 'if_player', 'if_entity'}

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
    def __init__(self, name: str, args: Tuple=(), target: Target=DEFAULT_TARGET, data: dict={}, tags: dict[str, str]={}):
        self.name = name
        self.args = args
        self.target = target
        self.data = data
        self.tags = tags
    
    def __repr__(self) -> str:
        if self.name == 'dynamic':
            return f'CodeBlock({self.data["block"]}, {self.data["data"]})'
        if self.name == 'else':
            return 'CodeBlock(else)'
        if 'block' in self.data:
            return f'CodeBlock({self.data["block"]}, {self.name})'
        return f'CodeBlock(bracket, {self.data["type"]}, {self.data["direct"]})'

    def __eq__(self, value):
        if not isinstance(value, CodeBlock):
            return False
        return self.name == value.name and \
            self.args == value.args and \
            self.target == value.target and \
            self.data == value.data and \
            self.tags == value.tags

    def build(self, include_tags: bool=True) -> dict:
        """
        Builds a properly formatted block from a CodeBlock object.
        """
        built_block = self.data.copy()
        codeblock_type = self.data.get('block')
        
        # add target if necessary ('Selection' is the default when 'target' is blank)
        if codeblock_type in TARGET_CODEBLOCKS and self.target != DEFAULT_TARGET:
            built_block['target'] = self.target.get_string_value()
        
        # add items into args
        final_args = [arg.format(slot) for slot, arg in enumerate(self.args) if arg.type in VARIABLE_TYPES]
        
        # check for unrecognized name, add tags
        if codeblock_type is not None and codeblock_type != 'else':
            if self.name not in CODEBLOCK_DATA[codeblock_type]:
                _warn_unrecognized_name(codeblock_type, self.name)
            elif include_tags:
                tags = _get_codeblock_tags(codeblock_type, self.name, self.tags)
                if len(final_args) + len(tags) > 27:
                    final_args = final_args[:(27-len(tags))]  # trim list if over 27 elements
                final_args.extend(tags)  # add tags to end
    
        # if final_args:
        built_block['args'] = {'items': final_args}
        return built_block


def _warn_unrecognized_name(codeblock_type: str, codeblock_name: str):
    close = get_close_matches(codeblock_name, CODEBLOCK_DATA[codeblock_type].keys())
    if close:
        warn(f'Code block name "{codeblock_name}" not recognized. Did you mean "{close[0]}"?')
    else:
        warn(f'Code block name "{codeblock_name}" not recognized. Try spell checking or retyping without spaces.')


def _add_inverted(data, inverted):
    """
    If inverted is true, add 'attribute': 'NOT' to data.
    """
    if inverted:
        data['attribute'] = 'NOT'


def _convert_args(args):
    return tuple(map(convert_argument, args))


def _check_applied_tags(tags: list[dict], applied_tags: dict[str, str], codeblock_name: str) -> dict[str, str]:
    if len(applied_tags) > 0 and len(tags) == 0:
        warn(f'Action "{codeblock_name}" does not have any tags, but still received {len(applied_tags)}.')
        return {}
    valid_tags = {}
    tags_formatted = {t['name']: t for t in tags}
    for name, option in applied_tags.items():
        if name not in tags_formatted:
            tag_names_joined = '\n'.join(map(lambda s: '    - '+s, tags_formatted.keys()))
            warn(f'Tag "{name}" does not exist for action "{codeblock_name}". Available tags:\n{tag_names_joined}')
        elif option not in tags_formatted[name]['options']:
            options_joined = '\n'.join(map(lambda s: '    - '+s, tags_formatted[name]['options']))
            warn(f'Tag "{name}" does not have the option "{option}". Available tag options:\n{options_joined}')
        else:
            valid_tags[name] = option
    return valid_tags


def _reformat_codeblock_tags(tags: list[dict], codeblock_type: str, codeblock_name: str, applied_tags: dict[str, str]):
    """
    Turns tag objects into DiamondFire formatted tag items
    """
    
    valid_applied_tags = _check_applied_tags(tags, applied_tags, codeblock_name)
    reformatted_tags = []
    for tag_item in tags:
        tag_name = tag_item['name']
        tag_option = tag_item['default']
        if tag_name in valid_applied_tags:
            tag_option = valid_applied_tags[tag_name]

        new_tag_item = {
            'item': {
                'id': 'bl_tag',
                'data': {
                    'option': tag_option,
                    'tag': tag_name,
                    'action': codeblock_name,
                    'block': codeblock_type
                }
            },
            'slot': tag_item['slot']
        }
        reformatted_tags.append(new_tag_item)
    return reformatted_tags


def _get_codeblock_tags(codeblock_type: str, codeblock_name: str, applied_tags: dict[str, str]):
    """
    Get tags for the specified codeblock type and name
    """
    action_data = CODEBLOCK_DATA[codeblock_type][codeblock_name]
    if 'deprecatedNote' in action_data:
        warn(f'Action "{codeblock_name}" is deprecated: {action_data["deprecatedNote"]}')
    tags = action_data['tags']
    return _reformat_codeblock_tags(tags, codeblock_type, codeblock_name, applied_tags)


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
    template_item.set_custom_data('PublicBukkitValues', pbv_tag, raw=True)

    return template_item


class DFTemplate:
    """
    Represents a DiamondFire code template.
    """
    def __init__(self, name: str=None, author: str='pyre'):
        self.codeblocks: list[CodeBlock] = []
        self.bracket_stack: list[str] = []
        self.name = name
        self.author = author
    

    def __repr__(self) -> str:
        return f'DFTemplate(name: {self.name}, author: {self.author}, codeblocks: {len(self.codeblocks)})'


    @staticmethod
    def from_code(template_code: str):
        """
        Create a template object from an existing template code.
        """
        template_dict = json.loads(df_decode(template_code))
        template = DFTemplate()
        template._set_template_name(template_dict['blocks'][0])
        for block_dict in template_dict['blocks']:
            block_tags = get_default_tags(block_dict.get('block'), block_dict.get('action'))
            if 'args' in block_dict:
                args = []
                for item_dict in block_dict['args']['items']:
                    if item_dict['item'].get('id') == 'bl_tag':
                        tag_data = item_dict['item']['data']
                        block_tags[tag_data['tag']] = tag_data['option']
                    parsed_item = item_from_dict(item_dict['item'])
                    if parsed_item is not None:
                        args.append(parsed_item)
            target = Target(TARGETS.index(block_dict['target'])) if 'target' in block_dict else DEFAULT_TARGET

            codeblock_action = 'bracket'
            if block_dict.get('block') == 'else':
                codeblock_action = 'else'
            elif block_dict.get('block') in DYNAMIC_CODEBLOCKS:
                codeblock_action = 'dynamic'
            elif 'action' in block_dict:
                codeblock_action = block_dict['action']
            
            if codeblock_action == 'bracket' or block_dict['block'] == 'else':
                codeblock = CodeBlock(codeblock_action, data=block_dict)
            else:
                codeblock = CodeBlock(codeblock_action, args, target, block_dict, tags=block_tags)
            template.codeblocks.append(codeblock)
        
        return template


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

        :param bool include_tags: If True, include item tags in code blocks. Otherwise omit them.
        :return: String containing encoded template data.
        """
        template_dict_blocks = [codeblock.build(include_tags) for codeblock in self.codeblocks]
        template_dict = {'blocks': template_dict_blocks}
        first_block = template_dict_blocks[0]
        if first_block['block'] not in TEMPLATE_STARTERS:
            warn('Template does not start with an event, function, or process.')

        self._set_template_name(first_block)

        json_string = json.dumps(template_dict, separators=(',', ':'))
        return df_encode(json_string)
    

    def build_and_send(self, method: Literal['recode', 'codeclient'], include_tags: bool=True) -> int:
        """
        Builds this template and sends it to DiamondFire automatically.
        
        :param bool include_tags: If True, include item tags in code blocks. Otherwise omit them.
        """
        template_code = self.build(include_tags)
        template_item = _get_template_item(template_code, self.name, self.author)
        return template_item.send_to_minecraft(method, 'pyre')
    

    def clear(self):
        """
        Clears this template's data.
        """
        self.__init__()
    

    def _add_codeblock(self, codeblock: CodeBlock, index: int|None):
        if index is None:
            self.codeblocks.append(codeblock)
        else:
            self.codeblocks.insert(index, codeblock)
    

    def _openbracket(self, index: int|None, btype: Literal['norm', 'repeat']='norm'):
        bracket = CodeBlock('bracket', data={'id': 'bracket', 'direct': 'open', 'type': btype})
        self._add_codeblock(bracket, index)
        self.bracket_stack.append(btype)
    

    # command methods
    def player_event(self, name: str, index: int|None=None):
        cmd = CodeBlock(name, data={'id': 'block', 'block': 'event', 'action': name})
        self._add_codeblock(cmd, index)
    

    def entity_event(self, name: str, index: int|None=None):
        cmd = CodeBlock(name, data={'id': 'block', 'block': 'entity_event', 'action': name})
        self._add_codeblock(cmd, index)
    

    def function(self, name: str, *args, tags: dict[str, str]={}, index: int|None=None):
        args = _convert_args(args)
        cmd = CodeBlock('dynamic', args, data={'id': 'block', 'block': 'func', 'data': name}, tags=tags)
        self._add_codeblock(cmd, index)
    

    def process(self, name: str, *args, tags: dict[str, str]={}, index: int|None=None):
        args = _convert_args(args)
        cmd = CodeBlock('dynamic', args, data={'id': 'block', 'block': 'process', 'data': name}, tags=tags)
        self._add_codeblock(cmd, index)
    

    def call_function(self, name: str, *args, index: int|None=None):
        args = _convert_args(args)
        cmd = CodeBlock('dynamic', args, data={'id': 'block', 'block': 'call_func', 'data': name})
        self._add_codeblock(cmd, index)    


    def start_process(self, name: str, tags: dict[str, str]={}, index: int|None=None):
        cmd = CodeBlock('dynamic', data={'id': 'block', 'block': 'start_process', 'data': name}, tags=tags)
        self._add_codeblock(cmd, index)


    def player_action(self, name: str, *args, target: Target=DEFAULT_TARGET, tags: dict[str, str]={}, index: int|None=None):
        args = _convert_args(args)
        cmd = CodeBlock(name, args, target=target, data={'id': 'block', 'block': 'player_action', 'action': name}, tags=tags)
        self._add_codeblock(cmd, index)
    

    def game_action(self, name: str, *args, tags: dict[str, str]={}, index: int|None=None):
        args = _convert_args(args)
        cmd = CodeBlock(name, args, data={'id': 'block', 'block': 'game_action', 'action': name}, tags=tags)
        self._add_codeblock(cmd, index)
    

    def entity_action(self, name: str, *args, target: Target=DEFAULT_TARGET, tags: dict[str, str]={}, index: int|None=None):
        args = _convert_args(args)
        cmd = CodeBlock(name, args, target=target, data={'id': 'block', 'block': 'entity_action', 'action': name}, tags=tags)
        self._add_codeblock(cmd, index)
    

    def if_player(self, name: str, *args, target: Target=DEFAULT_TARGET, tags: dict[str, str]={}, inverted: bool=False, index: int|None=None):
        args = _convert_args(args)
        data = {'id': 'block', 'block': 'if_player', 'action': name}
        _add_inverted(data, inverted)
        cmd = CodeBlock(name, args, target=target, data=data, tags=tags)
        self._add_codeblock(cmd, index)
        self._openbracket(index)
    

    def if_variable(self, name: str, *args, tags: dict[str, str]={}, inverted: bool=False, index: int|None=None):
        args = _convert_args(args)
        data = {'id': 'block', 'block': 'if_var', 'action': name}
        _add_inverted(data, inverted)
        cmd = CodeBlock(name, args, data=data, tags=tags)
        self._add_codeblock(cmd, index)
        self._openbracket(index)
    

    def if_game(self, name: str, *args, tags: dict[str, str]={}, inverted: bool=False, index: int|None=None):
        args = _convert_args(args)
        data = {'id': 'block', 'block': 'if_game', 'action': name}
        _add_inverted(data, inverted)
        cmd = CodeBlock(name, args, data=data, tags=tags)
        self._add_codeblock(cmd, index)
        self._openbracket(index)
    

    def if_entity(self, name: str, *args, target: Target=DEFAULT_TARGET, tags: dict[str, str]={}, inverted: bool=False, index: int|None=None):
        args = _convert_args(args)
        data = {'id': 'block', 'block': 'if_entity', 'action': name}
        _add_inverted(data, inverted)
        cmd = CodeBlock(name, args, target=target, data=data, tags=tags)
        self._add_codeblock(cmd, index)
        self._openbracket(index)


    def else_(self, index: int|None=None):
        cmd = CodeBlock('else', data={'id': 'block', 'block': 'else'})
        self._add_codeblock(cmd, index)
        self._openbracket(index)
    

    def repeat(self, name: str, *args, tags: dict[str, str]={}, sub_action: str=None, index: int|None=None):
        args = _convert_args(args)
        data = {'id': 'block', 'block': 'repeat', 'action': name}
        if sub_action is not None:
            data['subAction'] = sub_action
        cmd = CodeBlock(name, args, data=data, tags=tags)
        self._add_codeblock(cmd, index)
        self._openbracket(index, 'repeat')


    def bracket(self, *args, index: int|None=None):
        args = _convert_args(args)
        cmd = CodeBlock('bracket', data={'id': 'bracket', 'direct': 'close', 'type': self.bracket_stack.pop()})
        self._add_codeblock(cmd, index)
    

    def control(self, name: str, *args, tags: dict[str, str]={}, index: int|None=None):
        args = _convert_args(args)
        cmd = CodeBlock(name, args, data={'id': 'block', 'block': 'control', 'action': name}, tags=tags)
        self._add_codeblock(cmd, index)
    

    def select_object(self, name: str, *args, tags: dict[str, str]={}, index: int|None=None):
        args = _convert_args(args)
        cmd = CodeBlock(name, args, data={'id': 'block', 'block': 'select_obj', 'action': name}, tags=tags)
        self._add_codeblock(cmd, index)
    

    def set_variable(self, name: str, *args, tags: dict[str, str]={}, index: int|None=None):
        args = _convert_args(args)
        cmd = CodeBlock(name, args, data={'id': 'block', 'block': 'set_var', 'action': name}, tags=tags)
        self._add_codeblock(cmd, index)
    
    
    def generate_script(self, output_path: str, indent_size: int=4, literal_shorthand: bool=True, var_shorthand: bool=False):
        """
        Generate an equivalent python script for this template.

        :param str output_path: The file path to write the script to.
        :param int indent_size: The multiple of spaces to add when indenting lines.
        :param bool literal_shorthand: If True, `text` and `num` items will be written as strings and ints respectively.
        :param bool var_shorthand: If True, all variables will be written using variable shorthand.
        """
        flags = GeneratorFlags(indent_size, literal_shorthand, var_shorthand)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(generate_script(self, flags))
        