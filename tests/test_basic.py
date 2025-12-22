from dfpyre import *


TEMPLATE_CODE = 'H4sIAAAAAAAA/92U32/TMBDH/5XIEm+RWAdFIiqVhsZoH4omWu2FTdHNvmRWHTv4R7Wqyv+OE5fidsvoYOKBp8T2+e77/eRyG3IrFF0akn3bEM5IFtYk3T4zUjhJ/RJ06YN8jMVqG+3fup1wK7dQ+jgGFtpdVVuupD+5AGHQH7THGZmaZMIZQ9mmpNsQtpZQcXpYtGlSYoSyJDt919w0P3MTpubWFQVp0h7JtYA16nyb/7faqarqSLnXgn53xEAv89rpWuB4gcYmo9fx1uhWCTYewXcH47nVXJaR4JNO23GAFtpFfOQdam6TuV0LNDGkOUo2Q2OgxF6rEbG3z1BwxlhiaqBdwaBjgfc2uQLhMJmhLlt3f65l+AwtX7F0AvROyJngpaxQ2mSmGP6FiNBCj95+qUbqFr88hTOyOb/Iv3xcZG/eD4cpVU7abJByll2TikukGgqbMQ6VkuyaNHtNtKf4M1/htCvcstEl2g6PuOxEmn4XvMiDkX/gIK85XcI9Hjo5vgE+cet/geQOJNs1wcQvknmbKuIxNRP/B4bOfGi1/8vH93Ycz7EAJ2wEUQNdYluQcY20jVF1N7bsum7ng1S66mdu0OYrOIJ4CDqYPa9YkOMpmMsA1AcZqrrKThpYIXuSr3TVw7SD6MpgH8qHJ51TocIMP8Y6tvP+v+Z48qIcb5ofHWvHD4UHAAA='


def test_basic():
    t = DFTemplate.from_code(TEMPLATE_CODE)
    init_codeblocks = len(t.codeblocks)
    
    t.insert([
        PlayerAction.SendMessage('hi'),
        IfVariable.Equals('$ix', 5, codeblocks=[
            PlayerAction.GiveItems(Item('diamond'))
        ])
    ]).build()
    
    assert len(t.codeblocks) == init_codeblocks+5, 'Mismatched number of added codeblocks.'


def test_send():
    t = DFTemplate.from_code(TEMPLATE_CODE)
    assert t.build_and_send() == 0


def test_scriptgen():
    t = DFTemplate.from_code(TEMPLATE_CODE)
    assert t.generate_script()


def test_all_codeblocks():
    PlayerEvent.Join([
        PlayerAction.SendMessage('test'),
        EntityAction.Heal(20),
        GameAction.SetBlock(Item('stone'), Location(1.5, 2.5, 3.5)),
        SetVariable.Assign('$i x', 5),
        IfPlayer.IsHolding(Item('diamond_pickaxe')),
        IfEntity.IsGrounded(),
        IfGame.BlockEquals(Location(1.5, 2.5, 3.5), Item('stone')),
        IfVariable.Equals('$i x', 5),
        Repeat.Multiple('$i j', 10, codeblocks=[
            SelectObject.AllPlayers(),
            Control.Wait(1)
        ]),
        CallFunction('foo'),
        StartProcess('bar')
    ]).build()

    EntityEvent.FallingBlockLand([
        PlayerAction.SendMessage('landed', target=Target.ALL_PLAYERS)
    ]).build()

    Function('foo', codeblocks=[
        PlayerAction.SendMessage('called foo')
    ]).build()

    Process('bar', codeblocks=[
        PlayerAction.SendMessage('started bar')
    ]).build()