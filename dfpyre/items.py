"""
Contains class definitions for code items.
"""

from enum import Enum
import re
from typing import Literal, Any
from dfpyre.style import is_ampersand_coded, ampersand_to_minimessage
from dfpyre.util import PyreException, warn
from mcitemlib.itemlib import Item as NbtItem


NUMBER_REGEX = r'-?\d*\.?\d+'
VAR_SHORTHAND_CHAR = '$'
VAR_SCOPES = {'g': 'unsaved', 's': 'saved', 'l': 'local', 'i': 'line'}


def convert_argument(arg: Any):
    if type(arg) in {int, float}:
        return num(arg)
    elif isinstance(arg, str):
        if len(arg) > 2 and arg[0] == VAR_SHORTHAND_CHAR and arg[1] in VAR_SCOPES:
            return var(arg[2:], VAR_SCOPES[arg[1]])
        return text(arg)
    return arg


def _add_slot(d: dict, slot: int|None):
    if slot is not None:
        d['slot'] = slot


class item(NbtItem):
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


class string:
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


class text:
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


class num:
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


class loc:
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


class var:
    """
    Represents a DiamondFire variable object.
    """
    type = 'var'

    def __init__(self, name: str, scope: Literal['unsaved', 'saved', 'local', 'line']='unsaved'):
        self.name = name
        self.scope = scope

    def format(self, slot: int|None):
        formatted_dict = {"item": {"id": self.type,"data": {"name": self.name, "scope": self.scope}}}
        _add_slot(formatted_dict, slot)
        return formatted_dict

    def __repr__(self) -> str:
        return f'{self.__class__.__name__}({self.scope}, "{self.name}")'


class sound:
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


class particle:
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


class potion:
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


class gamevalue:
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


class vector:
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

class parameter:
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


def _some_or(value: Any, none_value: Any):
    """
    Returns `none_value` if `value` is None, otherwise returns `value`.
    """
    if value is None:
        return none_value
    return value


def item_from_dict(item_dict: dict) -> object:
    item_id = item_dict['id']
    item_data = item_dict['data']

    if item_id == 'item':
        return item.from_nbt(item_data['item'])
    elif item_id == 'txt':
        return string(item_data['name'])
    elif item_id == 'comp':
        return text(item_data['name'])
    elif item_id == 'num':
        num_value = item_data['name']
        if re.match(NUMBER_REGEX, num_value):
            num_value = float(item_data['name'])
            if num_value % 1 == 0:
                num_value = int(num_value)
            return num(num_value)
        return num(num_value)
    elif item_id == 'loc':
        item_loc = item_data['loc']
        return loc(item_loc['x'], item_loc['y'], item_loc['z'], item_loc['pitch'], item_loc['yaw'])
    elif item_id == 'var':
        return var(item_data['name'], item_data['scope'])
    elif item_id == 'snd':
        return sound(item_data['sound'], item_data['pitch'], item_data['vol'])
    elif item_id == 'part':
        return particle(item_data)
    elif item_id == 'pot':
        return potion(item_data['pot'], item_data['dur'], item_data['amp'])
    elif item_id == 'g_val':
        return gamevalue(item_data['type'], item_data['target'])
    elif item_id == 'vec':
        return vector(item_data['x'], item_data['y'], item_data['z'])
    elif item_id == 'pn_el':
        description = _some_or(item_data.get('description'), '')
        note = _some_or(item_data.get('note'), '')
        param_type = ParameterType(PARAMETER_TYPE_LOOKUP.index(item_data['type']))
        if item_data['optional']:
            if 'default_value' in item_data:
                return parameter(item_data['name'], param_type, item_data['plural'], True, description, note, item_from_dict(item_data['default_value']))
            return parameter(item_data['name'], param_type, item_data['plural'], True, description, note)
        return parameter(item_data['name'], param_type, item_data['plural'], False, description, note)
    elif item_id in {'bl_tag', 'hint'}:
        return
    else:
        raise PyreException(f'Unrecognized item id `{item_id}`')