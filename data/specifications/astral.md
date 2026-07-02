Project: `celestial_events`

## 1. High-Level Goal

Implement a Python library named `celestial_events` that calculates astronomical events (sun and moon behaviors) based on geographic coordinates, dates, and timezones. The library must provide precise, deterministic calculations for solar events (dawn, sunrise, noon, sunset, dusk) and lunar phases, while strictly handling timezone localizations, polar boundary conditions, and input validation.

## 2. Module Structure
You must create the following exact module and submodule structure:
* `celestial_events` (Root module exposing core classes)
* `celestial_events.geocoder` (Submodule for location lookups)
* `celestial_events.moon` (Submodule for lunar calculations)
* `celestial_events.sun` (Submodule for solar calculations)

---

## 3. Core Classes (Root Module)

### `Observer`
Implement a class representing a geographic observer.
* **Signature:** `Observer(latitude, longitude, elevation=0.0)`
* **Behaviors & Rules:**
  * Store `latitude`, `longitude`, and `elevation` as instance attributes.
  * **Type Coercion:** You must automatically coerce string inputs into `float` values upon instantiation (e.g., `"-41.2865"` must become `-41.2865`).
  * **Boundaries:** The class must accept extreme boundary coordinates (e.g., `latitude=90.0` or `-90.0`) without error.

### `LocationInfo`
Implement a class representing a named geographic location.
* **Signature:** `LocationInfo(name, region, timezone, latitude, longitude)`
* **Behaviors & Rules:**
  * Store `name`, `region`, and `timezone` as string attributes.
  * Store `latitude` and `longitude` as float attributes.
  * **Observer Generation:** Automatically generate and expose an attribute named `observer`. This attribute must be an instance of the `Observer` class, initialized with the `LocationInfo`'s latitude and longitude.

---

## 4. Geocoder Submodule (`celestial_events.geocoder`)

### `database`
* **Signature:** `database()`
* **Behaviors & Rules:**
  * Return a data structure (e.g., a dictionary or custom registry) containing geographic data for various cities. It must store at least the city name, region, timezone string, latitude, and longitude.

### `lookup`
* **Signature:** `lookup(query: str, db)`
* **Behaviors & Rules:**
  * Search the provided `db` object for the string `query` (representing a city name).
  * **Success:** Return a fully populated `LocationInfo` object corresponding to the matched city.
  * **Exceptions:** You must explicitly raise a `KeyError` if the query is not found, if the query is an empty string (`""`), or if the query is purely numeric (e.g., `"12345"`).

---

## 5. Moon Submodule (`celestial_events.moon`)

### `phase`
* **Signature:** `phase(date=None)`
* **Behaviors & Rules:**
  * **Default Date:** If `date` is `None` or omitted, default to the current local date (`datetime.date.today()`).
  * **Return Type:** Return a `float` representing the age of the moon in days since the last New Moon.
  * **Value Range:** The returned float must strictly fall between `0.0` and `29.53` (the length of a standard lunar cycle).
  * **Determinism & Variance:** The calculation must be deterministic (same date always yields the exact same float). The value must change daily. Over any 7-day period, the maximum phase minus the minimum phase must be greater than 0.
  * **Historical Accuracy:** Implement a standard astronomical algorithm for lunar age. It must correctly handle leap years and align with known historical phases:
    * A known New Moon (e.g., Jan 21, 2023) must return a value near the very beginning or very end of the cycle (either `< 1.0` or `> 27.0`).
    * A known Full Moon (e.g., Feb 5, 2023) must return a value between `13.5` and `15.5`.

---

## 6. Sun Submodule (`celestial_events.sun`)

### `sun`
* **Signature:** `sun(observer, date=None, tzinfo=None, dawn_dusk_depression=...)` *(Note: Provide a sensible default for depression, such as 18.0 or 6.0)*
* **Behaviors & Rules:**
  * **Input Validation:** 
    * You must verify that the `observer` argument is a valid `Observer` instance. If a primitive type (like a float) is passed, raise an `Exception`.
    * You must verify that `tzinfo`, if provided, is a valid timezone object (e.g., `zoneinfo.ZoneInfo`). If an invalid type (like a string) is passed, raise an `Exception`.
  * **Default Date:** If `date` is `None`, default to `datetime.date.today()`.
  * **Return Format:** Return a dictionary containing exactly these keys: `"dawn"`, `"sunrise"`, `"noon"`, `"sunset"`, `"dusk"`. The values must be `datetime.datetime` objects.
  * **Chronology:** The calculated times must strictly occur in this order: `dawn < sunrise < noon < sunset < dusk`.
  * **Timezone Handling:** 
    * If `tzinfo` is provided, all returned `datetime` objects must be timezone-aware and localized to that specific timezone.
    * The localization must correctly account for Daylight Saving Time (DST) transitions (e.g., correctly shifting UTC offsets between standard and daylight time for the given date).
  * **Depression Angle Logic:** The `dawn_dusk_depression` parameter (a float representing degrees below the horizon) must dictate the calculation of dawn and dusk. 
    * A *larger* depression angle must result in an *earlier* dawn and a *later* dusk.
    * The `sunrise`, `noon`, and `sunset` times must remain completely unaffected by the `dawn_dusk_depression` parameter.

### `sunrise` and `sunset`
* **Signatures:** 
  * `sunrise(observer, date=None, tzinfo=None)`
  * `sunset(observer, date=None, tzinfo=None)`
* **Behaviors & Rules:**
  * These functions must return the single `datetime.datetime` object for their respective events, following the exact same default date and timezone localization rules as the `sun()` function.
  * **Polar Boundary Exceptions:** If a solar event does not occur on the given date due to extreme latitudes (i.e., a diurnal cycle is missing, such as polar night or midnight sun), you must explicitly raise a `ValueError`.