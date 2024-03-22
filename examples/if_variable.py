from dfpyre import *

t = DFTemplate()
t.player_event('Join')
player_count = gamevalue('Player Count')
t.if_variable('>', player_count, 10)
t.bracket(
    t.player_action('SendMessage', 'There are more than 10 players online.')
)
t.else_()
t.bracket(
    t.player_action('SendMessage', 'There are less than 10 players online.')
)
t.build_and_send()