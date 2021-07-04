# Documentation

This documentation, as well as this whole project, has taken heavy inspiration from [dfprismarine](https://github.com/dfprismarine/dfprismarine.github.io) by EnjoyYourBan

## Basics

- [Setting up a program](#setup)
- [Events and Actions](#eventsactions)
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

## Conditionals and Loops

- [Conditionals and Brackets](#conditionalsbrackets)
- [Loops](#loops)

## Functions and Procedures

- [Creating Functions and Procedures](#create-functionsprocedures)
- [Calling Functions and Procedures](#call-functionsprocedures)

## Extras

- [Calling Functions with Parameters](#functions-with-parameters)
- [return_() method](#special-return)
- [Command List](#commands)

___

### Setup

To start creating in pyre, you have to create a DFTemplate object like so:

```py
from pyre import *
t = DFTemplate()
```

Basically everything stems from this template object.

This is the basic layout of a file:

```py
from pyre import *
t = DFTemplate()
# [Event, Function, Process]
# [Your code here]
t.build()
```

The commented lines represent where you will insert calls to methods in the template object.

Here's a complete program that prints a message to every player when a player joins:

```py
from pyre import *
t = DFTemplate()
t.player_event('Join')
t.player_action('SendMessage', '%default has joined!', target='AllPlayers')
t.buildAndSend()
```

### Events/Actions

You can find a list of events and actions [here](#commands)

As shown in [setup](#setup), every code line must start with an event, function, or process. After that, you're free to put anything you want.

The following program sends a message to all players and gives a player 10 apples upon joining:

```py
from pyre import *
t = DFTemplate()
t.player_event('Join')
t.player_action('SendMessage', '%default has joined!', target='AllPlayers')
t.player_action('GiveItems', item('apple', 10))
```

### Building

You basically have 2 different options for building your code line.
You can either:

1. Save the compressed code to a variable and send it to minecraft later
2. Build and send directly to your minecraft client (with codeutilities)

If you choose the first option, the code would look something like this:

```py
from pyre import *
t = DFTemplate()
t.player_event('Join')
t.player_action('SendMessage', '%default has joined!', target='AllPlayers')
code, templateName = t.build()  # NOTE: build() returns a tuple with code at index 0 and a formatted name at index 1.

t.sendToDF(code, name=templateName)  # Send to minecraft client via codeutils item api
```

If you choose the second option, you can do this:

```py
from pyre import *
t = DFTemplate()
t.player_event('Join')
t.player_action('SendMessage', '%default has joined!', target='AllPlayers')
t.buildAndSend()  # builds and sends automatically to minecraft
```

### Variable Items

### Text

Represents a diamondfire text item:

```py
text('hello %default.')
```

If a regular string is passed to a method as a chest parameter, it will automatically be converted to a text object:

```py
# These do the same thing:
t.player_action('SendMessage', text('%default joined.'))
t.player_action('SendMessage', '%default joined.')
```

### Number

Represents a diamondfire number item:

```py
num(5)
num(3.14)
```

If a regular integer or float is passed to a method as a chest parameter, it will automatically be converted to a num object:

```py
# These do the same thing:
t.set_var('=', var('number'), num(10))
t.set_var('=', var('number'), 10)
```

### Variable

Represents a diamondfire variable item:

```py
var('num')
var('text1')
```

You can set variable values by using the *set_var* method:

```py
t.set_var('=', var('num'), 12)  # sets 'num' to 12
t.set_var('x', var('doubled'), var('num'), 2)  # sets 'doubled' to 24
```

You can set the scope of the variable by using the *scope=* keyword:

```py
t.set_var('=', var(num1, scope='game'), 12)  # both 'game' or 'unsaved' can be passed for the scope here
t.set_var('=', var(num1, scope='saved'), 12)
t.set_var('=', var(num1, scope='local'), 12)
```

### Location

Represents a diamondfire location item:

```py
# (var= is not required if numbers are in order, but is more readable)
loc(x=25.5, y=50, z=25.5, pitch=0, yaw=-90)
```

Example:

```py
# teleport player on join
from pyre import *
t = DFTemplate()
t.player_event('Join')
t.player_action('Teleport', loc(10, 50, 10))
```

### Item

Represents a minecraft item:

```py
# (count= is not required)
item('stick', count=5)
item('stone', count=64)
```

Extra nbt (enchants, lore, etc.) is not supported right now.

### Sound

Represents a diamondfire sound item:

```py
sound('Wood Break', pitch=1.5, vol=2.0)
```

Example:

```py
# plays 'Grass Place' sound on join
from pyre import *
t = DFTemplate()
t.player_event('Join')
t.player_action('PlaySound', sound('Grass Place'))
```

### Particle

Represents a diamondfire particle item:

```py
particle(name='Cloud',amount=10,horizontal=1.0,vertical=0.5,x=1.0,y=0.0,z=0.0,motionVariation=100)
```

Example:

```py
# plays a white cloud particle effect at 5, 50, 5
from pyre import *
t = DFTemplate()
t.player_event('Join')
t.player_action('Particle', particle(), loc(5, 50, 5))
```

Currently, the particle object does not support colors.

### Potion

Represents a diamondfire potion item:

```py
# gives speed 1 for 1 minute
potion('Speed', dur=1200, amp=0)
```

Example:

```py
# gives the player infinite saturation 255
from pyre import *
t = DFTemplate()
t.player_event('Join')
t.player_action('GivePotion', potion('Saturation', amp=254))
```

### Game Value

Represents a diamondfire game value item:

```py
gamevalue('Player Count')
gamevalue('Location' target='Selection')
```

Example:

```py
# function that prints player count and cpu
from pyre import *
t = DFTemplate()
t.function('printData')
t.player_action('SendMessage', gamevalue('Player Count'), gamevalue('CPU Usage'))
```

### Vector

Represents a diamondfire vector item:

```py
vector(x=1.1, y=0.0, z=0.5)
```

Example:

```py
# sets the player's x velocity to 1.0 on join
from pyre import *
t = DFTemplate()
t.player_event('Join')
t.player_action('SetVelocity', vector(x=1.0, y=0.0, z=0.0))
```

### Conditionals/Brackets

A list of conditionals and loops can be found [here](#commands).

A specific syntax must be followed when creating conditionals and loops. Each conditional statement must be followed by a *bracket()* method, which will contain code. Here's an example:

```py
# prints 'clicked' when a player right clicks with a stick in their hand
from pyre import *
t = DFTemplate()
t.player_event('RightClick')
t.if_player('IsHolding', item('stick'))
t.bracket(
    t.player_action('SendMessage', 'clicked')
)
```

### Loops

As for loops, the bracket syntax is the exact same, and will auto-adjust to repeat brackets if necessary:

```py
# prints numbers 1-5
from pyre import *
t = DFTemplate()
t.player_event('Join')
t.repeat('Multiple', var('i'), 5)
t.bracket(
    t.player_action('SendMessage', var('i'))
)
```

### Create Functions/Procedures

To create a function or procedure, simple start the code line with a *function* or *procedure* method:

```py
# function that gives a player 64 golden apples
from pyre import *
t = DFTemplate()
t.function('doStuff')
t.player_action('GiveItems', item('golden_apple', 64))
```

### Call Functions/Procedures

Calling Functions and procedures is also pretty simple:

```py
from pyre import *
t = DFTemplate()
t.player_event('Join')
t.call_function('doStuff')
```

Function parameters can also be inputted easier. Check [here](#functions-with-parameters) for more info.

### Functions with Parameters

Lets say that we have this function that prints out double (numx2) of what was inputted (num):

```py
# prints numbers 1-5
from pyre import *
t = DFTemplate()
t.function('double')
t.set_var('x', var('numx2'), var('num'), 2)
t.player_action('SendMessage', var('numx2'))
```

To easily pass the required parameter *num*, we can use the **parameters=** keyword like this:

```py
# prints numbers 1-5
from pyre import *
t = DFTemplate()
t.player_event('Join')
t.call_function('double', parameters={'num': 5})
```

This basically just sets a local variable for each key in **parameters** before the function is called.

### Special Return

Similar to [functions with parameters](#functions-with-parameters), *return_()* is an extension of the *function()* method.

When you want to return a given value from a function, you can use *return_()* like this:

```py
from pyre import *
t = DFTemplate()
t.function('return10')
t.return_(returndata={'retnum': 10})
t.buildAndSend()
```

For each value in *returndata*, a local variable will be set for each key and value.
After all of the variables are set, a *control('Return')* block is automatically added to the end of the line. This allows you to access these local variables after the function returns.

### Commands

- Events / Function / Process
  - player_event
  - entity_event
  - function
  - process
  - call_function
  - start_process

- Actions
  - player_action
  - game_action
  - entity_action

- Conditionals / Loops
  - if_player
  - if_variable
  - if_game
  - if_entity
  - else_ (dont forget underscore)
  - repeat
  - bracket (more info above)

- Other
  - control
  - select_object
  - set_var
