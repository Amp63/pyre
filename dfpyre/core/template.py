"""
A package for making code templates for the DiamondFire Minecraft server.

By Amp
"""

import json
import datetime
import platform
from rapidnbt import CompoundTag, StringTag, DoubleTag
from dfpyre.util.util import df_encode, df_decode, flatten, deprecated
from dfpyre.core.items import *
from dfpyre.core.codeblock import CodeBlock, Target, TARGETS, DEFAULT_TARGET, CONDITIONAL_CODEBLOCKS, TEMPLATE_STARTERS, EVENT_CODEBLOCKS
from dfpyre.core.actiondump import get_default_tags
from dfpyre.gen.action_literals import *
from dfpyre.tool.scriptgen import generate_script, GeneratorFlags
from dfpyre.tool.slice import slice_template

__all__ = [
    'Target', 'CodeBlock', 'DFTemplate',
] + VAR_ITEM_TYPES


DYNAMIC_CODEBLOCKS = {'func', 'process', 'call_func', 'start_process'}

DATE_FORMAT_STR = "%b %#d, %Y" if platform.system() == "Windows" else "%b %-d, %Y"


class DFTemplate:
    """
    Represents a DiamondFire code template.
    """
    def __init__(self, codeblocks: list[CodeBlock], author: str='pyre'):
        self.codeblocks = codeblocks
        self.author = author
    

    def get_template_name(self):
        first_block_data = self.codeblocks[0].data
        if 'data' in first_block_data:
            name = first_block_data['data']
            return name if name else 'Unnamed Template'
        return first_block_data['block'] + '_' + first_block_data['action']


    @deprecated('Use get_template_name instead')
    def _get_template_name(self):
        return self.get_template_name()


    def __repr__(self) -> str:
        return f'DFTemplate(name: "{self.get_template_name()}", author: "{self.author}", codeblocks: {len(self.codeblocks)})'


    @staticmethod
    def from_code(template_code: str, preserve_item_slots: bool=True, author: str='pyre'):
        """
        Create a template object from an existing template code.

        :param str template_code: The base64 string to create a template from.
        :param bool preserve_item_slots: If True, the positions of items within chests will be saved.
        :param str author: The author of this template.
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

            codeblock_target = Target(TARGETS.index(block_dict['target'])) if 'target' in block_dict else DEFAULT_TARGET
            codeblock_type = block_dict.get('block')

            if codeblock_type is None:
                codeblock = CodeBlock.new_bracket(block_dict['direct'], block_dict['type'])
            
            elif codeblock_type == 'else':
                codeblock = CodeBlock.new_else()
            
            elif codeblock_type in DYNAMIC_CODEBLOCKS:
                codeblock = CodeBlock.new_data(codeblock_type, block_dict['data'], block_args, block_tags)
            
            elif 'action' in block_dict:
                codeblock_action = block_dict['action']
                attribute = block_dict.get('attribute')
                inverted = attribute == 'NOT'
                sub_action = block_dict.get('subAction')
                if sub_action is not None:
                    codeblock = CodeBlock.new_subaction_block(codeblock_type, codeblock_action, block_args, block_tags, sub_action, inverted)
                elif codeblock_type in EVENT_CODEBLOCKS:
                    ls_cancel = attribute == 'LS-CANCEL'
                    codeblock = CodeBlock.new_event(codeblock_type, codeblock_action, ls_cancel)
                elif codeblock_type in CONDITIONAL_CODEBLOCKS:
                    codeblock = CodeBlock.new_conditional(codeblock_type, codeblock_action, block_args, block_tags, inverted, codeblock_target)
                else:
                    codeblock = CodeBlock.new_action(codeblock_type, codeblock_action, block_args, block_tags, codeblock_target)
            
            codeblocks.append(codeblock)
        
        return DFTemplate(codeblocks, author)


    def generate_template_item(self) -> Item:
        template_code = self.build()

        now = datetime.datetime.now()
        name = self.get_template_name()
        
        template_item = Item('yellow_shulker_box')
        template_item.set_name(f'&x&f&f&5&c&0&0>> &x&f&f&c&7&0&0{name}')
        template_item.set_lore([
            f'&8Author: {self.author}',
            f'&8Date: {now.strftime(DATE_FORMAT_STR)}',
            '',
            '&7This template was generated by &6pyre&7.',
            '&7https://github.com/Amp63/pyre'
        ])
        
        custom_data_tag = CompoundTag({
            'PublicBukkitValues': CompoundTag({
                'hypercube:codetemplatedata': StringTag(f'{{"author":"{self.author}","name":"{name}","version": 1,"code":"{template_code}"}}'),
                'hypercube:pyre_creation_timestamp': DoubleTag(now.timestamp())
            })
        })
        template_item.set_component('minecraft:custom_data', custom_data_tag)

        return template_item

    
    def insert(self, insert_codeblocks: CodeBlock|list[CodeBlock], index: int=-1):
        """
        Insert `insert_codeblocks` into this template at `index`.

        :param CodeBlock|list[CodeBlock] insert_codeblocks: The block(s) to insert.
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


    def build(self) -> str:
        """
        Build this template.

        :return: String containing encoded template data.
        """
        template_dict_blocks = [codeblock.build() for codeblock in self.codeblocks]
        template_dict = {'blocks': template_dict_blocks}
        first_block = template_dict_blocks[0]
        if first_block['block'] not in TEMPLATE_STARTERS:
            warn('Template does not start with an event, function, or process.')

        json_string = json.dumps(template_dict, separators=(',', ':'))
        return df_encode(json_string)
    

    def build_and_send(self) -> int:
        """
        Builds this template and sends it to DiamondFire automatically.
        """
        template_item = self.generate_template_item()
        return template_item.send_to_minecraft()
    
    
    def generate_script(self, indent_size: int=4, literal_shorthand: bool=True, var_shorthand: bool=False, 
                        preserve_slots: bool=False, assign_variable: bool=False, include_import: bool=True, 
                        build_and_send: bool=False) -> str:
        """
        Generate an equivalent python script for this template.
        
        :param int indent_size: The multiple of spaces to add when indenting lines.
        :param bool literal_shorthand: If True, `Text` and `Number` items will be written as strings and ints respectively.
        :param bool var_shorthand: If True, all variables will be written using variable shorthand.
        :param bool preserve_slots: If True, the positions of items within chests will be saved.
        :param bool assign_variable: If True, the generated template will be assigned to a variable.
        :param bool include_import: If True, the `dfpyre` import statement will be added.
        :param bool build_and_send: If True, `.build_and_send()` will be added to the end of the generated template.
        """
        flags = GeneratorFlags(indent_size, literal_shorthand, var_shorthand, preserve_slots, assign_variable, include_import, build_and_send)
        return generate_script(self.codeblocks, flags)
    
    
    def slice(self, target_length: int) -> list['DFTemplate']:
        """
        Slice the current template into multiple other templates.
        Useful for compressing a template to fit on a smaller plot.

        :param int target_length: The maximum allowed length of each sliced template.
        """
        sliced_templates = slice_template(self.codeblocks, target_length, self.get_template_name())
        return [DFTemplate(t, self.author) for t in sliced_templates]


def _assemble_template(starting_block: CodeBlock, codeblocks: list[CodeBlock], author: str|None) -> DFTemplate:
    """
    Create a DFTemplate object from a starting block and a list of codeblocks.
    `codeblocks` can contain nested lists of CodeBlock objects, so it must be flattened.
    """
    if author is None:
        author = 'pyre'
    template_codeblocks = [starting_block] + list(flatten(codeblocks))  # Flatten codeblocks list and insert starting block
    return DFTemplate(template_codeblocks, author)
