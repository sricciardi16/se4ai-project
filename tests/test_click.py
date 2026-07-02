# 1. Testing Framework & Mocking
import pytest
import os

# 2. The Subject Under Test
import click
from click.testing import CliRunner


def test_command_parses_arguments_and_options_with_type_casting():
    @click.command()
    @click.argument('word')
    @click.option('--count', type=int, default=1)
    def cli(word, count):
        # The function executes the print statement 'count' times
        for _ in range(count):
            click.echo(word)

    runner = CliRunner()
    # Passing "3" as a string to an option expecting type=int
    result = runner.invoke(cli, ['hello', '--count', '3'])

    assert result.exit_code == 0
    # Verifying the function executed the expected number of times based on the parsed integer
    assert result.output == "hello\nhello\nhello\n"

def test_option_parses_slash_separated_boolean_flags():
    @click.command()
    @click.option('--flag/--no-flag', default=None)
    def cli(flag):
        click.echo(f"Flag state: {flag}")

    runner = CliRunner()

    # Test the positive flag (--flag -> True)
    result_positive = runner.invoke(cli, ['--flag'])
    assert result_positive.exit_code == 0
    assert "Flag state: True" in result_positive.output

    # Test the negative flag (--no-flag -> False)
    result_negative = runner.invoke(cli, ['--no-flag'])
    assert result_negative.exit_code == 0
    assert "Flag state: False" in result_negative.output

def test_group_routes_execution_to_correct_subcommand():
    @click.group()
    def cli():
        pass

    @cli.command()
    def hello():
        click.echo("Executing hello")

    @cli.command()
    def goodbye():
        click.echo("Executing goodbye")

    runner = CliRunner()

    # Test routing to 'hello'
    result_hello = runner.invoke(cli, ['hello'])
    assert result_hello.exit_code == 0
    assert "Executing hello" in result_hello.output
    assert "Executing goodbye" not in result_hello.output

    # Test routing to 'goodbye'
    result_goodbye = runner.invoke(cli, ['goodbye'])
    assert result_goodbye.exit_code == 0
    assert "Executing goodbye" in result_goodbye.output
    assert "Executing hello" not in result_goodbye.output

def test_help_flag_generates_formatted_documentation():
    @click.group(help="Main group help documentation.")
    def cli():
        pass

    @cli.command(help="Subcommand help documentation.")
    @click.option('--shout', is_flag=True, help="Print output in uppercase.")
    def speak(shout):
        pass

    runner = CliRunner()

    # Test group help menu
    group_result = runner.invoke(cli, ['--help'])
    assert group_result.exit_code == 0
    assert "Main group help documentation." in group_result.output
    assert "speak" in group_result.output  # Subcommand name is present

    # Test subcommand help menu to verify option signatures
    subcommand_result = runner.invoke(cli, ['speak', '--help'])
    assert subcommand_result.exit_code == 0
    assert "Subcommand help documentation." in subcommand_result.output
    assert "--shout" in subcommand_result.output  # Specific option flag is present

def test_context_object_propagates_state_to_subcommands():
    @click.group()
    @click.pass_context
    def cli(ctx):
        # Set a specific value in the group context object
        ctx.obj = {"config": "custom.cfg"}

    @cli.command()
    @click.pass_context
    def sub(ctx):
        # Retrieve the context and access the modified state
        click.echo(f"Loaded config: {ctx.obj['config']}")

    runner = CliRunner()
    result = runner.invoke(cli, ['sub'])

    assert result.exit_code == 0
    # Assert that the exact value is successfully read by the subcommand
    assert "Loaded config: custom.cfg" in result.output

def test_option_falls_back_to_envvar_and_default_values():
    @click.command()
    @click.option('--config', envvar='MY_CONFIG', default='default-string')
    def cli(config):
        click.echo(config)

    runner = CliRunner()

    # Scenario 1: Empty environment (expecting the default string)
    # Setting to None ensures it is explicitly removed from the environment
    result_empty = runner.invoke(cli, env={'MY_CONFIG': None})
    assert result_empty.exit_code == 0
    assert result_empty.output.strip() == 'default-string'

    # Scenario 2: Environment containing the target variable (expecting the environment string)
    result_env = runner.invoke(cli, env={'MY_CONFIG': 'env-string'})
    assert result_env.exit_code == 0
    assert result_env.output.strip() == 'env-string'


def test_prompt_option_reads_from_standard_input():
    @click.command()
    @click.option('--token', prompt=True)
    def cli(token):
        click.echo(f"Received: {token}")

    runner = CliRunner()

    # Simulate user input containing a newline character
    result = runner.invoke(cli, input="secret-token\n")

    assert result.exit_code == 0
    # Verify the command receives the stripped string
    assert "Received: secret-token" in result.output


def test_runner_default_map_overrides_option_defaults():
    @click.group()
    def cli():
        pass

    @cli.command()
    @click.option('--count', default=1, type=int)
    def run(count):
        click.echo(f"Count: {count}")

    runner = CliRunner()

    # Use a nested dictionary structure mapping the subcommand name to its option values
    result = runner.invoke(cli, ['run'], default_map={"run": {"count": 7}})

    assert result.exit_code == 0
    # Verify the overridden value is used
    assert result.output.strip() == "Count: 7"


def test_invalid_type_input_exits_with_validation_error():
    @click.command()
    @click.option('--count', type=int)
    def cli(count):
        click.echo(f"Count: {count}")

    runner = CliRunner()

    # Pass an intentionally invalid string to an option strictly typed as int
    result = runner.invoke(cli, ['--count', 'not-an-int'])

    # Intercept the error, prevent the function from running, exit with a non-zero code
    assert result.exit_code != 0
    # Print an invalid value error message
    assert "Invalid value for '--count': 'not-an-int' is not a valid integer." in result.output
    assert "Count:" not in result.output


def test_path_type_resolves_correctly_in_isolated_filesystem():
    @click.command()
    @click.option('--file', type=click.Path(dir_okay=False, writable=True))
    def cli(file):
        # Allow file operations (like writing) within this isolated environment
        with open(file, 'w') as f:
            f.write("isolated data")
        click.echo("Success")

    runner = CliRunner()

    # Execute within a temporary, empty directory
    with runner.isolated_filesystem():
        result = runner.invoke(cli, ['--file', 'output.txt'])

        assert result.exit_code == 0
        assert "Success" in result.output

        # Verify that the command successfully created and wrote to a new file
        with open('output.txt', 'r') as f:
            content = f.read()
            assert content == "isolated data"

def test_invoke_command_with_args_routes_parsed_values_to_routine():
    captured_number = None
    captured_text = None

    @click.command()
    @click.argument('number', type=int)
    @click.argument('text', type=str)
    def cli(number, text):
        nonlocal captured_number, captured_text
        captured_number = number
        captured_text = text

    runner = CliRunner()
    result = runner.invoke(cli, ["42", "complex string with spaces"])

    assert result.exit_code == 0
    assert captured_number == 42
    assert isinstance(captured_number, int)
    assert captured_text == "complex string with spaces"

def test_command_without_explicit_name_derives_hyphenated_name_from_function():
    @click.command()
    def process_user_data_and_sync():
        pass

    assert process_user_data_and_sync.name == "process-user-data-and-sync"

def test_invoke_group_without_subcommand_displays_help_and_exits():
    @click.group()
    def cli():
        pass

    @cli.command(name="initialize-db")
    def init_db():
        pass

    @cli.command(name="drop-db")
    def drop_db():
        pass

    runner = CliRunner()
    result = runner.invoke(cli, [])

    assert result.exit_code == 0
    assert "Usage:" in result.output
    assert "initialize-db" in result.output
    assert "drop-db" in result.output

def test_option_names_are_converted_to_snake_case_kwargs():
    captured_header = None

    @click.command()
    @click.option('--custom-header-value')
    def cli(custom_header_value):
        nonlocal captured_header
        captured_header = custom_header_value

    runner = CliRunner()
    result = runner.invoke(cli, ["--custom-header-value", "X-Auth-Token: abc-123-xyz"])

    assert result.exit_code == 0
    assert captured_header == "X-Auth-Token: abc-123-xyz"

def test_omitted_prompt_option_requests_stdin_and_passes_value():
    captured_email = None

    @click.command()
    @click.option('--admin-email', prompt="Enter Admin Email")
    def cli(admin_email):
        nonlocal captured_email
        captured_email = admin_email

    runner = CliRunner()
    result = runner.invoke(cli, [], input="admin+test@example.com\n")

    assert result.exit_code == 0
    assert "Enter Admin Email:" in result.output
    assert captured_email == "admin+test@example.com"

def test_hidden_confirmation_prompt_validates_matching_input():
    @click.command()
    @click.option('--password', prompt=True, hide_input=True, confirmation_prompt=True, required=True)
    def cli(password):
        click.echo(f"pwd={password}")

    runner = CliRunner()

    # Valid match sequence
    result = runner.invoke(cli, input="P@ssw0rd_2024!\nP@ssw0rd_2024!\n")
    assert result.exit_code == 0
    assert "pwd=P@ssw0rd_2024!" in result.output

    # Invalid match sequence (fails, then user provides correct match)
    result = runner.invoke(cli, input="P@ssw0rd_2024!\nwrong_pass\ncorrect_pass\ncorrect_pass\n")
    assert result.exit_code == 0
    assert "Error: The two entered values do not match." in result.output
    assert "pwd=correct_pass" in result.output

    # Empty input edge case (rejected because option is required, prompts again, then succeeds)
    result = runner.invoke(cli, input="\nvalid_pass\nvalid_pass\n")
    assert result.exit_code == 0
    assert "pwd=valid_pass" in result.output


def test_option_omitted_from_cli_extracts_value_from_envvar():
    @click.command()
    @click.option('--api-key', envvar='APP_API_KEY')
    def cli(api_key):
        click.echo(f"key={api_key}")

    runner = CliRunner()

    # Environment variable provided
    result = runner.invoke(cli, env={'APP_API_KEY': 'sk_test_8a9b2c3d4e5f6g7h8i9j0k'})
    assert result.exit_code == 0
    assert "key=sk_test_8a9b2c3d4e5f6g7h8i9j0k" in result.output

    # CLI flag takes absolute precedence over environment variable
    result = runner.invoke(cli, ['--api-key', 'cli_override'], env={'APP_API_KEY': 'sk_test_8a9b2c3d4e5f6g7h8i9j0k'})
    assert result.exit_code == 0
    assert "key=cli_override" in result.output


def test_mutually_exclusive_boolean_flags_pass_strict_booleans():
    @click.command()
    @click.option('--sync/--no-sync', default=False)
    def cli(sync):
        # Ensure strict boolean type is passed, not a string
        assert isinstance(sync, bool)
        click.echo(f"sync_value={sync}")

    runner = CliRunner()

    # Positive flag
    result = runner.invoke(cli, ['--sync'])
    assert result.exit_code == 0
    assert "sync_value=True" in result.output

    # Negative flag
    result = runner.invoke(cli, ['--no-sync'])
    assert result.exit_code == 0
    assert "sync_value=False" in result.output

    # Neither flag (falls back to default)
    result = runner.invoke(cli, [])
    assert result.exit_code == 0
    assert "sync_value=False" in result.output


def test_multiple_option_flags_aggregate_into_ordered_tuple():
    @click.command()
    @click.option('--tag', multiple=True)
    def cli(tag):
        # Ensure it is passed as a tuple
        assert isinstance(tag, tuple)
        click.echo(f"tags={tag}")

    runner = CliRunner()

    # Multiple flags provided in sequence
    result = runner.invoke(cli, ['--tag', 'backend', '--tag', 'frontend', '--tag', 'database'])
    assert result.exit_code == 0
    assert "tags=('backend', 'frontend', 'database')" in result.output

    # Zero times provided (must pass empty tuple)
    result = runner.invoke(cli, [])
    assert result.exit_code == 0
    assert "tags=()" in result.output


def test_invoke_parses_string_input_via_shlex():
    @click.command()
    @click.argument('source_file')
    @click.argument('destination_file')
    def cli(source_file, destination_file):
        click.echo(f"src={source_file}")
        click.echo(f"dst={destination_file}")

    runner = CliRunner()

    # Strict order parsing
    result = runner.invoke(cli, ['data_2023_v2.csv', 'backup_archive_final.csv'])
    assert result.exit_code == 0
    assert "src=data_2023_v2.csv" in result.output
    assert "dst=backup_archive_final.csv" in result.output

    # Spaces in positional argument (properly quoted by shell simulation)
    result = runner.invoke(cli, '"my data.csv" backup_archive_final.csv')
    assert result.exit_code == 0
    assert "src=my data.csv" in result.output
    assert "dst=backup_archive_final.csv" in result.output

def test_invoke_with_unlimited_positional_arguments_captures_all_as_tuple():
    captured_args = None

    # ignore_unknown_options is required so that "--looks-like-a-flag"
    # is not misinterpreted as an undefined option by the parser.
    @click.command(context_settings={"ignore_unknown_options": True})
    @click.argument("files", nargs=-1)
    def cli(files):
        nonlocal captured_args
        captured_args = files

    runner = CliRunner()
    input_args = ["file_A.txt", "12345", "--looks-like-a-flag", "file_B.csv"]

    result = runner.invoke(cli, input_args)

    assert result.exit_code == 0
    assert captured_args == ("file_A.txt", "12345", "--looks-like-a-flag", "file_B.csv")


def test_invoke_missing_required_positional_argument_halts_and_displays_error():
    routine_executed = False

    @click.command()
    @click.argument("req_arg")
    def cli(req_arg):
        nonlocal routine_executed
        routine_executed = True

    runner = CliRunner()
    result = runner.invoke(cli, [])

    assert not routine_executed
    assert result.exit_code == 2
    assert "Error: Missing argument" in result.output


def test_echo_with_unicode_characters_outputs_safely_without_encoding_errors():
    @click.command()
    def cli():
        click.echo("System Status 🌍: 影師嗎, ñ, å, œ")

    runner = CliRunner()
    result = runner.invoke(cli)

    assert result.exit_code == 0
    assert "System Status 🌍: 影師嗎, ñ, å, œ" in result.output


def test_echo_styled_text_to_non_interactive_stream_strips_ansi_codes():
    @click.command()
    def cli():
        # click.style adds ANSI color/style codes to the string
        styled_text = click.style("CRITICAL FAILURE", fg="red", bold=True)
        # click.echo automatically strips ANSI codes when writing to a non-interactive stream
        click.echo(styled_text)

    runner = CliRunner()
    result = runner.invoke(cli)

    assert result.exit_code == 0
    assert result.output == "CRITICAL FAILURE\n"


def test_echo_with_err_flag_routes_output_strictly_to_stderr():
    @click.command()
    def cli():
        click.echo("Diagnostic log: Process 992 failed.", err=True)

    # mix_stderr=False is required in Click >= 7.0 to capture stdout and stderr independently
    runner = CliRunner(mix_stderr=False)
    result = runner.invoke(cli)

    assert result.exit_code == 0
    assert result.stderr == "Diagnostic log: Process 992 failed.\n"
    assert result.stdout == ""

def test_invoke_with_invalid_path_constraints_halts_execution_and_handles_file_type_constraints():
    @click.command()
    @click.option('--file1', type=click.Path(exists=True))
    @click.option('--file2', type=click.Path(dir_okay=False))
    # CHANGED: Replaced writable=True with file_okay=False to avoid root permission bypass issues
    @click.option('--file3', type=click.Path(file_okay=False))
    def cli(file1, file2, file3):
        pass

    runner = CliRunner()

    # Use isolated filesystem to guarantee the environment state
    with runner.isolated_filesystem():
        os.mkdir('my_folder')
        with open('readonly.txt', 'w') as f:
            f.write('test')
        
        # REMOVED: os.chmod('readonly.txt', 0o444) is no longer needed

        # Constraint 1: exists=True
        result1 = runner.invoke(cli, ['--file1', 'non_existent_ghost_file_999.txt'])
        assert result1.exit_code != 0
        assert "does not exist" in result1.output

        # Constraint 2: dir_okay=False
        result2 = runner.invoke(cli, ['--file2', 'my_folder'])
        assert result2.exit_code != 0
        assert "is a directory" in result2.output

        # Constraint 3: file_okay=False
        result3 = runner.invoke(cli, ['--file3', 'readonly.txt'])
        assert result3.exit_code != 0
        # CHANGED: Assert the correct error message for the file_okay=False constraint
        assert "is a file" in result3.output


def test_invoke_with_unlisted_choice_raises_usage_error():
    @click.command()
    @click.option('--action', type=click.Choice(['start', 'stop', 'restart'], case_sensitive=True))
    def cli(action):
        pass

    runner = CliRunner()

    invalid_inputs = ['Start', 'pause', 'DROP TABLE users;']

    for invalid_input in invalid_inputs:
        result = runner.invoke(cli, ['--action', invalid_input])

        assert result.exit_code != 0
        assert "Invalid value for '--action'" in result.output
        assert "'start', 'stop', 'restart'" in result.output


def test_invoke_help_flag_displays_formatted_documentation():
    @click.command()
    @click.option('--verbose', is_flag=True, help="Enable verbose logging for debugging.")
    def cli(verbose):
        """Deploys the application to the specified environment."""
        pass

    runner = CliRunner()
    result = runner.invoke(cli, ['--help'])

    assert result.exit_code == 0
    assert "Deploys the application to the specified environment." in result.output
    assert "Enable verbose logging for debugging." in result.output
    assert "--verbose" in result.output


def test_invoke_missing_required_parameter_displays_usage_instructions():
    @click.command()
    @click.argument('target_id', required=True)
    def cli(target_id):
        pass

    runner = CliRunner()
    result = runner.invoke(cli, [])

    assert result.exit_code != 0
    assert "Error: Missing argument 'TARGET_ID'." in result.output
    assert "Usage:" in result.output


def test_raise_click_exception_suppresses_traceback_and_exits_cleanly():
    @click.command()
    def cli():
        raise click.ClickException("Database connection timeout: 3000ms")

    # mix_stderr=False must be passed to the CliRunner constructor, not invoke()
    runner = CliRunner(mix_stderr=False)

    result = runner.invoke(cli, [])

    assert result.exit_code == 1
    assert "Error: Database connection timeout: 3000ms" in result.stderr
    assert "Traceback (most recent call last):" not in result.stderr
