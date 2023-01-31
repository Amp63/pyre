import base64
import gzip
import socket
import time
import json
from difflib import get_close_matches
from tags import tagData, TAGDATA_KEYS, TAGDATA_EXTRAS_KEYS
from util import warn, COL_SUCCESS, COL_RESET, COL_ERROR

VARIABLE_TYPES = {'txt', 'num', 'item', 'loc', 'var', 'snd', 'part', 'pot', 'g_val', 'vec'}
TEMPLATE_STARTERS = {'event', 'entity_event', 'func', 'process'}

class DFTemplate:
    def __init__(self):
        self.commands = []
        self.closebracket = None
        self.definedVars = {}


    def build(self):
        mainDict = {'blocks': []}
        for cmd in self.commands:
            block = {'args': {'items': []}}
            
            # add keys from cmd.data
            for key in cmd.data.keys():
                block[key] = cmd.data[key]

            # bracket data
            if cmd.data.get('direct') != None:
                block['direct'] = cmd.data['direct']
                block['type'] = cmd.data['type']
            
            # add target if necessary
            if cmd.data.get('block') != 'event':
                if cmd.target != 'Default':
                    block['target'] = cmd.target
            

            # add items into args part of dictionary
            slot = 0
            if cmd.args:  # tuple isnt empty
                for arg in cmd.args[0]:
                    app = None
                    if arg.type in VARIABLE_TYPES:
                        app = arg.format(slot)
                        block['args']['items'].append(app)
                
                    slot += 1
            
            # set tags
            blockType = cmd.data.get('block')
            tags = None
            if blockType in TAGDATA_EXTRAS_KEYS:
                tags = tagData['extras'][blockType]
            elif blockType in TAGDATA_KEYS:
                tags = tagData[blockType].get(cmd.name)
                if tags is None:
                    close = get_close_matches(cmd.name, tagData[blockType].keys())
                    if close:
                        warn(f'Code block name "{cmd.name}" not recognized. Did you mean "{close[0]}"?')
                    else:
                        warn(f'Code block name "{cmd.name}" not recognized. Try spell checking or re-typing without spaces.')
            if tags is not None:
                items = block['args']['items']
                if len(items) > 27:
                    block['args']['items'] = items[:(26-len(tags))]  # trim list
                block['args']['items'].extend(tags)  # add tags to end

            mainDict['blocks'].append(block)

        print(f'{COL_SUCCESS}Template built successfully.{COL_RESET}')

        templateName = 'Unnamed'
        if not mainDict['blocks'][0]['block'] in TEMPLATE_STARTERS:
            warn('Template does not start with an event, function, or process.')
        else:
            try:
                templateName = mainDict['blocks'][0]['block'] + '_' + mainDict['blocks'][0]['action']
            except KeyError:
                templateName = mainDict['blocks'][0]['data']
        
        return self._compress(str(mainDict)), templateName
    

    def build_and_send(self):
        built, templateName = self.build()
        self.send_to_df(built, name=templateName)
    

    def _compress(self, string: str):
        comp_string = gzip.compress(string.encode('utf-8'))
        return str(base64.b64encode(comp_string))[2:-1]
    

    # send template to diamondfire
    def send_to_df(self, code: str, name: str='None'):
        item_name = 'pyre Template - ' + name
        template_data = f"{{\"name\":\"{item_name}\",\"data\":\"{code}\"}}"
        data = {"type": "template", "source": f"pyre - {name}","data": template_data}
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            s.connect(('127.0.0.1', 31372))
        except ConnectionRefusedError:
            print(f'{COL_ERROR}Could not connect to recode item API. (Minecraft is not open or something else has gone wrong){COL_RESET}')
            s.close()
            return
        
        s.send((str(data) + '\n').encode())
        received = s.recv(1024).decode()
        received = json.loads(received)
        status = received['status']
        if status == 'success':
            print(f'{COL_SUCCESS}Template sent to client successfully.{COL_RESET}')
        else:
            error = received['error']
            print(f'{COL_ERROR}Error sending template: {error}{COL_RESET}')
        s.close()
        time.sleep(0.5)
    

    def _convert_data_types(self, lst):
        retList = []
        for element in lst:
            if type(element) in {int, float}:
                retList.append(num(element))
            elif type(element) == str:
                if element[0] == '^':
                    retList.append(self.definedVars[element[1:]])
                else:
                    retList.append(text(element))
            else:
                retList.append(element)
        return tuple(retList)
    

    def clear(self):
        self.commands = []
    

    def _openbracket(self, btype: str='norm'):
        bracket = Command('Bracket', data={'id': 'bracket', 'direct': 'open', 'type': btype})
        self.commands.append(bracket)
        self.closebracket = btype
    

    # command methods
    def player_event(self, name: str):
        cmd = Command(name, data={'id': 'block', 'block': 'event', 'action': name})
        self.commands.append(cmd)
    

    def entity_event(self, name: str):
        cmd = Command(name, data={'id': 'block', 'block': 'entity_event', 'action': name})
        self.commands.append(cmd)
    

    def function(self, name: str):
        cmd = Command('function', data={'id': 'block', 'block': 'func', 'data': name})
        self.commands.append(cmd)
    

    def process(self, name: str):
        cmd = Command('process', data={'id': 'block', 'block': 'process', 'data': name})
        self.commands.append(cmd)
    

    def call_function(self, name: str, parameters={}):
        if parameters:
            for key in parameters.keys():
                self.set_var('=', var(key, scope='local'), parameters[key])
        
        cmd = Command('call_func', data={'id': 'block', 'block': 'call_func', 'data': name})
        self.commands.append(cmd)
    

    def start_process(self, name: str):
        cmd = Command('start_process', data={'id': 'block', 'block': 'start_process', 'data': name})
        self.commands.append(cmd)


    def player_action(self, name: str, *args, target: str='Default'):
        args = self._convert_data_types(args)
        cmd = Command(name, args, target=target, data={'id': 'block', 'block': 'player_action', 'action': name})
        self.commands.append(cmd)
    

    def game_action(self, name: str, *args):
        args = self._convert_data_types(args)
        cmd = Command(name, args, data={'id': 'block', 'block': 'game_action', 'action': name})
        self.commands.append(cmd)
    

    def entity_action(self, name: str, *args):
        args = self._convert_data_types(args)
        cmd = Command(name, args, data={'id': 'block', 'block': 'entity_action', 'action': name})
        self.commands.append(cmd)
    

    def if_player(self, name: str, *args, target: str='Default'):
        args = self._convert_data_types(args)
        cmd = Command(name, args, target=target, data={'id': 'block', 'block': 'if_player', 'action': name})
        self.commands.append(cmd)
        self._openbracket()
    

    def if_variable(self, name: str, *args):
        args = self._convert_data_types(args)
        cmd = Command(name, args, data={'id': 'block', 'block': 'if_var', 'action': name})
        self.commands.append(cmd)
        self._openbracket()
    

    def if_game(self, name: str, *args):
        args = self._convert_data_types(args)
        cmd = Command(name, args, data={'id': 'block', 'block': 'if_game', 'action': name})
        self.commands.append(cmd)
        self._openbracket()
    

    def if_entity(self, name: str, *args):
        args = self._convert_data_types(args)
        cmd = Command(name, args, data={'id': 'block', 'block': 'if_entity', 'action': name})
        self.commands.append(cmd)
        self._openbracket()


    def else_(self):
        cmd = Command('else', data={'id': 'block', 'block': 'else'})
        self.commands.append(cmd)
        self._openbracket()
    

    def repeat(self, name: str, *args, subAction: str=None):
        args = self._convert_data_types(args)
        data = {'id': 'block', 'block': 'repeat', 'action': name}
        if subAction is not None:
            data['subAction'] = subAction
        cmd = Command(name, args, data=data)
        self.commands.append(cmd)
        self._openbracket('repeat')


    def bracket(self, *args):
        args = self._convert_data_types(args)
        cmd = Command('Bracket', data={'id': 'bracket', 'direct': 'close', 'type': self.closebracket})  # close bracket
        self.commands.append(cmd)
    

    def control(self, name: str, *args):
        args = self._convert_data_types(args)
        cmd = Command(name, args, data={'id': 'block', 'block': 'control', 'action': name})
        self.commands.append(cmd)
    

    def select_object(self, name: str, *args):
        args = self._convert_data_types(args)
        cmd = Command(name, args, data={'id': 'block', 'block': 'select_obj', 'action': name})
        self.commands.append(cmd)
    

    def set_var(self, name: str, *args):
        args = self._convert_data_types(args)
        cmd = Command(name, args, data={'id': 'block', 'block': 'set_var', 'action': name})
        self.commands.append(cmd)
    

    # extra methods
    def return_(self, returndata={}):
        for key in returndata:
            self.set_var('=', var(key, scope='local'), returndata[key])
        self.control('Return')
    

    def define_(self, name: str, value=0, scope: str='unsaved', createSetVar: bool=True):
        if createSetVar:
            self.set_var('=', var(name, scope=scope), value)
        self.definedVars[name] = var(name, scope=scope)


# command class
class Command:
    def __init__(self, name: str, *args, target: str='Default', data={}):
        self.name = name
        self.args = args
        self.target = target
        self.data = data


# item data classes
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
