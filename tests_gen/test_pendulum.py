# 1. Testing Framework & Mocking
import pytest

# 2. The Subject Under Test
import temporal_engine as pendulum
from temporal_engine.tz.zoneinfo.exceptions import InvalidTimezone

# 4. Auxiliary: Standard Library
import os
import time
import sys


def test_parse_iso8601_and_convert_timezone_updates_offset():
    # Parse ISO 8601 string with UTC offset
    dt = pendulum.parse("2020-01-01T12:00:00+00:00")

    # Verify initial UTC offset is 0 seconds
    assert dt.utcoffset().total_seconds() == 0

    # Convert to target timezone
    dt_tokyo = dt.in_timezone("Asia/Tokyo")

    # Verify the offset is updated to 32400 seconds (9 hours)
    assert dt_tokyo.utcoffset().total_seconds() == 32400

    # Verify the local time string is adjusted accordingly
    assert dt_tokyo.to_datetime_string() == "2020-01-01 21:00:00"


def test_datetime_add_and_duration_operator_equivalence():
    base_dt = pendulum.datetime(2021, 3, 15, 10, 30, 0, tz="UTC")

    # Case 1: Adding 2 days, 5 hours, 15 minutes
    added_dt_1 = base_dt.add(days=2, hours=5, minutes=15)
    diff_1 = added_dt_1 - base_dt
    dur_1 = pendulum.duration(days=2, hours=5, minutes=15)

    # Verify operator equivalence and duration matching
    assert base_dt + dur_1 == added_dt_1
    assert diff_1.total_seconds() == dur_1.total_seconds()

    # Case 2: Adding 3 days, 4 hours
    added_dt_2 = base_dt.add(days=3, hours=4)
    diff_2 = added_dt_2 - base_dt
    dur_2 = pendulum.duration(days=3, hours=4)

    # Verify operator equivalence and duration matching
    assert base_dt + dur_2 == added_dt_2
    assert diff_2.total_seconds() == dur_2.total_seconds()


def test_diff_for_humans_exactly_one_month_apart():
    base_dt = pendulum.datetime(2011, 8, 1, tz="UTC")

    # Create a DateTime exactly 1 month apart
    future_dt = base_dt.add(months=1)

    # Calculate human-readable difference
    diff_str = base_dt.diff_for_humans(future_dt)

    # Verify the string contains the word "month"
    assert "month" in diff_str.lower()


def test_parse_date_only_string_preserves_leap_year():
    # Parse a leap year date-only string
    parsed = pendulum.parse("2020-02-29")

    # Verify extracted components
    assert parsed.year == 2020
    assert parsed.month == 2
    assert parsed.day == 29

    # Verify formatting back to date string matches original input
    assert parsed.to_date_string() == "2020-02-29"


def test_datetime_to_iso8601_string_includes_utc_designator():
    # Create base UTC DateTime
    dt = pendulum.datetime(2020, 1, 1, 12, 0, 0, tz="UTC")

    # Convert to ISO 8601 string
    iso_str = dt.to_iso8601_string()

    # Verify correct date and time components
    assert iso_str.startswith("2020-01-01T12:00:00")

    # Verify it ends with a valid UTC timezone designator
    assert iso_str.endswith("Z") or iso_str.endswith("+00:00")

def test_format_datetime_with_custom_tokens():
    dt = pendulum.datetime(2021, 12, 31, 23, 59, 58, tz="UTC")
    formatted = dt.format("YYYY/MM/DD HH:mm:ss")

    assert formatted == "2021/12/31 23:59:58"

def test_start_of_and_end_of_day_boundaries():
    dt = pendulum.datetime(2020, 5, 20, 13, 14, 15, tz="UTC")

    start_dt = dt.start_of("day")
    assert start_dt.year == 2020
    assert start_dt.month == 5
    assert start_dt.day == 20
    assert start_dt.hour == 0
    assert start_dt.minute == 0
    assert start_dt.second == 0

    end_dt = dt.end_of("day")
    assert end_dt.year == 2020
    assert end_dt.month == 5
    assert end_dt.day == 20
    assert end_dt.hour == 23
    assert end_dt.minute == 59
    assert end_dt.second == 59

def test_date_weekday_and_isoweekday_indices():
    # 2020-01-01 is a Wednesday
    d = pendulum.date(2020, 1, 1)

    assert d.weekday() == 2
    assert d.isoweekday() == 3

def test_duration_total_seconds_and_component_attributes():
    dur = pendulum.duration(days=1, hours=2, minutes=3, seconds=4)

    assert dur.total_seconds() == 93784
    assert dur.days == 1
    assert dur.hours == 2
    assert dur.minutes == 3
    # timedelta.seconds returns total seconds modulo 86400 (1 day)
    # 2 hours (7200) + 3 minutes (180) + 4 seconds = 7384
    assert dur.seconds == 7384

def test_period_range_days_includes_endpoints():
    # In Pendulum 2.1, period() is the idiomatic standard over the legacy interval()
    start = pendulum.date(2020, 1, 1)
    end = pendulum.date(2020, 1, 5)

    period = pendulum.period(start, end)
    days_range = list(period.range("days"))

    assert len(days_range) == 5
    assert days_range[0] == start
    assert days_range[-1] == end

def test_in_timezone_preserves_unix_timestamp():
    # Instantiate UTC date 2020-06-01 00:00:00 UTC
    dt_utc = pendulum.datetime(2020, 6, 1, 0, 0, 0, tz="UTC")

    # Convert to target timezone "America/New_York"
    dt_ny = dt_utc.in_timezone("America/New_York")

    # Verify the timestamp remains unchanged
    assert dt_utc.timestamp() == dt_ny.timestamp()

    # Verify the local date shifts backwards to 2020-05-31
    assert dt_ny.year == 2020
    assert dt_ny.month == 5
    assert dt_ny.day == 31
    assert dt_ny.hour == 20  # 8:00 PM EDT

def test_date_diff_in_days_returns_exact_integer():
    # Instantiate dates 2020-01-01 and 2020-01-11
    d1 = pendulum.date(2020, 1, 1)
    d2 = pendulum.date(2020, 1, 11)

    # Calculate difference
    diff = d1.diff(d2)

    # Expecting exactly 10 days as an integer
    days_diff = diff.in_days()
    assert days_diff == 10
    assert isinstance(days_diff, int)

def test_add_months_crosses_year_boundary_correctly():
    # Base date 2019-12-15
    base_date = pendulum.date(2019, 12, 15)

    # Adding 2 months
    new_date = base_date.add(months=2)

    # Expecting 2020-02-15
    assert new_date.year == 2020
    assert new_date.month == 2
    assert new_date.day == 15

def test_now_formats_to_custom_and_iso8601_strings():
    # Instantiate current time
    now = pendulum.now()

    # Format into custom string using specific token string
    custom_format = now.format("YYYY-MM-DD HH:mm:ss")

    # Serialize into standard ISO 8601 string
    iso_format = now.to_iso8601_string()

    # Validate custom format structure
    assert len(custom_format) == 19
    assert custom_format[4] == "-"
    assert custom_format[7] == "-"
    assert custom_format[10] == " "
    assert custom_format[13] == ":"
    assert custom_format[16] == ":"

    # Validate ISO 8601 format structure
    assert "T" in iso_format
    assert iso_format.startswith(str(now.year))

def test_timezone_aware_datetime_arithmetic_and_conversion():
    # Instantiate with specific IANA timezone strings
    dt_paris = pendulum.now("Europe/Paris")
    dt_tokyo = pendulum.now("Asia/Tokyo")

    # Arithmetic: adding days=30, hours=5, minutes=30
    dt_paris_modified = dt_paris.add(days=30, hours=5, minutes=30)

    # Arithmetic: subtracting weeks=2
    dt_tokyo_modified = dt_tokyo.subtract(weeks=2)

    # Convert to other timezones
    dt_ny = dt_paris_modified.in_timezone("America/New_York")
    dt_utc = dt_tokyo_modified.in_timezone("UTC")

    # Verify absolute point in time remains the same during conversion
    assert dt_paris_modified.timestamp() == dt_ny.timestamp()
    assert dt_tokyo_modified.timestamp() == dt_utc.timestamp()

    # Verify timezones are correctly set
    assert dt_ny.timezone_name == "America/New_York"
    assert dt_utc.timezone_name == "UTC"

def test_parse_invalid_calendar_date_raises_exception():
    """
    When the parser is provided with a string representing a non-existent calendar date,
    it should fail safely rather than silently rolling over.
    """
    with pytest.raises(ValueError):
        pendulum.parse("2023-02-30")

def test_now_without_timezone_returns_local_system_time(monkeypatch):
    
    # Configure the test environment with a specific local timezone before execution
    monkeypatch.setenv("TZ", "America/Chicago")
    if hasattr(time, "tzset"):
        time.tzset()

    # Clear Pendulum's local timezone cache so it is forced to re-evaluate the TZ env var.
    # Because pendulum.tz.local_timezone is exposed as a function, we must access the 
    # underlying module directly via sys.modules to patch its internal cache.
    local_tz_module = sys.modules.get("temporal_engine.tz.local_timezone")
    if local_tz_module and hasattr(local_tz_module, "_local_timezone"):
        monkeypatch.setattr(local_tz_module, "_local_timezone", None)

    dt = pendulum.now()
    assert dt.timezone_name == "America/Chicago"

@pytest.mark.parametrize("tz_name", [
    "Asia/Tokyo",
    "Europe/Paris",
    "Australia/Sydney"
])
def test_now_with_valid_timezone_returns_localized_time(tz_name):
    """
    When pendulum.now() is invoked with a valid IANA timezone string, it must return
    a DateTime object explicitly localized to that exact timezone.
    """
    dt = pendulum.now(tz_name)
    assert dt.timezone_name == tz_name

@pytest.mark.parametrize("invalid_tz", [
    "America/Not_A_City",
    "Mars/Phobos",
    ""
])
def test_invalid_timezone_identifier_raises_exception(invalid_tz):
    """
    Pendulum 2.1 raises InvalidTimezone for invalid names, and ValueError for empty strings.
    """
    with pytest.raises((ValueError, InvalidTimezone)):
        pendulum.now(invalid_tz)



def test_datetime_with_calendar_values_defaults_to_utc():
    """
    When pendulum.datetime() is invoked with specific year, month, and day integers
    but no explicit timezone argument, it must return a DateTime object matching those
    exact calendar values, and its timezone must default strictly to UTC.
    """
    dt = pendulum.datetime(year=2024, month=2, day=29, hour=15, minute=30, second=45)

    assert dt.year == 2024
    assert dt.month == 2
    assert dt.day == 29
    assert dt.hour == 15
    assert dt.minute == 30
    assert dt.second == 45
    assert dt.timezone_name == "UTC"

def test_datetime_with_impossible_calendar_values_raises_value_error():
    # Out-of-bounds clock values
    with pytest.raises(ValueError):
        pendulum.datetime(2023, 1, 1, hour=25)

    with pytest.raises(ValueError):
        pendulum.datetime(2023, 1, 1, minute=60)

    # Out-of-bounds months
    with pytest.raises(ValueError):
        pendulum.datetime(2023, 13, 1)

    with pytest.raises(ValueError):
        pendulum.datetime(2023, 0, 1)

    # Strictly invalid leap-year day
    with pytest.raises(ValueError):
        pendulum.datetime(2023, 2, 29)


def test_parse_standard_iso8601_string_returns_accurate_datetime_object():
    dt = pendulum.parse("2023-10-31T23:59:59")

    assert dt.year == 2023
    assert dt.month == 10
    assert dt.day == 31
    assert dt.hour == 23
    assert dt.minute == 59
    assert dt.second == 59


def test_parse_string_with_offset_creates_fixed_timezone():
    # Positive offset, Japan Standard Time
    dt_positive = pendulum.parse("2024-01-15T08:30:00+09:00")
    assert dt_positive.timezone_name == "+09:00"
    assert dt_positive.offset == 32400  # 9 hours * 3600 seconds

    # Negative offset, Eastern Daylight Time
    dt_negative = pendulum.parse("2024-07-04T12:00:00-04:00")
    assert dt_negative.timezone_name == "-04:00"
    assert dt_negative.offset == -14400  # -4 hours * 3600 seconds


def test_parse_string_without_offset_defaults_to_utc_or_provided_fallback():
    input_string = "2023-05-15T14:00:00"

    # Default behavior (UTC)
    dt_default = pendulum.parse(input_string)
    assert dt_default.timezone_name == "UTC"

    # Explicit fallback argument
    dt_fallback = pendulum.parse(input_string, tz="Europe/Berlin")
    assert dt_fallback.timezone_name == "Europe/Berlin"


def test_parse_invalid_or_empty_string_raises_value_error():
    # Empty string
    with pytest.raises(ValueError):
        pendulum.parse("")

    # Completely malformed gibberish
    with pytest.raises(ValueError):
        pendulum.parse("not-a-date")

    # Mathematically impossible calendar and clock values
    with pytest.raises(ValueError):
        pendulum.parse("2023-13-45T25:99:99")

def test_datetime_math_operations_return_new_instance_and_preserve_original_state():
    original = pendulum.datetime(2020, 2, 28)
    new_instance = original.add(days=2)

    assert new_instance.to_date_string() == "2020-03-01"
    assert original.to_date_string() == "2020-02-28"
    assert id(original) != id(new_instance)

def test_add_and_subtract_standard_units_calculates_correct_moment():
    base_date = pendulum.datetime(2023, 1, 1, 12, 0, 0, tz="UTC")

    modified_date = base_date.add(days=5, hours=12, minutes=30, seconds=45)
    final_date = modified_date.subtract(days=5, hours=12, minutes=30, seconds=45)

    assert final_date == base_date

def test_add_variable_calendar_units_resolves_leap_year_and_month_boundaries():
    # Leap Year Boundary
    base_leap_year = pendulum.datetime(2020, 2, 29)
    result_leap_year = base_leap_year.add(years=1)
    assert result_leap_year.to_date_string() == "2021-02-28"

    # Standard Month Boundary
    base_standard_month = pendulum.datetime(2023, 1, 31)
    result_standard_month = base_standard_month.add(months=1)
    assert result_standard_month.to_date_string() == "2023-02-28"

    # Leap Year Month Boundary
    base_leap_month = pendulum.datetime(2024, 1, 31)
    result_leap_month = base_leap_month.add(months=1)
    assert result_leap_month.to_date_string() == "2024-02-29"

def test_in_timezone_shifts_local_clock_while_maintaining_absolute_time():
    base_date = pendulum.datetime(2023, 6, 15, 12, 0, 0, tz="UTC")
    target_date = base_date.in_timezone("America/New_York")

    assert target_date.to_time_string() == "08:00:00"
    assert target_date.timestamp() == 1686830400.0
    assert base_date.timestamp() == 1686830400.0

def test_duration_instantiation_stores_variable_and_fixed_units_accurately():
    duration = pendulum.duration(years=2, months=3, days=15, hours=10)

    assert duration.years == 2
    assert duration.months == 3
    # timedelta.days returns the total normalized days (2 years + 3 months + 15 days = 835)
    assert duration.days == 835
    assert duration.hours == 10

def test_diff_between_two_datetimes_generates_precise_duration():
    start_date = pendulum.datetime(2020, 1, 1, 12, 0, 0, tz="UTC")
    end_date = pendulum.datetime(2022, 4, 15, 14, 30, 0, tz="UTC")

    duration = start_date.diff(end_date)

    assert duration.years == 2
    assert duration.months == 3
    # timedelta.days returns the total normalized days in the period
    assert duration.days == 835
    assert duration.hours == 2
    assert duration.minutes == 30

def test_diff_without_target_moment_defaults_to_current_time():
    anchor_date = pendulum.datetime(2000, 1, 1, tz="UTC")

    now = pendulum.now("UTC")
    duration = anchor_date.diff()

    expected_duration = anchor_date.diff(now)

    # Verify the difference is within a strict execution tolerance delta (< 1 second)
    assert abs(duration.total_seconds() - expected_duration.total_seconds()) < 1.0

def test_diff_for_humans_outputs_directional_strings_for_explicit_dates():
    dt1 = pendulum.datetime(2023, 1, 1)
    dt2 = pendulum.datetime(2023, 1, 2)

    # Past comparison (Explicit dates use 'before' instead of 'ago')
    assert dt1.diff_for_humans(dt2) == "1 day before"

    # Future comparison (Explicit dates use 'after' instead of 'in')
    assert dt2.diff_for_humans(dt1) == "1 day after"

    # Complex boundary
    dt3 = pendulum.datetime(2023, 1, 1)
    dt4 = pendulum.datetime(2024, 2, 1)
    assert dt3.diff_for_humans(dt4) == "1 year before"

def test_diff_for_humans_with_absolute_flag_removes_directional_words():
    dt1 = pendulum.datetime(2023, 1, 1)
    dt2 = pendulum.datetime(2023, 2, 1)

    assert dt1.diff_for_humans(dt2, absolute=True) == "1 month"
    assert dt2.diff_for_humans(dt1, absolute=True) == "1 month"

def test_duration_in_words_outputs_exact_constituent_units():
    # Complex Duration
    complex_duration = pendulum.duration(years=2, months=3, days=4, hours=5, seconds=0)
    assert complex_duration.in_words() == "2 years 3 months 4 days 5 hours"

    # Edge Case (Singular vs Plural)
    singular_duration = pendulum.duration(years=1, days=1)
    assert singular_duration.in_words() == "1 year 1 day"

def test_format_translates_moment_using_custom_token_pattern():
    # Create the specific instance (Leap year day, single-digit minute/second, 24-hour time)
    dt = pendulum.datetime(2024, 2, 29, 14, 5, 9)

    # Test standard formatting with Pendulum-specific tokens
    format_string = "dddd, MMMM Do YYYY, HH:mm:ss"
    expected_output = "Thursday, February 29th 2024, 14:05:09"
    assert dt.format(format_string) == expected_output

    # Test edge case (Escaped characters using square brackets)
    edge_format_string = "YYYY [YYYY]"
    edge_expected_output = "2024 YYYY"
    assert dt.format(edge_format_string) == edge_expected_output
