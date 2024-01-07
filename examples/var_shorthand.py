from dfpyre import *

t = DFTemplate()
resultParam = parameter('resultVar', ParameterType.VAR)
num1Param = parameter('num1', ParameterType.NUMBER)
num2Param = parameter('num2', ParameterType.NUMBER)
t.function('add', resultParam, num1Param, num2Param)
t.setVariable('+', '$iresultVar', '$inum1', '$inum2')
t.buildAndSend()