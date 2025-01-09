from dfpyre import *

player_event('Join', [
    player_action('SendMessage', 'Hello %default!')
]).build_and_send('codeclient')