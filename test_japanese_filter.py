from src.utils import contains_japanese

# Test cases
test_cases = [
    ("これは日本語です", True),
    ("This is English only", False),
    ("This contains 日本語", True),
    ("", False),
    ("123456", False),
    ("カタカナのみ", True),
    ("ひらがなのみ", True),
    ("漢字のみ", True)
]

print("Testing Japanese character detection:")
for text, expected in test_cases:
    result = contains_japanese(text)
    status = "✅" if result == expected else "❌"
    print(f"{status} '{text}' -> {result} (Expected: {expected})")

