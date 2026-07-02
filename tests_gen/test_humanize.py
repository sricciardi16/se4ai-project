# 1. Testing Framework & Mocking
import pytest

# 2. The Subject Under Test
import friendly_formatter as humanize
import friendly_formatter.i18n

# 4. Auxiliary: Standard Library
import datetime


def test_intcomma_formats_integers_with_commas():
    assert humanize.intcomma(1000) == "1,000"
    assert humanize.intcomma(123456789) == "123,456,789"
    assert humanize.intcomma(-12345) == "-12,345"

def test_ordinal_formats_integers_with_suffixes():
    assert humanize.ordinal(1) == "1st"
    assert humanize.ordinal(2) == "2nd"
    assert humanize.ordinal(3) == "3rd"
    assert humanize.ordinal(11) == "11th"
    assert humanize.ordinal(23) == "23rd"

def test_naturalsize_formats_bytes_base_1000():
    assert humanize.naturalsize(1024) == "1.0 kB"
    assert humanize.naturalsize(10_000_000).endswith("MB")

def test_precisedelta_formats_numeric_seconds():
    result = humanize.precisedelta(3661)
    assert "1 hour" in result
    assert "1 minute" in result
    assert "1 second" in result
    assert result == "1 hour, 1 minute and 1 second"

def test_naturaldelta_formats_timedelta():
    delta = datetime.timedelta(days=1, hours=2)
    result = humanize.naturaldelta(delta)
    assert "day" in result

def test_naturaltime_formats_past_datetime_relative_to_reference():
    when = datetime.datetime(2023, 1, 1, 12, 10, 0)
    target = datetime.datetime(2023, 1, 1, 12, 0, 0)

    result = humanize.naturaltime(target, when=when)

    assert result == "10 minutes ago"

def test_intcomma_formats_floats_preserving_decimals():
    result = humanize.intcomma(1234.56)

    assert result == "1,234.56"

def test_naturalsize_formats_bytes_base_1024_with_binary_flag():
    result = humanize.naturalsize(1536, binary=True)

    assert "KiB" in result
    assert result == "1.5 KiB"

def test_precisedelta_formats_timedelta_with_multiple_units():
    delta = datetime.timedelta(days=2, hours=1, minutes=1, seconds=1)

    result = humanize.precisedelta(delta)

    assert "2 days" in result
    assert "1 hour" in result
    assert "1 minute" in result
    assert "1 second" in result
    assert result == "2 days, 1 hour, 1 minute and 1 second"

def test_naturaltime_formats_future_datetime_relative_to_reference():
    when = datetime.datetime(2023, 1, 1, 12, 0, 0)
    target = datetime.datetime(2023, 1, 1, 12, 10, 0)

    result = humanize.naturaltime(target, when=when)

    assert "10 minutes" in result
    assert result == "10 minutes from now"

def test_apnumber_formats_integers_ap_style():
    """
    Test that apnumber formats numbers 1-9 as words and 10+ as digits,
    according to Associated Press style.
    """
    assert humanize.apnumber(1) == "one"
    assert humanize.apnumber(9) == "nine"
    assert humanize.apnumber(10) == "10"

def test_intword_formats_millions():
    """
    Test that intword correctly formats large integers in the millions.
    """
    assert humanize.intword(1_200_000) == "1.2 million"

def test_intword_formats_thousands():
    """
    Test that intword correctly formats thousands.
    """
    assert humanize.intword(12_000) == "12.0 thousand"

def test_format_bytes_default_returns_base_1000_string():
    assert humanize.naturalsize(1000) == "1.0 kB"
    assert humanize.naturalsize(1500000) == "1.5 MB"
    assert humanize.naturalsize(1000000000) == "1.0 GB"
    assert humanize.naturalsize(500) == "500 Bytes"

def test_format_bytes_with_binary_flag_returns_base_1024_string():
    assert humanize.naturalsize(1024, binary=True) == "1.0 KiB"
    assert humanize.naturalsize(1048576, binary=True) == "1.0 MiB"
    assert humanize.naturalsize(1073741824, binary=True) == "1.0 GiB"

def test_naturalsize_with_gnu_flag_returns_single_letter_suffix():
    # GNU format uses base-1024 math
    assert humanize.naturalsize(1500, gnu=True) == "1.5K"
    assert humanize.naturalsize(1500000, gnu=True) == "1.4M"
    assert humanize.naturalsize(1500000000, gnu=True) == "1.4G"

def test_naturalsize_with_negative_string_input_returns_negative_formatted_string():
    assert humanize.naturalsize("-1500000") == "-1.5 MB"
    assert humanize.naturalsize("-1048576.0", binary=True) == "-1.0 MiB"

def test_naturalsize_with_uncastable_string_raises_exception():
    with pytest.raises((ValueError, TypeError)):
        humanize.naturalsize("not_a_number")

    with pytest.raises((ValueError, TypeError)):
        humanize.naturalsize("1.5 MB")

    with pytest.raises((ValueError, TypeError)):
        humanize.naturalsize("")

def test_format_large_integer_inserts_thousands_separators():
    assert humanize.intcomma(1234567) == "1,234,567"
    assert humanize.intcomma(999) == "999"
    assert humanize.intcomma(1000) == "1,000"
    assert humanize.intcomma(-987654321) == "-987,654,321"

def test_intcomma_with_ndigits_rounds_and_inserts_separators():
    assert humanize.intcomma(12345.6789, ndigits=2) == "12,345.68"
    assert humanize.intcomma(9999.999, ndigits=2) == "10,000.00"
    assert humanize.intcomma(1000.1, ndigits=0) == "1,000"

def test_format_large_number_converts_to_magnitude_word():
    assert humanize.intword(1000000) == "1.0 million"
    assert humanize.intword(1200000000) == "1.2 billion"
    assert humanize.intword(3500000000000) == "3.5 trillion"
    assert humanize.intword(-1500000) == "-1.5 million"

def test_format_small_number_returns_raw_string_without_words():
    # Numbers under 1000 are returned as raw strings
    assert humanize.intword(999) == "999"
    assert humanize.intword(500) == "500"
    assert humanize.intword(0) == "0"
    assert humanize.intword(-999) == "-999"

def test_intword_applies_custom_decimal_precision():
    assert humanize.intword(1234567, format="%.2f") == "1.23 million"
    assert humanize.intword(1990000000, format="%.0f") == "2 billion"
    assert humanize.intword(1500000, format="%.3f") == "1.500 million"

def test_ordinal_formats_integer_and_string_inputs():
    # Standard suffixes
    assert humanize.ordinal(1) == "1st"
    assert humanize.ordinal(2) == "2nd"
    assert humanize.ordinal(3) == "3rd"
    assert humanize.ordinal(4) == "4th"

    # The "teen" exceptions
    assert humanize.ordinal(11) == "11th"
    assert humanize.ordinal(12) == "12th"
    assert humanize.ordinal(13) == "13th"

    # Large numbers ending in 1, 2, or 3
    assert humanize.ordinal(101) == "101st"
    assert humanize.ordinal(1002) == "1002nd"

    # String inputs
    assert humanize.ordinal("22") == "22nd"

def test_ordinal_with_uncastable_string_returns_input_string():
    # ordinal() catches ValueErrors and returns the raw string
    assert humanize.ordinal("abc") == "abc"
    assert humanize.ordinal("12.34") == "12.34"
    assert humanize.ordinal("") == ""

def test_naturaltime_below_minimum_unit_returns_zero_or_now():
    # Microseconds below seconds minimum
    delta_1 = datetime.timedelta(microseconds=500000)
    assert humanize.naturaltime(delta_1, minimum_unit="seconds") == "now"

    # Microseconds below milliseconds minimum
    delta_2 = datetime.timedelta(microseconds=500)
    # When minimum_unit is not "seconds", it falls back to standard formatting
    assert humanize.naturaltime(delta_2, minimum_unit="milliseconds") == "0 milliseconds ago"

def test_naturaltime_with_months_disabled_uses_days_then_years():
    # 45 days -> 45 days ago (weeks are not used)
    delta_45 = datetime.timedelta(days=45)
    assert humanize.naturaltime(delta_45, months=False) == "45 days ago"

    delta_400 = datetime.timedelta(days=400)
    result = humanize.naturaltime(delta_400, months=False)
    assert "year" in result

def test_naturaltime_mixed_timezone_awareness_raises_type_error():
    value = datetime.datetime(2023, 1, 1, 12, 0, 0, tzinfo=datetime.timezone.utc)
    when = datetime.datetime(2023, 1, 1, 12, 5, 0)

    with pytest.raises(TypeError):
        humanize.naturaltime(value, when=when)

def test_naturaldelta_positive_duration_returns_absolute_phrase():
    delta_1 = datetime.timedelta(days=3, hours=4)
    assert humanize.naturaldelta(delta_1) == "3 days"

    delta_2 = datetime.timedelta(seconds=3600)
    assert humanize.naturaldelta(delta_2) == "an hour"

def test_naturaldelta_negative_duration_returns_positive_absolute_phrase():
    delta_1 = datetime.timedelta(days=-5)
    assert humanize.naturaldelta(delta_1) == "5 days"

    delta_2 = -86400
    assert humanize.naturaldelta(delta_2) == "a day"

@pytest.mark.parametrize("invalid_locale", [
    "xx_XX",
    "fake_LOCALE",
    "zz_ZZ"
])
def test_activate_unsupported_locale_raises_file_not_found_error(invalid_locale):
    # Activating an unsupported locale strictly raises a FileNotFoundError
    with pytest.raises(FileNotFoundError):
        humanize.i18n.activate(invalid_locale)
