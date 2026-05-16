# todo

## Actiondump
- The actiondump seems to alias leading and trailing space actions (such as " SetDirection ") by creating blank entries with fixed names ("SetDirection" in this example)
  - This results in duplicate methods, with one method being basically empty
  - We need to check if these aliases exist and then either use them or omit them completely

## Other
- Convert `CodeBlock` class `data` field from dict into dataclass
- Add option to set string conversion
  - By default, python `str` converts to `String` but could be set to convert to `Text` instead.
- Separate scriptgen `argument_item_to_string` clauses into methods in each item class