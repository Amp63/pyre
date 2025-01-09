from dfpyre import *
import os
import sys


TEMPLATE_CODE = 'H4sIAAAAAAAA/91V247aMBD9lchS3yKV7VWKKNK2dAsPVKuC+lJW0WBPgoVjp76gRSj/XsehyLDLdtmu+tAnmPFczjkeT7ZkIRRdGZL92BLOSNbZJN39ZqRwknoTdOmDfIzFahft/wVPm7Xk0vooBhb2vjbTciVJ06TECGVJ9uptkx5lLkRuoYxyVR2SMnIFwqA/aI8zMjbJiDOGsgVDdyFsI6Hi9Bhu1PBdc9P8rk2YmlpXFCSAuI9sLWCDOt/V/yNrqqo6Qu6xoPf2GehVXjtdCxzM0Nik/zJ29RdKsEEffjoYTK3msowA984QaKZdpI9couY2mdqNQBOLNEXJJmgMlHiSaqTYmzMQXDKWmBpoaNjhmOGtTb6DcJhMUJctu6djOWdcvmHpBOg9kEvBS1mhtMlEMfwLEN0I3Zv9XIMUjOj5hDOy/aSctNnFIh1e5V8/zrLX73u9lLNsTioukWoobMY4VEqyOWkOpugA8he+xnHo3IqjS7RBH3EdUJrTNHiRd0z+BYW85nQFtzgnqb/BbDuEymvsuTRPfB+fufVvIlmCZPupGHkjmbalIn3GZuSfZDeqd6mfHoU4b6/rEAtwwkaiaqArDOuRa6RtjKrDHrObul0YUunq9B0YtPkaHnEDXdDRMnrBOjheBXPd6euDDFWhs5MG1sge1Fe66m7Ziyjl4lCUDw8yp0J1S/0x1LH9APzXOvaeVceb5hcmKlpO0AcAAA=='


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