# 1. Testing Framework & Mocking
import pytest

# 2. The Subject Under Test
import survival_analysis as lifelines
from survival_analysis import CoxPHFitter, KaplanMeierFitter
from survival_analysis.datasets import load_rossi, load_waltons
from survival_analysis.exceptions import ConvergenceError
from survival_analysis.statistics import logrank_test

# 3. Auxiliary: Third-Party
import matplotlib.axes
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.axes import Axes
from matplotlib.collections import PolyCollection
from matplotlib.lines import Line2D


def test_kmf_survival_function_is_bounded_and_non_increasing():
    durations = [5, 6, 6, 2.5, 4, 4]
    events = [1, 0, 1, 1, 1, 1]

    kmf = KaplanMeierFitter()
    kmf.fit(durations, event_observed=events)

    sf = kmf.survival_function_
    probs = sf.iloc[:, 0].values

    assert np.all(probs >= 0.0)
    assert np.all(probs <= 1.0)

    diffs = np.diff(probs)
    assert np.all(diffs <= 1e-8)

def test_kmf_predict_differentiates_distinct_cohorts():
    df = load_waltons()
    group1 = df[df['group'] == 'control']
    group2 = df[df['group'] == 'miR-137']

    kmf1 = KaplanMeierFitter()
    kmf1.fit(group1['T'], event_observed=group1['E'])

    kmf2 = KaplanMeierFitter()
    kmf2.fit(group2['T'], event_observed=group2['E'])

    p1 = kmf1.predict(10.0)
    p2 = kmf2.predict(10.0)

    assert 0.0 <= p1 <= 1.0
    assert 0.0 <= p2 <= 1.0
    assert abs(p1 - p2) > 1e-3

def test_coxph_summary_contains_standard_statistical_metrics():
    df = pd.DataFrame({
        'T': [5, 6, 6, 2.5, 4, 4],
        'E': [1, 0, 1, 1, 1, 1],
        'var1': [0, 1, 1, 0, 1, 0],
        'var2': [1.5, 2.0, 3.1, 2.2, 1.1, 0.5]
    })

    cph = CoxPHFitter()
    cph.fit(df, duration_col='T', event_col='E')

    summary = cph.summary

    assert "coef" in summary.columns
    assert "se(coef)" in summary.columns
    assert "p" in summary.columns

    if "exp(coef)" in summary.columns:
        assert np.all(summary["exp(coef)"] > 0)

def test_kmf_predict_at_time_zero_returns_at_least_0_99():
    durations = [5, 6, 6, 2.5, 4, 4]
    events = [1, 0, 1, 1, 1, 1]

    kmf = KaplanMeierFitter()
    kmf.fit(durations, event_observed=events)

    p0 = kmf.predict(0.0)
    assert p0 >= 0.99

def test_kmf_predict_returns_non_increasing_probabilities():
    durations = [5, 6, 6, 2.5, 4, 4]
    events = [1, 0, 1, 1, 1, 1]

    kmf = KaplanMeierFitter()
    kmf.fit(durations, event_observed=events)

    times = [1.0, 3.0, 10.0]
    probs = kmf.predict(times).values

    assert np.all(probs >= 0.0)
    assert np.all(probs <= 1.0)

    diffs = np.diff(probs)
    assert np.all(diffs <= 1e-8)

def test_kmf_cumulative_density_is_non_decreasing():
    kmf = KaplanMeierFitter()
    durations = [2, 4, 4, 6, 8, 10]
    events = [1, 1, 0, 1, 0, 1]
    kmf.fit(durations, event_observed=events)

    cd = kmf.cumulative_density_

    # Verify it is a DataFrame
    assert isinstance(cd, pd.DataFrame)

    # Check bounds between 0.0 and 1.0
    first_column = cd.columns[0]
    vals = cd[first_column].values
    assert (vals >= 0.0).all() and (vals <= 1.0).all()

    # Check non-decreasing property with a 1e-8 tolerance
    diffs = np.diff(vals)
    assert (diffs >= -1e-8).all()

def test_kmf_event_table_contains_standard_columns():
    kmf = KaplanMeierFitter()
    durations = [5, 6, 6, 2.5, 4, 4]
    events = [1, 0, 1, 1, 1, 1]
    kmf.fit(durations, event_observed=events)

    event_table = kmf.event_table

    # Verify it is a DataFrame
    assert isinstance(event_table, pd.DataFrame)

    # Verify the exact presence of the required columns
    required_columns = {"removed", "observed", "censored", "at_risk"}
    assert required_columns.issubset(set(event_table.columns))

def test_kmf_confidence_interval_aligns_with_survival_function():
    kmf = KaplanMeierFitter()
    durations = [1, 2, 3, 4, 5, 6]
    events = [1, 0, 1, 0, 1, 1]
    kmf.fit(durations, event_observed=events)

    ci = kmf.confidence_interval_
    sf = kmf.survival_function_

    # Assert exact alignment and shape constraints
    assert ci.index.equals(sf.index)
    assert ci.shape[0] == sf.shape[0]
    assert ci.shape[1] >= 2

def test_kmf_median_survival_time_is_within_observed_durations():
    kmf = KaplanMeierFitter()
    # Using data that guarantees the survival function drops below 0.5
    # so median_survival_time_ is finite.
    durations = [1, 2, 3, 4, 5]
    events = [1, 1, 1, 1, 1]
    kmf.fit(durations, event_observed=events)

    median_st = kmf.median_survival_time_

    # Assert median survival time falls within the bounds of observed durations
    assert min(durations) <= median_st <= max(durations)

def test_coxph_params_index_matches_input_covariates():
    cph = CoxPHFitter()
    df = pd.DataFrame({
        'duration': [5, 6, 6, 2.5, 4, 4],
        'event': [1, 0, 1, 1, 1, 1],
        'age': [45, 50, 30, 25, 60, 35],
        'treatment': [1, 1, 0, 0, 1, 0]
    })

    cph.fit(df, duration_col='duration', event_col='event')

    params = cph.params_

    # Verify it is a Series
    assert isinstance(params, pd.Series)

    # Verify the index matches the exact list of covariate column names
    expected_covariates = ["age", "treatment"]
    assert list(params.index) == expected_covariates

def test_coxph_baseline_cumulative_hazard_is_non_decreasing():
    df = load_rossi()
    cph = CoxPHFitter()
    cph.fit(df, duration_col='week', event_col='arrest')

    bch = cph.baseline_cumulative_hazard_

    assert isinstance(bch, pd.DataFrame)

    # Calculate differences between consecutive time steps
    diffs = bch.diff().dropna()

    # Assert non-decreasing with a tolerance of 1e-10
    assert (diffs >= -1e-10).all().all()

def test_coxph_predict_partial_hazard_returns_positive_varying_values():
    df = load_rossi()
    cph = CoxPHFitter()
    cph.fit(df, duration_col='week', event_col='arrest')

    # Create two distinct covariate profiles (e.g., low age/no treatment vs. high age/treatment)
    profile1 = df.iloc[[0]].copy()
    profile1['age'] = 20
    profile1['fin'] = 0

    profile2 = df.iloc[[0]].copy()
    profile2['age'] = 60
    profile2['fin'] = 1

    profiles = pd.concat([profile1, profile2], ignore_index=True)

    hazards = cph.predict_partial_hazard(profiles)

    val1 = hazards.iloc[0]
    val2 = hazards.iloc[1]

    assert val1 > 0.0
    assert val2 > 0.0
    assert abs(val1 - val2) > 1e-12

def test_coxph_predict_survival_function_returns_bounded_decreasing_probabilities():
    df = load_rossi()
    cph = CoxPHFitter()
    cph.fit(df, duration_col='week', event_col='arrest')

    new_individuals = df.iloc[:3].copy()

    surv_func = cph.predict_survival_function(new_individuals)

    assert isinstance(surv_func, pd.DataFrame)
    # Verify output shape (columns equal to the number of input individuals)
    assert surv_func.shape[1] == 3

    for col in surv_func.columns:
        curve = surv_func[col]
        first_value = curve.iloc[0]
        last_value = curve.iloc[-1]

        # Verify bounded probabilities
        assert 0.0 <= last_value <= first_value <= 1.0

        # Verify it decreases over time (allowing for tiny float tolerance)
        diffs = curve.diff().dropna()
        assert (diffs <= 1e-10).all()

def test_coxph_concordance_index_is_bounded_between_zero_and_one():
    df = load_rossi()
    cph = CoxPHFitter()
    cph.fit(df, duration_col='week', event_col='arrest')

    c_index = cph.concordance_index_

    assert isinstance(c_index, float)
    assert 0.0 <= c_index <= 1.0

def test_coxph_fit_computes_valid_coefficient_for_binary_feature():
    df = load_waltons()

    # Derive a binary "treated" column from the "group" column
    df['treated'] = (df['group'] == 'miR-137').astype(int)
    df = df.drop('group', axis=1)

    cph = CoxPHFitter()
    cph.fit(df, duration_col='T', event_col='E')

    coef = cph.params_.loc['treated']

    # Assert that the resulting coefficient is not NaN
    assert not pd.isna(coef)

def test_kaplan_meier_fitter_fits_valid_toy_data():
    """
    When KaplanMeierFitter.fit() is called with valid, equal-length numeric arrays
    for durations and observed events, it should successfully execute without crashing.
    """
    kmf = KaplanMeierFitter()
    T = [5, 6, 6, 2, 4]
    E = [1, 0, 1, 1, 0]

    # If this crashes, the test will naturally fail.
    kmf.fit(T, event_observed=E)


def test_kmf_fit_calculates_survival_probabilities():
    """
    KaplanMeierFitter.fit must populate the survival_function_ attribute with a DataFrame
    containing the estimated survival probabilities mapped to each unique time point.
    """
    kmf = KaplanMeierFitter()
    T = [0.0, 5.0, 5.0, 10.0, 15.0]
    E = [True, True, False, True, False]

    kmf.fit(T, event_observed=E)
    sf = kmf.survival_function_

    # Verification: The resulting DataFrame index must exactly match the unique sorted durations
    expected_index = [0.0, 5.0, 10.0, 15.0]
    assert list(sf.index) == expected_index

    # Verification: The survival probability at time 0.0 must be strictly less than 1.0
    # because an event occurred exactly at time zero.
    prob_at_zero = sf.loc[0.0].iloc[0]
    assert prob_at_zero < 1.0


def test_kmf_custom_alpha_generates_confidence_intervals():
    """
    When KaplanMeierFitter is instantiated with a specific alpha value and fitted,
    it must populate the confidence_interval_ attribute with exactly two columns
    representing the lower and upper bounds.
    """
    # alpha=0.01 represents a 99% confidence interval, overriding the default 0.05
    kmf = KaplanMeierFitter(alpha=0.01)
    T = [2, 4, 6, 8, 10]
    E = [1, 1, 0, 1, 0]

    kmf.fit(T, event_observed=E)
    ci = kmf.confidence_interval_

    # Verification: The DataFrame must contain exactly two columns
    assert ci.shape[1] == 2

    # Dynamically identify upper and lower bound columns to remain robust
    lower_col = next(c for c in ci.columns if 'lower' in c.lower())
    upper_col = next(c for c in ci.columns if 'upper' in c.lower())

    # Verification: For every time point t, upper bound >= lower bound
    for t in ci.index:
        assert ci.loc[t, upper_col] >= ci.loc[t, lower_col]


def test_kmf_calculates_exact_median_survival_time():
    """
    KaplanMeierFitter.fit must expose the exact time point where the survival probability
    drops to or below 0.5 via the median_survival_time_ attribute.
    """
    kmf = KaplanMeierFitter()

    # Dataset A (Standard)
    T_A = [10, 20, 30, 40, 50]
    E_A = [True, True, True, True, True]
    kmf.fit(T_A, event_observed=E_A)

    # The median_survival_time_ must exactly equal 30.0
    assert kmf.median_survival_time_ == 30.0

    # Dataset B (Heavily Censored)
    T_B = [10, 20, 30, 40, 50]
    E_B = [False, False, False, False, False]
    kmf.fit(T_B, event_observed=E_B)

    # The median_survival_time_ must exactly equal float('inf')
    assert kmf.median_survival_time_ == float('inf')

def test_plot_survival_function_returns_matplotlib_axes():
    kmf = KaplanMeierFitter()
    durations = [5, 10, 15]
    events = [1, 0, 1]

    kmf.fit(durations, event_observed=events)
    ax = kmf.plot_survival_function()

    assert isinstance(ax, Axes)

    children = ax.get_children()
    has_line = any(isinstance(child, Line2D) for child in children)
    has_poly = any(isinstance(child, PolyCollection) for child in children)

    assert has_line, "Expected at least one Line2D object representing the survival curve."
    assert has_poly, "Expected at least one PolyCollection object representing the confidence interval."

def test_logrank_test_compares_distributions_and_returns_p_value():
    durations_A = [1, 2, 3, 4, 5]
    events_A = [1, 1, 1, 1, 1]

    durations_B = [100, 200, 300, 400, 500]
    events_B = [1, 1, 1, 1, 1]

    result = logrank_test(
        durations_A,
        durations_B,
        event_observed_A=events_A,
        event_observed_B=events_B
    )

    assert result.test_statistic > 0.0
    assert 0.0 <= result.p_value < 0.01

def test_logrank_test_omitted_event_indicators_assumes_all_observed():
    durations_A = [10.5, 22.1, 30.0]
    durations_B = [15.0, 25.5, 35.2]

    result_omitted = logrank_test(durations_A, durations_B)

    events_A = [True, True, True]
    events_B = [True, True, True]
    result_explicit = logrank_test(
        durations_A,
        durations_B,
        event_observed_A=events_A,
        event_observed_B=events_B
    )

    assert result_omitted.test_statistic == result_explicit.test_statistic
    assert result_omitted.p_value == result_explicit.p_value

def test_logrank_test_empty_durations_handled_gracefully():
    """
    lifelines does not raise a ValueError for empty arrays. 
    Instead, it gracefully computes and returns a StatisticalResult.
    """
    res1 = logrank_test([], [10, 20, 30])
    assert hasattr(res1, 'p_value'), "Expected a StatisticalResult with a p_value attribute"

    res2 = logrank_test([10, 20, 30], [])
    assert hasattr(res2, 'p_value'), "Expected a StatisticalResult with a p_value attribute"

def test_logrank_test_mismatched_array_lengths_raises_assertion_error():
    """
    lifelines uses assert statements for length validation, 
    so it raises an AssertionError rather than a ValueError.
    """
    durations_A = [10, 20, 30]
    event_observed_A = [True, False]

    durations_B = [15, 25]
    event_observed_B = [True, True]

    with pytest.raises(AssertionError, match="inputs must be of the same length"):
        logrank_test(
            durations_A,
            durations_B,
            event_observed_A=event_observed_A,
            event_observed_B=event_observed_B
        )

def test_coxphfitter_fit_calculates_feature_coefficients():
    df = pd.DataFrame({
        'T': [5.0, 10.0, 15.0, 20.0],
        'E': [1, 0, 1, 1],
        'age_at_diagnosis': [50, 60, 45, 55],
        'treatment_dosage': [120.5, 140.0, 130.5, 110.0]
    })

    cph = CoxPHFitter()
    cph.fit(df, duration_col='T', event_col='E')

    assert hasattr(cph, 'params_')
    assert isinstance(cph.params_, pd.Series)
    assert set(cph.params_.index) == {"age_at_diagnosis", "treatment_dosage"}

def test_coxphfitter_fit_generates_comprehensive_statistical_summary():
    df = pd.DataFrame({
        'time': [5.0, 10.0, 15.0, 20.0, 25.0],
        'status': [1, 0, 1, 1, 0],
        'weight_kg': [70.5, 80.0, 65.0, 90.0, 75.0],
        'height_cm': [170, 180, 165, 185, 175]
    })

    cph = CoxPHFitter()
    cph.fit(df, duration_col='time', event_col='status')

    summary = cph.summary
    assert isinstance(summary, pd.DataFrame)

    expected_columns = {"coef", "exp(coef)", "se(coef)", "p"}
    assert expected_columns.issubset(set(summary.columns))
    assert set(summary.index) == {"weight_kg", "height_cm"}

def test_coxph_predict_survival_function_returns_subject_specific_curves():
    train_df = pd.DataFrame({
        'T': [10, 20, 30],
        'E': [1, 0, 1],
        'age': [40, 50, 60]
    })

    cph = CoxPHFitter()
    cph.fit(train_df, duration_col='T', event_col='E')

    new_df = pd.DataFrame({'age': [35, 75]})
    surv_func = cph.predict_survival_function(new_df)

    assert isinstance(surv_func, pd.DataFrame)
    assert surv_func.shape == (3, 2)
    assert [float(x) for x in surv_func.index] == [10.0, 20.0, 30.0]

    for col in surv_func.columns:
        probs = surv_func[col].values
        assert (probs >= 0.0).all() and (probs <= 1.0).all()
        assert np.all(np.diff(probs) <= 0)

def test_coxph_plot_generates_axes_with_feature_labels():
    df = pd.DataFrame({
        'T': [5, 10, 15, 20],
        'E': [1, 1, 0, 1],
        'blood_pressure': [120, 130, 110, 140],
        'is_smoker': [0, 1, 0, 1]
    })

    cph = CoxPHFitter()
    cph.fit(df, duration_col='T', event_col='E')

    ax = cph.plot()

    assert isinstance(ax, matplotlib.axes.Axes)

    # Force a canvas draw to ensure tick labels are populated before extraction
    ax.figure.canvas.draw()
    y_labels = [t.get_text() for t in ax.get_yticklabels()]

    assert set(y_labels) == {'blood_pressure', 'is_smoker'}

def test_fit_with_collinear_features_raises_convergence_error():
    df = pd.DataFrame({
        'T': [10, 20, 30, 40, 50],
        'E': [1, 1, 0, 1, 1],
        'feature_A': [1.0, 2.0, 3.0, 4.0, 5.0],
        'feature_B': [2.0, 4.0, 6.0, 8.0, 10.0]
    })

    cph = CoxPHFitter()

    with pytest.raises(ConvergenceError):
        cph.fit(df, duration_col='T', event_col='E')
