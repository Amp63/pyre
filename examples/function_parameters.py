from dfpyre import *

t = DFTemplate()
resultParam = parameter('resultVar', ParameterType.VAR)
num1Param = parameter('num1', ParameterType.NUMBER)
num2Param = parameter('num2', ParameterType.NUMBER)
t.function('add', resultParam, num1Param, num2Param)
t.setVariable('+', var('resultVar', 'line'), var('num1', 'line'), var('num2', 'line'))
t.buildAndSend()