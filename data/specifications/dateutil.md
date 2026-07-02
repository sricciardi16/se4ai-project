Project: `datetime_kit`


## 1. High-Level Goal
Implement a Python library named `datetime_kit` that provides advanced date and time parsing, calendar-aware datetime arithmetic, recurrence rule generation, and timezone manipulation. The library must strictly adhere to the module structures, class signatures, and logical behaviors defined below to pass an exhaustive, unseen test suite.

## 2. Module Structure
You must create a root package named `datetime_kit` with the following submodules:
*   `datetime_kit.parser`
*   `datetime_kit.relativedelta`
*   `datetime_kit.rrule`
*   `datetime_kit.tz`

You must expose specific functions at the root level in `datetime_kit/__init__.py` as detailed below.

---

## 3. Module: `datetime_kit.parser`

### Exceptions
*   **`ParserError`**: Implement a custom exception class named `ParserError` (inheriting from `ValueError` or `Exception`).

### Functions
*   **`parse(timestr, dayfirst=False, yearfirst=False, default=None, fuzzy=False, tzinfos=None)`**
    *   **Routing:** This function must be defined in `datetime_kit.parser` and also imported into the root `datetime_kit` namespace so it can be called as `datetime_kit.parse()`.
    *   **Input Validation:** 
        *   If `timestr` is not a string (e.g., `None`, `int`, `bool`, `list`, `dict`), you MUST raise a `TypeError`.
        *   If `timestr` is a string but contains no recognizable date/time information (e.g., `"Hello World"`, `"1234567890"`, `""`, `"this is not a date at all !!!"`), you MUST raise a `ParserError`.
    *   **Parsing Rules:**
        *   **Standard Formats:** It must correctly parse ISO-8601 strings (e.g., `"2020-05-17T13:45:00Z"`) and natural language strings (e.g., `"May 17, 2020 1:45 pm UTC"`, `"Jan 2 2023 03:04:05"`) into `datetime.datetime` objects.
        *   **Date-Only Strings:** If the string contains only a date (e.g., `"2020-05-17"`), default the time components to midnight (`00:00:00`).
        *   **Timezones:** If the string contains a timezone offset (e.g., `+09:00` or `Z`), the returned `datetime` must be timezone-aware.
    *   **Keyword Arguments Logic:**
        *   `dayfirst` (bool): If `True`, ambiguous dates (like `"01/02/2020"`) must be parsed with the first number as the day (Feb 1st). If `False`, parse it as the month (Jan 2nd).
        *   `yearfirst` (bool): If `True` and `dayfirst=False`, a string like `"01-02-03"` must be parsed as Year-Month-Day (2001-02-03). If `dayfirst=True` and `yearfirst=False`, it must be parsed as Year-Month-Day but with day and month swapped (2003-02-01).
        *   `default` (`datetime`): If provided, any missing components in the parsed string (year, month, day, hour, minute, second) must be filled using the exact values from this `default` datetime object.
        *   `fuzzy` (bool): If `True`, the parser must ignore unrecognized extraneous text surrounding the date (e.g., `"Noise before 2020-12-31 noise after"` must successfully parse to `2020-12-31`).
        *   `tzinfos` (dict): A dictionary mapping timezone string abbreviations to `tzinfo` objects (e.g., `{"PST": tzoffset("PST", -28800)}`). If provided, the parser must use this mapping to resolve abbreviations in the string into the corresponding timezone-aware `datetime`.

---

## 4. Module: `datetime_kit.relativedelta`

### Constants
*   Implement weekday constants: `MO`, `TU`, `WE`, `TH`, `FR`, `SA`, `SU`.
*   These constants must be callable/instantiable with an integer argument to represent a positional offset (e.g., `MO(+1)` means the *next* Monday, `FR(-1)` means the *previous* Friday).

### Class: `relativedelta`
*   **Signature:** `relativedelta(dt1=None, dt2=None, years=0, months=0, days=0, year=None, month=None, day=None, hour=None, weekday=None)` *(Note: Support all standard datetime components, but these are the strictly tested ones).*
*   **Behavior 1: Difference Calculation**
    *   If instantiated with two date/datetime objects (`dt1`, `dt2`), it must calculate the calendar difference (`dt1 - dt2`).
    *   The resulting object must expose `.years`, `.months`, and `.days` attributes representing the exact calendar difference.
*   **Behavior 2: Plural Arguments (Relative Math)**
    *   Arguments ending in 's' (`years`, `months`, `days`) represent relative additions/subtractions.
    *   **Leap Year Logic:** Adding 1 month to Jan 31st must yield Feb 29th in a leap year, and Feb 28th in a non-leap year. Adding 1 year to Feb 29th must yield Feb 28th of the following year.
*   **Behavior 3: Singular Arguments (Absolute Replacement)**
    *   Arguments without an 's' (`year`, `month`, `day`, `hour`) represent absolute replacements.
    *   When added to a datetime, they replace that specific component (e.g., `month=1, day=5, hour=9` forces the resulting datetime to be Jan 5th at 09:00).
*   **Behavior 4: Weekday Anchoring & Order of Operations**
    *   The `weekday` argument accepts one of the weekday constants (e.g., `FR(-1)`).
    *   When adding a `relativedelta` to a datetime, operations MUST occur in this strict logical order:
        1. Apply relative math (months, years).
        2. Apply absolute replacements (e.g., `day=31`). *Note: If `day=31` is applied to a month with fewer days, it must safely truncate to the actual last day of that month.*
        3. Apply the weekday anchor (e.g., from that new date, step backward to find the previous Friday).

---

## 5. Module: `datetime_kit.rrule`

### Constants
*   Implement frequency constants: `DAILY`, `WEEKLY`, `MONTHLY`.
*   Implement weekday constants for rules: `MO`, `TU`, `WE`, `TH`, `FR`, `SA`, `SU`. (These can be the same underlying objects as in `relativedelta`, but must be importable from `datetime_kit.rrule`).

### Class: `rrule`
*   **Signature:** `rrule(freq, dtstart=None, interval=1, count=None, until=None, byweekday=None, bymonthday=None)`
*   **Core Behavior:** 
    *   Must implement the `Iterable` protocol (`__iter__`).
    *   Yields a sequential series of `datetime` objects matching the recurrence pattern.
    *   The time components (hour, minute, second) of the yielded datetimes MUST exactly match the time components of `dtstart`.
    *   The first yielded value is `dtstart` (assuming +0 days), meaning the *nth* iteration is exactly `n-1` intervals away. (e.g., The 5000th iteration of a `DAILY` rule starting `2000-01-01` must be exactly `2013-09-08`, which is +4999 days).
*   **Keyword Arguments Logic:**
    *   `freq`: The base frequency (e.g., `DAILY`, `MONTHLY`).
    *   `interval`: The step size (e.g., `interval=2` with `DAILY` means every other day).
    *   `count`: The maximum number of occurrences to yield.
    *   `until`: A `datetime` representing the inclusive upper bound of the schedule.
    *   `byweekday`: A tuple/list of weekday constants (e.g., `(MO, WE, FR)`). Filters occurrences to only these days. Can also accept positional offsets (e.g., `WE(3)` for the 3rd Wednesday of the month).
    *   `bymonthday`: An integer. Filters occurrences to this specific day of the month.
*   **Method: `between(after, before, inc=False)`**
    *   Returns a `list` of `datetime` occurrences that fall between the `after` and `before` datetimes.
    *   If `inc=False`, the boundaries are exclusive.
    *   If `inc=True`, the boundaries are inclusive.
*   **Method: `count()`**
    *   Returns the exact integer total of occurrences in the rule.
    *   Must respect `until` boundaries (including leap years).
    *   If `dtstart` is strictly greater than `until`, it must return `0`.

---

## 6. Module: `datetime_kit.tz`

### Constants
*   **`UTC`**: A constant representing the UTC timezone.

### Classes & Functions
*   **`tzutc()`**
    *   A class inheriting from `datetime.tzinfo` that represents the UTC timezone. `UTC` should be an instance of this.
*   **`tzoffset(name, offset)`**
    *   A class inheriting from `datetime.tzinfo`.
    *   `name`: A string representing the timezone abbreviation (e.g., `"UTC-5"`).
    *   `offset`: An integer representing the offset in seconds from UTC (e.g., `-18000`).
    *   Must be fully compatible with the standard library's `datetime.astimezone()` method.
*   **`gettz(name)`**
    *   A function that takes a timezone string (e.g., `"America/New_York"`, `"UTC"`).
    *   If the string is a valid IANA timezone, it returns a valid `datetime.tzinfo` object.
    *   If the string is invalid or unrecognizable (e.g., `"America/Not_A_City"`), it MUST return `None`.