import pytest

# The function we want to test
def add(a, b):
    """A simple function to add two numbers."""
    return a + b

# The test functions
def test_add_positive_numbers():
    # 1. Arrange
    num1 = 10
    num2 = 5
    expected_result = 15

    # 2. Act
    actual_result = add(num1, num2)

    # 3. Assert
    assert actual_result == expected_result

def test_add_negative_numbers():
    # Arrange
    num1 = -10
    num2 = -5
    expected_result = -15

    # Act
    actual_result = add(num1, num2)

    # Assert
    assert actual_result == expected_result

def test_add_positive_and_negative_number():
    # Arrange
    num1 = -10
    num2 = 5
    expected_result = -5

    # Act
    actual_result = add(num1, num2)

    # Assert
    assert actual_result == expected_result

def test_add_with_zero():
    # Arrange
    num1 = 10
    num2 = 0
    expected_result = 10

    # Act
    actual_result = add(num1, num2)

    # Assert
    assert actual_result == expected_result

def test_add_float_numbers():
    # Arrange
    num1 = 10.5
    num2 = 2.2

    # Act
    actual_result = add(num1, num2)

    # Assert
    assert actual_result == pytest.approx(12.7)
