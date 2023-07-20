# pyre

A package for external creation of code templates for the DiamondFire Minecraft server (mcdiamondfire.com).

## Features
- All code block types
- All code item types
- Direct sending to DF via recode
- Automatic type conversion (int to num, str to text)
- Name checking ("did you mean ___?" for close matches)
- Default tag values

## Documentation
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
from dfpyre import *
t = DFTemplate()
```

Basically everything stems from this template object.

This is the basic layout of a file:

```py
from dfpyre import *
t = DFTemplate()
# [Event, Function, or Process]
# [Your code here]
t.build()
```

The commented lines represent where you will insert calls to methods in the template object.

Here's a complete program that prints a message to every player when a player joins:

```py
from dfpyre import *
t = DFTemplate()
t.playerEvent('Join')
t.playerAction('SendMessage', '%default has joined!', target='AllPlayers')
t.buildAndSend()
```

### Events/Actions

You can find a list of events and actions [here](#commands)

As shown in [setup](#setup), every code line must start with an event, function, or process. After that, you're free to put anything you want.

The following program sends a message to all players and gives a player 10 apples upon joining:

```py
from dfpyre import *
t = DFTemplate()
t.playerEvent('Join')
t.playerAction('SendMessage', '%default has joined!', target='AllPlayers')
t.playerAction('GiveItems', item('apple', 10))
```

### Building

You basically have 2 different options for building your code line.
You can either:

1. Save the compressed template code to a variable and send it to minecraft later
2. Build and send directly to your minecraft client (recommended)

If you choose the first option, the code would look something like this:

```py
from dfpyre import *
t = DFTemplate()
t.playerEvent('Join')
t.playerAction('SendMessage', '%default has joined!', target='AllPlayers')
templateCode, templateName = t.build()  # NOTE: build() returns a tuple with code at index 0 and a formatted name at index 1.

sendToDf(code, name=templateName)  # Send to minecraft client via recode item api
```

If you choose the second option, you can do this:

```py
from dfpyre import *
t = DFTemplate()
t.playerEvent('Join')
t.playerAction('SendMessage', '%default has joined!', target='AllPlayers')
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
t.playerAction('SendMessage', text('%default joined.'))
t.playerAction('SendMessage', '%default joined.')
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
t.setVariable('=', var('number'), num(10))
t.setVariable('=', var('number'), 10)
```

### Variable

Represents a diamondfire variable item:

```py
var('num')
var('text1')
```

You can set variable values by using the `setVariable` method:

```py
t.setVariable('=', var('num'), 12)  # sets 'num' to 12
t.setVariable('x', var('doubled'), var('num'), 2)  # sets 'doubled' to 24
```

You can set the scope of the variable by using the `scope` keyword:

```py
t.setVariable('=', var(num1, scope='game'), 12)  # both 'game' or 'unsaved' can be passed for the scope here
t.setVariable('=', var(num1, scope='saved'), 12)
t.setVariable('=', var(num1, scope='local'), 12)
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
from dfpyre import *
t = DFTemplate()
t.playerEvent('Join')
t.playerAction('Teleport', loc(10, 50, 10))
```

### Item

Represents a minecraft item:

```py
item('stick', count=5)
item('stone', 64)
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
from dfpyre import *
t = DFTemplate()
t.playerEvent('Join')
t.playerAction('PlaySound', sound('Grass Place'))
```

### Particle

Represents a diamondfire particle item:

```py
particle(name='Cloud', amount=10, horizontal=1.0, vertical=0.5, x=1.0, y=0.0, z=0.0, motionVariation=100)
```

Example:

```py
# plays a white cloud particle effect at 5, 50, 5
from dfpyre import *
t = DFTemplate()
t.playerEvent('Join')
t.playerAction('Particle', particle('Cloud'), loc(5, 50, 5))
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
from dfpyre import *
t = DFTemplate()
t.playerEvent('Join')
t.playerAction('GivePotion', potion('Saturation', amp=254))
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
from dfpyre import *
t = DFTemplate()
t.function('printData')
t.playerAction('SendMessage', gamevalue('Player Count'), gamevalue('CPU Usage'))
```

### Vector

Represents a diamondfire vector item:

```py
vector(x=1.1, y=0.0, z=0.5)
```

Example:

```py
# sets the player's x velocity to 1.0 on join
from dfpyre import *
t = DFTemplate()
t.playerEvent('Join')
t.playerAction('SetVelocity', vector(x=1.0, y=0.0, z=0.0))
```

### Conditionals/Brackets

A list of conditionals and loops can be found [here](#commands).

A specific syntax must be followed when creating conditionals and loops. Each conditional statement must be followed by a `bracket()` method, which will contain code. Here's an example:

```py
# prints 'clicked' when a player right clicks with a stick in their hand
from dfpyre import *
t = DFTemplate()
t.playerEvent('RightClick')
t.ifPlayer('IsHolding', item('stick'))
t.bracket(
    t.playerAction('SendMessage', 'clicked')
)
```

To create an `else` statement, use the `else_` method:

```py
# says the player is 'on the ground' when grounded and 'in the air' otherwise.
from dfpyre import *
t = DFTemplate()
t.function('grounded')
t.ifPlayer('IsGrounded')
t.bracket(
    t.playerAction('ActionBar', 'on the ground')
)
t.else_()
t.bracket(
    t.playerAction('ActionBar', 'in the air')
)
t.build()
```

### Loops

As for loops, the bracket syntax is the same and will automatically change to "repeat-type" brackets:

```py
# prints numbers 1-5
from dfpyre import *
t = DFTemplate()
t.playerEvent('Join')
t.repeat('Multiple', var('i'), 5)
t.bracket(
    t.playerAction('SendMessage', var('i'))
)
```

### Creating Functions/Processes

To create a function or process, just start the template with a `function` or `process` method:

```py
# function that gives a player 64 golden apples
from dfpyre import *
t = DFTemplate()
t.function('doStuff')
t.playerAction('GiveItems', item('golden_apple', 64))
```

### Calling Functions/Processes

Calling Functions and processes is also simple:

```py
from dfpyre import *
t = DFTemplate()
t.playerEvent('Join')
t.callFunction('doStuff')
```

Function parameters can also be inputted easier. Check [here](#functions-with-parameters) for more info.

### Functions with Parameters

Lets say that we have this function that prints out double (numx2) of what was inputted (num):

```py
# prints numbers 1-5
from dfpyre import *
t = DFTemplate()
t.function('double')
t.setVariable('x', var('numx2'), var('num'), 2)
t.playerAction('SendMessage', var('numx2'))
```

To easily pass the required parameter `num`, we can use the `parameters` keyword like this:

```py
# prints numbers 1-5
from dfpyre import *
t = DFTemplate()
t.playerEvent('Join')
t.callFunction('double', parameters={'num': 5})
```

This basically just sets a local variable for each key in `parameters` before the function is called.

### Special Return

Similar to [functions with parameters](#functions-with-parameters), `return_` is an extension of the `function` method.

When you want to return a given value from a function, you can use `return_` like this:

```py
from dfpyre import *
t = DFTemplate()
t.function('return10')
t.return_(returndata={'retnum': 10})
t.buildAndSend()
```

For each value in `returndata`, a local variable will be set for each entry.
After all of the variables are set, a `control('Return')` block is automatically added to the end of the line. This allows you to access these local variables after the function returns.

### Method List

- Events / Function / Process
  - playerEvent
  - entityEvent
  - function
  - process
  - callFunction
  - startProcess

- Actions
  - playerAction
  - gameAction
  - entityAction

- Conditionals / Loops
  - ifPlayer
  - ifVariable
  - ifGame
  - ifEntity
  - else_ (dont forget underscore)
  - repeat
  - bracket (more info above)

- Other
  - control
  - selectObject
  - setVariable

- Extras
  - return_