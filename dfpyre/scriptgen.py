import dataclasses
import re
from dfpyre.items import *
from dfpyre.actiondump import get_default_tags


SCRIPT_START = '''from dfpyre import *\n\n'''

TEMPLATE_FUNCTION_LOOKUP = {
    'event': 'player_event',
    'entity_event': 'entity_event',
    'func': 'function',
    'process': 'process',
    'call_func': 'call_function',
    'start_process': 'start_process',
    'player_action': 'player_action',
    'game_action': 'game_action',
    'entity_action': 'entity_action',
    'if_player': 'if_player',
    'if_var': 'if_variable',
    'if_game': 'if_game',
    'if_entity': 'if_entity',
    'else': 'else_',
    'repeat': 'repeat',
    'control': 'control',
    'select_obj': 'select_object',
    'set_var': 'set_variable'
}

TARGET_CODEBLOCKS = {'player_action', 'entity_action', 'if_player', 'if_entity'}
CONTAINER_CODEBLOCKS = {'event', 'entity_event', 'func', 'process', 'if_player', 'if_entity', 'if_game', 'if_var', 'else', 'repeat'}
VAR_SCOPES = {'unsaved': 'g', 'saved': 's', 'local': 'l', 'line': 'i'}


@dataclasses.dataclass
class GeneratorFlags:
    indent_size: int
    literal_shorthand: bool
    var_shorthand: bool
    preserve_slots: bool


def item_to_string(class_name: str, i: Item, slot_argument: str):
    i.nbt.pop('DF_NBT', None)
    stripped_id = i.get_id().replace('minecraft:', '')
    if set(i.nbt.keys()) == {'id', 'count'}:
        if i.get_count() == 1:
            return f'{class_name}("{stripped_id}"{slot_argument})'
        return f'{class_name}("{stripped_id}", {i.get_count()}{slot_argument})'
    return f'{class_name}.from_snbt("""{i.get_snbt()}""")'


def argument_item_to_string(flags: GeneratorFlags, arg_item: object) -> str:
    class_name = arg_item.__class__.__name__
    has_slot = arg_item.slot is not None and flags.preserve_slots
    slot_argument = f', slot={arg_item.slot}' if has_slot else ''

    if isinstance(arg_item, Item):
        return item_to_string(class_name, arg_item, slot_argument)
    
    if isinstance(arg_item, String):
        value = arg_item.value.replace('\n', '\\n')
        if not has_slot and flags.literal_shorthand:
            return f'"{value}"'
        return f'{class_name}("{value}"{slot_argument})'
    
    if isinstance(arg_item, Text):
        value = arg_item.value.replace('\n', '\\n')
        return f'{class_name}("{value}"{slot_argument})'
    
    if isinstance(arg_item, Number):
        if not re.match(NUMBER_REGEX, str(arg_item.value)):
            return f'{class_name}("{arg_item.value}"{slot_argument})' 
        if not has_slot and flags.literal_shorthand:
            return str(arg_item.value)
        return f'{class_name}({arg_item.value}{slot_argument})'
    
    if isinstance(arg_item, Location):
        loc_components = [arg_item.x, arg_item.y, arg_item.z]
        if arg_item.pitch != 0:
            loc_components.append(arg_item.pitch)
        if arg_item.yaw != 0:
            loc_components.append(arg_item.yaw)
        return f'{class_name}({", ".join(str(c) for c in loc_components)}{slot_argument})'
    
    if isinstance(arg_item, Variable):
        if not has_slot and flags.var_shorthand:
            return f'"${VAR_SCOPES[arg_item.scope]} {arg_item.name}"'
        if arg_item.scope == 'unsaved':
            return f'{class_name}("{arg_item.name}"{slot_argument})'
        return f'{class_name}("{arg_item.name}", "{arg_item.scope}"{slot_argument})'
    
    if isinstance(arg_item, Sound):
        return f'{class_name}("{arg_item.name}", {arg_item.pitch}, {arg_item.vol}{slot_argument})'
    
    if isinstance(arg_item, Particle):
        return f'{class_name}({arg_item.particle_data})'
    
    if isinstance(arg_item, Potion):
        return f'{class_name}("{arg_item.name}", {arg_item.dur}, {arg_item.amp}{slot_argument})'
    
    if isinstance(arg_item, GameValue):
        if arg_item.target == 'Default':
            return f'{class_name}("{arg_item.name}"{slot_argument})'
        return f'{class_name}("{arg_item.name}", "{arg_item.target}"{slot_argument})'
    
    if isinstance(arg_item, Parameter):
        param_type_class_name = arg_item.param_type.__class__.__name__
        param_args = [f'"{arg_item.name}"', f'{param_type_class_name}.{arg_item.param_type.name}']
        if arg_item.plural:
            param_args.append('plural=True')
        if arg_item.optional:
            param_args.append('optional=True')
            if arg_item.default_value is not None:
                param_args.append(f'default_value={argument_item_to_string(flags, arg_item.default_value)}')
        if arg_item.description:
            param_args.append(f'description="{arg_item.description}"')
        if arg_item.note:
            param_args.append(f'note="{arg_item.note}"')
        return f'{class_name}({", ".join(param_args)}{slot_argument})'
    
    if isinstance(arg_item, Vector):
        return f'{class_name}({arg_item.x}, {arg_item.y}, {arg_item.z}{slot_argument})'


def add_script_line(flags: GeneratorFlags, script_lines: list[str], indent_level: int, line: str, add_comma: bool=True):
    added_line = ' '*flags.indent_size*indent_level + line
    if add_comma and indent_level > 0:
        added_line += ','
    script_lines.append(added_line)


def generate_script(template, flags: GeneratorFlags) -> str:
    indent_level = 0
    script_lines = []

    def remove_comma_from_last_line():
        script_lines[-1] = script_lines[-1][:-1]

    for codeblock in template.codeblocks:
        # Handle closing brackets
        if codeblock.type == 'bracket':
            if codeblock.data['direct'] == 'close':
                remove_comma_from_last_line()
                indent_level -= 1
                add_script_line(flags, script_lines, indent_level, '])')
            continue

        # Get codeblock function and start its arguments with the action
        function_name = TEMPLATE_FUNCTION_LOOKUP[codeblock.type]
        function_args = [f'"{codeblock.action_name}"']

        # Set function or process name if necessary
        if codeblock.action_name == 'dynamic':
            function_args[0] = f'"{codeblock.data["data"]}"'
        
        # Convert argument objects to valid Python strings
        codeblock_args = [argument_item_to_string(flags, i) for i in codeblock.args]
        if codeblock_args:
            function_args.extend(codeblock_args)
        
        # Add target if necessary
        if function_name in TARGET_CODEBLOCKS and codeblock.target.name != 'SELECTION':
            function_args.append(f'target=Target.{codeblock.target.name}')
        
        # Add tags
        if codeblock.tags:
            default_tags = get_default_tags(codeblock.data.get('block'), codeblock.action_name)
            written_tags = {t: o for t, o in codeblock.tags.items() if default_tags[t] != o}
            if written_tags:
                function_args.append(f'tags={str(written_tags)}')
        
        # Add sub-action for repeat
        if codeblock.data.get('subAction'):
            function_args.append(f'sub_action="{codeblock.data["subAction"]}"')
        
        # Add inversion for NOT
        if codeblock.data.get('attribute') == 'NOT':
            function_args.append('inverted=True')

        if codeblock.type in CONTAINER_CODEBLOCKS:
            if codeblock.type == 'else':
                line = f'{function_name}(['
            elif codeblock.type in {'event', 'entity_event'}:
                line = f'{function_name}({", ".join(function_args)}, ['  # omit `codeblocks=` when we don't need it
            else:
                line = f'{function_name}({", ".join(function_args)}, codeblocks=['
            add_script_line(flags, script_lines, indent_level, line, False)
            indent_level += 1
        else:
            line = f'{function_name}({", ".join(function_args)})'
            add_script_line(flags, script_lines, indent_level, line)
    
    remove_comma_from_last_line()
    indent_level -= 1
    add_script_line(flags, script_lines, indent_level, '])')  # add final closing brackets
    return SCRIPT_START + '\n'.join(script_lines)
