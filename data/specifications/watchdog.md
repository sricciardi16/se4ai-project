Project: `fs_event_monitor`


## 1. High-Level Goal
Implement a Python library named `fs_event_monitor` that monitors file system directories for changes (creations, modifications, deletions, and moves) and asynchronously dispatches these events to customizable handler classes via a background thread. 

## 2. Module Structure
You must implement the following exact module and submodule structure:
* `fs_event_monitor.events`
* `fs_event_monitor.observers.api`
* `fs_event_monitor.observers`

---

## 3. Module: `fs_event_monitor.events`

This module contains the event payloads and the handler classes that process them.

### Event Classes
Implement the following event classes to represent file system changes. All event objects must possess at least three attributes: `src_path` (string), `event_type` (string), and `is_directory` (boolean).

**`FileCreatedEvent`**
* **Signature:** `__init__(self, src_path)`
* **Behavior:** Must initialize an event object where `event_type` is exactly `"created"`, `is_directory` is `False`, and `src_path` is the provided path.

**`DirModifiedEvent`**
* **Signature:** `__init__(self, src_path)`
* **Behavior:** Must initialize an event object where `event_type` is exactly `"modified"`, `is_directory` is `True`, and `src_path` is the provided path.

*(Note: The observer will dynamically generate other events with types `"deleted"` and `"moved"`. Moved events must additionally possess a `dest_path` string attribute).*

### Handler Classes

**`FileSystemEventHandler`**
Implement this as a base class for handling events.
* **Methods to implement:**
  * `on_any_event(self, event)`: A catch-all hook.
  * `on_created(self, event)`: Hook for creation events.
  * `on_modified(self, event)`: Hook for modification events.
  * `on_deleted(self, event)`: Hook for deletion events.
  * `on_moved(self, event)`: Hook for move/rename events.
  * `dispatch(self, event)`: The core routing method.
* **`dispatch` Behavior:** When called with an event object, it MUST:
  1. Always call `self.on_any_event(event)`.
  2. Dynamically route the event to the specific hook based on `event.event_type`. For example, if `event.event_type == "created"`, it must call `self.on_created(event)`.

**`PatternMatchingEventHandler`**
Implement this as a subclass of `FileSystemEventHandler`.
* **Signature:** `__init__(self, patterns=None, ignore_patterns=None, ignore_directories=False, case_sensitive=False)`
* **Behavior:** Must override the `dispatch(self, event)` method to act as a filter before routing.
* **Filtering Rules (in `dispatch`):**
  1. **Directory Ignore:** If `ignore_directories` is `True` AND `event.is_directory` is `True`, silently discard the event (do not call any `on_*` methods).
  2. **Ignore Patterns:** If `ignore_patterns` is provided, evaluate `event.src_path` against the glob patterns in the list. If it matches *any* ignore pattern, silently discard the event.
  3. **Inclusion Patterns:** If `patterns` is provided, evaluate `event.src_path` against the glob patterns. If it does *not* match at least one pattern, silently discard the event.
  4. **Case Sensitivity:** All glob pattern matching (both inclusion and exclusion) must strictly obey the `case_sensitive` flag. If `True`, matching is strictly case-sensitive. If `False`, matching must be case-insensitive.
  5. **Pass-through:** If the event survives all the above filters, pass it to the parent class's `dispatch` method to trigger the standard hooks.

---

## 4. Module: `fs_event_monitor.observers.api`

**`ObservedWatch`**
Implement a simple data class/object to represent a scheduled watch operation.
* **Attributes:**
  * `path` (string): The directory path being watched.
  * `is_recursive` (boolean): Whether the watch includes subdirectories.
* **Behavior:** Instances of this class are returned by the Observer's `schedule` method.

---

## 5. Module: `fs_event_monitor.observers`

**`Observer`**
Implement the core engine that monitors the file system in a background thread.

* **Signature:** `__init__(self)`
  * Must support default instantiation with no arguments.

* **Method:** `schedule(self, event_handler, path, recursive=False)`
  * **Arguments:** An instance of a handler, a string `path`, and a boolean `recursive` flag.
  * **Behavior:** Registers the path to be monitored. 
  * **Returns:** Must return an instance of `ObservedWatch` populated with the provided `path` and `recursive` flag.
  * **Rule:** Do *not* raise an error or exception if the provided `path` does not exist at the time `schedule` is called.

* **Method:** `start(self)`
  * **Behavior:** Spawns and starts a background thread to begin monitoring the scheduled paths.
  * **Rule:** This method must be non-blocking and return execution to the main thread in less than 0.1 seconds.

* **Method:** `is_alive(self)`
  * **Returns:** `True` if the background monitoring thread is currently running, `False` otherwise.

* **Method:** `stop(self)`
  * **Behavior:** Signals the background thread to terminate cleanly.

* **Method:** `join(self, timeout=None)`
  * **Behavior:** Blocks the calling thread until the background monitoring thread has completely terminated.

### File System Monitoring Rules (Background Thread)
Once `start()` is called, the background thread must monitor the OS file system and adhere to the following strict rules:

1. **Recursion:** If a path was scheduled with `recursive=True`, the observer must detect events in the target directory and all nested subdirectories. If `recursive=False`, it must completely ignore events in subdirectories.
2. **Event Dispatching:** When a file system change occurs, construct the appropriate event object and pass it to the `dispatch(event)` method of the `event_handler` associated with that path.
3. **Chronological Ordering:** Events must be dispatched in the exact chronological order they occurred (e.g., a file creation must be dispatched before its subsequent modification).
4. **Path Formatting:** Every event dispatched by the observer MUST have its `src_path` (and `dest_path` if applicable) formatted as an **absolute path** (`os.path.isabs` must be True) and **normalized** (`os.path.normpath`).
5. **Event Types to Detect:**
   * **Creation:** When a file or directory is created, dispatch an event with `event_type="created"`. Set `is_directory` appropriately.
   * **Modification:** When a file is modified, dispatch an event with `event_type="modified"`. Set `is_directory=False`.
   * **Deletion:** When a file or directory is deleted, dispatch an event with `event_type="deleted"`. Set `is_directory` appropriately.
   * **Move/Rename:** When a file is renamed, dispatch an event with `event_type="moved"`. This event MUST include a `dest_path` attribute containing the absolute, normalized new path. *(Fallback Rule: If the underlying OS/environment does not support atomic move detection, it is acceptable to emit a "deleted" event for the old path followed by a "created" event for the new path).*
6. **Empty Schedules:** The background thread must start, run, and terminate cleanly even if `schedule()` was never called (an empty watch list).