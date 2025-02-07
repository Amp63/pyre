from dfpyre import *

player_event('Join', [
    set_variable('CreateList', Variable('list', 'line')),
    repeat('Multiple', Variable('i', 'line'), 10, codeblocks=[
        set_variable('AppendValue', Variable('list', 'line'), Variable('i', 'line'))
    ])
]).build_and_send('codeclient')