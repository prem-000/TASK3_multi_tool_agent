
import pytest

from tools.calculator import calculate


def test_calculator_compound_expression():
    assert calculate("(18 * 24) / 3") == 144


def test_calculator_parentheses():
    assert calculate("(2 + 3) * 4") == 20


def test_calculator_division():
    assert calculate("10 / 4") == 2.5


def test_calculator_rejects_python_code():
    with pytest.raises((ValueError, SyntaxError)):
        calculate("__import__('os').system('echo unsafe')")


def test_calculator_rejects_large_exponent():
    with pytest.raises(ValueError):
        calculate("2 ** 20")