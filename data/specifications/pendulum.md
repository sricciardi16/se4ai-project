Project: `temporal_engine`


## 1. High-Level Goal
Implement a robust, immutable date, time, and duration manipulation library named `temporal_engine`. The library must provide precise timezone handling, human-readable formatting, ISO 8601 parsing, and strict calendar arithmetic. All date and time objects must be strictly immutable; any mathematical operation must return a new instance.

## 2. Module Structure & Exceptions
Create the following module structure and specific exception classes:
* **`temporal_engine`**: The root module exposing the public API.
* **`temporal_engine.tz.zoneinfo.exceptions`**: Must contain a custom exception class named `InvalidTimezone` (inheriting from `Exception`).
* **`temporal_engine.tz.local_timezone`**: Must contain a module-level variable named `_local_timezone` used to cache the system's local timezone.

## 3. Core Classes & Interfaces

### 3.1. `DateTime`
Implement a class representing a specific moment in time.
* **Properties**: `year`, `month`, `day`, `hour`, `minute`, `second`, `timezone_name` (string), `offset` (integer, total seconds of the timezone offset).
* **Immutability**: All instances must be immutable. Operations like `add()` and `subtract()` must return entirely new instances with different memory addresses (`id()`).
* **Methods**:
  * `utcoffset()`: Return an object (like `datetime.timedelta`) that has a `total_seconds()` method returning the offset in seconds.
  * `in_timezone(tz_string)`: Return a new `DateTime` shifted to the target IANA timezone or offset. **Rule:** The local clock values (`hour`, `day`, etc.) must shift, but the absolute Unix `timestamp()` must remain exactly the same.
  * `to_datetime_string()`: Return a string formatted as `YYYY-MM-DD HH:mm:ss`.
  * `to_date_string()`: Return a string formatted as `YYYY-MM-DD`.
  * `to_time_string()`: Return a string formatted as `HH:mm:ss`.
  * `to_iso8601_string()`: Return a standard ISO 8601 string. **Rule:** If the timezone is UTC, the string must end with either `Z` or `+00:00`.
  * `timestamp()`: Return the Unix timestamp as a float or integer.
  * `start_of(unit)`: Return a new `DateTime` at the boundary. If `unit="day"`, set `hour`, `minute`, and `second` to `0`.
  * `end_of(unit)`: Return a new `DateTime` at the boundary. If `unit="day"`, set `hour=23`, `minute=59`, and `second=59`.
  * `add(**kwargs)` / `subtract(**kwargs)`: Accept `years`, `months`, `weeks`, `days`, `hours`, `minutes`, `seconds`. Return a new `DateTime`.
  * `diff(other=None)`: Return a `Duration` object representing the exact difference. **Rule:** If `other` is not provided, default to the current time in UTC (`now("UTC")`).
  * `diff_for_humans(other, absolute=False)`: Return a human-readable string of the difference (e.g., "1 month", "1 year"). 
    * **Rule:** If `absolute=False`, append directional words: use "before" if `self` is older than `other`, and "after" if `self` is newer than `other`.
    * **Rule:** If `absolute=True`, omit the directional words entirely.
  * `format(fmt_string)`: Return a formatted string based on custom tokens (see Section 5.3).
* **Operators**: 
  * `DateTime + Duration` must be functionally equivalent to `DateTime.add(...)`.
  * `DateTime - DateTime` must return a `Duration` object.

### 3.2. `Date`
Implement a class representing a date without time.
* **Properties**: `year`, `month`, `day`.
* **Methods**:
  * `weekday()`: Return the day of the week as an integer where Monday is `0` and Sunday is `6`.
  * `isoweekday()`: Return the ISO day of the week where Monday is `1` and Sunday is `7`.
  * `diff(other)`: Return a `Duration` object.
  * `add(**kwargs)`: Return a new `Date` object.

### 3.3. `Duration`
Implement a class representing a span of time.
* **Properties**: `years`, `months`, `days`, `hours`, `minutes`, `seconds`.
  * **CRITICAL RULE for `days`**: The `days` property must return the *normalized total days* of the calendar units. For this calculation, strictly assume **1 year = 365 days** and **1 month = 30 days**. (e.g., 2 years + 3 months + 15 days MUST equal exactly 835 days).
  * **CRITICAL RULE for `seconds`**: The `seconds` property must return the remaining seconds *modulo 86400* (1 day). It must not include the seconds accounted for by the `days` property.
* **Methods**:
  * `total_seconds()`: Return the total duration in seconds, including all days, hours, minutes, and seconds.
  * `in_days()`: Return the exact difference in days as an `int`.
  * `in_words()`: Return a human-readable string of the exact constituent units (e.g., "2 years 3 months 4 days 5 hours"). 
    * **Rule:** Omit any units that are `0`.
    * **Rule:** Properly pluralize units (e.g., "1 year" vs "2 years").

### 3.4. `Period`
Implement a class representing a specific range between two dates.
* **Methods**:
  * `range(unit)`: Return an iterable (e.g., a list or generator) of dates from the start date to the end date. **Rule:** The returned range must be *inclusive* of both the start and end endpoints.

## 4. Public Factory Functions

* **`datetime(year, month, day, hour=0, minute=0, second=0, tz="UTC")`**
  * Return a `DateTime` object.
  * **Rule:** If `tz` is omitted, it must strictly default to `"UTC"`.
  * **Rule:** Raise a `ValueError` if provided with mathematically impossible calendar or clock values (e.g., `hour=25`, `minute=60`, `month=13`, `month=0`, or `day=29` on a non-leap year).

* **`date(year, month, day)`**
  * Return a `Date` object.

* **`now(tz=None)`**
  * Return the current `DateTime`.
  * **Rule:** If `tz` is a valid IANA timezone string, localize the time to that timezone.
  * **Rule:** If `tz` is an empty string `""`, raise a `ValueError`.
  * **Rule:** If `tz` is an invalid timezone string (e.g., "Mars/Phobos"), raise `InvalidTimezone`.
  * **Rule:** If `tz` is `None`, resolve the local system timezone (e.g., via the `TZ` environment variable). 
  * **Rule:** The resolved local timezone must be cached in `temporal_engine.tz.local_timezone._local_timezone`. If this variable is manually set to `None`, the function must re-evaluate the system environment variables.

* **`parse(text, tz=None)`**
  * Parse an ISO 8601 string (date-only or datetime) and return a `DateTime` or `Date`.
  * **Rule:** If the string contains a UTC offset (e.g., `+09:00` or `-04:00`), the resulting object's `timezone_name` must be that exact offset string, and its `offset` property must reflect the offset in total seconds.
  * **Rule:** If the string does *not* contain an offset, default the timezone to `"UTC"`. If a `tz` fallback argument is provided, use the fallback instead.
  * **Rule:** Raise a `ValueError` if the string is empty, malformed, or contains non-existent calendar dates (e.g., "2023-02-30").

* **`duration(**kwargs)`**
  * Return a `Duration` object. Accept `years`, `months`, `days`, `hours`, `minutes`, `seconds`.

* **`period(start, end)`**
  * Return a `Period` object bounded by the `start` and `end` dates.

## 5. Strict Behavioral & Mathematical Rules

### 5.1. Calendar Math Boundaries
When adding or subtracting variable calendar units (months, years), the library must safely resolve boundaries:
* **Leap Years:** Adding 1 year to `Feb 29` must result in `Feb 28` of the following year.
* **Month Boundaries:** Adding 1 month to `Jan 31` must result in `Feb 28` (or `Feb 29` in a leap year).

### 5.2. Reversibility
Adding standard units (days, hours, minutes, seconds) and immediately subtracting those exact same units must return a `DateTime` that is mathematically equivalent to the original moment.

### 5.3. String Formatting Tokens
The `format(fmt_string)` method must parse and replace the following specific tokens:
* `YYYY`: 4-digit year.
* `MM`: 2-digit padded month.
* `DD`: 2-digit padded day.
* `HH`: 2-digit padded hour (24-hour clock).
* `mm`: 2-digit padded minute.
* `ss`: 2-digit padded second.
* `dddd`: Full weekday name (e.g., "Thursday").
* `MMMM`: Full month name (e.g., "February").
* `Do`: Day of the month with an ordinal suffix (e.g., "1st", "2nd", "3rd", "29th").
* **Escaping Rule:** Any characters enclosed in square brackets `[...]` must be rendered literally and must not be evaluated as formatting tokens (e.g., `YYYY [YYYY]` -> `2024 YYYY`).