from mcitemlib.style import *

def isAmpersandCoded(s: str) -> bool:
    return bool(re.match(STYLE_CODE_REGEX, s))


def ampersandToMinimessage(ampersand_code: str) -> str:
    ampersand_code = ampersand_code.replace('&r', '<reset>')  # bad but should work most of the time
    styledString = StyledString.from_codes(ampersand_code)
    formattedStringList = []
    for substring in styledString.substrings:
        formattedSubstringList = []
        for styleType, value in substring.data.items():
            if styleType in FORMAT_CODES.values() and value:
                formattedSubstringList.append(f'<{styleType}>')
            if styleType == 'color':
                formattedSubstringList.append(f'<{value}>')
        
        formattedSubstringList.append(substring.data['text'])
        formattedStringList.append(''.join(formattedSubstringList))
    return ''.join(formattedStringList)