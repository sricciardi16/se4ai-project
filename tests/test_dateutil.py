# 1. Testing Framework & Mocking
import pytest

# 2. The Subject Under Test
import dateutil.parser
from dateutil import tz
from dateutil.parser import ParserError, parse
from dateutil.relativedelta import FR, MO as RelMO, TU, relativedelta
from dateutil.rrule import DAILY, FR as RrFR, MO as RrMO, MONTHLY, WE, WE as RrWE, WEEKLY, rrule
from dateutil.tz import UTC, gettz, tzoffset, tzutc

# 4. Auxiliary: Standard Library
from collections.abc import Iterable
import datetime
from datetime import date, datetime, tzinfo


def test_parse_iso_and_natural_language_strings():
    # ISO-8601 format
    iso_dt = parse("2020-05-17T13:45:00Z")
    assert iso_dt == datetime(2020, 5, 17, 13, 45, tzinfo=tzutc())

    # Natural language format
    natural_dt = parse("May 17, 2020 1:45 pm UTC")
    assert natural_dt == datetime(2020, 5, 17, 13, 45, tzinfo=tzutc())

    # Date-only format (defaults time to midnight)
    date_only_dt = parse("2020-05-17")
    assert date_only_dt == datetime(2020, 5, 17, 0, 0)

def test_parse_invalid_string_with_exclamations_raises_parser_error():
    with pytest.raises(ParserError):
        parse("this is not a date at all")

def test_parse_ambiguous_date_with_dayfirst():
    # dayfirst=True treats the first '01' as the day (Feb 1st)
    dt_dayfirst = parse("01/02/2020", dayfirst=True)
    assert dt_dayfirst == datetime(2020, 2, 1, 0, 0)

    # dayfirst=False treats the first '01' as the month (Jan 2nd)
    dt_monthfirst = parse("01/02/2020", dayfirst=False)
    assert dt_monthfirst == datetime(2020, 1, 2, 0, 0)

def test_parse_partial_date_with_default_datetime():
    default_dt = datetime(2020, 1, 1, 12, 34, 56)

    # The year and time components should be filled from default_dt
    dt = parse("March 5", default=default_dt)
    assert dt == datetime(2020, 3, 5, 12, 34, 56)

def test_parse_fuzzy_extracts_date_from_noise():
    # fuzzy=True ignores the unrecognized text surrounding the date
    dt = parse("Noise before 2020-12-31 noise after", fuzzy=True)
    assert dt == datetime(2020, 12, 31, 0, 0)

def test_parse_timezone_abbreviation_with_tzinfos_mapping():
    # Map the "PST" abbreviation to a specific tzoffset (-8 hours)
    pst_offset = tz.tzoffset("PST", -8 * 3600)
    tzinfos_mapping = {"PST": pst_offset}

    # Parse the string using the tzinfos mapping
    dt_str = "2020-01-01 10:00 PST"
    parsed_dt = parse(dt_str, tzinfos=tzinfos_mapping)

    # Verify the resulting datetime is timezone-aware and correctly offset
    expected_dt = datetime(2020, 1, 1, 10, 0, tzinfo=pst_offset)
    assert parsed_dt == expected_dt
    assert parsed_dt.tzinfo.utcoffset(parsed_dt).total_seconds() == -28800


def test_relativedelta_addition_and_difference_calculation():
    # Test calendar-aware addition
    start_date = date(2020, 1, 31)
    added_date = start_date + relativedelta(months=+1)
    assert added_date == date(2020, 2, 29)

    # Test difference calculation between two dates
    end_date = date(2021, 3, 15)
    diff_start_date = date(2020, 1, 10)
    diff = relativedelta(end_date, diff_start_date)

    assert diff.years == 1
    assert diff.months == 2
    assert diff.days == 5


def test_relativedelta_adds_year_to_leap_day():
    leap_day = date(2020, 2, 29)

    # Adding exactly one year to a leap day should roll back to Feb 28th in a non-leap year
    next_year_date = leap_day + relativedelta(years=+1)

    assert next_year_date == date(2021, 2, 28)


def test_relativedelta_advances_to_specific_weekday():
    # 2020-01-01 is a Wednesday
    start_date = date(2020, 1, 1)

    # Advance to the next Monday using the weekday constant with an offset
    next_monday = start_date + relativedelta(weekday=RelMO(+1))

    assert next_monday == date(2020, 1, 6)


def test_rrule_weekly_frequency_with_byweekday():
    # 2020-01-01 is a Wednesday
    start_dt = datetime(2020, 1, 1, 10, 0)

    # Generate a sequence occurring only on Mondays, Wednesdays, and Fridays
    rule = rrule(
        freq=WEEKLY,
        byweekday=(RrMO, RrWE, RrFR),
        count=4,
        dtstart=start_dt
    )

    occurrences = list(rule)

    assert len(occurrences) == 4
    assert occurrences[0] == datetime(2020, 1, 1, 10, 0)  # Wednesday
    assert occurrences[1] == datetime(2020, 1, 3, 10, 0)  # Friday
    assert occurrences[2] == datetime(2020, 1, 6, 10, 0)  # Monday
    assert occurrences[3] == datetime(2020, 1, 8, 10, 0)  # Wednesday

def test_rrule_daily_frequency_with_interval_and_count():
    dtstart = datetime(2023, 1, 1)
    rule = rrule(freq=DAILY, interval=2, count=4, dtstart=dtstart)
    occurrences = list(rule)

    assert len(occurrences) == 4
    assert occurrences[0] == datetime(2023, 1, 1)
    assert occurrences[1] == datetime(2023, 1, 3)
    assert occurrences[2] == datetime(2023, 1, 5)
    assert occurrences[3] == datetime(2023, 1, 7)

def test_rrule_monthly_frequency_with_bymonthday():
    # Using a specific time to verify time preservation
    dtstart = datetime(2023, 1, 1, 10, 30, 0)
    rule = rrule(freq=MONTHLY, bymonthday=15, count=3, dtstart=dtstart)
    occurrences = list(rule)

    assert len(occurrences) == 3
    assert occurrences[0] == datetime(2023, 1, 15, 10, 30, 0)
    assert occurrences[1] == datetime(2023, 2, 15, 10, 30, 0)
    assert occurrences[2] == datetime(2023, 3, 15, 10, 30, 0)

def test_tzoffset_conversion_with_astimezone():
    # Create explicit tzoffset objects for UTC-5 and UTC+0
    tz_minus_5 = tzoffset("UTC-5", -5 * 3600)
    tz_plus_0 = tzoffset("UTC+0", 0)

    # Attach UTC-5 to a naive datetime
    dt_local = datetime(2023, 6, 1, 12, 0, 0, tzinfo=tz_minus_5)

    # Convert to UTC+0 using standard astimezone()
    dt_utc = dt_local.astimezone(tz_plus_0)

    assert dt_utc.year == 2023
    assert dt_utc.month == 6
    assert dt_utc.day == 1
    assert dt_utc.hour == 17
    assert dt_utc.minute == 0
    assert dt_utc.tzinfo == tz_plus_0

def test_parse_explicit_timezone_offset_and_convert_to_utc():
    dt_str = "2020-01-01T00:00:00+09:00"
    dt_parsed = parse(dt_str)

    # Verify the parsed datetime is timezone-aware
    assert dt_parsed.tzinfo is not None

    # Convert to UTC
    dt_utc = dt_parsed.astimezone(UTC)

    # Verify the UTC conversion shifts the hour backward correctly to 15:00 the previous day
    assert dt_utc.year == 2019
    assert dt_utc.month == 12
    assert dt_utc.day == 31
    assert dt_utc.hour == 15
    assert dt_utc.minute == 0
    assert dt_utc.second == 0
    assert dt_utc.tzinfo == UTC

def test_parser_module_exposes_parse_function():
    # Structural validation of the API contract
    assert hasattr(dateutil.parser, "parse")
    assert callable(dateutil.parser.parse)
    assert dateutil.parser.parse is parse

def test_parse_common_date_string_formats():
    dt1 = parse("2023-01-01")
    assert dt1.year == 2023
    assert dt1.month == 1
    assert dt1.day == 1

    dt2 = parse("Jan 2 2023 03:04:05")
    assert dt2.year == 2023
    assert dt2.month == 1
    assert dt2.day == 2
    assert dt2.hour == 3
    assert dt2.minute == 4
    assert dt2.second == 5

    dt3 = parse("2023/01/03")
    assert dt3.year == 2023
    assert dt3.month == 1
    assert dt3.day == 3

def test_parse_invalid_string_with_exclamations_raises_parser_error():
    with pytest.raises(ParserError):
        parse("this is not a date at all !!!")

def test_relativedelta_addition_calculates_correct_datetime():
    base_date = datetime(2020, 1, 1)
    delta = relativedelta(months=+1, days=+2)
    result = base_date + delta
    expected = datetime(2020, 2, 3)
    assert result == expected

def test_gettz_returns_valid_tzinfo_for_iana_string():
    tz_obj = tz.gettz("UTC")
    # The system might lack timezone data, so we check if tz_obj is not None
    if tz_obj is not None:
        dt = parse("2020-01-01 00:00:00")
        dt_aware = dt.replace(tzinfo=tz_obj)
        assert dt_aware.tzinfo is not None
        assert dt_aware.tzname() == "UTC"

def test_parse_standard_datetime_string_returns_datetime_object():
    iso_string = "2023-10-25T14:30:00Z"
    human_string = "October 25, 2023 2:30 PM"
    expected = datetime(2023, 10, 25, 14, 30)

    # dateutil 2.8 parses 'Z' as UTC, returning an aware datetime.
    # We adapt the test logic by stripping tzinfo to match the expected naive datetime.
    dt_iso = parse(iso_string).replace(tzinfo=None)
    dt_human = parse(human_string)

    assert dt_iso == expected
    assert dt_human == expected

def test_parse_ambiguous_date_with_yearfirst_and_dayfirst():
    ambiguous_string = "01-02-03"

    # When dayfirst=True and yearfirst=False
    dt_dayfirst = parse(ambiguous_string, dayfirst=True, yearfirst=False)
    assert dt_dayfirst == datetime(2003, 2, 1, 0, 0)

    # When yearfirst=True and dayfirst=False
    dt_yearfirst = parse(ambiguous_string, yearfirst=True, dayfirst=False)
    assert dt_yearfirst == datetime(2001, 2, 3, 0, 0)

def test_parse_string_with_extraneous_text_and_fuzzy_flag_extracts_datetime():
    messy_string_1 = "The meeting is scheduled for Jan 15th 2024 at 9am sharp."
    dt1 = parse(messy_string_1, fuzzy=True)
    assert dt1 == datetime(2024, 1, 15, 9, 0)

    messy_string_2 = "I have three apples and will eat them on 2023-05-10."
    dt2 = parse(messy_string_2, fuzzy=True)
    assert dt2 == datetime(2023, 5, 10, 0, 0)

def test_parse_incomplete_date_string_with_default_fills_missing_components():
    incomplete_string = "March 15"
    baseline_default = datetime(2099, 1, 1, 12, 30, 0)

    dt = parse(incomplete_string, default=baseline_default)
    assert dt == datetime(2099, 3, 15, 12, 30, 0)

@pytest.mark.parametrize("bad_string", [
    "Hello World",
    "1234567890",
    ""
])
def test_parse_unrecognizable_string_raises_parser_error(bad_string):
    with pytest.raises(ParserError):
        parse(bad_string)

@pytest.mark.parametrize("invalid_input", [
    None,
    20231012,
    True,
    [],
    {}
])
def test_parse_non_string_or_none_raises_type_error(invalid_input):
    with pytest.raises(TypeError):
        parse(invalid_input)

@pytest.mark.parametrize("tz_string", [
    "America/New_York",
    "Europe/London",
    "Asia/Tokyo",
    "UTC"
])
def test_gettz_valid_iana_string_returns_tzinfo_object(tz_string):
    tz = gettz(tz_string)
    assert isinstance(tz, tzinfo)

@pytest.mark.parametrize("tz_string", [
    "America/Not_A_City",
    "Invalid/Timezone"
])
def test_gettz_invalid_timezone_string_returns_none(tz_string):
    tz = gettz(tz_string)
    assert tz is None

def test_relativedelta_plural_arguments_handles_calendar_math_correctly():
    # Leap year handling
    assert datetime(2020, 1, 31) + relativedelta(months=1) == datetime(2020, 2, 29)

    # Non-leap year handling
    assert datetime(2021, 1, 31) + relativedelta(months=1) == datetime(2021, 2, 28)

    # Leap day shifting to non-leap year
    assert datetime(2024, 2, 29) + relativedelta(years=1) == datetime(2025, 2, 28)

def test_relativedelta_singular_arguments_replaces_absolute_components():
    base_date = datetime(2023, 10, 15, 14, 30, 0)
    delta = relativedelta(month=1, day=5, hour=9)
    expected_date = datetime(2023, 1, 5, 9, 30, 0)

    assert base_date + delta == expected_date

def test_relativedelta_anchored_weekday_calculations():

    # Positional Constraint 1: Last Friday of the month
    base_date_1 = datetime(2023, 10, 12)
    # Anchor to the end of the month (day=31 safely truncates to the actual last day), then find the previous Friday
    delta_1 = relativedelta(day=31, weekday=FR(-1))
    assert base_date_1 + delta_1 == datetime(2023, 10, 27)

    # Positional Constraint 2: First Tuesday of the next month
    base_date_2 = datetime(2024, 2, 15)
    # Shift forward one month, anchor to the 1st of that month, then find the next Tuesday
    delta_2 = relativedelta(months=1, day=1, weekday=TU(1))
    assert base_date_2 + delta_2 == datetime(2024, 3, 5)

def test_instantiate_rrule_with_constraints_establishes_valid_schedule_object():
    schedule = rrule(
        freq=MONTHLY,
        dtstart=datetime(2024, 1, 1),
        byweekday=WE(3)
    )

    assert isinstance(schedule, rrule)
    assert isinstance(schedule, Iterable)
    assert hasattr(schedule, "__iter__")

def test_iterate_rrule_yields_sequential_datetime_objects_matching_pattern():
    schedule = rrule(
        freq=DAILY,
        dtstart=datetime(2024, 2, 28),
        count=3
    )

    result = list(schedule)

    expected = [
        datetime(2024, 2, 28),
        datetime(2024, 2, 29),
        datetime(2024, 3, 1)
    ]
    assert result == expected

def test_rrule_large_iteration_count_calculates_correct_offset():
    schedule = rrule(
        freq=DAILY,
        dtstart=datetime(2000, 1, 1)
    )
    iterator = iter(schedule)

    result = None
    # Execute a loop calling next(iterator) exactly 5,000 times.
    for _ in range(5000):
        result = next(iterator)

    # The 1st call yields the dtstart (2000-01-01, which is +0 days).
    # Therefore, the 5000th call is exactly +4999 days from dtstart.
    # datetime(2000, 1, 1) + timedelta(days=4999) evaluates strictly to datetime(2013, 9, 8).
    assert result == datetime(2013, 9, 8)

def test_rrule_between_returns_occurrences_within_boundaries_respecting_inclusive_flag():
    schedule = rrule(
        freq=DAILY,
        dtstart=datetime(2023, 1, 1)
    )

    after_dt = datetime(2023, 1, 1)
    before_dt = datetime(2023, 1, 5)

    # Execution 1: inc=False
    result_exclusive = schedule.between(after_dt, before_dt, inc=False)
    assert result_exclusive == [
        datetime(2023, 1, 2),
        datetime(2023, 1, 3),
        datetime(2023, 1, 4)
    ]

    # Execution 2: inc=True
    result_inclusive = schedule.between(after_dt, before_dt, inc=True)
    assert result_inclusive == [
        datetime(2023, 1, 1),
        datetime(2023, 1, 2),
        datetime(2023, 1, 3),
        datetime(2023, 1, 4),
        datetime(2023, 1, 5)
    ]

def test_count_bounded_rrule_returns_exact_total():
    # Standard boundary
    schedule_standard = rrule(
        freq=DAILY,
        dtstart=datetime(2023, 1, 1),
        until=datetime(2023, 1, 10)
    )
    assert schedule_standard.count() == 10

    # Leap year boundary
    schedule_leap = rrule(
        freq=DAILY,
        dtstart=datetime(2020, 2, 28),
        until=datetime(2020, 3, 1)
    )
    assert schedule_leap.count() == 3

    # Zero-occurrence boundary
    schedule_zero = rrule(
        freq=DAILY,
        dtstart=datetime(2023, 1, 10),
        until=datetime(2023, 1, 1)
    )
    assert schedule_zero.count() == 0
