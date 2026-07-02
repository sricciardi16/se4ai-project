Project: `task_scheduler`


## 1. High-Level Goal
Implement a lightweight, in-process Python task scheduling library named `task_scheduler`. The library must provide a global scheduler and a fluent, chainable API to schedule callable tasks (jobs) to execute at specific intervals, times, or days. 

## 2. Module Structure & Public Constants
Create a module named `task_scheduler`. Expose the following public constants and attributes at the module level:

*   **`jobs`**: A public list that stores all currently registered `Job` instances.
*   **`CancelJob`**: A sentinel object (or class) used to signal that a job should be permanently removed from the scheduler.
*   **`ScheduleValueError`**: A custom Exception class inheriting from `ValueError`, raised when invalid time strings are provided.

## 3. Global API Functions
Implement the following module-level functions. These functions operate on the global `jobs` list.

*   **`every(interval=1)`**: 
    *   Instantiate and return a new `Job` object with the specified `interval`. 
    *   *Note:* Do not add the job to the global `jobs` list yet. Registration happens later.
*   **`get_jobs(tag=None)`**: 
    *   Return a list of all registered `Job` instances. 
    *   If `tag` is provided (a string), return only the jobs that have that specific tag in their tags collection.
*   **`clear(tag=None)`**: 
    *   If no `tag` is provided, empty the global `jobs` list completely. 
    *   If a `tag` is provided, remove only the jobs that contain that specific tag.
*   **`cancel_job(job)`**: 
    *   Remove the exact `job` instance (by object identity) from the global `jobs` list. 
    *   If the job is not in the list (e.g., already canceled or never registered), return safely without raising an error.
*   **`run_pending()`**: 
    *   Iterate through all registered jobs. 
    *   If a job's `next_run` datetime is less than or equal to the current system time, execute it synchronously. 
    *   If no jobs are due, return `None` safely.
*   **`run_all(delay_seconds=0)`**: 
    *   Execute all registered jobs immediately, regardless of their `next_run` value. 
    *   Accept a `delay_seconds` argument (default `0`) which dictates a pause between job executions.
*   **`idle_seconds()`**: 
    *   Calculate and return the number of seconds (as an `int` or `float` > 0) until the earliest `next_run` among all registered jobs.
*   **`repeat(job_builder)`**: 
    *   Implement a decorator that takes an unregistered `Job` instance (e.g., `task_scheduler.every().seconds`). 
    *   When applied to a function, it must automatically call `.do()` on the `job_builder` with the decorated function, registering it to the scheduler, and then return the original function unmodified.

## 4. The `Job` Class (Fluent API)
Implement a `Job` class. This class must support method chaining (returning `self` from configuration methods).

### 4.1. Attributes
Every `Job` instance must expose the following public attributes:
*   `interval`: The integer interval provided during instantiation.
*   `latest`: An integer representing the upper bound for randomized intervals (default to the same as `interval`).
*   `tags`: A `set` or `list` of string tags assigned to the job.
*   `next_run`: A `datetime.datetime` object representing the exact next scheduled execution time.
*   `last_run`: A `datetime.datetime` object representing the last execution time (initialize as `None`).

### 4.2. Time Unit Modifiers (Properties/Methods)
Implement the following properties or methods that set the time unit for the job and return `self`. 
*   **Singular units:** `second`, `minute`, `hour`, `day`, `week`, `monday` (and implicitly other weekdays, where Monday corresponds to `datetime.weekday() == 0`).
*   **Plural units:** `seconds`, `minutes`, `hours`, `days`, `weeks`.
*   *Rule:* If multiple units are chained (e.g., `.seconds.minutes`), the latest unit called overwrites the previous one.

### 4.3. Configuration Methods
Implement the following chainable methods:

*   **`tag(*tags)`**: 
    *   Accept multiple string arguments. Add all provided strings to the job's `tags` collection.
*   **`to(latest)`**: 
    *   Accept an integer. Update the job's `latest` attribute. 
    *   *Rule:* When calculating the next run time, the job must randomize its actual interval duration between `interval` and `latest`.
*   **`until(deadline)`**: 
    *   Accept a deadline (must support `datetime.timedelta`). 
    *   *Rule:* If the current time strictly exceeds this deadline, the job must not execute and must automatically and permanently remove itself from the global scheduler.
*   **`at(time_str)`**: 
    *   Accept a string representing a specific time or offset.
    *   *Validation:* If the string is malformed (e.g., `"25:00"`, `"12:60"`, `"12:30:99"`, `"abc"`, `""`), raise a `task_scheduler.ScheduleValueError`.
    *   *Time Parsing:* Must parse `"HH:MM"` and `"HH:MM:SS"`.
    *   *Offset Parsing:* Must parse `":MM"` (for hourly jobs, setting the minute) and `":SS"` (for minute jobs, setting the second).
    *   *Next Run Logic:* 
        *   If scheduling a daily job at `"14:30:00"` and the current time is `"10:00:00"`, `next_run` is today. If current time is `"15:00:00"`, `next_run` is tomorrow.
        *   If scheduling an hourly job at `":45"`, `next_run` is exactly 45 minutes past the *current* hour.
        *   If scheduling an hourly job at `":00"` and the current time is exactly the top of the hour (e.g., `"10:00:00"`), `next_run` must be the *next* hour (`"11:00:00"`).

### 4.4. The `.do()` Method (Registration & Validation)
Implement the `do(func, *args, **kwargs)` method. This is the terminal method of the chain.

*   **Validation Rules:**
    *   If `func` is not callable, raise a `TypeError`.
    *   If the job's `interval` is not an integer or float (e.g., string, `None`, list), raise a `TypeError`.
    *   If the job's `interval` is negative (e.g., `-1`), raise an `OverflowError`.
*   **Registration:**
    *   Store the target `func`, `*args`, and `**kwargs` on the job.
    *   Calculate and set the initial `next_run` `datetime.datetime`.
    *   Append the `Job` instance to the global `task_scheduler.jobs` list.
    *   Return the `Job` instance.

### 4.5. Execution Logic
When a job is executed (via `run_pending` or `run_all`):
1.  Pass the exact `*args` and `**kwargs` to the target function without mutation or omission.
2.  Update the job's `last_run` attribute to the current `datetime.datetime`.
3.  Advance the `next_run` attribute by the exact interval duration (or the randomized duration if `.to()` was used).
4.  **Sentinel Check:** If the target function returns the `task_scheduler.CancelJob` sentinel, immediately and permanently remove the job from the global scheduler.