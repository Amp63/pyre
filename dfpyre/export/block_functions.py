"""
Contains Codeblock functions that do not require an action name. 
"""

from typing import Literal
from dfpyre.core.codeblock import CodeBlock
from dfpyre.core.template import DFTemplate
from dfpyre.core.items import ArgValue
from dfpyre.util.util import flatten


__all__ = ['Function', 'Process', 'CallFunction', 'StartProcess', 'Else']


def assemble_template(starting_block: CodeBlock, codeblocks: list[CodeBlock], author: str|None) -> DFTemplate:
    """
    Create a DFTemplate object from a starting block and a list of codeblocks.
    `codeblocks` can contain nested lists of CodeBlock objects, so it must be flattened.
    """
    if author is None:
        author = 'pyre'
    template_codeblocks = [starting_block] + list(flatten(codeblocks))  # Flatten codeblocks list and insert starting block
    return DFTemplate(template_codeblocks, author)


def add_brackets(block: CodeBlock, codeblocks: list[CodeBlock], bracket_type: str='norm') -> list[CodeBlock]:
    return [
        block,
        CodeBlock.new_bracket('open', bracket_type)
    ] + codeblocks + [
        CodeBlock.new_bracket('close', bracket_type)
    ]


def Function(function_name: str, *parameters: ArgValue, is_hidden: Literal["True", "False"]="False", codeblocks: list[CodeBlock]=[], author: str|None=None) -> DFTemplate:
    """
    Represents a Function codeblock.

    :param str event_name: The name of the function.
    :param tuple args: The argument items to include.
    :param dict[str, str] tags: The tags to include.
    :param list[CodeBlock] codeblocks: The list of codeblocks in this template.
    :param str|None author: The author of this template.
    """
    starting_block = CodeBlock.new_data('func', function_name, parameters, {"Is Hidden": is_hidden})
    return assemble_template(starting_block, codeblocks, author)


def Process(process_name: str, *parameters: ArgValue, is_hidden: Literal["True", "False"]="False", codeblocks: list[CodeBlock]=[], author: str|None=None) -> DFTemplate:
    """
    Represents a Process codeblock.

    :param str event_name: The name of the process.
    :param tuple args: The argument items to include.
    :param dict[str, str] tags: The tags to include.
    :param list[CodeBlock] codeblocks: The list of codeblocks in this template.
    :param str|None author: The author of this template.
    """
    starting_block = CodeBlock.new_data('process', process_name, parameters, {"Is Hidden": is_hidden})
    return assemble_template(starting_block, codeblocks, author)


def CallFunction(function_name: str, *args: ArgValue) -> CodeBlock:
    """
    Represents a Call Function codeblock.

    :param str event_name: The name of the function.
    :param tuple args: The argument items to include.
    """
    return CodeBlock.new_data('call_func', function_name, args, {})


def StartProcess(process_name: str, *args: ArgValue, tags: dict[str, str]={}) -> CodeBlock:
    """
    Represents a Call Function codeblock.

    :param str event_name: The name of the function.
    :param tuple args: The argument items to include.
    """
    return CodeBlock.new_data('start_process', process_name, args, tags)


def Else(codeblocks: list[CodeBlock]=[]) -> list[CodeBlock]:
    """
    Represents an Else codeblock.

    :param list[CodeBlock] codeblocks: The list of codeblocks inside the brackets.
    """
    block = CodeBlock.new_else()
    return add_brackets(block, codeblocks)