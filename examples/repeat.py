from dfpyre import *

player_event('Join', [
    set_variable('CreateList', '$ilist'),
    repeat('Multiple', '$ii', 10, codeblocks=[
        set_variable('AppendValue', '$ilist', '$ii')
    ])
]).build_and_send('codeclient')