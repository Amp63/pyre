from dfpyre import *

player_count = GameValue('Player Count')
PlayerEvent.Join([
    IfVariable.GreaterThan(player_count, 10, codeblocks=[
        PlayerAction.SendMessage('There are more than 10 players online.')
    ]),
    Else([
        PlayerAction.SendMessage('There are less than 10 players online.')
    ])
]).build_and_send()