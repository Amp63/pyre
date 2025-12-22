from dfpyre import *

PlayerEvent.Join([
    PlayerAction.SendMessage('Hello %default!')
]).build_and_send()