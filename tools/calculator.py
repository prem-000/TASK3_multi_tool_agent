
import ast
import math
import operator

from langchain.tools import tool

BINARY_OPERATORS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
}

UNARY_OPERATORS = {
    ast.UAdd: operator.pos,
    ast.USub: operator.neg,
}

MAX_EXPRESSION_LENGTH = 200
MAX_AST_NODES = 50
MAX_ABS_RESULT = 10**18
MAX_ABS_EXPONENT = 8


def _check_number(value):
    if type(value) not in (int, float):
        raise ValueError("Only real numeric values are supported.")

    if abs(value) > MAX_ABS_RESULT:
        raise ValueError("The result exceeds the allowed size.")

    if isinstance(value, float) and not math.isfinite(value):
        raise ValueError("The result is not finite.")

    return value


def _evaluate_node(node):
    if isinstance(node, ast.Constant):
        return _check_number(node.value)

    if isinstance(node, ast.UnaryOp):
        operation = UNARY_OPERATORS.get(type(node.op))

        if operation is None:
            raise ValueError("Unsupported unary operator.")

        return _check_number(operation(_evaluate_node(node.operand)))

    if isinstance(node, ast.BinOp):
        operation = BINARY_OPERATORS.get(type(node.op))

        if operation is None:
            raise ValueError("Unsupported mathematical operator.")

        left = _evaluate_node(node.left)
        right = _evaluate_node(node.right)

        if isinstance(node.op, ast.Pow) and abs(right) > MAX_ABS_EXPONENT:
            raise ValueError("Exponent magnitude cannot exceed 8.")

        return _check_number(operation(left, right))

    raise ValueError(
        "Only numbers, parentheses, and basic arithmetic operators are allowed."
    )


def calculate(expression: str):
    """Safely evaluate a limited arithmetic expression."""
    if not isinstance(expression, str) or not expression.strip():
        raise ValueError("Expression cannot be empty.")

    if len(expression) > MAX_EXPRESSION_LENGTH:
        raise ValueError("Expression is too long.")

    tree = ast.parse(expression, mode="eval")

    if sum(1 for _ in ast.walk(tree)) > MAX_AST_NODES:
        raise ValueError("Expression is too complex.")

    return _evaluate_node(tree.body)


@tool
def calculator(expression: str) -> str:
    """Calculate arithmetic accurately. Supports +, -, *, /, //, %, **,
    and parentheses. Use this tool instead of estimating numeric results.
    Example: (18 * 24) / 3
    """
    try:
        return f"{expression} = {calculate(expression)}"
    except Exception as exc:
        return f"ERROR: Calculation failed: {type(exc).__name__}: {exc}"