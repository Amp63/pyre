from dataclasses import dataclass
from collections import deque
from dfpyre.core.codeblock import CodeBlock, CONDITIONAL_CODEBLOCKS, TEMPLATE_STARTERS
from dfpyre.core.items import Variable, Parameter, ParameterType


BRACKET_CODEBLOCKS = CONDITIONAL_CODEBLOCKS
BRACKET_CODEBLOCKS.add('repeat')


@dataclass
class TemplateChunk:
    length: int
    start_index: int
    end_index: int
    contents1: list['TemplateChunk'] | None  # Inside brackets
    contents2: list['TemplateChunk'] | None  # Inside `else` brackets


def get_referenced_line_vars(codeblocks: list[CodeBlock]) -> set[str]:
    referenced_vars = set()
    for codeblock in codeblocks:
        for argument in codeblock.args:
            if isinstance(argument, Variable) and argument.scope == 'line':
                referenced_vars.add(argument.name)
    return referenced_vars


def find_closing_bracket(codeblocks: list[CodeBlock], start_index: int) -> int:
    """
    Returns the index of the cooresponding closing bracket assuming 
    that `start_index` is the index of the first codeblock inside the brackets.
    """
    nested_level = 1
    for i in range(start_index, len(codeblocks)):
        codeblock = codeblocks[i]
        if codeblock.type != 'bracket':
            continue

        direction = codeblock.data['direct']
        if direction == 'open':
            nested_level += 1
        else:  # Closed
            nested_level -= 1
        
        if nested_level == 0:
            return i
    
    return -1


def get_bracket_ranges(codeblocks: list[CodeBlock], start_index: int):
    bracket_range_end = find_closing_bracket(codeblocks, start_index)

    if len(codeblocks) > bracket_range_end+1 and codeblocks[bracket_range_end+1].type == 'else':
        else_range_start = bracket_range_end+3  # Add 3 to move inside `else` brackets
        else_range_end = find_closing_bracket(codeblocks, else_range_start)
        else_range = (else_range_start, else_range_end)
    else:
        else_range = None

    bracket_range = (start_index, bracket_range_end)
    return (bracket_range, else_range)


def get_template_length(codeblocks: list[CodeBlock]) -> int:
    return sum(b.get_length() for b in codeblocks)


def get_template_chunks(codeblocks: list[CodeBlock], start_index: int, end_index: int) -> list[TemplateChunk]:
    chunks: list[TemplateChunk] = []

    index = start_index
    while index < end_index:
        codeblock = codeblocks[index]
        if codeblock.type == 'bracket' or codeblock.type in TEMPLATE_STARTERS:
            index += 1
            continue

        if codeblock.type in BRACKET_CODEBLOCKS:
            bracket_range, else_range = get_bracket_ranges(codeblocks, index+2)
            inside_bracket = codeblocks[bracket_range[0]:bracket_range[1]]
            inside_bracket_length = get_template_length(inside_bracket)
            chunk_contents1 = get_template_chunks(codeblocks, bracket_range[0], bracket_range[1])
            if else_range is None:
                chunk_length = inside_bracket_length + 4
                chunk_end_index = bracket_range[1] + 1
                chunk_contents2 = None
            else:
                inside_else = codeblocks[else_range[0]:else_range[1]]
                inside_else_length = get_template_length(inside_else)
                chunk_length = inside_bracket_length + inside_else_length + 8
                chunk_end_index = else_range[1] + 1
                chunk_contents2 = get_template_chunks(codeblocks, else_range[0], else_range[1])
            
            chunk = TemplateChunk(length=chunk_length, start_index=index, end_index=chunk_end_index, contents1=chunk_contents1, contents2=chunk_contents2)
            chunks.append(chunk)
            index = chunk_end_index-1
        
        else:
            chunk = TemplateChunk(length=2, start_index=index, end_index=index+1, contents1=None, contents2=None)
            chunks.append(chunk)
        
        index += 1

    return chunks


def extract_one_template(codeblocks: list[CodeBlock], target_length: int, extracted_template_name: str) -> tuple[list[CodeBlock], list[CodeBlock]]:
    chunks = get_template_chunks(codeblocks, 0, len(codeblocks))
    current_slice_length = 2
    current_slice_start = -1
    current_slice_end = -1

    slices: dict[tuple[int, int], int] = {}

    chunks_to_iterate: deque[list[TemplateChunk]] = deque()
    chunks_to_iterate.append(chunks)

    def save_current_slice():
        nonlocal current_slice_start, current_slice_end, current_slice_length, slices
        current_slice_range = (current_slice_start, current_slice_end)
        slices[current_slice_range] = current_slice_length
        current_slice_length = 2
        current_slice_start = -1
        current_slice_end = -1

    while chunks_to_iterate:
        current_chunks = chunks_to_iterate.pop()
        for chunk in reversed(current_chunks):
            if chunk.contents1:
                chunks_to_iterate.append(chunk.contents1)
            if chunk.contents2:
                chunks_to_iterate.append(chunk.contents2)
            
            if current_slice_start == -1:
                current_slice_start = chunk.start_index
            if current_slice_end == -1:
                current_slice_end = chunk.end_index
            
            # Check if chunk is too long
            if chunk.length > target_length - 2:
                save_current_slice()
                continue
            
            new_slice_length = current_slice_length + chunk.length
            if new_slice_length <= target_length:
                current_slice_length = new_slice_length
                current_slice_start = chunk.start_index
            else:
                current_slice_range = (current_slice_start, current_slice_end)
                slices[current_slice_range] = current_slice_length
                current_slice_length = chunk.length + 2
                current_slice_start = chunk.start_index
                current_slice_end = chunk.end_index
    
        save_current_slice()
    
    sliced_range = max(slices.items(), key=lambda kv: kv[1])[0]  # Extract the longest slice
    extracted_codeblocks = codeblocks[sliced_range[0]:sliced_range[1]]
    del codeblocks[sliced_range[0]:sliced_range[1]]

    original_line_vars = get_referenced_line_vars(codeblocks)
    extracted_line_vars = get_referenced_line_vars(extracted_codeblocks)
    param_line_vars = set.intersection(original_line_vars, extracted_line_vars)
    function_parameters = []
    function_call_args = []
    for line_var in param_line_vars:
        function_parameters.append(Parameter(line_var, ParameterType.VAR))
        function_call_args.append(Variable(line_var, 'line'))
    
    function_codeblock = CodeBlock.new_data('func', extracted_template_name, tuple(function_parameters), tags={'Is Hidden': 'True'})
    extracted_codeblocks.insert(0, function_codeblock)

    call_function_codeblock = CodeBlock.new_data('call_func', extracted_template_name, tuple(function_call_args), {})
    codeblocks.insert(sliced_range[0], call_function_codeblock)

    return codeblocks, extracted_codeblocks


def slice_template(codeblocks: list[CodeBlock], target_length: int, template_name: str) -> list[list[CodeBlock]]:
    template_length = get_template_length(codeblocks)
    if template_length < target_length:
        return [codeblocks]

    codeblocks = codeblocks.copy()

    sliced_templates: list[list[CodeBlock]] = []

    # Extract single templates until the original template meets the target length
    template_number = 1 
    while get_template_length(codeblocks) > target_length:
        extracted_template_name = template_name + '_' + str(template_number)
        codeblocks, extracted_codeblocks = extract_one_template(codeblocks, target_length, extracted_template_name)
        sliced_templates.append(extracted_codeblocks)
        template_number += 1

    sliced_templates.insert(0, codeblocks)
    return sliced_templates
