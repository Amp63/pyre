from typing import Literal
from enum import Enum
from difflib import get_close_matches
from dfpyre.util.util import warn, flatten
from dfpyre.core.items import convert_literals
from dfpyre.core.actiondump import CODEBLOCK_DATA


VARIABLE_TYPES = {'txt', 'comp', 'num', 'item', 'loc', 'var', 'snd', 'part', 'pot', 'g_val', 'vec', 'pn_el', 'bl_tag'}
TEMPLATE_STARTERS = {'event', 'entity_event', 'func', 'process'}
EVENT_CODEBLOCKS = {'event', 'entity_event'}
CONDITIONAL_CODEBLOCKS = {'if_player', 'if_var', 'if_game', 'if_entity'}
TARGET_CODEBLOCKS = {'player_action', 'entity_action', 'if_player', 'if_entity'}
TARGETS = ['Selection', 'Default', 'Killer', 'Damager', 'Shooter', 'Victim', 'AllPlayers', 'Projectile', 'AllEntities', 'AllMobs', 'LastEntity']


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
        option_strings = [o['name'] for o in tags_formatted[name]['options']]
        if name not in tags_formatted:
            tag_names_joined = '\n'.join(map(lambda s: '    - '+s, tags_formatted.keys()))
            warn(f'Tag "{name}" does not exist for action "{codeblock_name}". Available tags:\n{tag_names_joined}')
        elif option not in option_strings:
            options_joined = '\n'.join(map(lambda s: '    - '+s, option_strings))
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


class CodeBlock:
    def __init__(self, codeblock_type: str, action_name: str, args: tuple=(), target: Target=DEFAULT_TARGET, data: dict={}, tags: dict[str, str]={}):
        self.type = codeblock_type
        self.action_name = action_name
        self.args = [convert_literals(a) for a in flatten(args) if a is not None]
        self.target = target
        self.data = data
        self.tags = tags
    

    @classmethod
    def new_action(cls, codeblock_type: str, action_name: str, args: tuple, tags: dict[str, str], target: Target=DEFAULT_TARGET) -> "CodeBlock":
        return cls(codeblock_type, action_name, args=args, data={'id': 'block', 'block': codeblock_type, 'action': action_name}, tags=tags, target=target)

    @classmethod
    def new_data(cls, codeblock_type: str, data_value: str, args: tuple, tags: dict[str, str]) -> "CodeBlock":
        return cls(codeblock_type, 'dynamic', args=args, data={'id': 'block', 'block': codeblock_type, 'data': data_value}, tags=tags)

    @classmethod
    def new_event(cls, codeblock_type: str, action_name: str, ls_cancel: bool):
        data = {'id': 'block', 'block': codeblock_type, 'action': action_name}
        if ls_cancel:
            data['attribute'] = 'LS-CANCEL'
        return cls(codeblock_type, action_name, data=data)

    @classmethod
    def new_conditional(cls, codeblock_type: str, action_name: str, args: tuple, tags: dict[str, str], inverted: bool, target: Target=DEFAULT_TARGET) -> "CodeBlock":
        data = {'id': 'block', 'block': codeblock_type, 'action': action_name}
        if inverted:
            data['attribute'] = 'NOT'
        return cls(codeblock_type, action_name, args=args, data=data, tags=tags, target=target)

    @classmethod
    def new_subaction_block(cls, codeblock_type: str, action_name: str, args: tuple, tags: dict[str, str], sub_action: str|None, inverted: bool) -> "CodeBlock":
        data = {'id': 'block', 'block': codeblock_type, 'action': action_name}
        if sub_action is not None:
            data['subAction'] = sub_action
            if inverted:
                data['attribute'] = 'NOT'
        return cls(codeblock_type, action_name, args=args, data=data, tags=tags)

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

    
    def get_length(self) -> int:
        """
        Returns the width of this codeblock in Minecraft blocks.
        """
        if self.type in CONDITIONAL_CODEBLOCKS or self.type in {'repeat', 'else'}:
            return 1
        if self.type == 'bracket' and self.data['direct'] == 'open':
            return 1
        return 2


    def build(self) -> dict:
        """
        Builds a properly formatted block from a CodeBlock object.
        """
        built_block = self.data.copy()
        
        # Add target if necessary ('Selection' is the default when 'target' is blank)
        if self.type in TARGET_CODEBLOCKS and self.target != DEFAULT_TARGET:
            built_block['target'] = self.target.get_string_value()
        
        # Add items into args
        final_args = [arg.format(slot) for slot, arg in enumerate(self.args) if arg.type in VARIABLE_TYPES]
        already_applied_tags: dict[str, dict] = {a['item']['data']['tag']: a for a in final_args if a['item']['id'] == 'bl_tag'}
        
        # check for unrecognized name, add tags
        if self.type not in {'bracket', 'else'}:
            if self.action_name not in CODEBLOCK_DATA[self.type]:
                _warn_unrecognized_name(self.type, self.action_name)
            
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
