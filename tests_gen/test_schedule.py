# 1. Testing Framework & Mocking
import pytest

# 2. The Subject Under Test
import task_scheduler as schedule

# 3. Auxiliary: Third-Party
from freezegun import freeze_time

# 4. Auxiliary: Standard Library
import datetime
import os
import time


@pytest.fixture(autouse=True)
def reset_scheduler():
    """Ensure a clean state for the scheduler before and after each test."""
    schedule.clear()
    yield
    schedule.clear()

def test_fluent_api_chaining_retains_job_reference_and_applies_tags():
    tracker = []

    def job1():
        tracker.append("job1_executed")

    def job2():
        tracker.append("job2_executed")

    # Crucial Data: Chaining .seconds and .minutes, applying multiple tags ("sec", "common")
    # Note: Chaining units like this overwrites the unit in schedule 1.2, but tests the fluent API's return of `self`.
    schedule.every().seconds.minutes.tag("sec", "common").do(job1)
    schedule.every().minutes.tag("min", "common").do(job2)

    jobs = schedule.get_jobs()
    assert len(jobs) == 2

    # Verify tags were applied correctly
    assert "sec" in jobs[0].tags
    assert "common" in jobs[0].tags

    # run_all should execute immediately regardless of next_run
    schedule.run_all()

    # Verify execution side-effects
    assert "job1_executed" in tracker
    assert "job2_executed" in tracker

def test_clear_with_tag_removes_only_matching_jobs():
    tracker = []
    def dummy_job():
        tracker.append(True)

    # Crucial Data: Multiple jobs sharing tags but differing in the target tag
    schedule.every().day.tag("keep", "common").do(dummy_job)
    schedule.every().day.tag("drop", "common").do(dummy_job)
    schedule.every().day.tag("drop").do(dummy_job)

    assert len(schedule.get_jobs()) == 3

    # Clear only jobs with the "drop" tag
    schedule.clear("drop")

    jobs = schedule.get_jobs()

    # Only the "keep" job should remain
    assert len(jobs) == 1
    assert "keep" in jobs[0].tags
    assert "drop" not in jobs[0].tags
    assert "common" in jobs[0].tags

def test_cancel_job_removes_specific_job_instance():
    def dummy_job():
        pass

    # Crucial Data: Pass the actual Job object reference returned by .do()
    job1 = schedule.every().day.do(dummy_job)
    job2 = schedule.every().day.do(dummy_job)

    assert len(schedule.get_jobs()) == 2

    schedule.cancel_job(job1)

    jobs = schedule.get_jobs()
    assert len(jobs) == 1
    # Verify the exact instance remaining is job2
    assert jobs[0] is job2

def test_repeat_decorator_registers_job_in_scheduler():
    tracker = []

    # Crucial Data: Pass a valid Job builder into the decorator
    @schedule.repeat(schedule.every().seconds)
    def decorated_job():
        tracker.append("decorated_executed")

    jobs = schedule.get_jobs()

    # Verify the job was automatically registered
    assert len(jobs) == 1

    # Verify it executes correctly
    schedule.run_all()
    assert tracker == ["decorated_executed"]

def test_run_pending_executes_only_due_jobs():
    tracker = []

    def job_due():
        tracker.append("due_executed")

    def job_not_due():
        tracker.append("not_due_executed")

    # Use freezegun (already imported in your file) to safely mock time
    with freeze_time("2023-01-01 12:00:00") as frozen_time:
        schedule.every(1).seconds.do(job_due)
        schedule.every(1).hours.do(job_not_due)

        # Simulate time advancing by 2 seconds
        frozen_time.move_to("2023-01-01 12:00:02")
        schedule.run_pending()

    # Only the job scheduled for every second should have run
    assert "due_executed" in tracker
    assert "not_due_executed" not in tracker

def dummy_task():
    """A simple callable to be used as a job target."""
    pass

def test_job_next_run_populated_with_datetime_on_schedule():
    job = schedule.every(10).minutes.do(dummy_task)

    assert isinstance(job.next_run, datetime.datetime)

def test_daily_job_at_specific_time_sets_correct_next_run():
    job = schedule.every().day.at("10:30").do(dummy_task)

    assert job.next_run.hour == 10
    assert job.next_run.minute == 30

def test_weekday_job_at_specific_time_sets_correct_next_run():
    job = schedule.every().monday.at("09:00").do(dummy_task)

    assert job.next_run.hour == 9
    assert job.next_run.minute == 0
    # In Python's datetime module, Monday is represented by 0
    assert job.next_run.weekday() == 0

def test_job_to_interval_supports_randomized_range():
    job = schedule.every(2).to(5).minutes.do(dummy_task)

    assert job in schedule.jobs
    # Verify the public attributes that define the randomized range
    assert job.interval == 2
    assert job.latest == 5

def test_idle_seconds_returns_time_until_next_job():
    schedule.every(1).hours.do(dummy_task)

    idle = schedule.idle_seconds()

    assert isinstance(idle, (int, float))
    assert idle > 0

def dummy_task():
    pass

def test_get_jobs_with_tag_returns_filtered_list():
    job1 = schedule.every().minute.do(dummy_task).tag("alpha")
    job2 = schedule.every().minute.do(dummy_task).tag("beta")
    job3 = schedule.every().minute.do(dummy_task).tag("alpha", "gamma")

    alpha_jobs = schedule.get_jobs("alpha")
    beta_jobs = schedule.get_jobs("beta")

    assert len(alpha_jobs) == 2
    assert job1 in alpha_jobs
    assert job3 in alpha_jobs
    assert job2 not in alpha_jobs

    assert len(beta_jobs) == 1
    assert job2 in beta_jobs

def test_job_execution_updates_last_run_datetime():
    job = schedule.every().minute.do(dummy_task)

    assert job.last_run is None

    schedule.run_all()

    assert job.last_run is not None
    assert isinstance(job.last_run, datetime.datetime)

def test_run_all_executes_jobs_immediately_and_clear_empties_queue():
    execution_count = 0

    def increment_task():
        nonlocal execution_count
        execution_count += 1

    schedule.every().day.do(increment_task)

    # Execute immediately with delay_seconds=0
    schedule.run_all(delay_seconds=0)

    assert execution_count == 1
    assert len(schedule.get_jobs()) == 1

    schedule.clear()

    assert len(schedule.get_jobs()) == 0

def test_fluent_api_accepts_singular_and_plural_time_units():
    # Singular units
    schedule.every(1).second.do(dummy_task)
    schedule.every(1).minute.do(dummy_task)
    schedule.every(1).hour.do(dummy_task)
    schedule.every(1).day.do(dummy_task)
    schedule.every(1).week.do(dummy_task)

    # Plural units
    schedule.every(2).seconds.do(dummy_task)
    schedule.every(2).minutes.do(dummy_task)
    schedule.every(2).hours.do(dummy_task)
    schedule.every(2).days.do(dummy_task)
    schedule.every(2).weeks.do(dummy_task)

    jobs = schedule.get_jobs()

    # If the API accepts all of them without throwing errors,
    # we should have exactly 10 jobs registered in the scheduler.
    assert len(jobs) == 10

def test_cancel_job_removes_job_and_maintains_scheduler_state():
    job1 = schedule.every().minute.do(dummy_task)
    job2 = schedule.every().hour.do(dummy_task)

    assert len(schedule.get_jobs()) == 2

    schedule.cancel_job(job1)

    remaining_jobs = schedule.get_jobs()
    assert len(remaining_jobs) == 1
    assert job2 in remaining_jobs
    assert job1 not in remaining_jobs

    # Ensure state is stable and new jobs can be scheduled immediately
    job3 = schedule.every().day.do(dummy_task)

    final_jobs = schedule.get_jobs()
    assert len(final_jobs) == 2
    assert job2 in final_jobs
    assert job3 in final_jobs

def test_scheduler_handles_large_volume_of_jobs():
    execution_count = 0

    def dummy_job():
        nonlocal execution_count
        execution_count += 1

    # Register a stress-load of 200 jobs in a single batch
    for _ in range(200):
        schedule.every().day.do(dummy_job)

    # Verify all jobs were registered successfully
    assert len(schedule.jobs) == 200

    # Execute all jobs simultaneously
    schedule.run_all()

    # Verify no jobs were dropped or failed to execute
    assert execution_count == 200

def test_register_routine_with_interval_queues_execution_at_exact_frequency():
    execution_count = 0

    def dummy_job():
        nonlocal execution_count
        execution_count += 1

    with freeze_time("2023-01-01 12:00:00.000000") as frozen_time:
        # Interval: 3, Unit: seconds
        job = schedule.every(3).seconds.do(dummy_job)

        # Initial next_run should be exactly 3 seconds in the future
        assert job.next_run == datetime.datetime(2023, 1, 1, 12, 0, 3)

        # Advance exactly 2.9 seconds (must not execute)
        frozen_time.move_to("2023-01-01 12:00:02.900000")
        schedule.run_pending()
        assert execution_count == 0

        # Advance to 3.0 seconds (must execute)
        frozen_time.move_to("2023-01-01 12:00:03.000000")
        schedule.run_pending()
        assert execution_count == 1
        # next_run must immediately advance by the exact interval duration again
        assert job.next_run == datetime.datetime(2023, 1, 1, 12, 0, 6)

        # Advance to 5.9 seconds (must not execute)
        frozen_time.move_to("2023-01-01 12:00:05.900000")
        schedule.run_pending()
        assert execution_count == 1

        # Advance to 6.0 seconds (must execute)
        frozen_time.move_to("2023-01-01 12:00:06.000000")
        schedule.run_pending()
        assert execution_count == 2
        assert job.next_run == datetime.datetime(2023, 1, 1, 12, 0, 9)

def test_register_routine_with_arguments_passes_exact_arguments_on_execution():
    received_args = None
    received_kwargs = None

    def dummy_job(*args, **kwargs):
        nonlocal received_args, received_kwargs
        received_args = args
        received_kwargs = kwargs

    with freeze_time("2023-01-01 12:00:00") as frozen_time:
        schedule.every().minute.do(
            dummy_job,
            42,
            "complex string with spaces",
            user_id=999,
            is_active=True,
            metadata=None
        )

        # Advance 1 minute to trigger the routine via run_pending
        frozen_time.move_to("2023-01-01 12:01:00")
        schedule.run_pending()

    # Assert exact positional and keyword arguments were passed without mutation or omission
    assert received_args == (42, "complex string with spaces")
    assert received_kwargs == {"user_id": 999, "is_active": True, "metadata": None}

def test_daily_job_at_specific_time_and_midnight_boundary():
    execution_count_1 = 0
    execution_count_2 = 0

    def dummy_job_1():
        nonlocal execution_count_1
        execution_count_1 += 1

    def dummy_job_2():
        nonlocal execution_count_2
        execution_count_2 += 1

    with freeze_time("2023-01-01 10:00:00") as frozen_time:
        job1 = schedule.every().day.at("14:30:00").do(dummy_job_1)
        job2 = schedule.every().day.at("00:00").do(dummy_job_2)

        # Verify next_run is set to the exact time on the current or next day
        assert job1.next_run == datetime.datetime(2023, 1, 1, 14, 30, 0)
        assert job2.next_run == datetime.datetime(2023, 1, 2, 0, 0, 0)

        # Mock system time boundary: "14:29:59" (must not run)
        frozen_time.move_to("2023-01-01 14:29:59")
        schedule.run_pending()
        assert execution_count_1 == 0

        # Mock system time boundary: "14:30:00" (must run)
        frozen_time.move_to("2023-01-01 14:30:00")
        schedule.run_pending()
        assert execution_count_1 == 1

        # Edge case time string: "00:00" (midnight boundary)
        frozen_time.move_to("2023-01-02 00:00:00")
        schedule.run_pending()
        assert execution_count_2 == 1

def test_register_routine_with_offset_string_executes_at_exact_offset():
    def dummy_job():
        pass

    with freeze_time("2023-01-01 10:00:00"):
        job1 = schedule.every().hour.at(":45").do(dummy_job)
        job2 = schedule.every().minute.at(":15").do(dummy_job)
        job3 = schedule.every().hour.at(":00").do(dummy_job)

        # Hourly offset string: ":45" (must schedule exactly at 45 minutes past the current hour)
        assert job1.next_run == datetime.datetime(2023, 1, 1, 10, 45, 0)

        # Minute offset string: ":15" (must schedule exactly at 15 seconds past the current minute)
        assert job2.next_run == datetime.datetime(2023, 1, 1, 10, 0, 15)

        # Edge case offset: ":00" (top of the hour/minute)
        # Since current time is exactly 10:00:00, the next top of the hour is 11:00:00
        assert job3.next_run == datetime.datetime(2023, 1, 1, 11, 0, 0)

# Fallback for older Python versions without zoneinfo
try:
    import zoneinfo
    ZoneInfo = zoneinfo.ZoneInfo
except ImportError:
    try:
        import pytz
        ZoneInfo = pytz.timezone
    except ImportError:
        ZoneInfo = None

def test_job_with_deadline_executes_then_removes_itself_after_deadline():
    counter = 0
    def mock_callable():
        nonlocal counter
        counter += 1

    with freeze_time("2023-01-01 00:00:00") as frozen_time:
        deadline = datetime.timedelta(seconds=5)
        schedule.every().seconds.until(deadline).do(mock_callable)

        # Mock system time state 1: Advance time by 3 seconds.
        frozen_time.move_to("2023-01-01 00:00:03")
        schedule.run_pending()

        # The job must execute normally prior to the deadline
        assert counter == 1
        assert len(schedule.get_jobs()) == 1

        # Mock system time state 2: Advance time by 6 seconds (total 6 seconds from start).
        frozen_time.move_to("2023-01-01 00:00:06")
        schedule.run_pending()

        # The job must not execute again, and must be automatically/permanently removed
        assert counter == 1
        assert schedule.get_jobs() == []


def test_job_tagged_with_multiple_labels_can_be_retrieved_and_cleared_by_label():
    def mock_callable():
        pass

    # Target job with multiple tags
    job1 = schedule.every().day.tag("database-sync", "high-priority", "tenant-12345").do(mock_callable)

    # Control job with no tags
    job2 = schedule.every().day.do(mock_callable)

    # Verify retrievability via any assigned label
    assert job1 in schedule.get_jobs("database-sync")
    assert job1 in schedule.get_jobs("high-priority")
    assert job1 in schedule.get_jobs("tenant-12345")

    # Action: Clear by one of the labels
    schedule.clear("tenant-12345")

    # Verification: Only the control job remains
    jobs = schedule.get_jobs()
    assert len(jobs) == 1
    assert jobs[0] == job2


def test_run_pending_executes_due_jobs_synchronously():
    counter = 0
    def mock_callable():
        nonlocal counter
        counter += 1

    with freeze_time("2023-01-01 00:00:00") as frozen_time:
        schedule.every(5).seconds.do(mock_callable)

        # Mock system time state: Advanced by exactly 6 seconds.
        frozen_time.move_to("2023-01-01 00:00:06")

        schedule.run_pending()

        # Verification: The counter must equal exactly 1
        assert counter == 1


def test_run_pending_with_no_due_jobs_returns_safely_without_execution():
    counter = 0
    def mock_callable():
        nonlocal counter
        counter += 1

    with freeze_time("2023-01-01 00:00:00") as frozen_time:
        schedule.every(1).hours.do(mock_callable)

        # Mock system time state: Advanced by exactly 59 minutes and 59 seconds.
        frozen_time.move_to("2023-01-01 00:59:59")

        result = schedule.run_pending()

        # Verification: Returns None, callable strictly never invoked
        assert result is None
        assert counter == 0

def dummy_task():
    """A no-op function to serve as a callable for scheduled jobs."""
    pass

def test_clear_without_arguments_removes_all_scheduled_jobs():
    schedule.every(1).minutes.tag("A").do(dummy_task)
    schedule.every(2).minutes.tag("B").do(dummy_task)
    schedule.every(3).minutes.do(dummy_task)

    assert len(schedule.get_jobs()) == 3

    schedule.clear()

    assert schedule.get_jobs() == []

def test_clear_with_tag_removes_only_tagged_jobs():
    job_a = schedule.every(1).minutes.tag("database_sync").do(dummy_task)
    job_b = schedule.every(2).minutes.tag("database_sync").do(dummy_task)
    job_c = schedule.every(3).minutes.tag("email_report").do(dummy_task)
    job_d = schedule.every(4).minutes.do(dummy_task)

    schedule.clear("database_sync")

    remaining_jobs = schedule.get_jobs()
    assert len(remaining_jobs) == 2
    assert job_c in remaining_jobs
    assert job_d in remaining_jobs
    assert job_a not in remaining_jobs
    assert job_b not in remaining_jobs

def test_get_jobs_returns_all_scheduled_jobs():
    job_1 = schedule.every(1).minutes.do(dummy_task)
    job_2 = schedule.every(5).hours.do(dummy_task)
    job_3 = schedule.every().day.do(dummy_task)

    jobs = schedule.get_jobs()

    assert len(jobs) == 3
    assert job_1 in jobs
    assert job_2 in jobs
    assert job_3 in jobs

def test_get_jobs_with_tag_returns_filtered_list_or_empty():
    job_a = schedule.every(1).minutes.tag("daily_cleanup").do(dummy_task)
    job_b = schedule.every(2).minutes.tag("daily_cleanup").do(dummy_task)
    job_c = schedule.every(3).minutes.tag("metrics").do(dummy_task)

    cleanup_jobs = schedule.get_jobs("daily_cleanup")
    assert len(cleanup_jobs) == 2
    assert job_a in cleanup_jobs
    assert job_b in cleanup_jobs

    empty_jobs = schedule.get_jobs("non_existent_tag_999")
    assert empty_jobs == []

def test_cancel_job_removes_specific_job_instance():
    def my_func():
        pass

    job_1 = schedule.every(1).minutes.do(my_func)
    job_2 = schedule.every(1).minutes.do(my_func)

    schedule.cancel_job(job_1)

    remaining_jobs = schedule.get_jobs()
    assert len(remaining_jobs) == 1
    assert remaining_jobs[0] is job_2


def test_job_returning_canceljob_sentinel_is_removed_after_execution():
    def one_time_task():
        return schedule.CancelJob

    schedule.every(1).seconds.do(one_time_task)

    # Simulating the passage of 1 second to ensure the job is pending
    time.sleep(1.1)
    schedule.run_pending()

    # The job should be permanently removed from the queue
    assert schedule.get_jobs() == []

@pytest.mark.parametrize("interval", [-1, -9999])
def test_every_with_negative_interval_raises_overflow_error(interval):
    with pytest.raises(OverflowError):
        # Validation happens when the job is scheduled via .do()
        schedule.every(interval).days.do(dummy_task)

@pytest.mark.parametrize("interval", ["5", None, []])
def test_every_with_invalid_interval_type_raises_type_error(interval):
    with pytest.raises(TypeError):
        # Validation happens when the job is scheduled via .do()
        schedule.every(interval).days.do(dummy_task)

@pytest.mark.parametrize("time_str", ["25:00", "12:60", "12:30:99", "abc", ""])
def test_job_at_with_malformed_time_string_raises_schedule_value_error(time_str):
    with pytest.raises(schedule.ScheduleValueError):
        schedule.every().day.at(time_str)

@pytest.mark.parametrize("payload", ["my_function", 123, None, []])
def test_job_do_with_non_callable_payload_raises_type_error(payload):
    with pytest.raises(TypeError):
        schedule.every().minute.do(payload)

def test_cancel_job_ignores_double_cancel_or_unregistered_job():
    schedule.clear()

    def dummy_task():
        pass

    # Scenario 1: Valid Job instance already canceled (double-cancellation)
    registered_job = schedule.every().day.do(dummy_task)
    schedule.cancel_job(registered_job)

    # Should NOT raise an error
    schedule.cancel_job(registered_job)
    assert registered_job not in schedule.get_jobs()

    # Scenario 2: Manually instantiated Job object never registered via schedule.every()
    manual_job = schedule.Job(interval=1)

    # Should NOT raise an error
    schedule.cancel_job(manual_job)
    assert manual_job not in schedule.get_jobs()