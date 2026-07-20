from tools import registry

calculator = registry.get_tools()[0]

print(calculator.forward("2 + 3"))
print(calculator.forward("10 * 5"))
print(calculator.forward("2 ** 8"))
print(calculator.forward("(15 + 5) / 4"))