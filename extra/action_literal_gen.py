"""
Generates `Literal` objects containing action names for each codeblock type.
This allows action names to be autocompleted if the user's IDE supports it.
"""

from dfpyre.actiondump import ACTIONDUMP


OUTPUT_PATH = 'dfpyre/action_literals.py'


def omit(action_name: str, action_data: dict) -> bool:
    return 'deprecatedNote' in action_data or 'legacy' in action_name.lower()


def generate_action_literals():
    generated_lines: list[str] = ['from typing import Literal\n']
    for codeblock_type, actions in ACTIONDUMP['codeblock_data'].items():
        if len(actions) == 1:
            continue

        filtered_actions = [a for a, d in actions.items() if not omit(a, d)]  # Omit deprecated actions
        action_list = str(filtered_actions)
        literal_line = f'{codeblock_type.upper()}_ACTION = Literal{action_list}'
        generated_lines.append(literal_line)
    
    game_value_names = list(ACTIONDUMP['game_values'].keys())
    generated_lines += [
        f'GAME_VALUE_NAME = Literal{str(game_value_names)}',
        f'SOUND_NAME = Literal{str(ACTIONDUMP['sound_names'])}',
        f'POTION_NAME = Literal{str(ACTIONDUMP['potion_names'])}',
        'SUBACTION = IF_PLAYER_ACTION | IF_ENTITY_ACTION | IF_GAME_ACTION | IF_VAR_ACTION'
    ]
    
    with open(OUTPUT_PATH, 'w') as f:
        f.write('\n'.join(generated_lines) + '\n')


if __name__ == '__main__':
    generate_action_literals()
    print(f'Wrote codeblock action Literals to {OUTPUT_PATH}.')
