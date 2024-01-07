from dfpyre import *

t = DFTemplate()
t.playerEvent('Join')
t.playerAction('SendMessage', 'Hello %default!')
t.buildAndSend()