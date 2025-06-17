from dfpyre import *
import os
import sys


TEMPLATE_CODE = 'H4sIAAAAAAAA/92U32/TMBDH/5XIEm+RWAdFIiqVhsZoH4omWu2FTdHNvmRWHTv4R7Wqyv+OE5fidsvoYOKBp8T2+e77/eRyG3IrFF0akn3bEM5IFtYk3T4zUjhJ/RJ06YN8jMVqG+3fup1wK7dQ+jgGFtpdVVuupD+5AGHQH7THGZmaZMIZQ9mmpNsQtpZQcXpYtGlSYoSyJDt919w0P3MTpubWFQVp0h7JtYA16nyb/7faqarqSLnXgn53xEAv89rpWuB4gcYmo9fx1uhWCTYewXcH47nVXJaR4JNO23GAFtpFfOQdam6TuV0LNDGkOUo2Q2OgxF6rEbG3z1BwxlhiaqBdwaBjgfc2uQLhMJmhLlt3f65l+AwtX7F0AvROyJngpaxQ2mSmGP6FiNBCj95+qUbqFr88hTOyOb/Iv3xcZG/eD4cpVU7abJByll2TikukGgqbMQ6VkuyaNHtNtKf4M1/htCvcstEl2g6PuOxEmn4XvMiDkX/gIK85XcI9Hjo5vgE+cet/geQOJNs1wcQvknmbKuIxNRP/B4bOfGi1/8vH93Ycz7EAJ2wEUQNdYluQcY20jVF1N7bsum7ng1S66mdu0OYrOIJ4CDqYPa9YkOMpmMsA1AcZqrrKThpYIXuSr3TVw7SD6MpgH8qHJ51TocIMP8Y6tvP+v+Z48qIcb5ofHWvHD4UHAAA='


def test_basic():
    t = DFTemplate.from_code(TEMPLATE_CODE)
    init_codeblocks = len(t.codeblocks)
    
    t.insert([
        player_action('SendMessage', 'hi'),
        if_variable('=', '$ix', 5, codeblocks=[
            player_action('GiveItems', Item('diamond'))
        ])
    ]).build()
    
    assert len(t.codeblocks) == init_codeblocks+5, 'Mismatched number of added codeblocks.'


def test_send():
    t = DFTemplate.from_code(TEMPLATE_CODE)
    assert t.build_and_send('codeclient') == 0


def test_scriptgen():
    t = DFTemplate.from_code(TEMPLATE_CODE)

    directory = os.path.dirname(os.path.abspath(__file__))
    module_name = 'generated_test_script'
    script_path = f'{directory}/{module_name}.py'
    t.generate_script(script_path)
    assert os.path.exists(script_path), 'File was not generated.'

    os.remove(script_path)


def test_all_codeblocks():
    player_event('Join', [
        player_action('SendMessage', 'test'),
        entity_action('Heal', 20),
        game_action('SetBlock', Item('stone'), Location(1.5, 2.5, 3.5)),
        set_variable('=', '$i x', 5),
        if_player('IsHolding', Item('diamond_pickaxe')),
        if_entity('IsGrounded'),
        if_game('BlockEquals', Location(1.5, 2.5, 3.5), Item('stone')),
        if_variable('=', '$i x', 5),
        repeat('Multiple', 10, codeblocks=[
            select_object('AllPlayers'),
            control('Wait', 1)
        ]),
        call_function('foo'),
        start_process('bar')
    ]).build()

    entity_event('FallingBlockLand', [
        player_action('SendMessage', 'landed', target=Target.ALL_PLAYERS)
    ]).build()

    function('foo', codeblocks=[
        player_action('SendMessage', 'called foo')
    ]).build()

    process('bar', codeblocks=[
        player_action('SendMessage', 'started bar')
    ]).build()