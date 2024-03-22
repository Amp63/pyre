import re
from mcitemlib.style import STYLE_CODE_REGEX, FORMAT_CODES, StyledString

def is_ampersand_coded(s: str) -> bool:
    return bool(re.match(STYLE_CODE_REGEX, s))


def ampersand_to_minimessage(ampersand_code: str) -> str:
    ampersand_code = ampersand_code.replace('&r', '<reset>')  # bad but should work most of the time
    styled_string = StyledString.from_codes(ampersand_code)
    formatted_string_list = []
    for substring in styled_string.substrings:
        formatted_substring_list = []
        for style_type, value in substring.data.items():
            if style_type in FORMAT_CODES.values() and value:
                formatted_substring_list.append(f'<{style_type}>')
            if style_type == 'color':
                formatted_substring_list.append(f'<{value}>')
        
        formatted_substring_list.append(substring.data['text'])
        formatted_string_list.append(''.join(formatted_substring_list))
    return ''.join(formatted_string_list)