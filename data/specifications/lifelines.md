Project: `survival_analysis`


## 1. High-Level Goal
Implement a Python library named `survival_analysis` that provides tools for survival analysis, specifically Kaplan-Meier estimates, Cox Proportional Hazards models, and log-rank testing. The library must heavily integrate with `pandas`, `numpy`, and `matplotlib`, accepting and returning standard pandas DataFrames and Series for most operations.

## 2. Module Structure
You must create the following exact module and submodule structure:
* `survival_analysis/` (Root package)
  * `__init__.py` (Must expose `CoxPHFitter` and `KaplanMeierFitter`)
  * `exceptions.py`
  * `datasets.py`
  * `statistics.py`

---

## 3. Exceptions (`survival_analysis.exceptions`)

### `ConvergenceError`
* **Action:** Implement a custom exception class named `ConvergenceError` inheriting from `Exception`.
* **Trigger:** This must be raised by the `CoxPHFitter` when it fails to converge (e.g., when input features are perfectly collinear).

---

## 4. Datasets (`survival_analysis.datasets`)

Implement two mock data loading functions that return `pandas.DataFrame` objects. 

### `load_rossi()`
* **Action:** Return a DataFrame containing at least the following numeric columns: `'week'` (duration), `'arrest'` (event indicator), `'age'`, and `'fin'`.

### `load_waltons()`
* **Action:** Return a DataFrame containing at least the following columns: `'T'` (duration), `'E'` (event indicator), and `'group'` (categorical string, containing at least the values `'control'` and `'miR-137'`).

---

## 5. Statistics (`survival_analysis.statistics`)

### `logrank_test`
* **Signature:** `def logrank_test(durations_A, durations_B, event_observed_A=None, event_observed_B=None)`
* **Inputs:** 
  * `durations_A`, `durations_B`: Iterables of numeric time durations.
  * `event_observed_A`, `event_observed_B`: Iterables of boolean/integer event indicators (1/True = event, 0/False = censored).
* **Rules & Behaviors:**
  1. **Default Events:** If `event_observed_A` or `event_observed_B` is `None`, you must assume all events are observed (i.e., internally generate an array of `True` or `1`s matching the length of the respective duration array).
  2. **Length Validation:** You must validate that the length of a duration array exactly matches its corresponding event array. If they do not match, you **must** raise an `AssertionError` (not a `ValueError`) with the exact message: `"inputs must be of the same length"`.
  3. **Empty Arrays:** If either duration array is empty, do NOT raise an error. Gracefully compute and return the result object.
  4. **Return Type:** Return an object (e.g., a `StatisticalResult` class) that contains at least two properties:
     * `test_statistic`: A float representing the computed test statistic.
     * `p_value`: A float bounded between `0.0` and `1.0`.

---

## 6. Core Classes (`survival_analysis`)

### Class: `KaplanMeierFitter`

#### `__init__(self, alpha=0.05)`
* **Action:** Initialize the fitter. Store `alpha`, which represents the significance level for confidence intervals (e.g., `alpha=0.01` means a 99% confidence interval).

#### `fit(self, durations, event_observed=None)`
* **Inputs:** `durations` (iterable of times), `event_observed` (iterable of event indicators).
* **Action:** Compute the Kaplan-Meier survival estimates.
* **State Changes (Attributes to populate):**
  1. **`survival_function_`**: A `pandas.DataFrame`. 
     * *Index:* The unique, sorted time points from `durations`.
     * *Values:* Survival probabilities bounded between `0.0` and `1.0`.
     * *Rule:* The probabilities must be monotonically non-increasing (the difference between consecutive values must be `<= 1e-8`).
     * *Rule:* If an event occurs exactly at time `0.0`, the survival probability at `0.0` must be strictly `< 1.0`.
  2. **`cumulative_density_`**: A `pandas.DataFrame`.
     * *Values:* Bounded between `0.0` and `1.0`.
     * *Rule:* Must be monotonically non-decreasing (difference between consecutive values `>= -1e-8`).
  3. **`event_table`**: A `pandas.DataFrame`.
     * *Columns:* Must contain exactly (at least) these column names: `"removed"`, `"observed"`, `"censored"`, `"at_risk"`.
  4. **`confidence_interval_`**: A `pandas.DataFrame`.
     * *Shape/Index:* Index must exactly match `survival_function_.index`. Must have exactly two columns.
     * *Columns:* One column name must contain the substring `'lower'` (case-insensitive) and the other must contain `'upper'`.
     * *Rule:* For every time point, the upper bound value must be `>=` the lower bound value.
  5. **`median_survival_time_`**: A float.
     * *Rule:* The exact time point where the survival probability drops to or below `0.5`.
     * *Rule:* If the survival probability never drops to or below `0.5` (e.g., heavily censored data), this must be set to `float('inf')`.

#### `predict(self, times)`
* **Inputs:** `times` (a scalar or iterable of time points).
* **Action:** Return the estimated survival probabilities at the requested times.
* **Rules:**
  * Return type should be a `pandas.Series` or similar numeric array.
  * Values must be bounded between `0.0` and `1.0` and be non-increasing over time.
  * If predicting for time `0.0` (and no events occurred at `0.0` during training), the returned probability must be `>= 0.99`.
  * The predictions must accurately reflect the fitted data (i.e., fitting two distinct cohorts must yield distinct prediction values).

#### `plot_survival_function(self)`
* **Action:** Generate a plot of the survival function and its confidence intervals.
* **Return Type:** Must return a `matplotlib.axes.Axes` object.
* **Rules:** The returned Axes object must contain at least one `matplotlib.lines.Line2D` object (representing the survival curve) and at least one `matplotlib.collections.PolyCollection` object (representing the shaded confidence interval).

---

### Class: `CoxPHFitter`

#### `__init__(self)`
* **Action:** Initialize the Cox Proportional Hazards fitter.

#### `fit(self, df, duration_col, event_col)`
* **Inputs:** 
  * `df`: A `pandas.DataFrame` containing covariates, durations, and events.
  * `duration_col`: String, the name of the column in `df` representing time.
  * `event_col`: String, the name of the column in `df` representing the event indicator.
* **Action:** Fit the Cox Proportional Hazards model to the data.
* **Rules & Exceptions:**
  * If the input features (covariates) are perfectly collinear (e.g., one feature is an exact multiple of another), you **must** raise a `survival_analysis.exceptions.ConvergenceError`.
  * Must successfully compute valid (non-NaN) coefficients for binary and continuous features.
* **State Changes (Attributes to populate):**
  1. **`params_`**: A `pandas.Series`.
     * *Index:* Must exactly match the names of the covariate columns provided in `df`.
     * *Values:* The computed hazard coefficients.
  2. **`summary`**: A `pandas.DataFrame`.
     * *Index:* Must exactly match the names of the covariate columns.
     * *Columns:* Must contain at least `"coef"`, `"exp(coef)"`, `"se(coef)"`, and `"p"`.
     * *Rule:* All values in the `"exp(coef)"` column must be strictly `> 0`.
  3. **`baseline_cumulative_hazard_`**: A `pandas.DataFrame`.
     * *Rule:* Values must be monotonically non-decreasing over time (difference between consecutive time steps `>= -1e-10`).
  4. **`concordance_index_`**: A float.
     * *Rule:* Must be bounded between `0.0` and `1.0`.

#### `predict_partial_hazard(self, X)`
* **Inputs:** `X`, a `pandas.DataFrame` of covariates for new individuals.
* **Action:** Compute the partial hazard for each individual.
* **Rules:**
  * Returns a `pandas.Series` or `pandas.DataFrame`.
  * All returned hazard values must be strictly positive (`> 0.0`).
  * Different covariate profiles must yield mathematically distinct hazard values.

#### `predict_survival_function(self, X)`
* **Inputs:** `X`, a `pandas.DataFrame` of covariates for new individuals.
* **Action:** Compute the subject-specific survival curves.
* **Rules:**
  * **Return Type:** A `pandas.DataFrame`.
  * **Shape:** The number of columns must exactly equal the number of rows (individuals) in `X`.
  * **Index:** Must exactly match the unique, sorted time durations from the training data.
  * **Values:** Every column's values must be bounded between `0.0` and `1.0`.
  * **Values:** Every column's values must be monotonically non-increasing over time (difference between consecutive values `<= 1e-10`).

#### `plot(self)`
* **Action:** Generate a forest plot (or similar) of the fitted coefficients.
* **Return Type:** Must return a `matplotlib.axes.Axes` object.
* **Rules:** The y-axis tick labels (`ax.get_yticklabels()`) of the returned plot must exactly match the names of the covariate features used during `fit`.