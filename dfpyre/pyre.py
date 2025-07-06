"""
A package for making code templates for the DiamondFire Minecraft server.

By Amp
"""

import json
from difflib import get_close_matches
import datetime
from enum import Enum
from amulet_nbt import CompoundTag
from dfpyre.util import *
from dfpyre.items import *
from dfpyre.scriptgen import generate_script, GeneratorFlags
from dfpyre.actiondump import CODEBLOCK_DATA, get_default_tags
from dfpyre.action_literals import *


VARIABLE_TYPES = {'txt', 'comp', 'num', 'item', 'loc', 'var', 'snd', 'part', 'pot', 'g_val', 'vec', 'pn_el', 'bl_tag'}
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


def _convert_args(args):
    return tuple(map(convert_argument, args))


class CodeBlock:
    def __init__(self, codeblock_type: str, action_name: str, args: tuple=(), target: Target=DEFAULT_TARGET, data: dict={}, tags: dict[str, str]={}):
        self.type = codeblock_type
        self.action_name = action_name
        self.args = args
        self.target = target
        self.data = data
        self.tags = tags
    

    @classmethod
    def new_action(cls, codeblock_type: str, action_name: str, args: tuple, tags: dict[str, str], target: Target=DEFAULT_TARGET) -> "CodeBlock":
        args = _convert_args(args)
        return cls(codeblock_type, action_name, args=args, data={'id': 'block', 'block': codeblock_type, 'action': action_name}, tags=tags, target=target)

    @classmethod
    def new_data(cls, codeblock_type: str, data_value: str, args: tuple, tags: dict[str, str]) -> "CodeBlock":
        args = _convert_args(args)
        return cls(codeblock_type, 'dynamic', args=args, data={'id': 'block', 'block': codeblock_type, 'data': data_value}, tags=tags)

    @classmethod
    def new_conditional(cls, codeblock_type: str, action_name: str, args: tuple, tags: dict[str, str], inverted: bool, target: Target=DEFAULT_TARGET) -> "CodeBlock":
        args = _convert_args(args)
        data = {'id': 'block', 'block': codeblock_type, 'action': action_name}
        if inverted:
            data['attribute'] = 'NOT'
        return cls(codeblock_type, action_name, args=args, data=data, tags=tags, target=target)

    @classmethod
    def new_repeat(cls, action_name: str, args: tuple, tags: dict[str, str], sub_action: str|None, inverted: bool) -> "CodeBlock":
        args = _convert_args(args)
        data = {'id': 'block', 'block': 'repeat', 'action': action_name}
        if inverted:
            data['attribute'] = 'NOT'
        if sub_action is not None:
            data['subAction'] = sub_action
        return cls('repeat', action_name, args=args, data=data, tags=tags)

    @classmethod
    def new_else(cls) -> "CodeBlock":
        return cls('else', 'else', data={'id': 'block', 'block': 'else'})

    @classmethod
    def new_bracket(cls, direction: Literal['open', 'close'], bracket_type: Literal['norm', 'repeat']) -> "CodeBlock":
        return cls('bracket', 'bracket', data={'id': 'bracket', 'direct': direction, 'type': bracket_type})


    def __repr__(self) -> str:
        if self.action_name == 'dynamic':
            return f'CodeBlock({self.data["block"]}, {self.data["data"]})'
        if self.action_name == 'else':
            return 'CodeBlock(else)'
        if 'block' in self.data:
            return f'CodeBlock({self.data["block"]}, {self.action_name})'
        return f'CodeBlock(bracket, {self.data["type"]}, {self.data["direct"]})'


    def build(self, include_tags: bool=True) -> dict:
        """
        Builds a properly formatted block from a CodeBlock object.
        """
        built_block = self.data.copy()
        
        # add target if necessary ('Selection' is the default when 'target' is blank)
        if self.type in TARGET_CODEBLOCKS and self.target != DEFAULT_TARGET:
            built_block['target'] = self.target.get_string_value()
        
        # add items into args
        final_args = [arg.format(slot) for slot, arg in enumerate(self.args) if arg.type in VARIABLE_TYPES]
        already_applied_tags: dict[str, dict] = {a['item']['data']['tag']: a for a in final_args if a['item']['id'] == 'bl_tag'}
        
        # check for unrecognized name, add tags
        if self.type not in {'bracket', 'else'}:
            if self.action_name not in CODEBLOCK_DATA[self.type]:
                _warn_unrecognized_name(self.type, self.action_name)
            
            elif include_tags:
                tags = _get_codeblock_tags(self.type, self.action_name, self.tags)
                for i, tag_data in enumerate(tags):
                    already_applied_tag_data = already_applied_tags.get(tag_data['item']['data']['tag'])
                    if already_applied_tag_data is not None:
                        tags[i] = already_applied_tag_data
                
                if len(final_args) + len(tags) > 27:
                    final_args = final_args[:(27-len(tags))]  # trim list if over 27 elements
                final_args.extend(tags)  # add tags to end

        built_block['args'] = {'items': final_args}
        return built_block


def _warn_unrecognized_name(codeblock_type: str, codeblock_name: str):
    close = get_close_matches(codeblock_name, CODEBLOCK_DATA[codeblock_type].keys())
    if close:
        warn(f'Code block name "{codeblock_name}" not recognized. Did you mean "{close[0]}"?')
    else:
        warn(f'Code block name "{codeblock_name}" not recognized. Try spell checking or retyping without spaces.')


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


def _reformat_codeblock_tags(tags: list[dict], codeblock_type: str, codeblock_action: str, applied_tags: dict[str, str]) -> list[dict]:
    """
    Turns tag objects into DiamondFire formatted tag items.
    """

    def format_tag(option: str, name: str):
        return {
            'item': {
                'id': 'bl_tag',
                'data': {'option': option, 'tag': name, 'action': codeblock_action, 'block': codeblock_type}
            },
            'slot': tag_item['slot']
        }
    
    valid_applied_tags = _check_applied_tags(tags, applied_tags, codeblock_action)
    reformatted_tags = []
    for tag_item in tags:
        tag_name = tag_item['name']
        tag_option = tag_item['default']
        if tag_name in valid_applied_tags:
            tag_option = valid_applied_tags[tag_name]

        new_tag_item = format_tag(tag_option, tag_name)
        reformatted_tags.append(new_tag_item)
    return reformatted_tags


def _get_codeblock_tags(codeblock_type: str, codeblock_name: str, applied_tags: dict[str, str]) -> list[dict]:
    """
    Get tags for the specified codeblock type and name.
    """
    action_data = CODEBLOCK_DATA[codeblock_type][codeblock_name]
    if 'deprecatedNote' in action_data:
        warn(f'Action "{codeblock_name}" is deprecated: {action_data["deprecatedNote"]}')
    tags = action_data['tags']
    return _reformat_codeblock_tags(tags, codeblock_type, codeblock_name, applied_tags)


def _generate_template_item(template_code: str, name: str, author: str) -> Item:
    now = datetime.datetime.now()

    template_item = Item('yellow_shulker_box')
    template_item.set_name(f'&x&f&f&5&c&0&0>> &x&f&f&c&7&0&0{name}')
    template_item.set_lore([
        f'&8Author: {author}',
        f'&8Date: {now.strftime("%Y-%m-%d")}',
        '',
        '&7This template was generated by &6pyre&7.',
        '&7https://github.com/Amp63/pyre'
    ])
    
    custom_data_tag = CompoundTag({
        'PublicBukkitValues': CompoundTag({
            'hypercube:codetemplatedata': StringTag(f'{{"author":"{author}","name":"{name}","version": 1,"code":"{template_code}"}}'),
            'hypercube:pyre_creation_timestamp': DoubleTag(now.timestamp())
        })
    })
    template_item.set_component('minecraft:custom_data', custom_data_tag)

    return template_item


class DFTemplate:
    """
    Represents a DiamondFire code template.
    """
    def __init__(self, codeblocks: list[CodeBlock], author: str='pyre'):
        self.codeblocks = codeblocks
        self.author = author
    

    def _get_template_name(self):
        first_block_data = self.codeblocks[0].data
        if 'data' in first_block_data:
            name = first_block_data['data']
            return name if name else 'Unnamed Template'
        return first_block_data['block'] + '_' + first_block_data['action']


    def __repr__(self) -> str:
        return f'DFTemplate(name: "{self._get_template_name()}", author: "{self.author}", codeblocks: {len(self.codeblocks)})'


    @staticmethod
    def from_code(template_code: str, preserve_item_slots: bool=True):
        """
        Create a template object from an existing template code.

        :param str template_code: The base64 string to create a template from.
        :param bool preserve_item_slots: If True, the positions of items within chests will be saved.
        """
        template_dict = json.loads(df_decode(template_code))
        codeblocks: list[CodeBlock] = []
        for block_dict in template_dict['blocks']:
            block_tags = get_default_tags(block_dict.get('block'), block_dict.get('action'))
            if 'args' in block_dict:
                block_args = []
                for item_dict in block_dict['args']['items']:
                    if item_dict['item'].get('id') == 'bl_tag':
                        tag_data = item_dict['item']['data']
                        block_tags[tag_data['tag']] = tag_data['option']
                    parsed_item = item_from_dict(item_dict, preserve_item_slots)
                    if parsed_item is not None:
                        block_args.append(parsed_item)
            block_target = Target(TARGETS.index(block_dict['target'])) if 'target' in block_dict else DEFAULT_TARGET

            codeblock_type = block_dict.get('block')

            if codeblock_type is None:
                codeblock = CodeBlock.new_bracket(block_dict['direct'], block_dict['type'])
            if codeblock_type == 'else':
                codeblock = CodeBlock.new_else()
            elif codeblock_type in DYNAMIC_CODEBLOCKS:
                codeblock = CodeBlock.new_data(codeblock_type, block_dict['data'], block_args, block_tags)
            elif 'action' in block_dict:
                codeblock = CodeBlock.new_action(codeblock_type, block_dict['action'], block_args, block_tags, block_target)
            codeblocks.append(codeblock)
        
        return DFTemplate(codeblocks)

    
    def insert(self, insert_codeblocks: CodeBlock|list[CodeBlock], index: int=-1) -> "DFTemplate":
        """
        Insert `insert_codeblocks` into this template at `index`.

        :param CodeBlock|list[CodeBlock] insert_codeblocks: The block(s) to insert
        :param int index: The index to insert at.
        :return: self
        """
        if isinstance(insert_codeblocks, list):
            insert_codeblocks = list(flatten(insert_codeblocks))
            if index == -1:
                self.codeblocks.extend(insert_codeblocks)
            else:
                self.codeblocks[index:index+len(insert_codeblocks)] = insert_codeblocks
        elif isinstance(insert_codeblocks, CodeBlock):
            if index == -1:
                index = len(self.codeblocks)
            self.codeblocks.insert(index, insert_codeblocks)
        else:
            raise PyreException('Expected CodeBlock or list[CodeBlock] to insert.')
        return self


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

        json_string = json.dumps(template_dict, separators=(',', ':'))
        return df_encode(json_string)
    

    def build_and_send(self, include_tags: bool=True) -> int:
        """
        Builds this template and sends it to DiamondFire automatically.
        
        :param bool include_tags: If True, include item tags in code blocks. Otherwise omit them.
        """
        template_code = self.build(include_tags)
        template_item = _generate_template_item(template_code, self._get_template_name(), self.author)
        return template_item.send_to_minecraft()
    
    
    def generate_script(self, output_path: str, indent_size: int=4, literal_shorthand: bool=True, var_shorthand: bool=False, preserve_slots: bool=False):
        """
        Generate an equivalent python script for this template.

        :param str output_path: The file path to write the script to.
        :param int indent_size: The multiple of spaces to add when indenting lines.
        :param bool literal_shorthand: If True, `text` and `num` items will be written as strings and ints respectively.
        :param bool var_shorthand: If True, all variables will be written using variable shorthand.
        :param bool preserve_slots: If True, the positions of items within chests will be saved.
        """
        flags = GeneratorFlags(indent_size, literal_shorthand, var_shorthand, preserve_slots)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(generate_script(self, flags))


def _assemble_template(starting_block: CodeBlock, codeblocks: list[CodeBlock], author: str|None) -> DFTemplate:
    """
    Create a DFTemplate object from a starting block and a list of codeblocks.
    `codeblocks` can contain nested lists of CodeBlock objects, so it must be flattened.
    """
    if author is None:
        author = 'pyre'
    template_codeblocks = [starting_block] + list(flatten(codeblocks))  # flatten codeblocks list and insert starting block
    return DFTemplate(template_codeblocks, author)


def player_event(event_name: EVENT_ACTION, codeblocks: list[CodeBlock]=(), author: str|None=None) -> DFTemplate:
    """
    Represents a Player Event codeblock.

    :param str event_name: The name of the event. (Ex: "Join")
    :param list[CodeBlock] codeblocks: The list of codeblocks in this template.
    :param str|None author: The author of this template.
    """
    starting_block = CodeBlock.new_action('event', event_name, (), {})
    return _assemble_template(starting_block, codeblocks, author)


def entity_event(event_name: ENTITY_EVENT_ACTION, codeblocks: list[CodeBlock]=[], author: str|None=None) -> DFTemplate:
    """
    Represents an Entity Event codeblock.

    :param str event_name: The name of the event. (Ex: "EntityDmg")
    :param list[CodeBlock] codeblocks: The list of codeblocks in this template.
    :param str|None author: The author of this template.
    """
    starting_block = CodeBlock.new_action('entity_event', event_name, (), {})
    return _assemble_template(starting_block, codeblocks, author)


def function(function_name: str, *args, tags: dict[str, str]={}, codeblocks: list[CodeBlock]=[], author: str|None=None) -> DFTemplate:
    """
    Represents a Function codeblock.

    :param str event_name: The name of the function.
    :param tuple args: The argument items to include.
    :param dict[str, str] tags: The tags to include.
    :param list[CodeBlock] codeblocks: The list of codeblocks in this template.
    :param str|None author: The author of this template.
    """
    starting_block = CodeBlock.new_data('func', function_name, args, tags)
    return _assemble_template(starting_block, codeblocks, author)


def process(process_name: str, *args, tags: dict[str, str]={}, codeblocks: list[CodeBlock]=[], author: str|None=None) -> DFTemplate:
    """
    Represents a Process codeblock.

    :param str event_name: The name of the process.
    :param tuple args: The argument items to include.
    :param dict[str, str] tags: The tags to include.
    :param list[CodeBlock] codeblocks: The list of codeblocks in this template.
    :param str|None author: The author of this template.
    """
    starting_block = CodeBlock.new_data('process', process_name, args, tags)
    return _assemble_template(starting_block, codeblocks, author)


def call_function(function_name: str, *args) -> CodeBlock:
    """
    Represents a Call Function codeblock.

    :param str event_name: The name of the function.
    :param tuple args: The argument items to include.
    """
    return CodeBlock.new_data('call_func', function_name, args, {})


def start_process(process_name: str, *args, tags: dict[str, str]={}) -> CodeBlock:
    """
    Represents a Call Function codeblock.

    :param str event_name: The name of the function.
    :param tuple args: The argument items to include.
    """
    return CodeBlock.new_data('start_process', process_name, args, tags)


def player_action(action_name: PLAYER_ACTION_ACTION, *args, target: Target=DEFAULT_TARGET, tags: dict[str, str]={}) -> CodeBlock:
    """
    Represents a Player Action codeblock.

    :param str action_name: The name of the action.
    :param tuple args: The argument items to include.
    :param Target target: The target for the action.
    :param dict[str, str] tags: The tags to include.
    """
    return CodeBlock.new_action('player_action', action_name, args, tags, target=target)


def entity_action(action_name: ENTITY_ACTION_ACTION, *args, target: Target=DEFAULT_TARGET, tags: dict[str, str]={}) -> CodeBlock:
    """
    Represents an Entity Action codeblock.

    :param str action_name: The name of the action.
    :param tuple args: The argument items to include.
    :param Target target: The target for the action.
    :param dict[str, str] tags: The tags to include.
    """
    return CodeBlock.new_action('entity_action', action_name, args, tags, target=target)


def game_action(action_name: GAME_ACTION_ACTION, *args, tags: dict[str, str]={}) -> CodeBlock:
    """
    Represents a Game Action codeblock.

    :param str action_name: The name of the action.
    :param tuple args: The argument items to include.
    :param dict[str, str] tags: The tags to include.
    """
    return CodeBlock.new_action('game_action', action_name, args, tags)


def if_player(action_name: IF_PLAYER_ACTION, *args, target: Target=DEFAULT_TARGET, tags: dict[str, str]={}, inverted: bool=False, codeblocks: list[CodeBlock]=[]) -> list[CodeBlock]:
    """
    Represents an If Player codeblock.

    :param str action_name: The name of the condition.
    :param tuple args: The argument items to include.
    :param Target target: The target for the condition.
    :param dict[str, str] tags: The tags to include.
    :param bool inverted: Whether the condition should be inverted.
    :param list[CodeBlock] codeblocks: The list of codeblocks inside the brackets.
    """
    return [
        CodeBlock.new_conditional('if_player', action_name, args, tags, inverted, target),
        CodeBlock.new_bracket('open', 'norm')
    ] + list(codeblocks) + [
        CodeBlock.new_bracket('close', 'norm')
    ]

def if_entity(action_name: IF_ENTITY_ACTION, *args, target: Target=DEFAULT_TARGET, tags: dict[str, str]={}, inverted: bool=False, codeblocks: list[CodeBlock]=[]) -> list[CodeBlock]:
    """
    Represents an If Entity codeblock.

    :param str action_name: The name of the condition.
    :param tuple args: The argument items to include.
    :param Target target: The target for the condition.
    :param dict[str, str] tags: The tags to include.
    :param bool inverted: Whether the condition should be inverted.
    :param list[CodeBlock] codeblocks: The list of codeblocks inside the brackets.
    """
    return [
        CodeBlock.new_conditional('if_entity', action_name, args, tags, inverted, target),
        CodeBlock.new_bracket('open', 'norm')
    ] + list(codeblocks) + [
        CodeBlock.new_bracket('close', 'norm')
    ]


def if_game(action_name: IF_GAME_ACTION, *args, tags: dict[str, str]={}, inverted: bool=False, codeblocks: list[CodeBlock]=[]) -> list[CodeBlock]:
    """
    Represents an If Game codeblock.

    :param str action_name: The name of the condition.
    :param tuple args: The argument items to include.
    :param dict[str, str] tags: The tags to include.
    :param bool inverted: Whether the condition should be inverted.
    :param list[CodeBlock] codeblocks: The list of codeblocks inside the brackets.
    """
    return [
        CodeBlock.new_conditional('if_game', action_name, args, tags, inverted),
        CodeBlock.new_bracket('open', 'norm')
    ] + list(codeblocks) + [
        CodeBlock.new_bracket('close', 'norm')
    ]


def if_variable(action_name: IF_VAR_ACTION, *args, tags: dict[str, str]={}, inverted: bool=False, codeblocks: list[CodeBlock]=[]) -> list[CodeBlock]:
    """
    Represents an If Variable codeblock.

    :param str action_name: The name of the condition.
    :param tuple args: The argument items to include.
    :param dict[str, str] tags: The tags to include.
    :param bool inverted: Whether the condition should be inverted.
    :param list[CodeBlock] codeblocks: The list of codeblocks inside the brackets.
    """
    return [
        CodeBlock.new_conditional('if_var', action_name, args, tags, inverted),
        CodeBlock.new_bracket('open', 'norm')
    ] + list(codeblocks) + [
        CodeBlock.new_bracket('close', 'norm')
    ]


def else_(codeblocks: list[CodeBlock]=[]) -> list[CodeBlock]:
    """
    Represents an Else codeblock.

    :param list[CodeBlock] codeblocks: The list of codeblocks inside the brackets.
    """
    return [
        CodeBlock.new_else(),
        CodeBlock.new_bracket('open', 'norm')
    ] + list(codeblocks) + [
        CodeBlock.new_bracket('close', 'norm')
    ]


def repeat(action_name: REPEAT_ACTION, *args, tags: dict[str, str]={}, sub_action: REPEAT_SUBACTION|None=None, inverted: bool=False, codeblocks: list[CodeBlock]=[]) -> CodeBlock:
    """
    Represents a Repeat codeblock.

    :param str action_name: The name of the action.
    :param tuple args: The argument items to include.
    :param dict[str, str] tags: The tags to include.
    :param str|None sub_action: The sub-action for the repeat action (Only relevant for `While`)
    :param bool inverted: Whether the sub-action condition should be inverted.
    :param list[CodeBlock] codeblocks: The list of codeblocks inside the brackets.
    """
    return [
        CodeBlock.new_repeat(action_name, args, tags, sub_action, inverted),
        CodeBlock.new_bracket('open', 'repeat')
    ] + list(codeblocks) + [
        CodeBlock.new_bracket('close', 'repeat')
    ]


def control(action_name: CONTROL_ACTION, *args, tags: dict[str, str]={}) -> CodeBlock:
    """
    Represents a Control codeblock.

    :param str action_name: The name of the action.
    :param tuple args: The argument items to include.
    :param dict[str, str] tags: The tags to include.
    """
    return CodeBlock.new_action('control', action_name, args, tags)


def select_object(action_name: SELECT_OBJ_ACTION, *args, tags: dict[str, str]={}) -> CodeBlock:
    """
    Represents a Select Object codeblock.

    :param str action_name: The name of the action.
    :param tuple args: The argument items to include.
    :param dict[str, str] tags: The tags to include.
    """
    return CodeBlock.new_action('select_obj', action_name, args, tags) 


def set_variable(action_name: SET_VAR_ACTION, *args, tags: dict[str, str]={}) -> CodeBlock:
    """
    Represents a Set Variable codeblock.

    :param str action_name: The name of the action.
    :param tuple args: The argument items to include.
    :param dict[str, str] tags: The tags to include.
    """
    return CodeBlock.new_action('set_var', action_name, args, tags)
