"""
Class definitions for code items.
"""

from enum import Enum
import re
from typing import Literal, Any
from dfpyre.style import is_ampersand_coded, ampersand_to_minimessage
from dfpyre.util import PyreException, warn
from mcitemlib.itemlib import Item as NbtItem


NUMBER_REGEX = r'^-?\d*\.?\d+$'
VAR_SHORTHAND_REGEX = r'^\$([gsli]) (.+)$'
VAR_SCOPES = {'g': 'unsaved', 's': 'saved', 'l': 'local', 'i': 'line'}


def convert_argument(arg: Any):
    if type(arg) in {int, float}:
        return Number(arg)
    elif isinstance(arg, str):
        shorthand_match: re.Match = re.match(VAR_SHORTHAND_REGEX, arg)
        if shorthand_match:
            scope = VAR_SCOPES[shorthand_match.group(1)]
            return Variable(shorthand_match.group(2), scope)
        return Text(arg)
    return arg


def _add_slot(d: dict, slot: int|None):
    if slot is not None:
        d['slot'] = slot


class Item(NbtItem):
    """
    Represents a Minecraft item.
    """
    type = 'item'

    def format(self, slot: int|None):
        formatted_dict = {"item": {"id": self.type, "data": {"item": self.get_nbt()}}}
        _add_slot(formatted_dict, slot)
        return formatted_dict

    def __repr__(self) -> str:
        return f'{self.__class__.__name__}({self.get_id()}, {self.get_count()})'


class String:
    """
    Represents a DiamondFire string object. (`txt`)
    """
    type = 'txt'

    def __init__(self, value: str):
        self.value = value
    
    def format(self, slot: int|None):
        formatted_dict = {"item": {"id": self.type, "data": {"name": self.value}}}
        _add_slot(formatted_dict, slot)
        return formatted_dict
    
    def __repr__(self) -> str:
        return f'{self.__class__.__name__}("{self.value}")'
    
Str = String  # String alias


class Text:
    """
    Represents a DiamondFire styled text object (`comp`)
    """
    type = 'comp'

    def __init__(self, value: str):
        if is_ampersand_coded(value):
            value = ampersand_to_minimessage(value)
        self.value = value
    
    def format(self, slot: int|None):
      formatted_dict = {"item": {"id": self.type, "data": {"name": self.value}}}
      _add_slot(formatted_dict, slot)
      return formatted_dict

    def __repr__(self) -> str:
        return f'{self.__class__.__name__}("{self.value}")'


class Number:
    """
    Represents a DiamondFire number object.
    """
    type = 'num'

    def __init__(self, num: int|float|str):
        self.value = num
    
    def format(self, slot: int|None):
        formatted_dict = {"item": {"id": self.type, "data": {"name": str(self.value)}}}
        _add_slot(formatted_dict, slot)
        return formatted_dict

    def __repr__(self) -> str:
        return f'{self.__class__.__name__}({self.value})'

Num = Number  # Number alias


class Location:
    """
    Represents a DiamondFire location object.
    """
    type = 'loc'

    def __init__(self, x: float=0, y: float=0, z: float=0, pitch: float=0, yaw: float=0):
        self.x = float(x)
        self.y = float(y)
        self.z = float(z)
        self.pitch = float(pitch)
        self.yaw = float(yaw)
    
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
        _add_slot(formatted_dict, slot)
        return formatted_dict

    def __repr__(self) -> str:
        return f'{self.__class__.__name__}({self.x}, {self.y}, {self.z}, {self.pitch}, {self.yaw})'

Loc = Location  # Location alias


class Variable:
    """
    Represents a DiamondFire variable object.
    """
    type = 'var'

    def __init__(self, name: str, scope: Literal['unsaved', 'game', 'saved', 'local', 'line']='unsaved'):
        self.name = name

        if scope == 'game':
            scope = 'unsaved'
        self.scope = scope

    def format(self, slot: int|None):
        formatted_dict = {"item": {"id": self.type,"data": {"name": self.name, "scope": self.scope}}}
        _add_slot(formatted_dict, slot)
        return formatted_dict

    def __repr__(self) -> str:
        return f'{self.__class__.__name__}({self.scope}, "{self.name}")'

Var = Variable  # Variable alias


class Sound:
    """
    Represents a DiamondFire sound object.
    """
    type = 'snd'

    def __init__(self, name: str, pitch: float=1.0, vol: float=2.0):
        self.name = name
        self.pitch = pitch
        self.vol = vol

    def format(self, slot: int|None):
        formatted_dict = {"item": {"id": self.type,"data": {"sound": self.name, "pitch": self.pitch, "vol": self.vol}}}
        _add_slot(formatted_dict, slot)
        return formatted_dict

    def __repr__(self) -> str:
        return f'{self.__class__.__name__}(pitch: {self.pitch}, volume: {self.vol})'

Snd = Sound  # Sound alias


class Particle:
    """
    Represents a DiamondFire particle object.
    """
    type = 'part'
    def __init__(self, particle_data: dict):
        self.particle_data = particle_data
    
    def format(self, slot: int|None):
        formatted_dict = {"item": {"id": self.type, "data": self.particle_data}}
        _add_slot(formatted_dict, slot)
        return formatted_dict

    def __repr__(self) -> str:
        return f'{self.__class__.__name__}({self.particle_data})'


class Potion:
    """
    Represents a DiamondFire potion object.
    """
    type = 'pot'

    def __init__(self, name: str, dur: int=1000000, amp: int=0):
        self.name = name
        self.dur = dur
        self.amp = amp
    
    def format(self, slot: int|None):
        formatted_dict = {"item": {"id": self.type,"data": {"pot": self.name, "dur": self.dur, "amp": self.amp}}}
        _add_slot(formatted_dict, slot)
        return formatted_dict

    def __repr__(self) -> str:
        return f'{self.__class__.__name__}(effect: {self.name}, duration: {self.dur}, amplifier: {self.amp})'

Pot = Potion  # Potion alias


class GameValue:
    """
    Represents a DiamondFire game value object.
    """
    type = 'g_val'

    def __init__(self, name: str, target: str='Default'):
        self.name = name
        self.target = target
    
    def format(self, slot: int|None):
        formatted_dict = {"item": {"id": self.type, "data": {"type": self.name, "target": self.target}}}
        _add_slot(formatted_dict, slot)
        return formatted_dict

    def __repr__(self) -> str:
        return f'{self.__class__.__name__}({self.name}, target: {self.target})'


class Vector:
    """
    Represents a DiamondFire vector object.
    """
    type = 'vec'

    def __init__(self, x: float=0.0, y: float=0.0, z: float=0.0):
        self.x = float(x)
        self.y = float(y)
        self.z = float(z)
    
    def format(self, slot: int|None):
        formatted_dict = {"item": {"id": self.type, "data": {"x": self.x, "y": self.y, "z": self.z}}}
        _add_slot(formatted_dict, slot)
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

    def __init__(self, name: str, param_type: ParameterType, plural: bool=False, optional: bool=False, description: str="", note: str="", default_value=None):
        self.name = name
        self.param_type = param_type
        self.plural = plural
        self.optional = optional
        self.description = description
        self.note = note
        self.default_value = convert_argument(default_value)
      
    
    def format(self, slot: int):
        formatted_dict = {"item": {
            "id": self.type,
            "data": {
                "name": self.name,
                "type": self.param_type.get_string_value(),
                "plural": self.plural,
                "optional": self.optional,
            }},
            "slot": slot
        }
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


def item_from_dict(item_dict: dict) -> object:
    item_id = item_dict['id']
    item_data = item_dict['data']

    if item_id == 'item':
        return Item.from_nbt(item_data['item'])
    
    elif item_id == 'txt':
        return String(item_data['name'])
    
    elif item_id == 'comp':
        return Text(item_data['name'])
    
    elif item_id == 'num':
        num_value = item_data['name']
        if re.match(NUMBER_REGEX, num_value):
            num_value = float(item_data['name'])
            if num_value % 1 == 0:
                num_value = int(num_value)
            return Number(num_value)
        return Number(num_value)
    
    elif item_id == 'loc':
        item_loc = item_data['loc']
        return Location(item_loc['x'], item_loc['y'], item_loc['z'], item_loc['pitch'], item_loc['yaw'])
    
    elif item_id == 'var':
        return Variable(item_data['name'], item_data['scope'])
    
    elif item_id == 'snd':
        return Sound(item_data['sound'], item_data['pitch'], item_data['vol'])
    
    elif item_id == 'part':
        return Particle(item_data)
    
    elif item_id == 'pot':
        return Potion(item_data['pot'], item_data['dur'], item_data['amp'])
    
    elif item_id == 'g_val':
        return GameValue(item_data['type'], item_data['target'])
    
    elif item_id == 'vec':
        return Vector(item_data['x'], item_data['y'], item_data['z'])
    
    elif item_id == 'pn_el':
        description = item_data.get('description') or ''
        note = item_data.get('note') or ''
        param_type = ParameterType(PARAMETER_TYPE_LOOKUP.index(item_data['type']))
        if item_data['optional']:
            if 'default_value' in item_data:
                return Parameter(item_data['name'], param_type, item_data['plural'], True, description, note, item_from_dict(item_data['default_value']))
            return Parameter(item_data['name'], param_type, item_data['plural'], True, description, note)
        return Parameter(item_data['name'], param_type, item_data['plural'], False, description, note)
    
    elif item_id in {'bl_tag', 'hint'}:  # Ignore tags and hints
        return
    
    else:
        raise PyreException(f'Unrecognized item id `{item_id}`')