import os
import sys
import io

STATE_NOMINAL = 1
STATE_AFTER_TOKEN1 = 2
STATE_IN_VAR = 3


class MissingVariableError(Exception):
    def __init__(self, varname, line):
        super().__init__("Missing environment variable '{}' in line {}".format(varname, line))


def injectenv(inp):
    output = io.StringIO()
    variable = ""
    line = 1
    state = STATE_NOMINAL
    for char in inp:
        if state == STATE_NOMINAL:
            if char == "$":
                state = STATE_AFTER_TOKEN1
            else:
                if char == '\n':
                    line += 1
                output.write(char)
        elif state == STATE_AFTER_TOKEN1:
            if char == "{":
                state = STATE_IN_VAR
                variable = ""
            else:
                output.write("$")
                output.write(char)
                state = STATE_NOMINAL
        elif state == STATE_IN_VAR:
            if char == '}':
                v = os.getenv(variable)
                if v is None or v == "":
                    raise MissingVariableError(variable, line)
                output.write(v)
                state = STATE_NOMINAL
            elif char.isalnum() or char == "_":
                variable += char
            else:
                # Must reject
                output.write("${" + variable + char)
                state = STATE_NOMINAL
        else:
            raise Exception("Unknow state '{}'".format(state))
    return output.getvalue()

#
# test1 = """Ceci est un test
# Home: '${HOME}'
# Et oui
# Autre ${123456
# }
# User: '${USER}'
# Virtual env: "${VIRTUAL_ENV}"
# Fin"""
#
# test2 = """Test error
# User: '${USER}'
# Missing var: ${A_VARIABLE}
# Fin"""
#
#
# def main():
#     out = injectenv(test1)
#     print("-------------------")
#     print(out)
#     print("-------------------")
#     try:
#         out = injectenv(test2)
#         print("-------------------")
#         print(out)
#         print("-------------------")
#     except MissingVariableError as err:
#         print(err)
#
#
# if __name__ == '__main__':
#     sys.exit(main())
#
