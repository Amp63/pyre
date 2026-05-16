"""
Generates Codeblock classes with static methods for each action.
"""

from dataclasses import dataclass
import re
from num2words import num2words
from dfpyre.core.actiondump import ACTIONDUMP, ActionArgument, ActionTag, TagOption
from dfpyre.util.util import flatten, to_valid_identifier_noparen
from dfpyre.gen.gen_data import INDENT
from dfpyre.gen.action_gen_data import (
    CODEBLOCK_LOOKUP, PARAM_NAME_REPLACEMENTS, PARAM_TYPE_LOOKUP, TEMPLATE_OVERRIDES, OUTPUT_PATH, IMPORTS, CLASS_ALIASES,
    get_method_name_and_aliases
)


@dataclass
class ParameterData:
    name: str
    types: str
    description: str
    notes: str
    is_optional: bool
    has_none: bool

    def get_varname(self) -> str:
        if self.description == 'Variable to set':
            return 'result'
        
        if ' OR ' in self.description:
            # Only take the first part if it has multiple types
            varname = to_valid_identifier_noparen(self.description.partition(' OR ')[0]).lower()
        else:
            varname = to_valid_identifier_noparen(self.description).lower()

        if varname == 'target':
            varname = f'{varname}_{self.name}'
        
        # Simplify some names
        if m := re.match(r'^_(\d+)_(.*)$', varname):
            # Make names starting with numbers more readable
            readable_num: str = num2words(int(m.group(1)))
            varname = readable_num + '_' + m.group(2)
        
        if m := re.match(r'^(.+)_to_get.*$', varname):
            # Replace "___ to get ___" with simpler name
            varname = m.group(1)
        
        if m := re.match(r'^gets_the_current_(.+)_each_iteration$', varname):
            # Make this name shorter
            varname = m.group(1) + '_var'
        
        if m := re.match(r'^(.+)_of_(.+)_to_.+$', varname):
            # Replace "___ of ___ to ___" with simpler name
            varname = m.group(2) + '_' + m.group(1)
        
        if m := re.match(r'^(.+)_in_ticks$', varname):
            # Replace "___ in ticks" with simpler name
            varname = m.group(1)
        
        if len(varname) > 20:
            print(varname)

        return varname

    def get_param_string(self) -> str:
        param_str = f'{self.get_varname()}: {self.types}'
        if self.has_none or self.is_optional:
            param_str += '=None'
        return param_str

    def get_docstring(self) -> str:
        docstring = f':param {self.types} {self.get_varname()}: {self.description}'
        if self.is_optional:
            docstring += ' (optional)'
        if self.notes:
            docstring += f' ({self.notes})'
        return docstring

    def __eq__(self, value):
        return self is value


def parse_parameters(action_arguments: list[tuple[ActionArgument, ...]]) -> list[ParameterData]:
    parameter_list: list[ParameterData] = []
    prev_optional_exists = False

    for arg_union in action_arguments:
        if len(arg_union) == 1:
            param_name = arg_union[0].type.lower()
            if param_name in PARAM_NAME_REPLACEMENTS:
                param_name = PARAM_NAME_REPLACEMENTS[param_name]
        else:
            param_name = f'arg'

        is_optional = arg_union[0].optional
        has_none = 'NONE' in (arg.type for arg in arg_union)
        
        param_types_list = list(flatten(PARAM_TYPE_LOOKUP[arg.type] for arg in arg_union))
        if is_optional:
            param_types_list.append('None')
            prev_optional_exists = True
        elif prev_optional_exists:
            # If a previous optional param exists, all subsequent params must be
            # optional as well, so we set `has_none` to True to add `=None` to future params.
            has_none = True
        
        param_types_dedup = list(dict.fromkeys(param_types_list))
        param_types = ' | '.join(param_types_dedup)

        if arg_union[0].plural:
            param_name += 's'
            plural_param_types = ' | '.join(t for t in param_types_dedup if t != 'None')  # Doesn't make sense to have a list of None
            param_types = f'list[{plural_param_types}] | {param_types}'

        param_description = ' OR '.join(arg.description for arg in arg_union if arg.description)
        param_notes = ' OR '.join(arg.notes for arg in arg_union if arg.notes)

        param = ParameterData(param_name, param_types, param_description, param_notes, is_optional, has_none)
        parameter_list.append(param)
    
    # Add numbers to params with duplicate names
    param_names = [p.name for p in parameter_list]
    param_name_lookup = {p.name: [q for q in parameter_list if p.name == q.name] for p in parameter_list}
    for param in parameter_list:
        if param_names.count(param.name) > 1:
            params_with_name = param_name_lookup[param.name]
            param_index = params_with_name.index(param)
            param.name += str(param_index + 1)

    return parameter_list


@dataclass
class TagData:
    name: str
    options: list[TagOption]
    default: str

    def get_varname(self, param_names: set[str]) -> str:
        valid_name = to_valid_identifier_noparen(self.name.lower())
        if valid_name in param_names:
            valid_name += '_tag'
        return valid_name

    # Pass `param_names` here to prevent name conflicts with existing parameters
    def get_param_string(self, param_names: set[str]) -> str:
        options_list = ', '.join(f'"{o.name}"' for o in self.options)
        tag_type = f'Literal[{options_list}]'
        return f'{self.get_varname(param_names)}: {tag_type}="{self.default}"'

    def get_docstring(self, param_names: set[str]) -> str:
        docstring_lines = [f':param str {self.get_varname(param_names)}: {self.name}']
        docstring_lines += [f'{INDENT*2}- {o.name}: {o.description}' for o in self.options if o.description]
        if len(docstring_lines) > 1:
            docstring_lines.insert(1, '')
        return '\n'.join(docstring_lines)


def parse_tags(action_tags: list[ActionTag]) -> list[TagData]:
    return [TagData(t.name, t.options, t.default) for t in action_tags]


def generate_actions():
    generated_lines: list[str] = IMPORTS.copy()
    generated_lines += ['']
    
    for codeblock_type, actions in ACTIONDUMP.action_data.items():
        codeblock_data = CODEBLOCK_LOOKUP.get(codeblock_type)
        if codeblock_data is None:
            continue
            
        class_name, method_template = codeblock_data

        class_docstring = ACTIONDUMP.codeblock_data[codeblock_type].description
        class_def_lines = [
            f'class {class_name}:',
            f'{INDENT}"""',
            f'{INDENT}{class_docstring}',
            f'{INDENT}"""',
            ''
        ]
        generated_lines += class_def_lines

        for action_name, action_data in actions.items():
            if action_data.is_deprecated:
                # Skip deprecated actions
                continue
            
            # Get method name
            method_data = get_method_name_and_aliases(codeblock_type, action_name)
            if method_data is None:
                continue
            method_name, method_aliases = method_data

            # Choose method template to use
            current_method_template = method_template
            template_overrides = TEMPLATE_OVERRIDES.get(codeblock_type)
            if template_overrides:
                override_template = template_overrides.get(action_name)
                if override_template is not None:
                    current_method_template = override_template
            
            # Get description
            action_description = action_data.description or ''
            if action_description:
                action_description = f'{INDENT}{action_description}\n\n'
            
            # Get parameter data
            parameters = parse_parameters(action_data.arguments)

            parameter_list = ', '.join(p.get_param_string() for p in parameters)
            if parameter_list:
                parameter_list += ', '
            
            parameter_names = ', '.join(p.get_varname() for p in parameters)
            if parameter_names:
                parameter_names += ','
            
            
            # Get tag data
            tags = parse_tags(action_data.tags)

            param_name_set = set(p.get_varname() for p in parameters)
            tag_parameter_list = ', '.join(t.get_param_string(param_name_set) for t in tags)
            if tag_parameter_list:
                tag_parameter_list = f'{tag_parameter_list}, '
            
            tag_values = ', '.join(f"'{t.name}': {t.get_varname(param_name_set)}" for t in tags)

            # Create docstrings
            docstring_list = [p.get_docstring() for p in parameters] + [t.get_docstring(param_name_set) for t in tags]
            parameter_docstrings = '\n'.join(INDENT + s for s in docstring_list)

            if parameter_docstrings:
                parameter_docstrings += '\n'
            
            if action_description or parameter_docstrings:
                # Fix indentation
                parameter_docstrings += INDENT

            # Assemble the method
            method_code = current_method_template.format(
                method_name = method_name,
                parameter_list = parameter_list,
                parameter_names = parameter_names,
                parameter_docstrings = parameter_docstrings,
                tag_parameter_list = tag_parameter_list,
                tag_values = tag_values,
                codeblock_type = codeblock_type,
                action_name = action_name,
                action_description = action_description
            )

            method_lines = [f'@staticmethod']
            method_lines += method_code.split('\n')

            # Add aliases
            for alias in method_aliases:
                method_lines += [f'{alias} = {method_name}']
            
            method_lines = [INDENT + l for l in method_lines]
            method_lines += ['']
            generated_lines += method_lines
        
        # Add class aliases (e.g. "PE", "EE", etc.)
        class_aliases = CLASS_ALIASES.get(codeblock_type) or []
        for alias in class_aliases:
            alias_def = f'{alias} = {class_name}'
            generated_lines.append(alias_def)

    
    with open(OUTPUT_PATH, 'w', encoding='utf-8') as f:
        f.write('\n'.join(generated_lines) + '\n')
        

if __name__ == '__main__':
    generate_actions()
    print(f'Wrote Codeblock action classes to {OUTPUT_PATH}.')
