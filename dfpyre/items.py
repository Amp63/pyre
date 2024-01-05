"""
Contains class definitions for code items.
"""

from typing import Literal
from dfpyre.style import isAmpersandCoded, ampersandToMinimessage


class item:
    """
    Represents a Minecraft item.
    """
    def __init__(self, itemID: str, count: int=1):
        self.id = itemID
        self.count = count
        self.type = 'item'
    
    def format(self, slot):
        return dict({
            "item": {
              "id": "item",
              "data": {
                "item": f"{{DF_NBT:2586,id:\"{self.id}\",Count:{self.count}b}}"
              }
            },
            "slot": slot
          })


class string:
    """
    Represents a DiamondFire string object. (`txt`)
    """
    def __init__(self, value: str):
        self.value = value
        self.type = 'txt'
    
    def format(self, slot: int):
        return {
              "item": {
                "id": "txt",
                "data": {
                  "name": self.value
                }
              },
              "slot": slot
            }


class text:
    """
    Represents a DiamondFire styled text object (`comp`)
    """
    def __init__(self, value: str):
        if isAmpersandCoded(value):
            value = ampersandToMinimessage(value)
        self.value = value
        self.type = 'comp'
      
    def format(self, slot: int):
      return {
              "item": {
                "id": "comp",
                "data": {
                  "name": self.value
                }
              },
              "slot": slot
            }


class num:
    """
    Represents a DiamondFire number object.
    """
    def __init__(self, num: int|float):
        self.value = num
        self.type = 'num'
    
    def format(self, slot: int):
        return {
            "item": {
              "id": "num",
              "data": {
                "name": str(self.value)
              }
            },
            "slot": slot
          }


class loc:
    """
    Represents a DiamondFire location object.
    """
    def __init__(self, x: float=0, y: float=0, z: float=0, pitch: float=0, yaw: float=0):
        self.x = float(x)
        self.y = float(y)
        self.z = float(z)
        self.pitch = float(pitch)
        self.yaw = float(yaw)
        self.type = 'loc'
    
    def format(self, slot: int):
        return {
            "item": {
              "id": "loc",
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
            },
            "slot": slot
          }


class var:
    """
    Represents a DiamondFire variable object.
    """
    def __init__(self, name: str, scope: Literal['unsaved', 'saved', 'local', 'line']='unsaved'):
        if scope == 'game':
            scope = 'unsaved'
        
        self.name = name
        self.scope = scope
        self.type = 'var'

    def format(self, slot: int):
        return {
            "item": {
              "id": "var",
              "data": {
                "name": self.name,
                "scope": self.scope
              }
            },
            "slot": slot
          }


class sound:
    """
    Represents a DiamondFire sound object.
    """
    def __init__(self, name: str, pitch: float=1.0, vol: float=2.0):
        self.name = name
        self.pitch = pitch
        self.vol = vol
        self.type = 'snd'

    def format(self, slot: int):
        return {
            "item": {
              "id": "snd",
              "data": {
                "sound": self.name,
                "pitch": self.pitch,
                "vol": self.vol
              }
            },
            "slot": slot
          }


class particle:
    """
    Represents a DiamondFire particle object.
    """
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
        self.type = 'part'
    
    def format(self, slot: int):
        return {
            "item": {
              "id": "part",
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
            },
            "slot": slot
          }


class potion:
    """
    Represents a DiamondFire potion object.
    """
    def __init__(self, name: str, dur: int=1000000, amp: int=0):
        self.name = name
        self.dur = dur
        self.amp = amp
        self.type = 'pot'
    
    def format(self, slot: int):
        return {
            "item": {
              "id": "pot",
              "data": {
                "pot": self.name,
                "dur": self.dur,
                "amp": self.amp
              }
            },
            "slot": slot
          }


class gamevalue:
    """
    Represents a DiamondFire game value object.
    """
    def __init__(self, name: str, target: str='Default'):
        self.name = name
        self.target = target
        self.type = 'g_val'
    
    def format(self, slot: int):
        return {
            "item": {
              "id": "g_val",
              "data": {
                "type": self.name,
                "target": self.target
              }
            },
            "slot": slot
          }


class vector:
    """
    Represents a DiamondFire vector object.
    """
    def __init__(self, x: float=0.0, y: float=0.0, z: float=0.0):
        self.x = float(x)
        self.y = float(y)
        self.z = float(z)
        self.type = 'vec'
    
    def format(self, slot: int):
        return {
            "item": {
              "id": "vec",
              "data": {
                "x": self.x,
                "y": self.y,
                "z": self.z
              }
            },
            "slot": slot
          }