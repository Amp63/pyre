import dataclasses
import re
from dfpyre.items import *

SCRIPT_START = '''from dfpyre import *
t = DFTemplate()
'''

TEMPLATE_METHOD_LOOKUP = {
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
SINGLE_NAME_CODEBLOCKS = {'func', 'process', 'call_func', 'start_process'}
VAR_SCOPES = {'unsaved': 'g', 'saved': 's', 'local': 'l', 'line': 'i'}


@dataclasses.dataclass
class GeneratorFlags:
    indent_size: int
    literal_shorthand: bool
    var_shorthand: bool


def argument_item_to_string(flags: GeneratorFlags, arg_item: object) -> str:
    class_name = arg_item.__class__.__name__
    if isinstance(arg_item, item):
        return f'{class_name}.from_nbt("""{arg_item.get_nbt()}""")'
    
    if isinstance(arg_item, string):
        value = arg_item.value.replace('\n', '\\n')
        return f'{class_name}("{value}")'
    
    if isinstance(arg_item, text):
        value = arg_item.value.replace('\n', '\\n')
        if flags.literal_shorthand:
            return f'"{value}"'
        return f'{class_name}("{value}")'
    
    if isinstance(arg_item, num):
        if not re.match(NUMBER_REGEX, str(arg_item.value)):
            return f'{class_name}("{arg_item.value}")' 
        if flags.literal_shorthand:
            return str(arg_item.value)
        return f'{class_name}({arg_item.value})'
    
    if isinstance(arg_item, loc):
        loc_components = [arg_item.x, arg_item.y, arg_item.z]
        if arg_item.pitch != 0:
            loc_components.append(arg_item.pitch)
        if arg_item.yaw != 0:
            loc_components.append(arg_item.yaw)
        return f'{class_name}({", ".join(str(c) for c in loc_components)})'
    
    if isinstance(arg_item, var):
        if flags.var_shorthand:
            return f'"${VAR_SCOPES[arg_item.scope]}{arg_item.name}"'
        if arg_item.scope == 'unsaved':
            return f'{class_name}("{arg_item.name}")'
        return f'{class_name}("{arg_item.name}", "{arg_item.scope}")'
    
    if isinstance(arg_item, sound):
        return f'{class_name}("{arg_item.name}", {arg_item.pitch}, {arg_item.vol})'
    
    if isinstance(arg_item, particle):
        return f'{class_name}({arg_item.particle_data})'
    
    if isinstance(arg_item, potion):
        return f'{class_name}("{arg_item.name}", {arg_item.dur}, {arg_item.amp})'
    
    if isinstance(arg_item, gamevalue):
        return f'{class_name}("{arg_item.name}", "{arg_item.target}")'
    
    if isinstance(arg_item, parameter):
        param_type_class_name = arg_item.param_type.__class__.__name__
        param_args = [f'"{arg_item.name}"', f'{param_type_class_name}.{arg_item.param_type.name}']
        if arg_item.plural:
            param_args.append('plural=True')
        if arg_item.optional:
            param_args.append('optional=True')
            if arg_item.default_value is not None:
                param_args.append(f'default_value={argument_item_to_string(arg_item.default_value)}')
        if arg_item.description:
            param_args.append(f'description="{arg_item.description}"')
        if arg_item.note:
            param_args.append(f'note="{arg_item.note}"')
        return f'{class_name}({", ".join(param_args)})'
    
    if isinstance(arg_item, vector):
        return f'{class_name}({arg_item.x}, {arg_item.y}, {arg_item.z})'


def add_script_line(flags: GeneratorFlags, script_lines: list[str], indent_level: int, line: str, add_comma: bool=True):
    added_line = ' '*flags.indent_size*indent_level + line
    if add_comma and indent_level > 0:
        added_line += ','
    script_lines.append(added_line)


def generate_script(template, flags: GeneratorFlags) -> str:
    indent_level = 0
    script_lines = []
    for codeblock in template.codeblocks:
        if codeblock.name == 'bracket':
            if codeblock.data['direct'] == 'open':
                add_script_line(flags, script_lines, indent_level, 't.bracket(', False)
                indent_level += 1
            elif codeblock.data['direct'] == 'close':
                indent_level -= 1
                add_script_line(flags, script_lines, indent_level, ')')
            continue
        if codeblock.name == 'else':
            add_script_line(flags, script_lines, indent_level, 't.else_()')
            continue

        method_name = TEMPLATE_METHOD_LOOKUP[codeblock.data['block']]
        method_args = [f'"{codeblock.name}"']
        if codeblock.name in SINGLE_NAME_CODEBLOCKS:
            method_args[0] = f'"{codeblock.data["data"]}"'
        
        codeblock_args = [argument_item_to_string(flags, i) for i in codeblock.args]
        if codeblock_args:
            method_args.extend(codeblock_args)
        if method_name in TARGET_CODEBLOCKS and codeblock.target.name != 'SELECTION':
            method_args.append(f'target=Target.{codeblock.target.name}')
        
        line = f't.{method_name}({", ".join(method_args)})'
        add_script_line(flags, script_lines, indent_level, line)
    return SCRIPT_START + '\n'.join(script_lines)