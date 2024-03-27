from dfpyre import *

t = DFTemplate()
result_param = parameter('resultVar', ParameterType.VAR)
num1_param = parameter('num1', ParameterType.NUMBER)
num2_param = parameter('num2', ParameterType.NUMBER)
t.function('add', result_param, num1_param, num2_param)
t.set_variable('+', '$iresultVar', '$inum1', '$inum2')
t.build_and_send('recode')