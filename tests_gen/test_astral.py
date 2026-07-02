# 1. Testing Framework & Mocking
import pytest

# 2. The Subject Under Test
from celestial_events import LocationInfo, Observer
from celestial_events.geocoder import database, lookup
from celestial_events.moon import phase
from celestial_events.sun import sun, sunrise, sunset

# 4. Auxiliary: Standard Library
import datetime
from datetime import date, timedelta
from zoneinfo import ZoneInfo


def test_sun_returns_chronological_events_for_valid_input():
    obs = Observer(latitude=51.5074, longitude=-0.1278)
    test_date = date(2020, 6, 1)

    sun_events = sun(obs, date=test_date)

    assert "dawn" in sun_events
    assert "sunrise" in sun_events
    assert "noon" in sun_events
    assert "sunset" in sun_events
    assert "dusk" in sun_events

    assert sun_events["dawn"] < sun_events["sunrise"] < sun_events["noon"] < sun_events["sunset"] < sun_events["dusk"]

def test_sun_events_change_on_consecutive_days():
    obs = Observer(latitude=51.5074, longitude=-0.1278)

    sun_day_1 = sun(obs, date=date(2020, 1, 1))
    sun_day_2 = sun(obs, date=date(2020, 1, 2))

    assert sun_day_1["sunrise"] != sun_day_2["sunrise"]
    assert sun_day_1["sunset"] != sun_day_2["sunset"]

def test_moon_phase_returns_valid_float_and_changes_daily():
    phase_day_1 = phase(date(2020, 1, 1))
    phase_day_2 = phase(date(2020, 1, 2))

    assert isinstance(phase_day_1, float)
    assert 0.0 <= phase_day_1 <= 30.0
    assert 0.0 <= phase_day_2 <= 30.0

    diff = abs(phase_day_2 - phase_day_1)

    # Handle potential wrap-around at the end of the lunar cycle (approx 29.53 days)
    if diff > 15.0:
        diff = 29.53 - diff

    assert 0.0 < diff < 3.0

def test_locationinfo_exposes_latitude_and_longitude():
    loc = LocationInfo("London", "England", "Europe/London", 51.5074, -0.1278)

    assert isinstance(loc.latitude, float)
    assert isinstance(loc.longitude, float)

    assert 51.0 <= loc.latitude <= 52.5
    assert -1.5 <= loc.longitude <= 0.5

    # Verify the nested Observer object also exposes these correctly
    assert isinstance(loc.observer, Observer)
    assert loc.observer.latitude == loc.latitude
    assert loc.observer.longitude == loc.longitude

def test_locationinfo_exposes_timezone_attribute():
    loc = LocationInfo("London", "England", "Europe/London", 51.5074, -0.1278)

    assert hasattr(loc, "timezone")
    assert loc.timezone is not None
    assert loc.timezone == "Europe/London"

def test_sun_returns_timezone_aware_datetimes():
    london = LocationInfo("London", "England", "Europe/London", 51.5074, -0.1278)
    test_date = date(2020, 6, 1)

    sun_events = sun(london.observer, date=test_date, tzinfo=ZoneInfo(london.timezone))

    for event_name, event_time in sun_events.items():
        assert event_time.tzinfo is not None, f"The datetime for {event_name} is not timezone-aware."

def test_sun_noon_occurs_between_sunrise_and_sunset():
    london = LocationInfo("London", "England", "Europe/London", 51.5074, -0.1278)
    test_date = date(2020, 3, 1)

    sun_events = sun(london.observer, date=test_date, tzinfo=ZoneInfo(london.timezone))

    assert sun_events["sunrise"] < sun_events["noon"] < sun_events["sunset"]

def test_sun_events_differ_for_distinct_locations_on_same_date():
    test_date = date(2020, 6, 1)

    london = LocationInfo("London", "England", "Europe/London", 51.5074, -0.1278)
    new_york = LocationInfo("New York", "USA", "America/New_York", 40.7128, -74.0060)

    london_events = sun(london.observer, date=test_date, tzinfo=ZoneInfo(london.timezone))
    ny_events = sun(new_york.observer, date=test_date, tzinfo=ZoneInfo(new_york.timezone))

    assert london_events["sunrise"] != ny_events["sunrise"]
    assert london_events["sunset"] != ny_events["sunset"]

def test_moon_phase_is_deterministic_for_same_date():
    test_date = date(2020, 2, 20)

    phase_call_1 = phase(test_date)
    phase_call_2 = phase(test_date)

    assert isinstance(phase_call_1, float)
    assert phase_call_1 == phase_call_2

def test_moon_phase_varies_within_valid_range_over_seven_days():
    base_date = date(2020, 1, 1)
    phases = []

    for i in range(7):
        current_date = base_date + timedelta(days=i)
        phases.append(phase(current_date))

    for p in phases:
        assert 0.0 <= p <= 30.0, f"Phase {p} is out of the valid 0.0 to 30.0 range."

    assert max(phases) - min(phases) > 0, "Moon phase did not vary over the 7-day period."

def test_sun_raises_exceptions_on_invalid_tzinfo_or_observer():
    observer = Observer(latitude=51.4733, longitude=-0.0008333)

    with pytest.raises(Exception):
        sun(observer.latitude, tzinfo="Not/A_Timezone")

    # In Astral 2.0, sun() takes an Observer object directly
    with pytest.raises(Exception):
        sun(observer, tzinfo="Not/A_Timezone")

def test_instantiate_observer_with_coordinates_stores_exact_values():
    # Standard floats
    obs_floats = Observer(latitude=51.4733, longitude=-0.0008333, elevation=25.5)
    assert obs_floats.latitude == 51.4733
    assert obs_floats.longitude == -0.0008333
    assert obs_floats.elevation == 25.5

    # String coercion edge cases
    obs_strings = Observer(latitude="-41.2865", longitude="174.7762", elevation="0.0")
    assert obs_strings.latitude == -41.2865
    assert obs_strings.longitude == 174.7762
    assert obs_strings.elevation == 0.0

    # Boundary values
    obs_north = Observer(latitude=90.0, longitude=0.0)
    assert obs_north.latitude == 90.0

    obs_south = Observer(latitude=-90.0, longitude=0.0)
    assert obs_south.latitude == -90.0

def test_instantiate_locationinfo_generates_valid_observer_and_timezone():
    loc = LocationInfo(
        name="Oymyakon",
        region="Russia",
        timezone="Asia/Srednekolymsk",
        latitude=63.4608,
        longitude=142.7858
    )

    # Exposes metadata exactly as provided
    assert loc.name == "Oymyakon"
    assert loc.region == "Russia"
    assert loc.timezone == "Asia/Srednekolymsk"

    # Automatically generates a valid Observer instance
    assert isinstance(loc.observer, Observer)
    assert loc.observer.latitude == 63.4608
    assert loc.observer.longitude == 142.7858


def test_lookup_valid_city_returns_populated_locationinfo():
    # In Astral 2.0, lookup requires the database to be passed explicitly
    db = database()
    loc = lookup("London", db)

    assert isinstance(loc, LocationInfo)
    assert loc.name == "London"
    assert loc.region == "England"
    assert loc.timezone == "Europe/London"
    assert loc.observer.latitude == pytest.approx(51.473, abs=0.01)

def test_lookup_invalid_city_raises_keyerror():
    db = database()

    # Completely invalid string
    with pytest.raises(KeyError):
        lookup("Atlantis", db)

    # Empty string
    with pytest.raises(KeyError):
        lookup("", db)

    # Numeric string
    with pytest.raises(KeyError):
        lookup("12345", db)


def test_sun_calculations_without_date_defaults_to_current_local_date():
    obs = Observer(latitude=51.4733, longitude=-0.0008333)

    result_sun = sun(obs, date=None)
    result_sunrise = sunrise(obs, date=None)
    result_sunset = sunset(obs, date=None)

    expected_date = datetime.date.today()

    for event_time in result_sun.values():
        assert event_time.date() == expected_date

    assert result_sunrise.date() == expected_date
    assert result_sunset.date() == expected_date


def test_sun_with_varying_depression_angles_shifts_dawn_and_dusk_times():
    obs = Observer(latitude=51.4733, longitude=-0.0008333)
    test_date = datetime.date(2023, 3, 21)

    result_civil = sun(obs, date=test_date, dawn_dusk_depression=6.0)
    result_nautical = sun(obs, date=test_date, dawn_dusk_depression=12.0)
    result_astronomical = sun(obs, date=test_date, dawn_dusk_depression=18.0)

    # Dawn should be progressively earlier
    assert result_astronomical['dawn'] < result_nautical['dawn'] < result_civil['dawn']

    # Dusk should be progressively later
    assert result_astronomical['dusk'] > result_nautical['dusk'] > result_civil['dusk']

    # Sunrise, noon, and sunset must remain completely unaffected
    assert result_civil['sunrise'] == result_nautical['sunrise'] == result_astronomical['sunrise']
    assert result_civil['noon'] == result_nautical['noon'] == result_astronomical['noon']
    assert result_civil['sunset'] == result_nautical['sunset'] == result_astronomical['sunset']


def test_sun_with_timezone_identifier_returns_localized_datetime_objects():
    obs = Observer(latitude=40.7128, longitude=-74.0060)
    tz = ZoneInfo("America/New_York")

    date_est = datetime.date(2023, 3, 10)
    date_edt = datetime.date(2023, 3, 15)

    result_est = sun(obs, date=date_est, tzinfo=tz)
    result_edt = sun(obs, date=date_edt, tzinfo=tz)

    for key in ['dawn', 'sunrise', 'noon', 'sunset', 'dusk']:
        # Assert EST (UTC-5)
        assert result_est[key].tzinfo is not None
        assert result_est[key].utcoffset() == datetime.timedelta(hours=-5)

        # Assert EDT (UTC-4)
        assert result_edt[key].tzinfo is not None
        assert result_edt[key].utcoffset() == datetime.timedelta(hours=-4)

def test_solar_event_without_diurnal_cycle_raises_value_error():
    observer = Observer(latitude=78.2232, longitude=15.6267)

    with pytest.raises(ValueError):
        sunrise(observer, date=datetime.date(2023, 12, 21))

    with pytest.raises(ValueError):
        sunset(observer, date=datetime.date(2023, 6, 21))

def test_moon_phase_matches_known_historical_lunar_events():
    # Known historical New Moon date
    new_moon_date = datetime.date(2023, 1, 21)
    new_moon_phase = phase(new_moon_date)
    assert isinstance(new_moon_phase, float)
    assert 0.0 <= new_moon_phase < 28.0
    assert new_moon_phase < 1.0 or new_moon_phase > 27.0

    # Known historical Full Moon date
    full_moon_date = datetime.date(2023, 2, 5)
    full_moon_phase = phase(full_moon_date)
    assert isinstance(full_moon_phase, float)
    assert 0.0 <= full_moon_phase < 28.0
    assert 13.5 <= full_moon_phase <= 15.5

    # Leap year boundary date
    leap_year_date = datetime.date(2024, 2, 29)
    leap_year_phase = phase(leap_year_date)
    assert isinstance(leap_year_phase, float)
    assert 0.0 <= leap_year_phase < 28.0

def test_calculate_phase_without_date_defaults_to_current_local_date():
    expected_phase = phase(datetime.date.today())

    phase_no_args = phase()
    phase_none = phase(date=None)

    assert phase_no_args == expected_phase
    assert phase_none == expected_phase
