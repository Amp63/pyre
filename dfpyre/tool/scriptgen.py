import dataclasses
from dfpyre.util.util import is_number
from dfpyre.core.items import *
from dfpyre.core.actiondump import get_default_tags
from dfpyre.core.codeblock import CodeBlock, CONDITIONAL_CODEBLOCKS, TARGET_CODEBLOCKS, EVENT_CODEBLOCKS
from dfpyre.gen.action_class_data import get_method_name_and_aliases, to_valid_identifier


IMPORT_STATEMENT = 'from dfpyre import *'

CODEBLOCK_FUNCTION_LOOKUP = {
    'event': 'PlayerEvent',
    'entity_event': 'EntityEvent',
    'func': 'Function',
    'process': 'Process',
    'call_func': 'CallFunction',
    'start_process': 'StartProcess',
    'player_action': 'PlayerAction',
    'game_action': 'GameAction',
    'entity_action': 'EntityAction',
    'if_player': 'IfPlayer',
    'if_var': 'IfVariable',
    'if_game': 'IfGame',
    'if_entity': 'IfEntity',
    'else': 'Else',
    'repeat': 'Repeat',
    'control': 'Control',
    'select_obj': 'SelectObject',
    'set_var': 'SetVariable'
}

NO_ACTION_BLOCKS = {'func', 'process', 'call_func', 'start_process', 'else'}
CONTAINER_CODEBLOCKS = {'event', 'entity_event', 'func', 'process', 'if_player', 'if_entity', 'if_game', 'if_var', 'else', 'repeat'}
VAR_SCOPE_LOOKUP = {'unsaved': 'g', 'saved': 's', 'local': 'l', 'line': 'i'}


@dataclasses.dataclass
class GeneratorFlags:
    indent_size: int
    literal_shorthand: bool
    var_shorthand: bool
    preserve_slots: bool
    assign_variable: bool
    include_import: bool
    build_and_send: bool


def item_to_string(class_name: str, i: Item, slot_argument: str):
    i.nbt.pop('DF_NBT')
    stripped_id = i.get_id().replace('minecraft:', '')
    if set(i.nbt.keys()) == {'id', 'count'}:
        if i.get_count() == 1:
            return f"{class_name}('{stripped_id}'{slot_argument})"
        return f"{class_name}('{stripped_id}', {i.get_count()}{slot_argument})"
    
    snbt_string = i.get_snbt().replace('\\"', '\\\\"')
    return f'{class_name}.from_snbt("""{snbt_string}""")'


def escape(s: str) -> str:
    return s.replace('\n', '\\n').replace("\'", "\\'")


def str_literal(s: str) -> str:
    return "'" + escape(s) + "'"


def argument_item_to_string(flags: GeneratorFlags, arg_item: CodeItem) -> str: 
    class_name = arg_item.__class__.__name__
    has_slot = arg_item.slot is not None and flags.preserve_slots
    slot_argument = f', slot={arg_item.slot}' if has_slot else ''

    if isinstance(arg_item, Item):
        return item_to_string(class_name, arg_item, slot_argument)
    
    if isinstance(arg_item, String):
        literal = str_literal(arg_item.value)
        if not has_slot and flags.literal_shorthand:
            return literal
        return f"{class_name}({literal}{slot_argument})"
    
    if isinstance(arg_item, Text):
        literal = str_literal(arg_item.value)
        return f"{class_name}({literal}{slot_argument})"
    
    if isinstance(arg_item, Number):
        if not is_number(str(arg_item.value)):  # Probably a math expression
            return f"{class_name}({str_literal(arg_item.value)}{slot_argument})"
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
        name = escape(arg_item.name)
        if not has_slot and flags.var_shorthand:
            return f"'${VAR_SCOPE_LOOKUP[arg_item.scope]} {name}'"
        if arg_item.scope == 'unsaved':
            return f"{class_name}('{name}'{slot_argument})"
        return f"{class_name}('{name}', '{arg_item.scope}'{slot_argument})"
    
    if isinstance(arg_item, Sound):
        return f"{class_name}({str_literal(arg_item.name)}, {arg_item.pitch}, {arg_item.vol}{slot_argument})"
    
    if isinstance(arg_item, Particle):
        return f'{class_name}({arg_item.particle_data})'
    
    if isinstance(arg_item, Potion):
        return f"{class_name}({str_literal(arg_item.name)}, {arg_item.dur}, {arg_item.amp}{slot_argument})"
    
    if isinstance(arg_item, GameValue):
        name = str_literal(arg_item.name)
        if arg_item.target == 'Default':
            return f"{class_name}({name}{slot_argument})"
        return f"{class_name}({name}, '{arg_item.target}'{slot_argument})"
    
    if isinstance(arg_item, Parameter):
        param_type_class_name = arg_item.param_type.__class__.__name__
        param_args = [str_literal(arg_item.name), f'{param_type_class_name}.{arg_item.param_type.name}']
        if arg_item.plural:
            param_args.append('plural=True')
        if arg_item.optional:
            param_args.append('optional=True')
            if arg_item.default_value is not None:
                param_args.append(f'default_value={argument_item_to_string(flags, arg_item.default_value)}')
        if arg_item.description:
            param_args.append(f"description={str_literal(arg_item.description)}")
        if arg_item.note:
            param_args.append(f"note={str_literal(arg_item.note)}")
        return f'{class_name}({", ".join(param_args)}{slot_argument})'
    
    if isinstance(arg_item, Vector):
        return f'{class_name}({arg_item.x}, {arg_item.y}, {arg_item.z}{slot_argument})'


def string_to_python_name(string: str) -> str:
    """Converts `string` into a valid python identifier."""
    string = string.strip()
    if string[0].isnumeric():
        string = '_' + string
    return ''.join(c if c.isalnum() else '_' for c in string)


def add_script_line(flags: GeneratorFlags, script_lines: list[str], indent_level: int, line: str, add_comma: bool=True):
    added_line = ' '*flags.indent_size*indent_level + line
    if add_comma and indent_level > 0:
        added_line += ','
    script_lines.append(added_line)


def generate_script(codeblocks: list[CodeBlock], flags: GeneratorFlags) -> str:
    indent_level = 0
    script_lines = []
    variable_assigned = False

    if flags.include_import:
        script_lines.append(IMPORT_STATEMENT + '\n')
        
    def remove_comma_from_last_line():
        if script_lines[-1].endswith(','):
            script_lines[-1] = script_lines[-1][:-1]
    
    def get_var_assignment_snippet() -> str:
        first_block_data = codeblocks[0].data
        if 'data' in first_block_data:
            name = first_block_data['data']
            var_name = name if name else 'unnamed_template'
        else:
            var_name = first_block_data['block'] + '_' + first_block_data['action']
        return f'{string_to_python_name(var_name)} = '


    for codeblock in codeblocks:
        # Handle closing brackets
        if codeblock.type == 'bracket':
            if codeblock.data['direct'] == 'close':
                remove_comma_from_last_line()
                indent_level -= 1
                add_script_line(flags, script_lines, indent_level, '])')
            continue

        # Get codeblock function and start its arguments with the action
        function_name = CODEBLOCK_FUNCTION_LOOKUP[codeblock.type]
        if codeblock.type in NO_ACTION_BLOCKS:
            function_args = [str_literal(codeblock.action_name)]
        else:
            method_data = get_method_name_and_aliases(codeblock.type, codeblock.action_name)
            if method_data is None:
                raise PyreException(f'scriptgen: Failed to get method data of {codeblock.action_name}')

            function_name += f'.{method_data[0]}'
            function_args = []

        # Add variable assignment if necessary
        var_assignment_snippet = ''
        if flags.assign_variable and not variable_assigned:
            var_assignment_snippet = get_var_assignment_snippet()
            variable_assigned = True

        # Set function or process name if necessary
        if codeblock.action_name == 'dynamic':
            function_args[0] = str_literal(codeblock.data["data"])
        
        # Convert argument objects to valid Python strings
        codeblock_args = [argument_item_to_string(flags, i) for i in codeblock.args]
        if codeblock_args:
            function_args.extend(codeblock_args)
        
        sub_action = codeblock.data.get('subAction')
        
        # Add tags
        if codeblock.tags:
            default_tags = codeblock.tags
            if sub_action is not None:
                for conditional_block_type in CONDITIONAL_CODEBLOCKS:
                    default_tags = get_default_tags(conditional_block_type, sub_action)
                    if default_tags:
                        break
            else:
                default_tags = get_default_tags(codeblock.data.get('block'), codeblock.action_name)
            
            for tag, option in codeblock.tags.items():
                if default_tags[tag] != option:
                    tag_param_name = to_valid_identifier(tag.lower())
                    function_args.append(f"{tag_param_name}='{option}'")
        
        # Add sub-action for repeat and select object
        if sub_action is not None:
            function_args.append(f"sub_action='{sub_action}'")
        
        # Add target if necessary
        if codeblock.type in TARGET_CODEBLOCKS and codeblock.target.name != 'SELECTION':
            function_args.append(f'target=Target.{codeblock.target.name}')
        
        codeblock_attribute = codeblock.data.get('attribute')
        # Add inversion for NOT
        if codeblock_attribute == 'NOT':
            function_args.append('inverted=True')
        
        # Add LS Cancel
        elif codeblock_attribute == 'LS-CANCEL':
            function_args.append('ls_cancel=True')

        # Create and add the line
        if codeblock.type in CONTAINER_CODEBLOCKS:
            if codeblock.type == 'else':
                line = f'{function_name}(['
            elif codeblock.type in EVENT_CODEBLOCKS and codeblock_attribute is None:
                line = f'{var_assignment_snippet}{function_name}(['  # omit `codeblocks=` when we don't need it
            else:
                line = f'{var_assignment_snippet}{function_name}({", ".join(function_args)}, codeblocks=['
            add_script_line(flags, script_lines, indent_level, line, False)
            indent_level += 1
        else:
            line = f'{function_name}({", ".join(function_args)})'
            add_script_line(flags, script_lines, indent_level, line)
    
    remove_comma_from_last_line()
    indent_level -= 1
    add_script_line(flags, script_lines, indent_level, '])')  # add final closing brackets

    # Add `.build_and_send()` if necessary
    if flags.build_and_send:
        script_lines[-1] += '.build_and_send()'
    
    return '\n'.join(script_lines)
