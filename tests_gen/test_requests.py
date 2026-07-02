# 1. Testing Framework & Mocking
import pytest
from unittest.mock import patch

# 2. The Subject Under Test
import http_client as requests
from http_client.adapters import BaseAdapter
from http_client.models import Response

# 3. Auxiliary: Third-Party
import responses
from urllib3.response import HTTPResponse

# 4. Auxiliary: Standard Library
from http.server import BaseHTTPRequestHandler, HTTPServer, ThreadingHTTPServer
from io import BytesIO
import json
import threading
import time
import urllib.parse


class MockServerRequestHandler(BaseHTTPRequestHandler):
    """
    A simple, dependency-free local HTTP server to act as a black-box
    target for our requests tests, ensuring we don't mock internal state.
    """
    def log_message(self, format, *args):
        pass  # Suppress logging to keep test output clean

    def do_GET(self):
        if self.path == '/hello':
            self.send_response(200)
            self.send_header('Content-Type', 'text/plain')
            self.end_headers()
            self.wfile.write(b'hello')
        elif self.path.startswith('/get'):
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            parsed_path = urllib.parse.urlparse(self.path)
            query = urllib.parse.parse_qs(parsed_path.query)
            args = {k: v[0] for k, v in query.items()}
            self.wfile.write(json.dumps({"args": args}).encode('utf-8'))
        elif self.path == '/redirect':
            self.send_response(302)
            self.send_header('Location', '/target')
            self.end_headers()
        elif self.path == '/target':
            self.send_response(200)
            self.send_header('Content-Type', 'text/plain')
            self.end_headers()
            self.wfile.write(b'target reached')
        elif self.path == '/json_valid':
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(b'{"id": 1042, "active": true, "tags": ["api", "test"], "metadata": {"key": null}}')
        elif self.path == '/json_empty':
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(b'')
        elif self.path == '/json_malformed':
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(b'{"key": "value", "broken_array": [1, 2, ')
        elif self.path.startswith('/status/'):
            status = int(self.path.split('/')[-1])
            self.send_response(status)
            self.end_headers()
        elif self.path == '/timeout':
            time.sleep(2.0)
            self.send_response(200)
            self.end_headers()
        elif self.path == '/delay/0.05':
            time.sleep(0.05)
            self.send_response(200)
            self.end_headers()
        elif self.path == '/stream':
            self.send_response(200)
            self.send_header('Content-Type', 'application/octet-stream')
            self.end_headers()
            self.wfile.write(b"Hello World")
        elif self.path == '/cookies/set':
            self.send_response(200)
            self.send_header('Set-Cookie', 'session=abc123; Path=/')
            self.end_headers()
        elif self.path == '/cookies':
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            cookie_header = self.headers.get('Cookie', '')
            cookies = {}
            if cookie_header:
                for item in cookie_header.split(';'):
                    if '=' in item:
                        k, v = item.strip().split('=', 1)
                        cookies[k] = v
            self.wfile.write(json.dumps({"cookies": cookies}).encode('utf-8'))
        elif self.path == '/basic-auth':
            auth_header = self.headers.get('Authorization')
            if auth_header == 'Basic dXNlcjpwYXNz':
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"authenticated": True, "user": "user"}).encode('utf-8'))
            else:
                self.send_response(401)
                self.end_headers()
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        content_length = int(self.headers.get('Content-Length', 0))
        post_data = self.rfile.read(content_length)

        if self.path == '/post-form':
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            parsed_form = urllib.parse.parse_qs(post_data.decode('utf-8'))
            form = {k: v[0] for k, v in parsed_form.items()}
            self.wfile.write(json.dumps({"form": form}).encode('utf-8'))
        elif self.path == '/post-json':
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            parsed_json = json.loads(post_data.decode('utf-8'))
            headers_dict = {k.lower(): v for k, v in self.headers.items()}
            self.wfile.write(json.dumps({"json": parsed_json, "headers": headers_dict}).encode('utf-8'))
        else:
            self.send_response(404)
            self.end_headers()

@pytest.fixture(scope="module")
def mock_server():
    """Spins up the local HTTP server in a background thread."""
    server = ThreadingHTTPServer(('127.0.0.1', 0), MockServerRequestHandler)
    server_thread = threading.Thread(target=server.serve_forever)
    server_thread.daemon = True
    server_thread.start()

    yield f"http://127.0.0.1:{server.server_port}"

    server.shutdown()
    server.server_close()
    server_thread.join()


def test_get_request_returns_decoded_text_and_status(mock_server):
    with requests.Session() as session:
        response = session.get(f"{mock_server}/hello")

        assert response.status_code == 200
        assert response.text == "hello"


def test_get_request_encodes_params_and_parses_json_response(mock_server):
    with requests.Session() as session:
        params = {"a": "1", "b": "two"}
        response = session.get(f"{mock_server}/get", params=params)

        assert response.status_code == 200
        data = response.json()
        assert data["args"] == {"a": "1", "b": "two"}


def test_post_request_encodes_dict_as_form_data(mock_server):
    with requests.Session() as session:
        data = {"x": "10", "y": "20"}
        response = session.post(f"{mock_server}/post-form", data=data)

        assert response.status_code == 200
        response_data = response.json()
        assert response_data["form"] == {"x": "10", "y": "20"}


def test_post_request_serializes_dict_as_json(mock_server):
    with requests.Session() as session:
        json_payload = {"active": True, "count": 3, "name": "test"}
        response = session.post(f"{mock_server}/post-json", json=json_payload)

        assert response.status_code == 200
        response_data = response.json()

        assert response_data["json"] == {"active": True, "count": 3, "name": "test"}
        assert response_data["headers"]["content-type"] == "application/json"


def test_get_request_automatically_follows_redirects(mock_server):
    with requests.Session() as session:
        response = session.get(f"{mock_server}/redirect")

        assert response.status_code == 200
        assert response.url == f"{mock_server}/target"
        assert response.text == "target reached"

def test_session_persists_cookies_across_requests(mock_server):
    """
    When a Session makes a request and the server responds with a Set-Cookie header,
    the session should store that cookie and automatically include it in the Cookie header
    of subsequent requests to the same domain.
    """
    with requests.Session() as session:
        # First request: Server sets the cookie "session=abc123"
        session.get(f"{mock_server}/cookies/set")

        # Second request: The session should automatically include the cookie
        response = session.get(f"{mock_server}/cookies")

        assert response.status_code == 200
        data = response.json()

        # Verify the cookie string is echoed back on the second request
        assert data["cookies"].get("session") == "abc123"

def test_get_request_constructs_basic_auth_header(mock_server):
    """
    When a GET request is made with a (username, password) tuple passed to the auth argument,
    the library should correctly construct and send an Authorization: Basic <base64_encoded_credentials> header.
    """
    with requests.Session() as session:
        # Passing the standard tuple ("user", "pass")
        response = session.get(f"{mock_server}/basic-auth", auth=("user", "pass"))

        assert response.status_code == 200
        data = response.json()

        # Verify the server successfully authenticated the Base64 encoded header
        assert data.get("authenticated") is True
        assert data.get("user") == "user"

def test_streaming_request_yields_chunks_via_iter_content(mock_server):
    """
    When a request is made with stream=True, the response body is not immediately downloaded.
    The user can then call iter_content(chunk_size) on the response object to iterate over
    the raw bytes of the payload in specified chunk sizes.
    """
    with requests.Session() as session:
        response = session.get(f"{mock_server}/stream", stream=True)

        assert response.status_code == 200

        # Iterate over the raw bytes in chunk_size of 2
        chunks = list(response.iter_content(chunk_size=2))

        assert len(chunks) > 0
        # Verify the chunk size is respected
        assert len(chunks[0]) == 2

        # Verify that joining the yielded byte chunks reconstructs the full original payload
        full_payload = b"".join(chunks)
        assert full_payload == b"Hello World"

def test_request_succeeds_within_timeout_duration(mock_server):
    """
    When a request is made with a timeout argument (in seconds), the request should succeed
    normally and return a valid response if the server responds before the timeout duration expires.
    """
    with requests.Session() as session:
        # Endpoint has a known delay of 0.05 seconds, timeout is set to 1.0 seconds
        response = session.get(f"{mock_server}/delay/0.05", timeout=1.0)

        # Ensure no false-positive timeout exceptions are raised and response is valid
        assert response.status_code == 200

def test_prepare_request_retains_method_url_and_headers():
    # Injecting a custom header {"X-Test": "1"}
    req = requests.Request(
        method="GET",
        url="http://mock.local/get",
        headers={"X-Test": "1"}
    )

    with requests.Session() as session:
        prep = session.prepare_request(req)

        assert prep.method == "GET"
        assert prep.url == "http://mock.local/get"
        assert "X-Test" in prep.headers
        assert prep.headers["X-Test"] == "1"

def test_module_exposes_core_api_and_shortcuts():
    """
    Verifies that the requests module exposes its core submodules and
    primary top-level shortcuts like `get` and `Session`.
    """
    # Check core submodules
    assert hasattr(requests, 'api')
    assert hasattr(requests, 'sessions')
    assert hasattr(requests, 'models')
    assert hasattr(requests, 'auth')
    assert hasattr(requests, 'exceptions')

    # Check primary shortcuts
    assert hasattr(requests, 'get')
    assert hasattr(requests, 'Session')

    # Verify types of shortcuts
    assert callable(requests.get)
    assert isinstance(requests.Session, type)

def test_get_with_invalid_url_string_raises_request_exception():
    """
    Verifies that a completely malformed URL string raises a RequestException.
    """
    with pytest.raises(requests.exceptions.RequestException):
        requests.get("not a url")

def test_get_with_schemeless_url_raises_missing_schema():
    """
    Verifies that a URL lacking an HTTP scheme explicitly raises a MissingSchema exception.
    """
    with pytest.raises(requests.exceptions.MissingSchema):
        requests.get("example.com/path")

def test_response_json_with_invalid_payload_raises_json_decode_error():
    """
    Verifies that calling .json() on a Response with non-JSON data raises
    requests.exceptions.JSONDecodeError (which inherits from ValueError in 2.31).
    """
    # Constructing a Response object using only public attributes to remain strictly black-box
    response = requests.Response()
    response.status_code = 200
    response.headers['Content-Type'] = 'text/plain'

    # requests.Response reads from the `raw` attribute (a file-like object) to populate content
    response.raw = BytesIO(b"plain text")

    with pytest.raises(requests.exceptions.JSONDecodeError):
        response.json()

def test_get_with_params_dict_appends_serialized_query_string(mock_server):
    base_url = f"{mock_server}/get" # Changed from example.com
    params = {
        "search query": "python & requests",
        "symbols": "@#$%"
    }

    # We no longer need the try/except block because the local server is guaranteed to be up
    response = requests.get(base_url, params=params)

    expected_url = f"{mock_server}/get?search+query=python+%26+requests&symbols=%40%23%24%25"
    assert response.url == expected_url

# Helper to mock Session.send to prevent actual network I/O during tests,
# while allowing us to inspect the PreparedRequest and Response objects.
def mock_send_side_effect(request, **kwargs):
    resp = requests.Response()
    resp.request = request
    resp.url = request.url
    resp.status_code = 200
    return resp

@patch('http_client.Session.send', side_effect=mock_send_side_effect)
def test_get_with_none_param_value_omits_key_from_url(mock_send):
    params = {"active": "true", "filter_id": None, "empty_string": ""}
    response = requests.get('http://dummy.local/api', params=params)

    assert "active=true" in response.url
    assert "empty_string=" in response.url
    assert "filter_id" not in response.url
    assert "None" not in response.url

@pytest.mark.parametrize("invalid_url", [
    "google.com",
    "www.example.org/api/v1"
])
def test_request_without_schema_raises_missing_schema_error(invalid_url):
    with pytest.raises(requests.exceptions.MissingSchema):
        requests.get(invalid_url)

@patch('http_client.Session.send', side_effect=mock_send_side_effect)
def test_post_with_data_dict_formats_as_form_urlencoded(mock_send):
    payload = {"user name": "john doe", "email": "john+test@example.com"}
    response = requests.post('http://dummy.local/api', data=payload)

    assert response.request.body == 'user+name=john+doe&email=john%2Btest%40example.com'
    assert response.request.headers.get('Content-Type') == 'application/x-www-form-urlencoded'

@patch('http_client.Session.send', side_effect=mock_send_side_effect)
def test_post_with_json_argument_serializes_and_sets_headers(mock_send):
    payload = {
        "id": 101,
        "is_active": True,
        "tags": ["test", "api"],
        "metadata": {"key": None}
    }
    response = requests.post('http://dummy.local/api', json=payload)

    assert response.request.headers.get('Content-Type') == 'application/json'
    assert isinstance(response.request.body, bytes)

    # Verify the byte string is valid JSON and represents the exact values
    parsed_body = json.loads(response.request.body.decode('utf-8'))
    assert parsed_body == payload

@patch('http_client.Session.send', side_effect=mock_send_side_effect)
def test_post_with_data_and_json_prioritizes_data_and_ignores_json(mock_send):
    data_payload = {"form_key": "form_value"}
    json_payload = {"json_key": "json_value"}

    response = requests.post('http://dummy.local/api', data=data_payload, json=json_payload)

    # Changed from b'...' to '...'
    assert response.request.body == 'form_key=form_value'
    assert 'json_key' not in response.request.body
    assert response.request.headers.get('Content-Type') == 'application/x-www-form-urlencoded'

@responses.activate
def test_request_with_dynamic_method_string_executes_correct_http_verb():
    url = "http://mock.local/dynamic"
    methods = ["PATCH", "OPTIONS", "PURGE"]

    for method in methods:
        responses.add(method, url, status=200)
        response = requests.request(method, url)

        assert response.request.method == method


@responses.activate
def test_session_persists_headers_across_multiple_sequential_requests():
    url_a = "http://mock.local/endpoint_a"
    url_b = "http://mock.local/endpoint_b"

    responses.add(responses.GET, url_a, status=200)
    responses.add(responses.GET, url_b, status=200)

    session = requests.Session()
    session.headers.update({
        "Authorization": "Bearer persistent_token_9938",
        "X-Custom-Global": "global_value"
    })

    resp_a = session.get(url_a)
    resp_b = session.get(url_b)

    assert resp_a.request.headers["Authorization"] == "Bearer persistent_token_9938"
    assert resp_a.request.headers["X-Custom-Global"] == "global_value"

    assert resp_b.request.headers["Authorization"] == "Bearer persistent_token_9938"
    assert resp_b.request.headers["X-Custom-Global"] == "global_value"


@responses.activate
def test_request_level_headers_override_session_level_headers():
    url = "http://mock.local/override"
    responses.add(responses.GET, url, status=200)

    session = requests.Session()
    session.headers.update({
        "User-Agent": "GlobalAgent/1.0",
        "Accept-Language": "en-US"
    })

    resp = session.get(url, headers={"User-Agent": "OverrideAgent/2.0"})

    assert resp.request.headers["User-Agent"] == "OverrideAgent/2.0"
    assert resp.request.headers["Accept-Language"] == "en-US"


@responses.activate
def test_response_exposes_raw_binary_and_automatically_decoded_text():
    url = "http://mock.local/japanese"
    raw_bytes = b'\x82\xb1\x82\xf1\x82\xc9\x82\xbf\x82\xcd\x90\xa2\x8aE'

    responses.add(
        responses.GET,
        url,
        body=raw_bytes,
        headers={"Content-Type": "text/plain; charset=Shift_JIS"},
        status=200
    )

    resp = requests.get(url)

    assert resp.content == raw_bytes
    assert resp.encoding == "Shift_JIS"
    assert resp.text == "こんにちは世界"


@responses.activate
def test_followed_redirect_response_exposes_core_attributes():
    start_url = "http://mock.local/start"
    final_url = "https://mock.local/final-destination"

    # Mock the initial redirect response
    responses.add(
        responses.GET,
        start_url,
        status=301,
        headers={"Location": final_url}
    )

    # Mock the final destination response
    responses.add(
        responses.GET,
        final_url,
        status=200,
        headers={"X-Custom-Header": "TestValue"}
    )

    resp = requests.get(start_url)

    assert resp.status_code == 200
    assert resp.url == final_url
    assert resp.ok is True
    assert resp.headers["X-Custom-Header"] == "TestValue"



def test_invoke_json_deserializes_payload_to_native_structures(mock_server):
    response = requests.get(f"{mock_server}/json_valid")
    data = response.json()

    assert data["id"] == 1042
    assert isinstance(data["id"], int)
    assert data["active"] is True
    assert data["tags"] == ["api", "test"]
    assert data["metadata"]["key"] is None


def test_parse_invalid_json_raises_json_decode_error(mock_server):
    # Test 1: Entirely empty string
    response_empty = requests.get(f"{mock_server}/json_empty")
    with pytest.raises(requests.exceptions.JSONDecodeError):
        response_empty.json()

    # Test 2: Truncated/malformed JSON string
    response_malformed = requests.get(f"{mock_server}/json_malformed")
    with pytest.raises(requests.exceptions.JSONDecodeError):
        response_malformed.json()


def test_raise_for_status_triggers_on_error_codes_only(mock_server):
    # 200 (OK) - Must pass silently
    response_200 = requests.get(f"{mock_server}/status/200")
    response_200.raise_for_status()

    # 399 (Custom/Edge Redirect) - Must pass silently
    response_399 = requests.get(f"{mock_server}/status/399")
    response_399.raise_for_status()

    # 400 (Bad Request) - Must raise HTTPError
    response_400 = requests.get(f"{mock_server}/status/400")
    with pytest.raises(requests.exceptions.HTTPError):
        response_400.raise_for_status()

    # 500 (Internal Server Error) - Must raise HTTPError
    response_500 = requests.get(f"{mock_server}/status/500")
    with pytest.raises(requests.exceptions.HTTPError):
        response_500.raise_for_status()


def test_unreachable_destination_raises_connection_error():
    # 1. Invalid, non-resolvable domain name
    with pytest.raises(requests.exceptions.ConnectionError):
        requests.get("http://this-domain-is-guaranteed-to-not-exist.local")

    # 2. Valid localhost address on a closed port
    with pytest.raises(requests.exceptions.ConnectionError):
        requests.get("http://127.0.0.1:65534")


def test_request_exceeds_timeout_raises_timeout_exception(mock_server):
    url = f"{mock_server}/timeout"

    # Test with strict float timeout
    with pytest.raises(requests.exceptions.Timeout):
        requests.get(url, timeout=0.001)

    # Test with tuple timeout (connection timeout, read timeout)
    with pytest.raises(requests.exceptions.Timeout):
        requests.get(url, timeout=(0.001, 0.001))

class MockRedirectAdapter(BaseAdapter):
    """
    A custom requests adapter to simulate server redirect behaviors
    without requiring external mocking libraries or real network I/O.
    """
    def __init__(self, behavior="loop"):
        super().__init__()
        self.behavior = behavior
        self.request_count = 0

    def send(self, request, **kwargs):
        self.request_count += 1

        response = Response()
        response.request = request
        response.url = request.url
        response.reason = "Found"

        if self.behavior == "loop":
            # Edge Case 1: Infinite loop pointing to the exact same URL
            response.status_code = 302
            response.headers['Location'] = request.url

        elif self.behavior == "chain":
            # Edge Case 2: Chain of exactly 31 sequential redirects
            if self.request_count > 31:
                # If the library fails to enforce the limit of 30, it will hit this 32nd request.
                response.status_code = 200
                response.reason = "OK"
                response.raw = HTTPResponse(body=BytesIO(b"Success"), preload_content=False)
                return response

            response.status_code = 302
            response.headers['Location'] = f"http://mock.local/step/{self.request_count}"

        # Provide a dummy raw byte stream to satisfy requests' internal reading mechanisms
        response.raw = HTTPResponse(body=BytesIO(b""), preload_content=False)
        return response

    def close(self):
        pass


def test_request_exceeds_max_redirects_raises_too_many_redirects_exception():
    # --- Scenario 1: Infinite Loop (Same URL) ---
    session_loop = requests.Session()
    adapter_loop = MockRedirectAdapter(behavior="loop")
    session_loop.mount("http://", adapter_loop)

    with pytest.raises(requests.exceptions.TooManyRedirects) as exc_loop:
        session_loop.get("http://mock.local/loop")

    assert "Exceeded 30 redirects" in str(exc_loop.value)

    # --- Scenario 2: Chain of exactly 31 sequential redirects ---
    session_chain = requests.Session()
    adapter_chain = MockRedirectAdapter(behavior="chain")
    session_chain.mount("http://", adapter_chain)

    with pytest.raises(requests.exceptions.TooManyRedirects) as exc_chain:
        session_chain.get("http://mock.local/start")

    assert "Exceeded 30 redirects" in str(exc_chain.value)

    # Verify the strict enforcement of the default maximum threshold (30).
    # The adapter should receive exactly 31 requests:
    # 1 initial request + 30 followed redirects.
    # The 31st response is a redirect that is correctly aborted before being followed.
    assert adapter_chain.request_count == 31
