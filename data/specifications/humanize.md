Project: `friendly_formatter`


## High-Level Goal
Implement a Python library named `friendly_formatter` that converts numbers, dates, times, and byte sizes into human-readable strings. The library must handle specific formatting rules, pluralization, relative time calculations, and magnitude conversions exactly as specified below.

## Module Structure
You must create a main module named `friendly_formatter` and a submodule named `friendly_formatter.i18n`.

---

## 1. Number Formatting Functions

### `intcomma(value, ndigits=None)`
**Goal:** Format a number with commas as thousands separators.
*   **Inputs:** `value` (int, float, or string representation of a number), `ndigits` (int, optional).
*   **Rules:**
    *   Insert commas every three digits to the left of the decimal point.
    *   Handle negative numbers correctly (e.g., `-12345` becomes `"-12,345"`).
    *   If `value` is a float, preserve the decimal portion exactly as provided (e.g., `1234.56` becomes `"1,234.56"`).
    *   If `ndigits` is provided, round the number to `ndigits` decimal places before formatting.
    *   If `ndigits=0`, round the number and format it as an integer without any decimal point.

### `ordinal(value)`
**Goal:** Convert an integer to its ordinal string representation.
*   **Inputs:** `value` (int or string).
*   **Rules:**
    *   Attempt to cast the input to an integer. 
    *   **Exception Rule:** If the input cannot be cast to an integer (e.g., `"abc"`, `"12.34"`, `""`), catch the resulting `ValueError` and return the raw input string unmodified.
    *   Determine the suffix based on the last digits of the integer:
        *   If the last two digits are `11`, `12`, or `13`, the suffix is `"th"` (e.g., `11th`, `12th`, `13th`).
        *   Otherwise, if the last digit is `1`, the suffix is `"st"` (e.g., `1st`, `101st`).
        *   Otherwise, if the last digit is `2`, the suffix is `"nd"` (e.g., `2nd`, `1002nd`).
        *   Otherwise, if the last digit is `3`, the suffix is `"rd"` (e.g., `3rd`).
        *   For all other numbers (ending in 0, 4-9), the suffix is `"th"`.
    *   Return the integer as a string concatenated with the suffix.

### `apnumber(value)`
**Goal:** Format numbers according to Associated Press (AP) style.
*   **Inputs:** `value` (int).
*   **Rules:**
    *   If the integer is between `1` and `9` (inclusive), return its lowercase English word equivalent (e.g., `"one"`, `"nine"`).
    *   If the integer is `10` or greater, return it as a string of digits (e.g., `"10"`).

### `intword(value, format="%.1f")`
**Goal:** Convert large integers into human-readable magnitude words.
*   **Inputs:** `value` (int), `format` (string, default `"%.1f"`).
*   **Rules:**
    *   If the absolute value is less than `1000`, return it as a raw string of digits without any words (e.g., `999` -> `"999"`, `-500` -> `"-500"`, `0` -> `"0"`).
    *   If the absolute value is `1000` or greater, convert it to the appropriate magnitude word (`"thousand"`, `"million"`, `"billion"`, `"trillion"`).
    *   Format the numeric portion using the provided `format` string.
    *   Concatenate the formatted number, a single space, and the magnitude word (e.g., `1200000` -> `"1.2 million"`, `12000` -> `"12.0 thousand"`).
    *   Handle negative numbers correctly (e.g., `-1500000` -> `"-1.5 million"`).

---

## 2. File Size Formatting

### `naturalsize(value, binary=False, gnu=False)`
**Goal:** Format a byte count into a human-readable file size string.
*   **Inputs:** `value` (int, float, or string), `binary` (bool, default `False`), `gnu` (bool, default `False`).
*   **Rules:**
    *   Attempt to cast the input to a float. 
    *   **Exception Rule:** If the input cannot be cast to a number (e.g., `"not_a_number"`, `"1.5 MB"`, `""`), strictly raise a `ValueError` or `TypeError`.
    *   Handle negative values by formatting the absolute value and prepending a minus sign (e.g., `"-1.5 MB"`).
    *   **Base and Suffix Logic:**
        *   If `gnu=True`: Use base-1024 math. Suffixes are single letters without spaces: `"K"`, `"M"`, `"G"`.
        *   If `binary=True` (and `gnu=False`): Use base-1024 math. Suffixes are: `"KiB"`, `"MiB"`, `"GiB"`.
        *   If both are `False` (default): Use base-1000 math. Suffixes are: `"kB"`, `"MB"`, `"GB"`.
    *   **Formatting Logic:**
        *   If the absolute value is less than the base (1000 or 1024), return the value formatted as an integer with the suffix `"Bytes"` (e.g., `500` -> `"500 Bytes"`).
        *   Otherwise, divide the value by the base iteratively to find the correct magnitude.
        *   Format the resulting number to 1 decimal place.
        *   Append a space (unless `gnu=True`, which requires no space) followed by the suffix.

---

## 3. Time and Date Formatting

### `precisedelta(value)`
**Goal:** Format a duration into a precise, multi-unit string.
*   **Inputs:** `value` (numeric seconds as int/float, or a `datetime.timedelta` object).
*   **Rules:**
    *   Convert the input into a total duration.
    *   Break the duration down into its constituent units: days, hours, minutes, and seconds.
    *   Format each non-zero unit with correct pluralization (e.g., `"1 hour"`, `"2 days"`).
    *   Join the units with commas, and use `" and "` before the final unit (e.g., `"2 days, 1 hour, 1 minute and 1 second"`).

### `naturaldelta(value)`
**Goal:** Format a duration into a simple, absolute human-readable phrase.
*   **Inputs:** `value` (numeric seconds as int/float, or a `datetime.timedelta` object).
*   **Rules:**
    *   Take the absolute value of the duration (negative durations must be treated as positive).
    *   Return a phrase representing the largest significant unit.
    *   **Specific Phrasing Rules:**
        *   Exactly 1 day (86400 seconds) must return `"a day"`.
        *   Exactly 1 hour (3600 seconds) must return `"an hour"`.
        *   Multiple days must return `"[X] days"` (e.g., `"3 days"`, `"5 days"`).

### `naturaltime(value, when=None, minimum_unit="seconds", months=True)`
**Goal:** Format a datetime into a relative time string (e.g., "10 minutes ago").
*   **Inputs:** `value` (`datetime.datetime` or `datetime.timedelta`), `when` (`datetime.datetime`, optional), `minimum_unit` (string, default `"seconds"`), `months` (bool, default `True`).
*   **Rules:**
    *   If `when` is not provided, default to the current time.
    *   **Exception Rule:** If `value` is a timezone-aware datetime and `when` is a naive datetime (or vice versa), strictly raise a `TypeError`.
    *   Calculate the difference between `value` and `when`.
    *   **Direction Logic:**
        *   If `value` is in the past relative to `when`, format the result as `"[duration] ago"`.
        *   If `value` is in the future relative to `when`, format the result as `"[duration] from now"`.
    *   **Minimum Unit Logic:**
        *   If the absolute difference is less than the `minimum_unit`:
            *   If `minimum_unit` is `"seconds"`, return exactly `"now"`.
            *   If `minimum_unit` is anything else (e.g., `"milliseconds"`), return `"0 [minimum_unit] [direction]"` (e.g., `"0 milliseconds ago"`).
    *   **Months Flag Logic:**
        *   If `months=False`, do not use weeks or months as units. Scale directly from days to years (e.g., 45 days becomes `"45 days ago"`, 400 days uses `"year"`).
        *   If `months=True`, use standard units (minutes, hours, days, months, years).

---

## 4. Internationalization (Submodule: `friendly_formatter.i18n`)

### `activate(locale)`
**Goal:** Activate a specific locale for translations.
*   **Inputs:** `locale` (string, e.g., `"en_US"`, `"xx_XX"`).
*   **Rules:**
    *   Attempt to load the translation file for the given locale.
    *   **Exception Rule:** If the locale is unsupported or the translation file does not exist (e.g., `"xx_XX"`, `"fake_LOCALE"`), strictly raise a `FileNotFoundError`.