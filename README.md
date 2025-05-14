# pyre

A package for external creation of code templates for the DiamondFire Minecraft server (mcDiamondFire.com).

PyPi Link: https://pypi.org/project/dfpyre/

## Installation

Run the following command in a terminal:
```
pip install dfpyre
```


### CodeClient Installation

This module works best with [CodeClient](https://modrinth.com/mod/codeclient) installed. Once you've installed it, enable `CodeClient API` in the General config tab.

## Features
- All code block types
- All code item types
- Direct sending to DF via recode or codeclient
- Automatic type conversion (`int` to `Number`, `str` to `String`)
- Auto completed action names (if your IDE supports type hints)
- Warnings for unrecognized actions and tags
- Shorthand format for variables
- Convert existing templates into equivalent Python code (see [Script Generation](#script-generation))

## Documentation
## Basics

- [Setting up a program](#setup)
- [Events and Actions](#events-and-actions)
- [Building](#building)

## Var Items

- [Text](#text)
- [Number](#number)
- [Variable](#variable)
- [Location](#location)
- [Item](#item)
- [Sound](#sound)
- [Particle](#particle)
- [Potion](#potion)
- [Game Value](#game-value)
- [Vector](#vector)
- [Parameter](#parameter)

## Conditionals and Loops

- [Conditionals and Brackets](#conditionals-and-brackets)
- [Loops](#loops)

## Functions and Procedures

- [Creating Functions and Processes](#creating-functions-and-processes)
- [Calling Functions and Processes](#calling-functions-and-processes)

## Extras

- [Editing Tags](#editing-tags)
- [Importing from Code](#importing-from-code)
- [Script Generation](#script-generation)
- [Function List](#function-list)

___

## Setup

To start creating in pyre, use the `player_event`, `entity_event`, `function`, or `process` functions to start a template.

```py
from dfpyre import *

template = player_event('Join', [

])
```

You can then insert additional codeblocks inside of that first function call.

Here's a complete program that prints a message to every player when a player joins:

```py
from dfpyre import *

player_event('Join', [
  player_action('SendMessage', '%default has joined!', target=Target.ALL_PLAYERS)
]).build_and_send('codeclient')
```

## Events and Actions

You can find a list of events and actions [here](#function-list)

The following program sends a message to all players and gives a player 10 apples upon joining:

```py
from dfpyre import *

player_event('Join', [
  player_action('SendMessage', '%default has joined!', target=Target.ALL_PLAYERS),
  player_action('GiveItems', Item('apple', 10))
]).build_and_send('codeclient')
```

## Building

You have 2 different options for building your code line.
You can either:

1. Save the compressed template code to a variable and send it to minecraft later
   - Use the `build` method on a template object
2. Build and send directly to your minecraft client (recommended)
   - Use the `build_and_send` method on a template object

## Variable Items

### Text

Represents a DiamondFire text item:

```py
Text('hello %default.')
```

If a regular string is passed to a method as a chest parameter, it will automatically be converted to a text object:

```py
# These do the same thing:
player_action('SendMessage', Text('%default joined.'))
player_action('SendMessage', '%default joined.')
```

### Number

Alias: `Num`

Represents a DiamondFire number item:

```py
Number(5)
Number(3.14)
```

If a regular integer or float is passed to a method as a chest parameter, it will automatically be converted to a num object:

```py
# These do the same thing:
set_variable('=', Variable('number'), Number(10))
set_variable('=', Variable('number'), 10)
```

### Variable

Alias: `Var`

Represents a DiamondFire variable item:

```py
Variable('num')
Variable('text1')
```

You can set variable values by using the `set_variable` method:

```py
set_variable('=', Variable('num'), 12)  # sets 'num' to 12
set_variable('x', Variable('doubled'), Variable('num'), 2)  # sets 'doubled' to 24
```

You can set the scope of the variable using the `scope` argument:

```py
set_variable('=', Variable('num1', scope='unsaved'), 12)  # `unsaved` is the same as a game variable.
set_variable('=', Variable('num2', scope='saved'), 12)
set_variable('=', Variable('num3', scope='local'), 12)
```

#### Shorthand Variables

You can also use the variable shorthand format to express variables more tersely:
```py
# These do the same thing:
set_variable('=', Variable('lineVar', scope='line'), 5)
set_variable('=', '$i lineVar', 5)
```

Shorthand vars should be formatted like this: `$[scope id] [var name]`

Here's the list of scope IDs:
- `g` = Game (unsaved)
- `s` = Saved
- `l` = Local
- `i` = Line

### Location

Alias: `Loc`

Represents a DiamondFire location item:

```py
Location(x=25.5, y=50, z=25.5, pitch=0, yaw=-90)
```

Example:

```py
# Teleport player on join
from dfpyre import *

player_event('Join', [
  player_action('Teleport', Location(10, 50, 10))
])
```

### Item

Represents a minecraft item:

```py
Item('stick', count=5)
Item('stone', 64)
```

To add extra data to an item, you can use any methods from the [mcitemlib](https://github.com/Amp63/mcitemlib) library

### Sound

Alias: `Snd`

Represents a DiamondFire sound item:

```py
Sound('Wood Break', pitch=1.5, vol=2.0)
```

Example:

```py
# Plays 'Grass Place' sound on join
from dfpyre import *

player_event('Join', [
  player_action('PlaySound', Sound('Grass Place'))
])
```

### Particle

Represents a DiamondFire particle item:

```py
Particle({'particle':'Cloud','cluster':{'amount':1,'horizontal':0.0,'vertical':0.0},'data':{'x':1.0,'y':0.0,'z':0.0,'motionVariation':100}})
```

Example:

```py
# Plays a white cloud particle effect at 5, 50, 5
from dfpyre import *

part = Particle({'particle':'Cloud','cluster':{'amount':1,'horizontal':0.0,'vertical':0.0},'data':{'x':1.0,'y':0.0,'z':0.0,'motionVariation':100}})
player_event('Join', [
  player_action('Particle', part, Location(5, 50, 5))
])
```

Currently, the particle object does not support colors.

### Potion

Alias: `Pot`

Represents a DiamondFire potion item:

```py
# Gives speed 1 for 1 minute
Potion('Speed', dur=1200, amp=0)
```

Example:

```py
# Gives the player infinite saturation 10
from dfpyre import *

player_event('Join', [
  player_action('GivePotion', Potion('Saturation', amp=10))
])
```

### Game Value

Represents a DiamondFire game value item:

```py
GameValue('Player Count')
GameValue('Location' target='Selection')
```

Example:

```py
# Function that prints player count and CPU usage
from dfpyre import *

function('printData', [
  player_action('SendMessage', GameValue('Player Count'), GameValue('CPU Usage'))
])
```

### Vector

Alias: `Vec`

Represents a DiamondFire vector item:

```py
Vector(x=1.1, y=0.0, z=0.5)
```

Example:

```py
# Sets the player's x velocity to 1.0 on join
from dfpyre import *

player_event('Join', [
  player_action('SetVelocity', Vector(x=1.0, y=0.0, z=0.0))
])
```

### Parameter

Represents a DiamondFire parameter item:

```py
Parameter('text', ParameterType.STRING)
```

Example:

```py
# Builds a function that says "Hello, [name]" where `name` is the inputted parameter.
from dfpyre import *

name_parameter = parameter('name', ParameterType.TEXT)
function('SayHi', name_parameter, codeblocks=[
  player_action('SendMessage', 'Hello, ', Variable('name', 'line'))
])
```

### Conditionals and Brackets

A list of conditionals and loops can be found [here](#function-list).

To create code inside of brackets, use the `codeblocks` argument. Here's an example:

```py
# Prints 'clicked' when a player right clicks with a stick in their hand
from dfpyre import *

player_event('RightClick', [
  if_player('IsHolding', Item('stick'), codeblocks=[
    player_action('SendMessage', 'clicked')
  ])
])
```

To create an `else` statement, use the `else_` method:

```py
# Says the player is 'on the ground' when grounded and 'in the air' otherwise.
from dfpyre import *

function('grounded', codeblocks=[
  if_player('IsGrounded', codeblocks=[
    player_action('ActionBar', 'on the ground')
  ]),
  else_([
    player_action('ActionBar', 'in the air')
  ])
])
```

Note that `player_event`, `entity_event`, and `else_` do not require `codeblocks=`, but all other bracket blocks do.

### Loops

As for loops, the syntax is the same and will automatically change to "repeat-type" brackets:

```py
# Prints numbers 1-5
from dfpyre import *

player_event('Join', [
  repeat('Multiple', Variable('i'), 5, codeblocks=[
    player_action('SendMessage', Variable('i'))
  ])
])
```

### Creating Functions and Processes

To create a function or process, just start the template with `function` or `process`:

```py
# Function that gives a player 64 golden apples
from dfpyre import *

function('giveApples', codeblocks=[
  player_action('GiveItems', Item('golden_apple', 64))
])
```

### Calling Functions and Processes

Calling Functions and processes is also simple:

```py
from dfpyre import *

player_event('Join', [
  call_function('giveApples')
])
```

### Editing Tags
You can modify an action's tags by passing the `tags` argument to a template method:

```py
from dfpyre import *

player_event('Join', [
  player_action('SendMessage', 'hello', tags={'Alignment Mode': 'Centered'})
])
```

If you choose not to modify a specific tag, its default value will be used.
Order does not matter when adding multiple tag entries.
 
### Importing from Code

You can import existing templates from their built code using the `from_code` method:

```py
from dfpyre import *

template_code = 'H4sIAGVyIGYC/3WOMQ7CMAxFz4LnDsw5AhITI6qQSaw2IrGrxkJCVe5eh3boAJP9n/Kfs8AziX8VcPcFYgC3Zej26YDexGoZvUZhAxeJ3PI8WMtKSrnV+1q7P4op4Yfmx244qG7E4Uql4EA/jNv2Jc3qJU/2KqBiY4yZjI6UkpzAjkNJouDO1X7S1xUDaGUl2QAAAA=='
t = DFTemplate.from_code(template_code)
# Do stuff with the template here
```


### Script Generation

You can also generate an equivalent Python script for a template from a template object:

```py
from dfpyre import *

template_code = 'H4sIAGVyIGYC/3WOMQ7CMAxFz4LnDsw5AhITI6qQSaw2IrGrxkJCVe5eh3boAJP9n/Kfs8AziX8VcPcFYgC3Zej26YDexGoZvUZhAxeJ3PI8WMtKSrnV+1q7P4op4Yfmx244qG7E4Uql4EA/jNv2Jc3qJU/2KqBiY4yZjI6UkpzAjkNJouDO1X7S1xUDaGUl2QAAAA=='
t = DFTemplate.from_code(template_code)
t.generate_script('my_template.py')    # generated python script will be written to my_template.py
```

This feature is useful for getting a text representation of existing templates.


### Inserting Codeblocks

Use the `insert` method to insert additional codeblocks into an existing template. By default, codeblocks will be added to the end of the template.

```py
from dfpyre import *

my_template = player_event('Join', [
  player_action('SendMessage', '%default has joined!', target=Target.ALL_PLAYERS)
])
my_template.insert(player_action('SendMessage', 'Welcome!'))  # Add a new codeblock to the end
```


### Function List

- **Events / Function / Process**
  - player_event
  - entity_event
  - function
  - process
  - call_function
  - start_process

- **Actions**
  - player_action
  - game_action
  - entity_action

- **Control Flow**
  - if_player
  - if_variable
  - if_game
  - if_entity
  - else_
  - repeat

- **Other**
  - control
  - select_object
  - set_variable