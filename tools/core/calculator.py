from smolagents import Tool


class CalculatorTool(Tool):
    name = "calculator"

    description = (
        "Evaluates basic mathematical expressions. "
        "Supports +, -, *, /, %, ** and parentheses."
    )

    inputs = {
        "expression": {
            "type": "string",
            "description": "Mathematical expression to evaluate."
        }
    }

    output_type = "string"

    def forward(self, expression: str) -> str:
        try:
            result = eval(
                expression,
                {"__builtins__": {}},
                {}
            )
            return str(result)

        except Exception as e:
            return f"Error: {str(e)}"