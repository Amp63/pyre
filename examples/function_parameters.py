from dfpyre import *

result_param = Parameter('resultVar', ParameterType.VAR)
num1_param = Parameter('num1', ParameterType.NUMBER)
num2_param = Parameter('num2', ParameterType.NUMBER)
function('add', result_param, num1_param, num2_param, codeblocks=[
    set_variable('+', Variable('resultVar', 'line'), Variable('num1', 'line'), Variable('num2', 'line'))
]).build_and_send('codeclient')