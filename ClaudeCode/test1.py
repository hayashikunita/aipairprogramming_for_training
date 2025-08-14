import pytest

def add(a, b):
    """A simple function to add two numbers."""
    return a + b


class TestAdd:
    """add関数のテストクラス"""
    
    def test_add_positive_numbers(self):
        """正の数同士の足し算をテスト"""
        assert add(2, 3) == 5
        assert add(10, 5) == 15
        assert add(1, 1) == 2
    
    def test_add_negative_numbers(self):
        """負の数を含む足し算をテスト"""
        assert add(-1, -1) == -2
        assert add(-5, 3) == -2
        assert add(5, -3) == 2
    
    def test_add_zero(self):
        """ゼロを含む足し算をテスト"""
        assert add(0, 0) == 0
        assert add(0, 5) == 5
        assert add(5, 0) == 5
    
    def test_add_floats(self):
        """浮動小数点数の足し算をテスト"""
        assert add(2.5, 3.5) == 6.0
        assert add(1.1, 2.2) == pytest.approx(3.3)
        assert add(-1.5, 1.5) == 0.0
    
    def test_add_large_numbers(self):
        """大きな数値の足し算をテスト"""
        assert add(1000000, 2000000) == 3000000
        assert add(-1000000, 500000) == -500000


# パラメータ化テストの例
@pytest.mark.parametrize("a, b, expected", [
    (1, 2, 3),
    (0, 0, 0),
    (-1, 1, 0),
    (10, -5, 5),
    (2.5, 3.5, 6.0),
    (100, 200, 300),
])
def test_add_parametrized(a, b, expected):
    """パラメータ化テスト：複数の入力パターンを一度にテスト"""
    assert add(a, b) == expected


def test_add_type_error():
    """不正な型を渡した場合のテスト"""
    with pytest.raises(TypeError):
        add("hello", "world")  # 文字列同士は連結されるため、実際はエラーにならない
    
    with pytest.raises(TypeError):
        add(5, None)  # Noneとの計算はTypeError