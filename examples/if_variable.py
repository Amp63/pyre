from dfpyre import *

t = DFTemplate()
t.playerEvent('Join')
playerCount = gamevalue('Player Count')
t.ifVariable('>', playerCount, 10)
t.bracket(
    t.playerAction('SendMessage', 'There are more than 10 players online.')
)
t.else_()
t.bracket(
    t.playerAction('SendMessage', 'There are less than 10 players online.')
)
t.buildAndSend()