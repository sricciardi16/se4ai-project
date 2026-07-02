# 1. Testing Framework & Mocking
import pytest

# 2. The Subject Under Test
import slugify as slugify_module
from slugify import slugify, slugify as make_slug

# 4. Auxiliary: Standard Library
from functools import partial


def test_slugify_basic_ascii_string():
    """
    When slugify is called with a standard ASCII string containing spaces and punctuation,
    it should return a lowercased string with words separated by a single hyphen,
    stripping out the punctuation.
    """
    result = slugify("This is a test ---")
    assert result == "this-is-a-test"


def test_slugify_collapses_consecutive_punctuation():
    """
    When slugify processes a string with multiple consecutive punctuation marks or spaces,
    it should collapse them into a single separator and ensure no leading or trailing separators remain.
    """
    result = slugify("Hello!!!  World??? -- Rich__Text")
    assert result == "hello-world-rich-text"


def test_slugify_default_strips_or_transliterates_unicode():
    """
    When slugify is called with a string containing non-ASCII Unicode characters
    (and allow_unicode is left as the default False), it should return an ASCII-only string.
    """
    result = slugify("影師嗎")

    # Verify the result is strictly ASCII
    assert result.isascii()
    # Verify the standard transliteration behavior of python-slugify for these characters
    assert result == "ying-shi-ma"


def test_slugify_allow_unicode_preserves_characters():
    """
    When slugify is called with allow_unicode=True, it should preserve non-ASCII
    Unicode characters in the resulting slug rather than stripping or transliterating them.
    """
    result = slugify("影師嗎", allow_unicode=True)
    assert result == "影師嗎"


def test_slugify_max_length_truncates_string():
    """
    When slugify is called with a max_length integer, the resulting slug must be
    truncated so its length does not exceed that number of characters.
    """
    result = slugify("one two three four five six seven", max_length=10)

    assert len(result) <= 10
    # "one-two-three..." truncated to 10 characters is "one-two-th"
    assert result == "one-two-th"

def test_slugify_word_boundary_prevents_partial_words():
    """
    When max_length is set and word_boundary=True, slugify should truncate
    at the nearest whole word and remove trailing separators.
    'alpha beta gamma delta' -> 'alpha-beta-gamma-delta'
    max_length=12 cuts at 'alpha-beta-g', word_boundary=True rolls back to 'alpha-beta'.
    """
    result = slugify("alpha beta gamma delta", max_length=12, word_boundary=True)
    assert result == "alpha-beta"


def test_slugify_custom_separator():
    """
    When a custom separator is provided, it should be used instead of the default hyphen.
    """
    result = slugify("This is a test", separator="_")
    assert result == "this_is_a_test"


def test_slugify_custom_regex_pattern_overrides_defaults():
    """
    When a custom regex_pattern is provided, it overrides the default allowed character set.
    The default pattern replaces non-alphanumeric characters. By adding '_' to the negated
    character class, underscores are preserved instead of being replaced by the separator.
    """
    result = slugify("___This is a test___", regex_pattern=r"[^-a-z0-9_]+")
    assert result == "___this-is-a-test___"


def test_slugify_removes_stopwords():
    """
    When an iterable of stopwords is provided, those exact words should be removed
    from the resulting slug.
    """
    result = slugify(
        "the quick brown fox jumps over the lazy dog in a hurry",
        stopwords=["the", "in", "a", "hurry"]
    )
    assert result == "quick-brown-fox-jumps-over-lazy-dog"


def test_slugify_preserves_case_when_lowercase_false():
    """
    When lowercase=False is passed, the original casing of the string should be preserved.
    """
    result = slugify("thIs Has a stopword Stopword", lowercase=False)
    assert result == "thIs-Has-a-stopword-Stopword"

def test_slugify_applies_replacements_before_stripping():
    text = "C# is not C++"
    replacements = [["C#", "Csharp"], ["C++", "Cpp"]]

    result = make_slug(text, replacements=replacements)

    assert result == "csharp-is-not-cpp"


def test_slugify_trims_leading_and_trailing_separators():
    text = " --- spaced --- "

    result = make_slug(text)

    assert result == "spaced"


def test_slugify_handles_special_characters_and_punctuation():
    test_cases = [
        "Hello World",
        "Hello@World#$%^&*()",
        "Hello/World\\Path",
        "Hello World!@#$%^&*()_+[]{}|;:,.<>?"
    ]

    for text in test_cases:
        # The specification requires that it processes them successfully
        # without raising unhandled exceptions.
        result = make_slug(text)
        assert isinstance(result, str)


def test_slugify_handles_multilingual_strings_and_repeated_calls():
    multilingual_strings = [
        "你好，世界",
        "Привет мир",
        "こんにちは世界",
        "안녕하세요 세계",
        "Olá Mundo"
    ]

    # Verify successful processing of multilingual strings
    for text in multilingual_strings:
        result = make_slug(text)
        assert isinstance(result, str)

    # Verify batch processing stability (at least 800 sequential calls)
    # We will process the list of strings 800 times, resulting in 4000 calls.
    for _ in range(800):
        for text in multilingual_strings:
            make_slug(text)

def test_slugify_standard_string_returns_lowercased_hyphenated_slug():
    input_text = "Hello World! This is a TEST..."
    expected_output = "hello-world-this-is-a-test"

    assert slugify(input_text) == expected_output


def test_slugify_non_ascii_string_transliterates_to_ascii_equivalents():
    input_latin = "München is naïve and résumé"
    expected_latin = "munchen-is-naive-and-resume"

    input_cyrillic = "Кожушчек"
    expected_cyrillic = "kozhushchek"

    assert slugify(input_latin) == expected_latin
    assert slugify(input_cyrillic) == expected_cyrillic


def test_slugify_custom_separator_replaces_spaces_and_punctuation():
    input_text_1 = "Data: 2023/04/01"
    expected_output_1 = "data_2023_04_01"

    input_text_2 = "A B C"
    expected_output_2 = "abc"

    assert slugify(input_text_1, separator="_") == expected_output_1
    assert slugify(input_text_2, separator="") == expected_output_2


def test_slugify_max_length_truncates_string_to_exact_limit():
    input_text_1 = "The quick brown fox"
    expected_output_1 = "the-quick-br"

    input_text_2 = "Short"
    expected_output_2 = "short"

    assert slugify(input_text_1, max_length=12) == expected_output_1
    assert slugify(input_text_2, max_length=20) == expected_output_2


def test_slugify_max_length_with_word_boundary_truncates_at_whole_words():
    input_text = "The quick brown fox"
    expected_output = "the-quick"

    assert slugify(input_text, max_length=12, word_boundary=True) == expected_output

def test_slugify_with_stopwords_removes_exact_words():
    """
    Tests that exact standalone stopwords are removed without affecting
    partial word matches (e.g., 'the' is removed, but 'theater' and 'theme' remain).
    """
    text = "The theater is the best place for a theme"
    stopwords = ['the', 'a']

    result = slugify(text, stopwords=stopwords)

    assert result == "theater-is-best-place-for-theme"


def test_slugify_with_replacements_executes_custom_substitutions_first():
    """
    Tests that custom string replacements are executed before standard
    slugification strips out special characters.
    """
    text = "100% of the time, it works & is awesome!"
    replacements = [['%', ' percent'], ['&', 'and']]

    result = slugify(text, replacements=replacements)

    assert result == "100-percent-of-the-time-it-works-and-is-awesome"


def test_slugify_with_allow_unicode_preserves_non_ascii_characters():
    """
    Tests that allow_unicode=True bypasses ASCII transliteration and
    preserves non-ASCII characters (like Cyrillic and Logograms).
    """
    # Cyrillic test
    text1 = "Текст на русском языке, 100%!"
    result1 = slugify(text1, allow_unicode=True)
    assert result1 == "текст-на-русском-языке-100"

    # Logogram test
    text2 = "你好 世界!"
    result2 = slugify(text2, allow_unicode=True)
    assert result2 == "你好-世界"


def test_slugify_with_encoded_entities_decodes_to_standard_characters():
    """
    Tests that HTML entities, decimal, and hexadecimal encodings are decoded
    properly before transliteration.
    """
    text = "caf&eacute; &#233; &#xE9;"

    result = slugify(text, entities=True, decimal=True, hexadecimal=True)

    assert result == "cafe-e-e"


def test_slugify_partial_application_for_reusability():
    # Create a pre-configured callable acting as our "instance"
    custom_slugify = partial(slugify, separator='_', lowercase=False, max_length=10)

    # Input 1
    result1 = custom_slugify("Hello World!")
    assert result1 == "Hello_Worl"

    # Input 2
    result2 = custom_slugify("Another Test String")
    assert result2 == "Another_Te"

@pytest.mark.parametrize("input_text", [
    "",
    "     ",
    "!@#$%^&*()_+",
    " - . , "
])
def test_slugify_empty_or_stripped_string_returns_empty_string(input_text):
    """
    When `slugify` is called with an empty string, or a string consisting entirely
    of spaces and punctuation characters that are stripped by default, it must
    return an exact empty string `""`.
    """
    assert slugify(input_text) == ""


@pytest.mark.parametrize("input_data", [
    None,
    12345,
    ["hello", "world"],
    {"text": "hello"}
])
def test_slugify_non_string_input_raises_type_error(input_data):
    """
    When `slugify` is provided with an input argument that is not a string type,
    it must safely reject the input by raising a standard `TypeError`.
    """
    with pytest.raises(TypeError):
        slugify(input_data)
