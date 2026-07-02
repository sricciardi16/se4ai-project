Project: `string_normalizer`


## 1. High-Level Goal
Implement a robust, highly configurable Python library named `string_normalizer` that converts arbitrary text into clean, normalized, URL-friendly strings (slugs). The library must handle multilingual text, HTML entity decoding, custom string replacements, stopword removal, and precise truncation rules without crashing or leaking memory under heavy sequential loads.

## 2. Module Structure
* **Module Name:** `string_normalizer`
* **Public API:** The module must expose a single public function named `slugify`.
* **Aliases:** The `slugify` function must be importable directly from the module (e.g., `from string_normalizer import slugify`).

## 3. Function Signature & Types
Implement the `slugify` function with the following exact signature, argument names, and default values:

```python
def slugify(
    text: str,
    allow_unicode: bool = False,
    max_length: int = None,
    word_boundary: bool = False,
    separator: str = "-",
    regex_pattern: str = None,
    stopwords: list[str] = None,
    lowercase: bool = True,
    replacements: list[list[str, str]] = None,
    entities: bool = False,
    decimal: bool = False,
    hexadecimal: bool = False
) -> str:
    pass
```

## 4. Strict Behaviors & Rules

To guarantee a 100% test pass rate, the function must execute its logic in a specific order and adhere to the following strict rules:

### 4.1. Input Validation
* **Type Checking:** Immediately check the type of the `text` argument. If `text` is not a string (e.g., `None`, `int`, `list`, `dict`), you **must** raise a standard `TypeError`.

### 4.2. Decoding HTML Entities
If any of the entity decoding flags are set to `True`, decode them into their standard string representations *before* any other text processing occurs:
* If `entities=True`: Decode standard HTML entities (e.g., `&eacute;` becomes `é`).
* If `decimal=True`: Decode decimal HTML entities (e.g., `&#233;` becomes `é`).
* If `hexadecimal=True`: Decode hexadecimal HTML entities (e.g., `&#xE9;` becomes `é`).

### 4.3. Custom Replacements
* If the `replacements` argument is provided (an iterable of `[search_string, replacement_string]` pairs), execute these exact string substitutions on the text.
* **Rule:** This must happen *before* any special characters are stripped or transliterated. (e.g., replacing `C#` with `Csharp` ensures the `#` is not prematurely deleted by later punctuation removal).

### 4.4. Casing
* If `lowercase=True` (the default), convert the entire string to lowercase.
* If `lowercase=False`, strictly preserve the original casing of the string throughout the rest of the processing.

### 4.5. Stopword Removal
* If the `stopwords` argument is provided (an iterable of strings), remove those exact words from the text.
* **Rule:** You must only remove **whole words**. Do not remove partial matches (e.g., if the stopword is "the", remove "the" but do not alter "theater" or "theme").
* **Rule:** Stopword removal must be case-insensitive, successfully removing capitalized stopwords even if `lowercase=False`.

### 4.6. Transliteration & Unicode Handling
* **Default Behavior (`allow_unicode=False`):** You must transliterate all non-ASCII characters into their closest ASCII equivalents. This includes converting Latin extensions (e.g., `München` -> `Munchen`, `résumé` -> `resume`) and transliterating Cyrillic, Logograms, and other alphabets into ASCII characters.
* **Override (`allow_unicode=True`):** Bypass ASCII transliteration entirely. Preserve non-ASCII characters (like Cyrillic letters and Logograms) in the final output.

### 4.7. Character Stripping & Separator Injection
* **Regex Pattern:** Use a regular expression to identify characters that should be replaced by the `separator`. 
    * If `regex_pattern` is provided, use it.
    * If `regex_pattern` is `None`, default to a pattern that matches all non-alphanumeric characters (excluding the separator itself).
* **Separator:** Replace all matched characters, spaces, and punctuation with the string provided in the `separator` argument. The separator can be an empty string (`""`).
* **Collapsing:** If multiple replaceable characters or spaces appear consecutively, collapse them so that only a **single** separator is inserted (e.g., `Hello!!! World` becomes `hello-world`, not `hello---world`).
* **Trimming:** Always strip leading and trailing separators from the resulting string.

### 4.8. Truncation (`max_length` and `word_boundary`)
If `max_length` is provided (an integer):
* **Basic Truncation:** Truncate the string so its total length does not exceed `max_length`.
* **Word Boundary (`word_boundary=True`):** Instead of blindly cutting the string mid-word, truncate the string at the nearest whole word boundary that fits within the `max_length`. 
* **Post-Truncation Trimming:** After truncation, you must ensure no trailing separators remain at the end of the string (e.g., if truncating leaves `alpha-beta-`, it must be trimmed to `alpha-beta`).

### 4.9. Edge Cases & Stability
* **Empty Results:** If the input is an empty string, or if the string consists entirely of punctuation/spaces that get stripped away, the function must return an exact empty string `""`.
* **Unhandled Exceptions:** The function must safely process strings containing arbitrary special characters (e.g., `!@#$%^&*()_+[]{}|;:,.<>?/\`) without raising unhandled exceptions.
* **Performance/Stability:** The function must be stateless and stable enough to handle thousands of sequential calls (e.g., batch processing 4000+ multilingual strings) without memory leaks or crashes.
* **Partial Application:** The function must be fully compatible with standard library tools like `functools.partial` to allow developers to create pre-configured instances of the function.