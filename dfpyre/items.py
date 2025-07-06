"""
Class definitions for code items.
"""

from enum import Enum
import re
from typing import Literal, Any
import websocket
from mcitemlib.itemlib import Item as NbtItem, MCItemlibException
from amulet_nbt import DoubleTag, StringTag, CompoundTag
from dfpyre.style import is_ampersand_coded, ampersand_to_minimessage
from dfpyre.util import PyreException, warn, COL_SUCCESS, COL_ERROR, COL_RESET
from dfpyre.action_literals import GAME_VALUE_NAME, SOUND_NAME, POTION_NAME


NUMBER_REGEX = r'^-?\d*\.?\d+$'
VAR_SHORTHAND_REGEX = r'^\$([gsli]) (.+)$'
VAR_SCOPES = {'g': 'unsaved', 's': 'saved', 'l': 'local', 'i': 'line'}

CODECLIENT_URL = 'ws://localhost:31375'


def convert_argument(arg: Any):
    if type(arg) in {int, float}:
        return Number(arg)
    elif isinstance(arg, str):
        shorthand_match: re.Match = re.match(VAR_SHORTHAND_REGEX, arg)
        if shorthand_match:
            scope = VAR_SCOPES[shorthand_match.group(1)]
            return Variable(shorthand_match.group(2), scope)
        return String(arg)
    return arg


def _add_slot(d: dict, slot: int|None):
    if slot is not None:
        d['slot'] = slot


class String:
    """
    Represents a DiamondFire string object. (`txt`)
    """
    type = 'txt'

    def __init__(self, value: str, slot: int|None=None):
        self.value = value
        self.slot = slot
    
    def format(self, slot: int|None):
        formatted_dict = {"item": {"id": self.type, "data": {"name": self.value}}}
        _add_slot(formatted_dict, self.slot or slot)
        return formatted_dict
    
    def __repr__(self) -> str:
        return f'{self.__class__.__name__}("{self.value}")'
    
Str = String  # String alias


class Text:
    """
    Represents a DiamondFire styled text object (`comp`)
    """
    type = 'comp'

    def __init__(self, value: str, slot: int|None=None):
        if is_ampersand_coded(value):
            value = ampersand_to_minimessage(value)
        self.value = value
        self.slot = slot
    
    def format(self, slot: int|None):
      formatted_dict = {"item": {"id": self.type, "data": {"name": self.value}}}
      _add_slot(formatted_dict, self.slot or slot)
      return formatted_dict

    def __repr__(self) -> str:
        return f'{self.__class__.__name__}("{self.value}")'


class Number:
    """
    Represents a DiamondFire number object.
    """
    type = 'num'

    def __init__(self, num: int|float|str, slot: int|None=None):
        self.value = num
        self.slot = slot
    
    def format(self, slot: int|None):
        formatted_dict = {"item": {"id": self.type, "data": {"name": str(self.value)}}}
        _add_slot(formatted_dict, self.slot or slot)
        return formatted_dict

    def __repr__(self) -> str:
        return f'{self.__class__.__name__}({self.value})'

Num = Number  # Number alias


class Item(NbtItem):
    """
    Represents a Minecraft item.
    """
    type = 'item'

    def __init__(self, item_id: str, count: int=1, slot: int | None=None):
        super().__init__(item_id, count)
        self.slot = slot

    def format(self, slot: int|None):
        formatted_dict = {"item": {"id": self.type, "data": {"item": self.get_snbt()}}}
        _add_slot(formatted_dict, self.slot or slot)
        return formatted_dict

    def __repr__(self) -> str:
        return f'{self.__class__.__name__}({self.get_id()}, {self.get_count()})'
    
    def set_tag(self, tag_name: str, tag_value: str|int|float|String|Number):
        """
        Add a DiamondFire custom tag to this item.
        """
        if isinstance(tag_value, String):
            tag = StringTag(tag_value.value)
        elif isinstance(tag_value, str):
            tag = StringTag(tag_value)
        elif isinstance(tag_value, Number):
            tag = DoubleTag(float(tag_value.value))
        elif isinstance(tag_value, (int, float)):
            tag = DoubleTag(float(tag_value))
        
        try:
            custom_data_tag = self.get_component('minecraft:custom_data')
            if 'PublicBukkitValues' in custom_data_tag:
                pbv_tag = custom_data_tag['PublicBukkitValues']
            else:
                pbv_tag = CompoundTag()
        except MCItemlibException:
            custom_data_tag = CompoundTag()
            pbv_tag = CompoundTag()
        
        custom_data_tag['PublicBukkitValues'] = pbv_tag
        
        pbv_tag[f'hypercube:{tag_name}'] = tag
        self.set_component('minecraft:custom_data', custom_data_tag)
    
    def get_tag(self, tag_name: str) -> str|float|None:
        """
        Get a DiamondFire custom tag from this item.
        """
        try:
            custom_data_tag = self.get_component('minecraft:custom_data')
        except MCItemlibException:
            return None
        
        if 'PublicBukkitValues' not in custom_data_tag:
            return None
        
        pbv_tag = custom_data_tag['PublicBukkitValues']
        df_tag_value = pbv_tag.get(f'hypercube:{tag_name}')
        if df_tag_value is None:
            return None
        
        if isinstance(df_tag_value, DoubleTag):
            return float(df_tag_value)
        if isinstance(df_tag_value, StringTag):
            return str(df_tag_value)
    
    def remove_tag(self, tag_name: str):
        """
        Remove a DiamondFire custom tag from this item.
        """
        custom_data_tag = self.get_component('minecraft:custom_data')
        pbv_tag = custom_data_tag['PublicBukkitValues']
        del pbv_tag[f'hypercube:{tag_name}']

        return True
    
    def send_to_minecraft(self):
        """
        Sends this item to Minecraft automatically.
        """
        try:
            ws = websocket.WebSocket()
            ws.connect(CODECLIENT_URL)
            print(f'{COL_SUCCESS}Connected.{COL_RESET}')

            command = f'give {self.get_snbt()}'
            ws.send(command)
            ws.close()

            print(f'{COL_SUCCESS}Item sent to client successfully.{COL_RESET}')
            return 0
            
        except Exception as e:
            if isinstance(e, ConnectionRefusedError):
                print(f'{COL_ERROR}Could not connect to CodeClient API. Possible problems:')
                print(f'    - Minecraft is not open')
                print(f'    - CodeClient is not installed (get it here: https://modrinth.com/mod/codeclient)')
                print(f'    - CodeClient API is not enabled (enable it in CodeClient general settings){COL_RESET}')
                return 1
            
            print(f'Connection failed: {e}')
            return 2


class Location:
    """
    Represents a DiamondFire location object.
    """
    type = 'loc'

    def __init__(self, x: float=0, y: float=0, z: float=0, pitch: float=0, yaw: float=0, slot: int | None=None):
        self.x = float(x)
        self.y = float(y)
        self.z = float(z)
        self.pitch = float(pitch)
        self.yaw = float(yaw)
        self.slot = slot
    
    def format(self, slot: int|None):
        formatted_dict =  {"item": {
            "id": self.type,
            "data": {
                "isBlock": False,
                "loc": {
                    "x": self.x,
                    "y": self.y,
                    "z": self.z,
                    "pitch": self.pitch,
                    "yaw": self.yaw
                }
            }
        }}
        _add_slot(formatted_dict, self.slot or slot)
        return formatted_dict

    def __repr__(self) -> str:
        return f'{self.__class__.__name__}({self.x}, {self.y}, {self.z}, {self.pitch}, {self.yaw})'

Loc = Location  # Location alias


class Variable:
    """
    Represents a DiamondFire variable object.
    """
    type = 'var'

    def __init__(self, name: str, scope: Literal['unsaved', 'game', 'saved', 'local', 'line']='unsaved', slot: int | None=None):
        self.name = name

        if scope == 'game':
            scope = 'unsaved'
        self.scope = scope
        
        self.slot = slot

    def format(self, slot: int|None):
        formatted_dict = {"item": {"id": self.type,"data": {"name": self.name, "scope": self.scope}}}
        _add_slot(formatted_dict, self.slot or slot)
        return formatted_dict

    def __repr__(self) -> str:
        return f'{self.__class__.__name__}({self.scope}, "{self.name}")'

Var = Variable  # Variable alias


class Sound:
    """
    Represents a DiamondFire sound object.
    """
    type = 'snd'

    def __init__(self, name: SOUND_NAME, pitch: float=1.0, vol: float=2.0, slot: int | None=None):
        if name not in set(SOUND_NAME.__args__):
            warn(f'Sound name "{name}" not found.')
        
        self.name = name
        self.pitch = pitch
        self.vol = vol
        self.slot = slot

    def format(self, slot: int|None):
        formatted_dict = {"item": {"id": self.type,"data": {"sound": self.name, "pitch": self.pitch, "vol": self.vol}}}
        _add_slot(formatted_dict, self.slot or slot)
        return formatted_dict

    def __repr__(self) -> str:
        return f'{self.__class__.__name__}(pitch: {self.pitch}, volume: {self.vol})'

Snd = Sound  # Sound alias


class Particle:
    """
    Represents a DiamondFire particle object.
    """
    type = 'part'
    def __init__(self, particle_data: dict, slot: int | None=None):
        self.particle_data = particle_data
        self.slot = slot
    
    def format(self, slot: int|None):
        formatted_dict = {"item": {"id": self.type, "data": self.particle_data}}
        _add_slot(formatted_dict, self.slot or slot)
        return formatted_dict

    def __repr__(self) -> str:
        return f'{self.__class__.__name__}({self.particle_data})'


class Potion:
    """
    Represents a DiamondFire potion object.
    """
    type = 'pot'

    def __init__(self, name: POTION_NAME, dur: int=1000000, amp: int=0, slot: int | None=None):
        if name not in set(POTION_NAME.__args__):
            warn(f'Potion name "{name}" not found.')
        
        self.name = name
        self.dur = dur
        self.amp = amp
        self.slot = slot
    
    def format(self, slot: int|None):
        formatted_dict = {"item": {"id": self.type,"data": {"pot": self.name, "dur": self.dur, "amp": self.amp}}}
        _add_slot(formatted_dict, self.slot or slot)
        return formatted_dict

    def __repr__(self) -> str:
        return f'{self.__class__.__name__}(effect: {self.name}, duration: {self.dur}, amplifier: {self.amp})'

Pot = Potion  # Potion alias


class GameValue:
    """
    Represents a DiamondFire game value object.
    """
    type = 'g_val'

    def __init__(self, name: GAME_VALUE_NAME, target: str='Default', slot: int | None=None):
        if name not in set(GAME_VALUE_NAME.__args__):
            warn(f'Game value name "{name}" not found.')
        
        self.name = name
        self.target = target
        self.slot = slot
    
    def format(self, slot: int|None):
        formatted_dict = {"item": {"id": self.type, "data": {"type": self.name, "target": self.target}}}
        _add_slot(formatted_dict, self.slot or slot)
        return formatted_dict

    def __repr__(self) -> str:
        return f'{self.__class__.__name__}({self.name}, target: {self.target})'


class Vector:
    """
    Represents a DiamondFire vector object.
    """
    type = 'vec'

    def __init__(self, x: float=0.0, y: float=0.0, z: float=0.0, slot: int | None=None):
        self.x = float(x)
        self.y = float(y)
        self.z = float(z)
        self.slot = slot
    
    def format(self, slot: int|None):
        formatted_dict = {"item": {"id": self.type, "data": {"x": self.x, "y": self.y, "z": self.z}}}
        _add_slot(formatted_dict, self.slot or slot)
        return formatted_dict

    def __repr__(self) -> str:
        return f'{self.__class__.__name__}({self.x}, {self.y}, {self.z})'

Vec = Vector  # Vector alias



PARAMETER_TYPE_LOOKUP = ['txt', 'comp', 'num', 'loc', 'vec', 'snd', 'part', 'pot', 'item', 'any', 'var', 'list', 'dict']

class ParameterType(Enum):
    STRING = 0
    TEXT = 1
    NUMBER = 2
    LOCATION = 3
    VECTOR = 4
    SOUND = 5
    PARTICLE = 6
    POTION_EFFECT = 7
    ITEM = 8
    ANY = 9
    VAR = 10
    LIST = 11
    DICT = 12

    def get_string_value(self) -> str:
        return PARAMETER_TYPE_LOOKUP[self.value]

class Parameter:
    """
    Represents a DiamondFire parameter object.
    """
    type = 'pn_el'

    def __init__(self, name: str, param_type: ParameterType, plural: bool=False, optional: bool=False, 
                 description: str="", note: str="", default_value=None, slot: int | None=None):
        self.name = name
        self.param_type = param_type
        self.plural = plural
        self.optional = optional
        self.description = description
        self.note = note
        self.default_value = convert_argument(default_value)
        self.slot = slot
    
    def format(self, slot: int):
        formatted_dict = {"item": {
            "id": self.type,
            "data": {
                "name": self.name,
                "type": self.param_type.get_string_value(),
                "plural": self.plural,
                "optional": self.optional,
            }}
        }
        _add_slot(formatted_dict, self.slot or slot)

        if self.description:
            formatted_dict['item']['data']['description'] = self.description
        if self.note:
            formatted_dict['item']['data']['note'] = self.note
        if self.default_value is not None:
            if not self.optional:
                warn(f'For parameter "{self.name}": Default value cannot be set if optional is False.')
            elif self.plural:
                warn(f'For parameter "{self.name}": Default value cannot be set while plural is True.')
            else:
                formatted_dict['item']['data']['default_value'] = self.default_value.format(None)['item']
        
        return formatted_dict
    
    def __repr__(self) -> str:
        raw_type = str(self.param_type).partition('.')[2]
        return f'{self.__class__.__name__}({self.name}, type: {raw_type})'


class _Tag:
    """
    Represents a CodeBlock action tag.
    """
    type = 'bl_tag'

    def __init__(self, tag_data: dict, slot: int | None=None):
        self.tag_data = tag_data
        self.slot = slot
    
    def format(self, slot: int|None):
        formatted_dict = {"item": {"id": self.type, "data": self.tag_data}}
        _add_slot(formatted_dict, self.slot or slot)
        return formatted_dict

    def __repr__(self) -> str:
        return f'{self.__class__.__name__}({self.tag_data})'


def item_from_dict(item_dict: dict, preserve_item_slots: bool) -> Any:
    item_id = item_dict['item']['id']
    item_data = item_dict['item']['data']
    item_slot = item_dict['slot'] if preserve_item_slots else None

    if item_id == 'item':
        item = Item.from_snbt(item_data['item'])
        item.slot = item_slot
        return item
    
    elif item_id == 'txt':
        return String(item_data['name'], item_slot)
    
    elif item_id == 'comp':
        return Text(item_data['name'], item_slot)
    
    elif item_id == 'num':
        num_value = item_data['name']
        if re.match(NUMBER_REGEX, num_value):
            num_value = float(item_data['name'])
            if num_value % 1 == 0:
                num_value = int(num_value)
            return Number(num_value, item_slot)
        return Number(num_value, item_slot)
    
    elif item_id == 'loc':
        item_loc = item_data['loc']
        return Location(item_loc['x'], item_loc['y'], item_loc['z'], item_loc['pitch'], item_loc['yaw'], item_slot)
    
    elif item_id == 'var':
        return Variable(item_data['name'], item_data['scope'], item_slot)
    
    elif item_id == 'snd':
        return Sound(item_data['sound'], item_data['pitch'], item_data['vol'], item_slot)
    
    elif item_id == 'part':
        return Particle(item_data, item_slot)
    
    elif item_id == 'pot':
        return Potion(item_data['pot'], item_data['dur'], item_data['amp'], item_slot)
    
    elif item_id == 'g_val':
        return GameValue(item_data['type'], item_data['target'], item_slot)
    
    elif item_id == 'vec':
        return Vector(item_data['x'], item_data['y'], item_data['z'], item_slot)
    
    elif item_id == 'pn_el':
        description = item_data.get('description') or ''
        note = item_data.get('note') or ''
        param_type = ParameterType(PARAMETER_TYPE_LOOKUP.index(item_data['type']))
        if item_data['optional']:
            if 'default_value' in item_data:
                default_value_dict = {'item': item_data['default_value'], 'slot': None}
                default_value_item = item_from_dict(default_value_dict, preserve_item_slots)
                return Parameter(item_data['name'], param_type, item_data['plural'], True, description, note, default_value_item, item_slot)
            return Parameter(item_data['name'], param_type, item_data['plural'], True, description, note, slot=item_slot)
        return Parameter(item_data['name'], param_type, item_data['plural'], False, description, note, slot=item_slot)
    
    elif item_id == 'bl_tag':
        if 'variable' in item_data:
            return _Tag(item_data, item_slot)
    
    elif item_id == 'hint':  # Ignore hints
        return
    
    else:
        raise PyreException(f'Unrecognized item id `{item_id}`')
