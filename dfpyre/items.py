"""
Contains class definitions for code items.
"""


class item:
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


class text:
    def __init__(self, value: str):
        self.value = value
        self.type = 'txt'
    
    def format(self, slot: int):
        return dict({
              "item": {
                "id": "txt",
                "data": {
                  "name": self.value
                }
              },
              "slot": slot
            })


class num:
    def __init__(self, num: int|float):
        self.value = num
        self.type = 'num'
    
    def format(self, slot: int):
        return dict({
            "item": {
              "id": "num",
              "data": {
                "name": str(self.value)
              }
            },
            "slot": slot
          })


class loc:
    def __init__(self, x: float=0, y: float=0, z: float=0, pitch: float=0, yaw: float=0):
        self.x = float(x)
        self.y = float(y)
        self.z = float(z)
        self.pitch = float(pitch)
        self.yaw = float(yaw)
        self.type = 'loc'
    
    def format(self, slot: int):
        return dict({
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
          })


class var:
    def __init__(self, name: str, scope: str='unsaved'):
        if scope == 'game':
            scope = 'unsaved'
        
        self.name = name
        self.scope = scope
        self.type = 'var'

    def format(self, slot: int):
        return dict({
            "item": {
              "id": "var",
              "data": {
                "name": self.name,
                "scope": self.scope
              }
            },
            "slot": slot
          })


class sound:
    def __init__(self, name: str, pitch: float=1.0, vol: float=2.0):
        self.name = name
        self.pitch = pitch
        self.vol = vol
        self.type = 'snd'

    def format(self, slot: int):
        return dict({
            "item": {
              "id": "snd",
              "data": {
                "sound": self.name,
                "pitch": self.pitch,
                "vol": self.vol
              }
            },
            "slot": slot
          })


class particle:
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
        return dict({
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
          })


class potion:
    def __init__(self, name: str, dur: int=1000000, amp: int=0):
        self.name = name
        self.dur = dur
        self.amp = amp
        self.type = 'pot'
    
    def format(self, slot: int):
        return dict({
            "item": {
              "id": "pot",
              "data": {
                "pot": self.name,
                "dur": self.dur,
                "amp": self.amp
              }
            },
            "slot": slot
          })


class gamevalue:
    def __init__(self, name: str, target: str='Default'):
        self.name = name
        self.target = target
        self.type = 'g_val'
    
    def format(self, slot: int):
        return dict({
            "item": {
              "id": "g_val",
              "data": {
                "type": self.name,
                "target": self.target
              }
            },
            "slot": slot
          })


class vector:
    def __init__(self, x: float=0.0, y: float=0.0, z: float=0.0):
        self.x = float(x)
        self.y = float(y)
        self.z = float(z)
        self.type = 'vec'
    
    def format(self, slot: int):
        return dict({
            "item": {
              "id": "vec",
              "data": {
                "x": self.x,
                "y": self.y,
                "z": self.z
              }
            },
            "slot": slot
          })