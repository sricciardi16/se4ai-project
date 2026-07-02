# 1. Testing Framework & Mocking
import pytest

# 2. The Subject Under Test
from pygments import highlight, lex
from pygments.formatters import HtmlFormatter, get_formatter_by_name
from pygments.lexer import Lexer
from pygments.lexers import PythonLexer, get_lexer_by_name, guess_lexer
from pygments.token import Token
from pygments.util import ClassNotFound
import pygments

# 4. Auxiliary: Standard Library
import io


def test_lex_python_code_yields_expected_tokens():
    code = 'def add(a, b):\n    return a + b\n'
    lexer = PythonLexer()
    tokens = list(lex(code, lexer))

    token_types = [t[0] for t in tokens]

    assert Token.Keyword in token_types
    assert Token.Name.Function in token_types

def test_highlight_generates_valid_html_with_css_classes():
    code = 'for i in range(3):\n    print(i)\n'
    lexer = PythonLexer()
    formatter = HtmlFormatter()
    result = highlight(code, lexer, formatter)

    assert '<span' in result
    assert 'class=' in result
    assert 'print' in result
    assert 'range' in result

def test_get_lexer_by_name_resolves_exact_names_and_aliases():
    lexer_python = get_lexer_by_name("python")
    lexer_json = get_lexer_by_name("json")
    lexer_py = get_lexer_by_name("py")

    assert isinstance(lexer_python, Lexer)
    assert isinstance(lexer_json, Lexer)
    assert isinstance(lexer_py, Lexer)

    assert lexer_python.name == 'Python'
    assert lexer_py.name == 'Python'
    assert lexer_json.name == 'JSON'

def test_html_formatter_generates_css_style_definitions():
    formatter = HtmlFormatter()
    css = formatter.get_style_defs(".highlight")

    assert ".highlight" in css
    assert "color:" in css or "background:" in css or "background-color:" in css

@pytest.mark.parametrize("lang", ["python", "javascript", "json", "html"])
def test_highlight_generates_html_for_multiple_languages(lang):
    lexer = get_lexer_by_name(lang)
    formatter = get_formatter_by_name("html")
    source = 'print("hello world");'

    result = highlight(source, lexer, formatter)

    assert isinstance(result, str)
    assert len(result) > 0

def test_highlight_valid_source_returns_formatted_string():
    source = "def foo():\n    pass"
    lexer = get_lexer_by_name("python")
    formatter = get_formatter_by_name("html")

    result = highlight(source, lexer, formatter)

    assert isinstance(result, str)
    assert '<span class="k">def</span>' in result

def test_highlight_with_outfile_writes_to_stream_and_returns_none():
    source = 'print("hello")'
    lexer = get_lexer_by_name("python")
    formatter = get_formatter_by_name("terminal")
    outfile = io.StringIO()

    result = highlight(source, lexer, formatter, outfile=outfile)

    assert result is None
    output = outfile.getvalue()
    assert "\x1b[" in output

def test_highlight_empty_string_returns_formatter_boilerplate_only():
    source = ""
    lexer = get_lexer_by_name("python")
    formatter = get_formatter_by_name("html", full=True)

    result = highlight(source, lexer, formatter)

    assert isinstance(result, str)
    assert "<html>" in result or "<html" in result
    assert "<body>" in result or "<body" in result
    assert "</body>" in result
    assert "</html>" in result
    assert '<span class="' not in result

def test_get_lexer_by_name_valid_alias_returns_correct_lexer_instance():
    lexer = get_lexer_by_name("python")

    assert isinstance(lexer, Lexer)
    assert lexer.name == "Python"

def test_lexer_stripall_option_removes_surrounding_whitespace():
    source = "\n\n\t  def foo(): pass  \n\n"
    lexer = get_lexer_by_name('python', stripall=True)
    formatter = get_formatter_by_name('text')

    output = highlight(source, lexer, formatter)

    assert output == "def foo(): pass\n"

def test_guess_lexer_with_distinct_syntax_returns_correct_lexer():
    python_snippet = "#!/usr/bin/env python\ndef __init__(self): yield True"
    lexer_py = guess_lexer(python_snippet)
    assert lexer_py.name == 'Python'

    html_snippet = "<!DOCTYPE html><html><body></body></html>"
    lexer_html = guess_lexer(html_snippet)
    assert lexer_html.name == 'HTML'

    bash_snippet = "#!/bin/bash\necho \"Hello\""
    lexer_bash = guess_lexer(bash_snippet)
    assert lexer_bash.name == 'Bash'


def test_get_formatter_by_name_with_valid_alias_returns_formatter_instance():
    fmt_html = get_formatter_by_name('html')
    assert 'html' in fmt_html.aliases

    fmt_term = get_formatter_by_name('terminal256')
    assert 'terminal256' in fmt_term.aliases

    fmt_latex = get_formatter_by_name('latex')
    assert 'latex' in fmt_latex.aliases

def test_html_formatter_kwargs_apply_visual_rules():
    lexer = get_lexer_by_name('python')
    formatter = get_formatter_by_name('html', full=True, linenos=True, style='monokai')

    output = highlight("print('hello')", lexer, formatter)

    # Verify full document tags
    assert "<!DOCTYPE html" in output
    assert "<html>" in output
    assert "<body>" in output

    # Verify HTML elements representing line numbers
    assert "lineno" in output

    # Verify inline CSS matching the requested style (Monokai background color)
    assert "272822" in output

def test_get_lexer_and_formatter_with_unknown_alias_raises_class_not_found():
    with pytest.raises(ClassNotFound):
        get_lexer_by_name('not-a-real-language-12345')

    with pytest.raises(ClassNotFound):
        get_formatter_by_name('fake-formatter-xyz')

    with pytest.raises(ClassNotFound):
        get_lexer_by_name('')

    with pytest.raises(ClassNotFound):
        get_formatter_by_name('')
