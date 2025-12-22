from dfpyre import *

PlayerEvent.Join([
    SetVariable.CreateList(Variable('list', 'line')),
    Repeat.Multiple(Variable('i', 'line'), 10, codeblocks=[
        SetVariable.AppendValue(Variable('list', 'line'), Variable('i', 'line'))
    ])
]).build_and_send()