# 1. Testing Framework & Mocking
import pytest

# 2. The Subject Under Test
from fs_event_monitor.events import DirModifiedEvent, FileCreatedEvent, FileSystemEventHandler, PatternMatchingEventHandler
from fs_event_monitor.observers import Observer
from fs_event_monitor.observers.api import ObservedWatch

# 4. Auxiliary: Standard Library
import os
import time
from pathlib import Path


class LifecycleRecordingEventHandler(FileSystemEventHandler):
    """
    A custom event handler that records file system events for black-box testing.
    """
    def __init__(self):
        super().__init__()
        self.created_events = []
        self.modified_events = []
        self.deleted_events = []

    def on_created(self, event):
        self.created_events.append(event)

    def on_modified(self, event):
        self.modified_events.append(event)

    def on_deleted(self, event):
        self.deleted_events.append(event)

def wait_for_event(event_list, target_path, timeout=5.0):
    """
    Helper function to poll for an event matching the target path.
    File system events are asynchronous, so we must wait for them to be dispatched.
    """
    start_time = time.time()
    while time.time() - start_time < timeout:
        # Copy the list to avoid RuntimeError if it's modified during iteration
        for event in list(event_list):
            if Path(event.src_path) == target_path:
                return event
        time.sleep(0.05)
    return None

def test_observer_lifecycle_terminates_cleanly():
    observer = Observer()

    observer.start()
    assert observer.is_alive() is True

    observer.stop()
    observer.join()
    assert observer.is_alive() is False

def test_observed_watch_is_recursive_attribute(tmp_path):
    observer = Observer()
    handler = FileSystemEventHandler()

    watch = observer.schedule(handler, str(tmp_path), recursive=True)

    assert Path(watch.path) == tmp_path

    assert watch.is_recursive is True
    


def test_observer_dispatches_file_created_event(tmp_path):
    observer = Observer()
    handler = LifecycleRecordingEventHandler()
    observer.schedule(handler, str(tmp_path), recursive=False)
    observer.start()

    try:
        target_file = tmp_path / "a.txt"
        target_file.write_text("hello")

        event = wait_for_event(handler.created_events, target_file)

        assert event is not None, "Creation event was not dispatched"
        assert Path(event.src_path) == target_file
    finally:
        observer.stop()
        observer.join()

def test_observer_dispatches_file_modified_event(tmp_path):
    observer = Observer()
    handler = LifecycleRecordingEventHandler()
    observer.schedule(handler, str(tmp_path), recursive=False)
    observer.start()

    try:
        target_file = tmp_path / "b.txt"

        # Write initial content and wait for creation
        target_file.write_text("v1")
        created_event = wait_for_event(handler.created_events, target_file)
        assert created_event is not None, "Initial creation event was not dispatched"

        # Clear any modification events that might have triggered during the initial write
        handler.modified_events.clear()

        # Write new content to trigger modification
        target_file.write_text("v2")

        modified_event = wait_for_event(handler.modified_events, target_file)

        assert modified_event is not None, "Modification event was not dispatched"
        assert Path(modified_event.src_path) == target_file
    finally:
        observer.stop()
        observer.join()

def test_observer_dispatches_file_deleted_event(tmp_path):
    observer = Observer()
    handler = LifecycleRecordingEventHandler()

    # Create file and ensure it exists before watching
    target_file = tmp_path / "c.txt"
    target_file.write_text("to be deleted")
    assert target_file.exists() is True

    observer.schedule(handler, str(tmp_path), recursive=False)
    observer.start()

    try:
        # Give the observer a moment to initialize its OS-level watches
        time.sleep(0.5)

        # Delete the file
        target_file.unlink()

        event = wait_for_event(handler.deleted_events, target_file)

        assert event is not None, "Deletion event was not dispatched"
        assert Path(event.src_path) == target_file
    finally:
        observer.stop()
        observer.join()

class MovementRecordingEventHandler(FileSystemEventHandler):
    """A simple handler that records specific events for assertions."""
    def __init__(self):
        super().__init__()
        self.moved_events = []
        self.created_events = []
        self.deleted_events = []

    def on_moved(self, event):
        self.moved_events.append(event)

    def on_created(self, event):
        self.created_events.append(event)

    def on_deleted(self, event):
        self.deleted_events.append(event)

class RecordingPatternHandler(PatternMatchingEventHandler):
    """A pattern matching handler that records all events that pass the filter."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.events = []

    def on_any_event(self, event):
        self.events.append(event)

@pytest.fixture
def observer():
    """Fixture to manage the lifecycle of the Watchdog Observer."""
    obs = Observer()
    yield obs
    obs.stop()
    try:
        obs.join()
    except RuntimeError:
        pass

def test_observer_detects_file_move_operation(tmp_path, observer):
    handler = MovementRecordingEventHandler()
    old_file = tmp_path / "old.txt"
    new_file = tmp_path / "new.txt"

    # Setup initial state
    old_file.write_text("content")

    observer.schedule(handler, str(tmp_path), recursive=False)
    observer.start()
    time.sleep(0.2)  # Allow observer thread to initialize

    # Perform the move
    old_file.rename(new_file)
    time.sleep(0.5)  # Allow observer to process the filesystem event

    # Check for strict on_moved event
    moved = [
        e for e in handler.moved_events
        if e.src_path.endswith("old.txt") and e.dest_path.endswith("new.txt")
    ]

    if not moved:
        # Fallback for OS-level edge cases (e.g., some Windows/Linux configurations)
        # where a move is emitted as a deletion of the old file and creation of the new file.
        deleted = [e for e in handler.deleted_events if e.src_path.endswith("old.txt")]
        created = [e for e in handler.created_events if e.src_path.endswith("new.txt")]
        assert deleted and created, (
            "Neither on_moved nor sequential (on_deleted + on_created) events "
            "were dispatched for the file move."
        )

def test_observer_dispatches_directory_created_event(tmp_path, observer):
    handler = MovementRecordingEventHandler()
    subdir = tmp_path / "subdir"

    observer.schedule(handler, str(tmp_path), recursive=False)
    observer.start()
    time.sleep(0.2)

    # Perform directory creation
    subdir.mkdir()
    time.sleep(0.5)

    created = [
        e for e in handler.created_events
        if e.src_path.endswith("subdir") and e.is_directory
    ]
    assert created, "Directory creation event (on_created) was not dispatched."

def test_observer_dispatches_directory_deleted_event(tmp_path, observer):
    handler = MovementRecordingEventHandler()
    gone_dir = tmp_path / "gone"
    gone_dir.mkdir()

    observer.schedule(handler, str(tmp_path), recursive=False)
    observer.start()
    time.sleep(0.2)

    # Perform directory deletion
    gone_dir.rmdir()
    time.sleep(0.5)

    deleted = [
        e for e in handler.deleted_events
        if e.src_path.endswith("gone") and e.is_directory
    ]
    assert deleted, "Directory deletion event (on_deleted) was not dispatched."

def test_observer_recursive_schedule_detects_nested_events(tmp_path, observer):
    handler = MovementRecordingEventHandler()
    nested_dir = tmp_path / "nested"
    deep_file = nested_dir / "deep.txt"

    # Schedule with recursive=True
    observer.schedule(handler, str(tmp_path), recursive=True)
    observer.start()
    time.sleep(0.2)

    # Create nested structure
    nested_dir.mkdir()
    time.sleep(0.2)  # Brief pause to ensure directory is registered
    deep_file.write_text("deep content")
    time.sleep(0.5)

    created = [
        e for e in handler.created_events
        if e.src_path.endswith("deep.txt") and not e.is_directory
    ]
    assert created, "Nested file creation event was not detected with recursive=True."

def test_pattern_matching_handler_filters_events_by_glob(tmp_path, observer):
    patterns = ["*.log", "**/*.log", "**\\*.log", "*/*.log", "*\\*.log"]
    handler = RecordingPatternHandler(
        patterns=patterns,
        ignore_directories=True
    )

    observer.schedule(handler, str(tmp_path), recursive=True)
    observer.start()
    time.sleep(0.2)

    a_log = tmp_path / "a.log"
    b_txt = tmp_path / "b.txt"

    # Create both matching and non-matching files
    a_log.write_text("log content")
    b_txt.write_text("txt content")
    time.sleep(0.5)

    # Verify a.log triggered the handler
    a_events = [e for e in handler.events if e.src_path.endswith("a.log")]
    assert a_events, "Matching file 'a.log' did not trigger the PatternMatchingEventHandler."

    # Verify b.txt was completely ignored
    b_events = [e for e in handler.events if e.src_path.endswith("b.txt")]
    assert not b_events, "Non-matching file 'b.txt' incorrectly triggered the PatternMatchingEventHandler."

def test_handler_on_any_event_receives_valid_event_type(tmp_path):
    class CatchAllHandler(FileSystemEventHandler):
        def __init__(self):
            super().__init__()
            self.captured_events = []

        def on_any_event(self, event):
            self.captured_events.append(event)

    handler = CatchAllHandler()
    observer = Observer()
    observer.schedule(handler, str(tmp_path), recursive=False)
    observer.start()

    try:
        # Crucial Data: Create a file named any.txt
        test_file = tmp_path / "any.txt"
        test_file.touch()

        # Allow a brief moment for the asynchronous file system event to be dispatched
        time.sleep(0.5)
    finally:
        observer.stop()
        observer.join()

    assert len(handler.captured_events) > 0, "No events were captured by on_any_event."

    # Verify the catch-all method receives an event object with the correct string identifier
    event_types = [event.event_type for event in handler.captured_events]
    assert "created" in event_types, f"Expected 'created' event, but got: {event_types}"

    for event in handler.captured_events:
        assert isinstance(event.event_type, str)

def test_observer_default_instantiation():
    # Crucial Data: Default instantiation (no arguments passed)
    observer = Observer()
    assert isinstance(observer, Observer)

def test_observer_lifecycle_empty_schedule_terminates_cleanly():
    observer = Observer()

    # Crucial Data: Thread lifecycle specifically when *no* paths have been scheduled
    observer.start()
    observer.stop()
    observer.join(timeout=5.0) # Timeout ensures the test doesn't hang indefinitely if it fails

    assert not observer.is_alive()

def test_schedule_valid_path_returns_observed_watch(tmp_path):
    observer = Observer()
    handler = FileSystemEventHandler()

    # Crucial Data: Dynamically generated, guaranteed-empty temporary directory path
    # tmp_path is provided by pytest and guaranteed to be empty and unique
    watch = observer.schedule(handler, str(tmp_path))

    assert isinstance(watch, ObservedWatch)
def test_schedule_nonexistent_path_does_not_raise_error_before_start():
    observer = Observer()
    handler = FileSystemEventHandler()

    # Crucial Data: Strictly hardcoded, guaranteed non-existent absolute path
    bad_path = "/tmp/this_directory_absolutely_does_not_exist_9999_xyz"

    watch = observer.schedule(handler, bad_path)
    
    assert isinstance(watch, ObservedWatch)
    assert watch.path == bad_path

class TupleRecordingEventHandler(FileSystemEventHandler):
    """A black-box event handler to record public event dispatches."""
    def __init__(self):
        super().__init__()
        self.events = []

    def on_created(self, event):
        if not event.is_directory:
            self.events.append(('created', str(Path(event.src_path))))

    def on_modified(self, event):
        if not event.is_directory:
            self.events.append(('modified', str(Path(event.src_path))))

    def on_deleted(self, event):
        if not event.is_directory:
            self.events.append(('deleted', str(Path(event.src_path))))


def test_schedule_recursive_flag_controls_subdirectory_event_dispatch(tmp_path):
    parent_dir = tmp_path / "parent_dir"
    child_dir = parent_dir / "child_dir"
    grandchild_dir = child_dir / "grandchild_dir"
    grandchild_dir.mkdir(parents=True)

    trigger_file = grandchild_dir / "trigger_file.txt"

    # 1. Test recursive=False (Must be completely ignored)
    handler_false = TupleRecordingEventHandler()
    obs_false = Observer()
    obs_false.schedule(handler_false, str(parent_dir), recursive=False)
    obs_false.start()
    try:
        trigger_file.touch()
        time.sleep(0.5)  # Allow time for potential event dispatch
    finally:
        obs_false.stop()
        obs_false.join(timeout=5.0)

    # Handler state must be unmodified
    assert len(handler_false.events) == 0

    trigger_file.unlink()  # Clean up for the next phase

    # 2. Test recursive=True (Must trigger on_created)
    handler_true = TupleRecordingEventHandler()
    obs_true = Observer()
    obs_true.schedule(handler_true, str(parent_dir), recursive=True)
    obs_true.start()
    try:
        trigger_file.touch()
        time.sleep(0.5)  # Allow time for event dispatch
    finally:
        obs_true.stop()
        obs_true.join(timeout=5.0)

    # Handler must have recorded the creation
    assert any(e[0] == 'created' and e[1] == str(trigger_file) for e in handler_true.events)


def test_start_observer_executes_in_background_without_blocking_main_thread(tmp_path):
    observer = Observer()
    handler = FileSystemEventHandler()
    observer.schedule(handler, str(tmp_path), recursive=False)

    start_time = time.perf_counter()
    observer.start()
    execution_duration = time.perf_counter() - start_time

    try:
        # Strict execution time assertion
        assert execution_duration < 0.1
        # Must evaluate to True
        assert observer.is_alive() is True
    finally:
        observer.stop()
        observer.join(timeout=5.0)


def test_stop_observer_terminates_background_thread_cleanly(tmp_path):
    observer = Observer()
    handler = FileSystemEventHandler()
    observer.schedule(handler, str(tmp_path), recursive=False)

    observer.start()
    # Running for exactly 0.5 seconds
    time.sleep(0.5)

    observer.stop()

    # Polling loop to verify is_alive() == False within a max timeout of 2.0 seconds
    timeout = 2.0
    start_poll = time.perf_counter()
    thread_terminated = False

    while time.perf_counter() - start_poll < timeout:
        if not observer.is_alive():
            thread_terminated = True
            break
        time.sleep(0.05)  # Brief yield

    assert thread_terminated is True
    observer.join(timeout=5.0)  # Ensure cleanup


def test_observer_join_blocks_until_thread_termination(tmp_path):
    observer = Observer()
    handler = FileSystemEventHandler()
    observer.schedule(handler, str(tmp_path), recursive=False)

    observer.start()
    time.sleep(0.1)
    observer.stop()

    # Strict timeout to the join call
    observer.join(timeout=5.0)

    # Verify background monitoring thread has completely terminated
    assert observer.is_alive() is False


def test_file_lifecycle_chronological_event_ordering(tmp_path):
    handler = TupleRecordingEventHandler()
    observer = Observer()
    observer.schedule(handler, str(tmp_path), recursive=False)
    observer.start()

    # Filename with spaces and non-ASCII characters
    target_file = tmp_path / "test_data_📝_v1.txt"
    target_path_str = str(target_file)

    try:
        # 1. Create and write initial data
        with open(target_file, "w", encoding="utf-8") as f:
            f.write("initial")
        time.sleep(0.5)  # Allow OS to flush and watchdog to process

        # 2. Modify (actual byte-size change)
        with open(target_file, "a", encoding="utf-8") as f:
            f.write(" update")
        time.sleep(0.5)

        # 3. Delete
        target_file.unlink()
        time.sleep(0.5)

    finally:
        observer.stop()
        observer.join(timeout=5.0)

    # Filter events specifically for our target file
    file_events = [e[0] for e in handler.events if e[1] == target_path_str]

    # OS file systems often emit multiple 'modified' events for a single write operation.
    # We deduplicate consecutive identical events to verify the chronological phase transitions.
    chronological_phases = []
    for event_type in file_events:
        if not chronological_phases or chronological_phases[-1] != event_type:
            chronological_phases.append(event_type)

    # Verify the exact chronological order: created -> modified -> deleted
    assert "created" in chronological_phases
    assert "modified" in chronological_phases
    assert "deleted" in chronological_phases

    idx_created = chronological_phases.index("created")
    idx_modified = chronological_phases.index("modified", idx_created)
    idx_deleted = chronological_phases.index("deleted", idx_modified)

    assert idx_created < idx_modified < idx_deleted

def test_file_rename_triggers_moved_event_with_paired_paths(tmp_path):
    class CaptureMovedHandler(FileSystemEventHandler):
        def __init__(self):
            self.moved_events = []

        def on_moved(self, event):
            self.moved_events.append(event)

    handler = CaptureMovedHandler()
    observer = Observer()

    # Schedule with an absolute path as required by the crucial data
    abs_watch_path = str(tmp_path.resolve())
    observer.schedule(handler, abs_watch_path, recursive=False)
    observer.start()

    try:
        src_file = tmp_path / "old_name_archive.log"
        dest_file = tmp_path / "new_name_archive_2023.log"

        # Create the initial file
        src_file.touch()

        # Allow the file system to settle so the creation event doesn't overlap
        time.sleep(0.5)

        # Trigger the rename (move) event
        src_file.rename(dest_file)

        # Poll for the moved event to handle async OS event delivery
        event = None
        for _ in range(20):
            event = next((e for e in handler.moved_events if e.src_path.endswith("old_name_archive.log")), None)
            if event:
                break
            time.sleep(0.1)

        assert event is not None, "The on_moved event was not triggered."

        # Assert crucial data: exact original and new paths
        assert os.path.normpath(event.src_path) == os.path.normpath(str(src_file.resolve()))
        assert os.path.normpath(event.dest_path) == os.path.normpath(str(dest_file.resolve()))

        # Assert crucial data: both paths resolve to absolute paths
        assert os.path.isabs(event.src_path)
        assert os.path.isabs(event.dest_path)

    finally:
        observer.stop()
        observer.join()


def test_directory_creation_event_metadata(tmp_path):
    class CaptureCreatedHandler(FileSystemEventHandler):
        def __init__(self):
            self.created_events = []

        def on_created(self, event):
            self.created_events.append(event)

    handler = CaptureCreatedHandler()
    observer = Observer()
    observer.schedule(handler, str(tmp_path.resolve()), recursive=False)
    observer.start()

    try:
        # Target creation: A directory named nested_dir_structure
        target_dir = tmp_path / "nested_dir_structure"
        target_dir.mkdir()

        # Poll for the created event
        event = None
        for _ in range(20):
            event = next((e for e in handler.created_events if e.src_path.endswith("nested_dir_structure")), None)
            if event:
                break
            time.sleep(0.1)

        assert event is not None, "The directory creation event was not intercepted."

        # Assert crucial data: standardized metadata
        assert os.path.normpath(event.src_path) == os.path.normpath(str(target_dir.resolve()))
        assert event.event_type == 'created'
        assert event.is_directory is True

    finally:
        observer.stop()
        observer.join()


def test_inclusion_patterns_filter_non_matching_events():
    class PatternCaptureHandler(PatternMatchingEventHandler):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.captured_paths = []

        def on_created(self, event):
            self.captured_paths.append(event.src_path)

    # Crucial Data: Specific inclusion patterns
    handler = PatternCaptureHandler(patterns=["*.csv", "data_*.json"])

    trigger_files = ["report.csv", "data_2023.json"]
    ignored_files = ["report.txt", "data_2023.xml", "csv_backup.bak"]

    # Dispatch events for all files
    for filename in trigger_files + ignored_files:
        # Using FileCreatedEvent as the idiomatic way to generate a creation event in 3.0
        event = FileCreatedEvent(f"/mock/dir/{filename}")
        handler.dispatch(event)

    # Assert that only the trigger files were captured
    assert len(handler.captured_paths) == 2

    captured_filenames = [os.path.basename(p) for p in handler.captured_paths]
    for trigger in trigger_files:
        assert trigger in captured_filenames

    for ignored in ignored_files:
        assert ignored not in captured_filenames


def test_dispatch_event_matching_ignore_pattern_silently_discards_event():
    class DiscardCheckHandler(PatternMatchingEventHandler):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.was_called = False

        def on_any_event(self, event):
            self.was_called = True

        def on_created(self, event):
            self.was_called = True

    # Crucial Data: Overlapping patterns and ignore_patterns
    handler = DiscardCheckHandler(
        patterns=["*.log"],
        ignore_patterns=["*debug*.log"]
    )

    # Crucial Data: Trigger Event matching both
    # FileCreatedEvent inherently sets event_type="created" and is_directory=False
    event = FileCreatedEvent("/var/app/system_debug_v2.log")

    # Verify the event payload matches the exact specification before dispatching
    assert event.event_type == "created"
    assert event.is_directory is False
    assert event.src_path == "/var/app/system_debug_v2.log"

    handler.dispatch(event)

    # Assert the event was silently discarded and no underlying methods were invoked
    assert handler.was_called is False


def test_dispatch_directory_event_with_ignore_directories_true_silently_discards_event():
    class DirDiscardCheckHandler(PatternMatchingEventHandler):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.was_called = False

        def on_any_event(self, event):
            self.was_called = True

        def on_modified(self, event):
            self.was_called = True

    # Crucial Data: ignore_directories=True and catch-all inclusion pattern
    handler = DirDiscardCheckHandler(
        patterns=["*"],
        ignore_directories=True
    )

    # Crucial Data: Trigger Event with is_directory=True and a .txt extension
    # DirModifiedEvent inherently sets event_type="modified" and is_directory=True
    event = DirModifiedEvent("/home/user/Documents/NewFolder.txt")

    # Verify the event payload matches the exact specification before dispatching
    assert event.event_type == "modified"
    assert event.is_directory is True
    assert event.src_path == "/home/user/Documents/NewFolder.txt"

    handler.dispatch(event)

    # Assert the event was silently discarded despite matching the inclusion pattern
    assert handler.was_called is False

class StrictPatternRecordingEventHandler(PatternMatchingEventHandler):
    """
    A custom handler to record dispatched events for assertions,
    adhering to black-box testing principles by only using public hooks.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.received_events = []

    def on_created(self, event):
        self.received_events.append(event)


def test_dispatch_event_with_strict_case_sensitivity_rejects_case_mismatch():

    # Crucial Data: Trigger Event
    target_src_path = "/api/responses/data_payload.json"
    event = FileCreatedEvent(src_path=target_src_path)

    # Crucial Data: patterns=["*.JSON"]
    target_patterns = ["*.JSON"]

    # 1. Test case_sensitive=True (Must silently discard the event)
    strict_handler = StrictPatternRecordingEventHandler(
        patterns=target_patterns,
        case_sensitive=True
    )
    strict_handler.dispatch(event)

    assert len(strict_handler.received_events) == 0, \
        "Handler initialized with case_sensitive=True should have discarded the case-mismatched event."

    # 2. Test case_sensitive=False (Must successfully trigger the handler method)
    loose_handler = StrictPatternRecordingEventHandler(
        patterns=target_patterns,
        case_sensitive=False
    )
    loose_handler.dispatch(event)

    assert len(loose_handler.received_events) == 1, \
        "Handler initialized with case_sensitive=False should have successfully dispatched the event."
    assert loose_handler.received_events[0] is event, \
        "The dispatched event payload does not match the triggered event."
