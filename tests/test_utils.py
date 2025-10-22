# tests/test_utils.py
from utils import analyze_string, sha256_hex

def test_analyze_string_palindrome():
    s = "Level"
    props = analyze_string(s)
    assert props["length"] == 5
    assert props["is_palindrome"] is True
    assert props["word_count"] == 1
    assert props["sha256_hash"] == sha256_hex(s)

def test_analyze_string_non_palindrome():
    s = "Hello"
    props = analyze_string(s)
    assert props["is_palindrome"] is False
    assert props["length"] == 5
