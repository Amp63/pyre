# pyre

A tool for creating and modifying code templates for the DiamondFire Minecraft server.

PyPi Link: https://pypi.org/project/dfpyre/

## Features
- All codeblock types and actions
- All code items
- Direct sending to DF via CodeClient
- Fully documented and typed actions
- Automatic type conversion (`int` to `Number`, `str` to `String`)
- Shorthand format for variables
- Convert existing templates into equivalent Python code


## Quick Start

To get started with pyre, install the module with pip:

```sh
pip install dfpyre
```

I also highly recommend you install CodeClient and enable `CodeClient API` in its General config tab. This will allow you to quickly send your templates to DiamondFire. [You can download it here on Modrinth.](https://modrinth.com/mod/codeclient)

Basic Template Example:

```py
from dfpyre import *

PlayerEvent.Join(codeblocks=[
    PlayerAction.SendMessage(Text('%default has joined!'), target=Target.ALL_PLAYERS),
    PlayerAction.GiveItems([Item('diamond_sword'), Item('steak', 10)])
]).build_and_send()
```


**For more information and examples, check out the [Wiki](https://github.com/Amp63/pyre/wiki) on Github.**
