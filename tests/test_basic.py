from dfpyre import *
import os
import sys


TEMPLATE_CODE = 'H4sIAAAAAAAA/91V247aMBD9lchS3yKV7VWKKNK2dAsPVKuC+lJW0WBPgoVjp76gRSj/XsehyLDLdtmu+tAnmPFczjkeT7ZkIRRdGZL92BLOSNbZJN39ZqRwknoTdOmDfIzFahft/wVPm7Xk0vooBhb2vjbTciVJ06TECGVJ9uptkx5lLkRuoYxyVR2SMnIFwqA/aI8zMjbJiDOGsgVDdyFsI6Hi9Bhu1PBdc9P8rk2YmlpXFCSAuI9sLWCDOt/V/yNrqqo6Qu6xoPf2GehVXjtdCxzM0Nik/zJ29RdKsEEffjoYTK3msowA984QaKZdpI9couY2mdqNQBOLNEXJJmgMlHiSaqTYmzMQXDKWmBpoaNjhmOGtTb6DcJhMUJctu6djOWdcvmHpBOg9kEvBS1mhtMlEMfwLEN0I3Zv9XIMUjOj5hDOy/aSctNnFIh1e5V8/zrLX73u9lLNsTioukWoobMY4VEqyOWkOpugA8he+xnHo3IqjS7RBH3EdUJrTNHiRd0z+BYW85nQFtzgnqb/BbDuEymvsuTRPfB+fufVvIlmCZPupGHkjmbalIn3GZuSfZDeqd6mfHoU4b6/rEAtwwkaiaqArDOuRa6RtjKrDHrObul0YUunq9B0YtPkaHnEDXdDRMnrBOjheBXPd6euDDFWhs5MG1sge1Fe66m7Ziyjl4lCUDw8yp0J1S/0x1LH9APzXOvaeVceb5hcmKlpO0AcAAA=='


def test_basic():
    t = DFTemplate.from_code(TEMPLATE_CODE)
    init_codeblocks = len(t.codeblocks)
    
    t.player_action('SendMessage', 'hi')
    t.if_variable('=', '$ix', 5)
    t.bracket(
        t.player_action('GiveItems', item('diamond'))
    )
    
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

    __import__(module_name)
    mod = sys.modules[module_name]
    assert hasattr(mod, 't'), 'Script does not have a template object.'

    assert len(t.codeblocks) == len(mod.t.codeblocks), 'Number of codeblocks does not match.'

    os.remove(script_path)


def test_all_codeblocks():
    t = DFTemplate()
    t.player_event('Join')
    t.player_action('SendMessage', 'test')
    t.entity_action('Heal', 20)
    t.game_action('SetBlock', item('stone'), loc(1.5, 2.5, 3.5))
    t.set_variable('=', '$ix', 5)
    t.if_player('IsHolding', item('diamond_pickaxe')); t.bracket()
    t.if_entity('IsGrounded'); t.bracket()
    t.if_game('BlockEquals', loc(1.5, 2.5, 3.5), item('stone')); t.bracket()
    t.if_variable('=', '$ix', 5); t.bracket()
    t.repeat('Multiple', 10); t.bracket()
    t.select_object('AllPlayers')
    t.control('Wait', 1)
    t.call_function('foo')
    t.start_process('bar')
    t.build()

    t = DFTemplate()
    t.entity_event('FallingBlockLand')
    t.build()

    t = DFTemplate()
    t.function('foo')
    t.build()

    t = DFTemplate()
    t.process('bar')
    t.build()