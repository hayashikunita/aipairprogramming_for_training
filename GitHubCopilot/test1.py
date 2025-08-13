import pytest

# The function we want to test
def add(a, b):
    """A simple function to add two numbers."""
    return a + b


def test_add_positive():
    assert add(2, 3) == 5

def test_add_negative():
    assert add(-1, -2) == -3

def test_add_zero():
    assert add(0, 0) == 0

def test_add_mixed():
    assert add(-5, 5) == 0