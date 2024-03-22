"""
Contains class definitions for code items.
"""

from enum import Enum
from typing import Literal, Dict
from dfpyre.style import isAmpersandCoded, ampersandToMinimessage
from mcitemlib.itemlib import Item as NbtItem


def _add_slot(d: Dict, slot: int|None):
    if slot is not None:
        d['slot'] = slot

class item(NbtItem):
    """
    Represents a Minecraft item.
    """
    type = 'item'

    def format(self, slot: int|None):
        formattedDict = {
            "item": {
              "id": self.type,
              "data": {
                "item": self.get_nbt()
              }
            }
          }
        _add_slot(formattedDict, slot)
        return formattedDict


class string:
    """
    Represents a DiamondFire string object. (`txt`)
    """
    type = 'txt'

    def __init__(self, value: str):
        self.value = value
    
    def format(self, slot: int|None):
        formattedDict = {
              "item": {
                "id": self.type,
                "data": {
                  "name": self.value
                }
              }
            }
        _add_slot(formattedDict, slot)
        return formattedDict


class text:
    """
    Represents a DiamondFire styled text object (`comp`)
    """
    type = 'comp'

    def __init__(self, value: str):
        if isAmpersandCoded(value):
            value = ampersandToMinimessage(value)
        self.value = value
      
    def format(self, slot: int|None):
      formattedDict = {
              "item": {
                "id": self.type,
                "data": {
                  "name": self.value
                }
              }
            }
      _add_slot(formattedDict, slot)
      return formattedDict


class num:
    """
    Represents a DiamondFire number object.
    """
    type = 'num'

    def __init__(self, num: int|float):
        self.value = num
    
    def format(self, slot: int|None):
        formattedDict = {
            "item": {
              "id": self.type,
              "data": {
                "name": str(self.value)
              }
            }
          }
        _add_slot(formattedDict, slot)
        return formattedDict


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
        formattedDict =  {
            "item": {
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
            }
          }
        _add_slot(formattedDict, slot)
        return formattedDict


class var:
    """
    Represents a DiamondFire variable object.
    """
    type = 'var'

    def __init__(self, name: str, scope: Literal['unsaved', 'saved', 'local', 'line']='unsaved'):
        self.name = name
        self.scope = scope

    def format(self, slot: int|None):
        formattedDict = {
            "item": {
              "id": self.type,
              "data": {
                "name": self.name,
                "scope": self.scope
              }
            }
          }
        _add_slot(formattedDict, slot)
        return formattedDict


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
        formattedDict = {
            "item": {
              "id": self.type,
              "data": {
                "sound": self.name,
                "pitch": self.pitch,
                "vol": self.vol
              }
            }
          }
        _add_slot(formattedDict, slot)
        return formattedDict


class particle:
    """
    Represents a DiamondFire particle object.
    """
    type = 'part'
    def __init__(self, name: str='Cloud', amount: int=1, horizontal: float=0.0, vertical: float=0.0, 
                 x: float=1.0, y: float=0.0, z: float=0.0, motionVariation: float=100):
        self.name = name
        self.amount = amount
        self.horizontal = horizontal
        self.vertical = vertical
        self.x = x
        self.y = y
        self.z = z
        self.motionVariation = motionVariation
    
    def format(self, slot: int|None):
        formattedDict = {
            "item": {
              "id": self.type,
              "data": {
                "particle": self.name,
                "cluster": {
                  "amount": self.amount,
                  "horizontal": self.horizontal,
                  "vertical": self.vertical
                },
                "data": {
                  "x": self.x,
                  "y": self.y,
                  "z": self.z,
                  "motionVariation": self.motionVariation
                }
              }
            }
          }
        _add_slot(formattedDict, slot)
        return formattedDict


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
        formattedDict = {
            "item": {
              "id": self.type,
              "data": {
                "pot": self.name,
                "dur": self.dur,
                "amp": self.amp
              }
            }
          }
        _add_slot(formattedDict, slot)
        return formattedDict


class gamevalue:
    """
    Represents a DiamondFire game value object.
    """
    type = 'g_val'

    def __init__(self, name: str, target: str='Default'):
        self.name = name
        self.target = target
    
    def format(self, slot: int|None):
        formattedDict = {
            "item": {
              "id": self.type,
              "data": {
                "type": self.name,
                "target": self.target
              }
            }
          }
        _add_slot(formattedDict, slot)
        return formattedDict


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
        formattedDict = {
            "item": {
              "id": self.type,
              "data": {
                "x": self.x,
                "y": self.y,
                "z": self.z
              }
            }
          }
        _add_slot(formattedDict, slot)
        return formattedDict


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

    def __init__(self, name: str, paramType: ParameterType, plural: bool=False, optional: bool=False, description: str="", note: str="", defaultValue=None):
        self.name = name
        self.paramType = paramType
        self.plural = plural
        self.optional = optional
        self.description = description
        self.note = note
        self.defaultValue = defaultValue
      
    
    def format(self, slot: int):
        formattedDict = {
            "item": {
              "id": self.type,
              "data": {
                "name": self.name,
                "type": self.paramType.get_string_value(),
                "plural": self.plural,
                "optional": self.optional,
              }
            },
            "slot": slot
          }
        if self.description:
            formattedDict['item']['data']['description'] = self.description
        if self.note:
            formattedDict['item']['data']['note'] = self.note
        if self.defaultValue is not None and not self.plural and self.optional:
            formattedDict['item']['data']['default_value'] = self.defaultValue.format(None)['item']
        
        return formattedDict