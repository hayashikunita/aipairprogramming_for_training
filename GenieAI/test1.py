# The function we want to test
def add(a, b):
    """A simple function to add two numbers."""
    return a + b

def test_add_positive_numbers():
    assert add(1, 2) == 3

def test_add_negative_numbers():
    assert add(-1, -2) == -3

def test_add_mixed_sign_numbers():
    assert add(-1, 2) == 1

def test_add_with_zero():
    assert add(0, 5) == 5
    assert add(5, 0) == 5
