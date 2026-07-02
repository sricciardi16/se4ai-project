# 1. Testing Framework & Mocking
import pytest

# 2. The Subject Under Test
from flexilog import logger

# 4. Auxiliary: Standard Library
import io
from io import StringIO
import json
import os
import re
import shutil
import sys
import threading


@pytest.fixture(autouse=True)
def reset_logger():
    """
    Fixture to ensure a clean logger state for each test.
    Loguru's logger is global, so we remove all handlers before and after tests.
    """
    logger.remove()
    yield
    logger.remove()

def test_logger_emits_formatted_strings_for_standard_levels():
    messages = []
    # Loguru appends a newline to the formatted message by default
    logger.add(lambda m: messages.append(str(m)), format="{level}:{message}")

    logger.debug("debug message")
    logger.info("info message")
    logger.warning("warning message")

    assert messages == [
        "DEBUG:debug message\n",
        "INFO:info message\n",
        "WARNING:warning message\n"
    ]

def test_logger_suppresses_records_below_configured_sink_level():
    messages = []
    logger.add(lambda m: messages.append(str(m)), level="INFO", format="{level}:{message}")

    logger.debug("this debug message should be ignored")
    logger.info("this info message should be written")

    assert len(messages) == 1
    assert messages[0] == "INFO:this info message should be written\n"

def test_log_method_emits_record_using_string_level_name():
    messages = []
    logger.add(lambda m: messages.append(str(m)), format="{level}:{message}")

    logger.log("INFO", "generic info message")
    logger.log("WARNING", "generic warning message")

    assert messages == [
        "INFO:generic info message\n",
        "WARNING:generic warning message\n"
    ]

def test_bind_injects_kwargs_into_record_extra_dict():
    messages = []
    logger.add(lambda m: messages.append(str(m)), format="{extra[user]}:{message}")

    bound_logger = logger.bind(user="alice")
    bound_logger.info("bound message")

    assert len(messages) == 1
    assert messages[0] == "alice:bound message\n"

def test_contextualize_injects_kwargs_during_context_block():
    messages = []
    logger.add(lambda m: messages.append(str(m)), format="{extra[user]}:{message}")

    with logger.contextualize(user="bob"):
        logger.info("contextualized message")

    assert len(messages) == 1
    assert messages[0] == "bob:contextualized message\n"

def test_logger_routes_single_emission_to_multiple_sinks():
    # Clear default handlers to ensure test isolation
    logger.remove()

    sink1 = StringIO()
    sink2 = StringIO()

    logger.add(sink1, format="{message}")
    logger.add(sink2, format="{message}")

    logger.info("Broadcast message")

    assert sink1.getvalue().strip() == "Broadcast message"
    assert sink2.getvalue().strip() == "Broadcast message"


def test_add_creates_file_and_writes_formatted_logs(tmp_path):
    logger.remove()

    log_file = tmp_path / "test_logs.log"
    logger.add(log_file, format="{message}")

    logger.info("First line")
    logger.info("Second line")
    logger.info("Third line")

    with open(log_file, "r") as f:
        lines = f.read().splitlines()

    assert len(lines) == 3
    assert lines[0] == "First line"
    assert lines[1] == "Second line"
    assert lines[2] == "Third line"


def test_serialize_true_emits_json_encoded_record():
    logger.remove()

    sink = StringIO()
    logger.add(sink, serialize=True)

    logger.info("JSON test message")

    output = sink.getvalue().strip()
    parsed_log = json.loads(output)

    assert "record" in parsed_log
    assert parsed_log["record"]["message"] == "JSON test message"
    assert parsed_log["record"]["level"]["name"] == "INFO"


def test_patch_modifies_record_dict_in_place_before_emission():
    logger.remove()

    sink = StringIO()
    logger.add(sink, format="{extra[dynamic_key]} | {message}")

    # Patch returns a new logger instance with the mutation applied
    patched_logger = logger.patch(lambda record: record["extra"].update({"dynamic_key": "InjectedValue"}))
    patched_logger.info("Patched message")

    assert sink.getvalue().strip() == "InjectedValue | Patched message"


def test_filter_callable_suppresses_records_evaluating_to_false():
    logger.remove()

    sink = StringIO()

    def info_only_filter(record):
        return record["level"].name == "INFO"

    logger.add(sink, filter=info_only_filter, format="{message}")

    logger.debug("Debug message - should be suppressed")
    logger.info("Info message - should be emitted")
    logger.warning("Warning message - should be suppressed")

    output = sink.getvalue().strip()

    # Only the INFO log should be present in the sink
    assert output == "Info message - should be emitted"

def test_add_without_format_uses_default_timestamp_and_level_format():
    sink = io.StringIO()
    handler_id = logger.add(sink)
    try:
        logger.info("default format test")
        output = sink.getvalue()

        assert "INFO" in output
        assert "default format test" in output
        assert re.search(r"\d", output) is not None
    finally:
        logger.remove(handler_id)

def test_logger_info_processes_standard_string_message():
    # Invoking the method with a standard string to ensure no hard crash occurs
    logger.info("robustness smoke log")

def test_logger_add_and_remove_handles_duplicate_sinks_with_unique_ids():
    id1 = logger.add(sys.stderr)
    id2 = logger.add(sys.stderr)
    id3 = logger.add(sys.stderr)

    assert isinstance(id1, int)
    assert isinstance(id2, int)
    assert isinstance(id3, int)

    # Ensure all returned IDs are strictly unique
    assert len({id1, id2, id3}) == 3

    # Remove them sequentially without crashing
    logger.remove(id1)
    logger.remove(id2)
    logger.remove(id3)

def test_import_logger_emits_to_default_destination_without_setup(capsys):
    # The autouse fixture removes the default handler. 
    # We simulate the out-of-the-box state by re-adding sys.stderr.
    logger.add(sys.stderr)
    
    logger.info("Out-of-the-box initialization test: \u2713")

    # capsys captures the default sys.stderr output
    captured = capsys.readouterr()
    assert "Out-of-the-box initialization test: \u2713" in captured.err

def test_add_custom_sink_routes_messages_to_destination():
    sink = io.StringIO()
    handler_id = logger.add(sink)
    try:
        logger.info("Routing test payload: 8675309")

        # Verify the exact payload was routed to the custom sink
        assert "Routing test payload: 8675309" in sink.getvalue()
    finally:
        logger.remove(handler_id)

def test_add_sink_with_level_filters_messages_below_threshold():
    stream = io.StringIO()
    # Register sink with INFO threshold
    handler_id = logger.add(stream, level="INFO", format="{message}")

    try:
        # Emit messages at various levels
        logger.debug("Hidden debug trace: 0x00F")
        logger.info("Visible info log: User login")
        logger.warning("Visible warning log: Disk space low")

        output = stream.getvalue()

        # Verify observable state
        assert "Visible info log: User login" in output
        assert "Visible warning log: Disk space low" in output
        assert "Hidden debug trace: 0x00F" not in output
    finally:
        logger.remove(handler_id)

def test_add_sink_with_format_string_structures_output_exactly():
    stream = io.StringIO()
    # Register sink with exact custom format
    handler_id = logger.add(stream, format="[{level}] ~ {message}", level="INFO")

    try:
        logger.info("Structured payload execution")

        # Verify exact string match including the default newline
        assert stream.getvalue() == "[INFO] ~ Structured payload execution\n"
    finally:
        logger.remove(handler_id)

def test_add_file_sink_with_missing_directories_creates_tree_automatically():
    log_path = "./loguru_test_volatile_9988/subdir_alpha/subdir_beta/app.log"
    base_dir = "./loguru_test_volatile_9988"

    # Ensure clean state before test
    if os.path.exists(base_dir):
        shutil.rmtree(base_dir)

    handler_id = logger.add(log_path, format="{message}")

    try:
        logger.info("Deeply nested log entry")

        # Verify directory tree and file creation
        assert os.path.exists(base_dir + "/subdir_alpha/subdir_beta")
        assert os.path.exists(log_path)

        with open(log_path, "r") as f:
            content = f.read()
        assert "Deeply nested log entry" in content
    finally:
        logger.remove(handler_id)
        # Cleanup volatile directory
        if os.path.exists(base_dir):
            shutil.rmtree(base_dir)

def test_file_sink_exceeds_rotation_size_creates_new_file(tmp_path):
    log_file = tmp_path / "test_rotation.log"

    # format="{message}" ensures exactly 101 bytes per emission (100 chars + \n)
    handler_id = logger.add(log_file, rotation="500 B", format="{message}")

    try:
        payload = "A" * 100
        # 5 emissions * 101 bytes = 505 bytes total.
        # Rotation happens BEFORE the 5th emission because 404 + 101 > 500.
        for _ in range(5):
            logger.info(payload)

        log_files = list(tmp_path.glob("test_rotation*.log"))

        # Verify exactly two files exist
        assert len(log_files) == 2

        active_file = log_file
        rotated_files = [f for f in log_files if f != active_file]
        assert len(rotated_files) == 1

        # The rotated file should contain the first 4 emissions (exactly 404 bytes)
        assert rotated_files[0].stat().st_size == 404

        # The active file should contain the final 5th emission
        with open(active_file, "r") as f:
            content = f.read()
        assert content == payload + "\n"
    finally:
        logger.remove(handler_id)

def test_file_sink_exceeds_retention_count_deletes_oldest_file(tmp_path):
    log_file = tmp_path / "test_retention.log"

    # format="{message}" ensures exactly 151 bytes per emission (150 chars + \n)
    handler_id = logger.add(log_file, rotation="100 B", retention=2, format="{message}")

    try:
        payload = "B" * 150

        # Emit 4 times, which triggers multiple rotations
        for _ in range(4):
            logger.info(payload)

        log_files = list(tmp_path.glob("test_retention*.log"))

        # Verify the filesystem contains exactly 3 log files (1 active + 2 retained rotated files)
        assert len(log_files) == 3
    finally:
        logger.remove(handler_id)


def test_enqueued_sink_multithreaded_emissions_prevents_data_corruption():
    sink = io.StringIO()
    # enqueue=True ensures thread-safe, non-blocking logging via an internal queue
    handler_id = logger.add(sink, format="{message}", enqueue=True)

    def worker(thread_id):
        for seq in range(1000):
            payload = f"THREAD_{thread_id}_SEQ_{seq}_PAYLOAD_" + ("X" * 50)
            logger.info(payload)

    threads = []
    for i in range(10):
        t = threading.Thread(target=worker, args=(i,))
        threads.append(t)
        t.start()

    for t in threads:
        t.join()

    # Removing the handler forces the enqueue worker thread to flush and join
    logger.remove(handler_id)

    output_lines = sink.getvalue().splitlines()

    # Verification: Exactly 10,000 complete lines
    assert len(output_lines) == 10000

    # Verification: Every sequence number for every thread must be present
    expected_messages = {
        f"THREAD_{i}_SEQ_{seq}_PAYLOAD_" + ("X" * 50)
        for i in range(10)
        for seq in range(1000)
    }
    actual_messages = set(output_lines)

    assert actual_messages == expected_messages

def test_add_raises_error_on_invalid_level_or_sink_type():
    # Invalid severity level string
    with pytest.raises(ValueError):
        logger.add(sys.stderr, level="SUPER_CRITICAL_FATAL")

    # Invalid sink type (instantiated empty object) raises TypeError, not ValueError
    with pytest.raises(TypeError):
        logger.add(object())

def test_remove_sink_by_returned_id_stops_log_routing():
    sink_a = io.StringIO()
    sink_b = io.StringIO()

    # Action: Add Sink A and Sink B
    id_a = logger.add(sink_a, format="{message}")
    id_b = logger.add(sink_b, format="{message}")

    # Action: Call logger.remove with Sink A's ID
    logger.remove(id_a)

    # Action: Emit log payload
    logger.info("POST_REMOVAL_CHECK")

    # Verification: Sink A must NOT contain the message, Sink B MUST contain it
    assert "POST_REMOVAL_CHECK" not in sink_a.getvalue()
    assert "POST_REMOVAL_CHECK" in sink_b.getvalue()

def test_remove_without_identifier_clears_all_registered_sinks():
    buffer = io.StringIO()

    # Register three distinct sinks
    logger.add(sys.stdout)
    logger.add(sys.stderr)
    logger.add(buffer, format="{message}")

    # Call logger.remove() without arguments
    logger.remove()

    # Emit a log message
    logger.info("GHOST_MESSAGE")

    # Assert the buffer remains completely empty and does not contain the message
    assert buffer.getvalue() == ""
    assert "GHOST_MESSAGE" not in buffer.getvalue()

def test_remove_with_nonexistent_identifier_raises_value_error():
    # Attempt to remove sinks using strictly invalid, hardcoded identifiers
    for invalid_id in [999999, 0, -1]:
        with pytest.raises(ValueError):
            logger.remove(invalid_id)

def test_sink_diagnose_true_logs_local_variables_on_exception():
    logger.remove()
    sink = io.StringIO()
    # diagnose=True ensures local variables are included in the traceback
    logger.add(sink, diagnose=True, backtrace=True, colorize=False)

    @logger.catch
    def faulty_function():
        diagnostic_secret = "CRASH_CONTEXT_8842"
        # We must use the variable in the crashing expression so the AST parser captures it
        return len(diagnostic_secret) / 0

    faulty_function()

    output = sink.getvalue()
    assert "CRASH_CONTEXT_8842" in output


def test_catch_decorator_suppresses_exception_and_returns_default_value():
    logger.remove()

    @logger.catch(default={"status": "FALLBACK_ENGAGED", "code": -99})
    def faulty_function():
        my_dict = {}
        return my_dict["missing_key"]

    result = faulty_function()

    assert result == {"status": "FALLBACK_ENGAGED", "code": -99}


class CustomDomainError(Exception):
    pass

def test_catch_decorator_with_reraise_true_propagates_exception_upward():
    logger.remove()

    @logger.catch(reraise=True)
    def faulty_function():
        raise CustomDomainError("CRITICAL_CORE_MELTDOWN")

    with pytest.raises(CustomDomainError) as exc_info:
        faulty_function()

    assert str(exc_info.value) == "CRITICAL_CORE_MELTDOWN"


def test_bind_contextual_data_injects_into_subsequent_log_records():
    logger.remove()
    sink = io.StringIO()
    logger.add(sink, format="{extra[request_id]} | {extra[retry_count]} | {message}")

    bound_logger = logger.bind(request_id="REQ-9988-XYZ@!", retry_count=3)
    bound_logger.info("Processing request")

    output = sink.getvalue().strip()
    assert output == "REQ-9988-XYZ@! | 3 | Processing request"


def test_bind_existing_key_overwrites_previous_context_value():
    logger.remove()
    sink = io.StringIO()
    logger.add(sink, format="{extra[session_user]} | {message}")

    logger1 = logger.bind(session_user="admin_01")
    logger2 = logger1.bind(session_user="guest_99")

    logger2.info("Second action")
    logger1.info("First action")

    lines = sink.getvalue().strip().split('\n')
    assert len(lines) == 2
    assert lines[0] == "guest_99 | Second action"
    assert lines[1] == "admin_01 | First action"


def test_opt_raw_bypasses_formatting():
    messages = []
    # Configure sink with a specific format to distinguish standard from raw emissions
    logger.add(messages.append, format="[STD] {message}")

    # First emission: using opt(raw=True)
    logger.opt(raw=True).info("Raw message\n")

    # Second emission: using the original logger instance
    logger.info("Standard message")

    assert len(messages) == 2
    # The raw message must bypass formatting entirely
    assert messages[0] == "Raw message\n"
    # The standard message must have the format applied (loguru appends \n by default)
    assert messages[1] == "[STD] Standard message\n"

def test_opt_lazy_defers_computation_and_skips_execution_if_level_rejected():
    messages = []
    # Configure sink with a minimum level of INFO
    logger.add(messages.append, level="INFO")

    # Attempt to emit a DEBUG log (which is below INFO) with a lazy callable that raises an error
    # The test will fail if ZeroDivisionError is raised
    logger.opt(lazy=True).debug("Value: {x}", x=lambda: 1 / 0)

    # Verify nothing was logged and execution continued safely
    assert len(messages) == 0

def test_opt_exception_attaches_current_traceback_to_log_emission():
    messages = []
    logger.add(messages.append, format="{message}")

    try:
        raise ValueError("CRITICAL_DB_CORRUPTION_0x99")
    except ValueError:
        # Emit log with exception=True to capture the active traceback
        logger.opt(exception=True).error("User message")

    assert len(messages) == 1
    emitted_log = messages[0]

    # Verify both the user message and the exact exception traceback string are present
    assert "User message" in emitted_log
    assert "ValueError: CRITICAL_DB_CORRUPTION_0x99" in emitted_log

def test_emit_log_with_format_placeholders_merges_arguments_correctly():
    messages = []
    # Configure a custom sink with a bare format to strictly capture the emitted message
    logger.add(messages.append, format="{message}")

    # Positional formatting
    logger.info("User {} logged in from {}", "Alice", "127.0.0.1")

    # Keyword formatting
    logger.info("Processed {count} items for {client}", count=42, client="AcmeCorp")

    # Advanced standard formatting specifiers
    logger.info("Latency: {ms:.2f}ms", ms=14.5678)

    assert len(messages) == 3
    # Using .strip() to safely ignore the trailing newline appended by loguru's Message object
    assert messages[0].strip() == "User Alice logged in from 127.0.0.1"
    assert messages[1].strip() == "Processed 42 items for AcmeCorp"
    assert messages[2].strip() == "Latency: 14.57ms"

def test_emit_log_with_arguments_but_no_placeholders_ignores_args():
    messages = []
    logger.add(messages.append, format="{message}")

    # Test with positional arguments
    logger.info("System initialized successfully", "unexpected_arg")

    # Test with keyword arguments
    logger.info("Database connection established", port=5432)

    # Verify that the extra arguments are safely ignored and the message is logged normally
    assert len(messages) == 2
    assert messages[0].strip() == "System initialized successfully"
    assert messages[1].strip() == "Database connection established"
