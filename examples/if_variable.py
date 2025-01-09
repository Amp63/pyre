from dfpyre import *

player_count = GameValue('Player Count')
player_event('Join', [
    if_variable('>', player_count, 10, codeblocks=[
        player_action('SendMessage', 'There are more than 10 players online.')
    ]),
    else_([
        player_action('SendMessage', 'There are less than 10 players online.')
    ])
]).build_and_send('codeclient')