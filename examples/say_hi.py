from dfpyre import *

t = DFTemplate()
t.player_event('Join')
t.player_action('SendMessage', 'Hello %default!')
t.build_and_send()