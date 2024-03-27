from dfpyre import *

t = DFTemplate()
t.player_event('Join')
t.set_variable('CreateList', '$ilist')
t.repeat('Multiple', '$ii', 10)
t.bracket(
    t.set_variable('AppendValue', '$ilist', '$ii')
)
t.build_and_send('recode')