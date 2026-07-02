Project: `http_client`


## 1. High-Level Goal
Implement a robust, user-friendly HTTP client library named `http_client`. The library must handle HTTP requests and responses, manage session state (cookies and headers), automatically follow redirects, serialize/deserialize JSON and form data, and provide a strict, predictable exception hierarchy for error handling.

## 2. Module Structure
Create a top-level module named `http_client`. It must expose the following submodules and shortcuts directly at the top level:

**Required Submodules:**
*   `http_client.api`
*   `http_client.sessions`
*   `http_client.models`
*   `http_client.auth`
*   `http_client.exceptions`
*   `http_client.adapters`

**Required Top-Level Shortcuts:**
*   `http_client.get` (callable function)
*   `http_client.post` (callable function)
*   `http_client.request` (callable function)
*   `http_client.Session` (class)
*   `http_client.Request` (class)
*   `http_client.Response` (class)

## 3. Exception Hierarchy (`http_client.exceptions`)
Implement the following exception classes. They must be importable from `http_client.exceptions`:

*   `RequestException`: The base exception for all request-related errors.
*   `MissingSchema`: Raised when a URL lacks an HTTP/HTTPS scheme (inherits from `RequestException`).
*   `ConnectionError`: Raised when a destination is unreachable (e.g., unresolvable domain, closed port).
*   `Timeout`: Raised when a request exceeds the configured timeout duration.
*   `TooManyRedirects`: Raised when the redirect limit is exceeded.
*   `HTTPError`: Raised by `Response.raise_for_status()` for failing HTTP status codes.
*   `JSONDecodeError`: Raised when attempting to parse invalid JSON. **Must inherit from Python's built-in `ValueError`.**

## 4. Core Classes & Behaviors

### `http_client.models.Request`
Implement a class representing an HTTP request before it is prepared or sent.
*   **Signature:** `__init__(self, method: str, url: str, headers: dict = None, ...)`
*   **Behavior:** Store the provided arguments as instance attributes.

### `http_client.models.PreparedRequest`
Implement a class representing a fully constructed request ready for network transmission.
*   **Attributes:** Must expose `method` (str), `url` (str), `headers` (dict-like), and `body` (bytes or str).

### `http_client.models.Response`
Implement a class representing an HTTP response.
*   **Attributes:**
    *   `status_code` (int): The HTTP status code.
    *   `url` (str): The final URL of the response (after any redirects).
    *   `headers` (dict): The response headers.
    *   `ok` (bool): Must evaluate to `True` if `status_code` is strictly less than 400, and `False` otherwise.
    *   `raw` (file-like object): A stream representing the raw socket response. The library must read from this attribute to populate the content.
    *   `content` (bytes): The raw binary payload of the response.
    *   `encoding` (str): The character encoding (e.g., `"Shift_JIS"`, `"utf-8"`) parsed from the `Content-Type` header.
    *   `text` (str): The decoded string representation of the payload. Must automatically decode `content` using the `encoding` attribute.
    *   `request` (`PreparedRequest`): The request object that generated this response.
*   **Methods:**
    *   `json()`: Parse the response body as JSON and return native Python data structures (dicts, lists, ints, bools, etc.). 
        *   *Rule:* If the payload is empty, truncated, or malformed, raise `http_client.exceptions.JSONDecodeError`.
    *   `iter_content(chunk_size: int)`: Return an iterator/generator that yields the raw binary payload (`bytes`) in chunks of exactly `chunk_size`.
    *   `raise_for_status()`: 
        *   *Rule:* If `status_code` is between 100 and 399 (inclusive), do nothing (pass silently).
        *   *Rule:* If `status_code` is 400 or greater, raise `http_client.exceptions.HTTPError`.

### `http_client.adapters.BaseAdapter`
Implement a base class for transport adapters.
*   **Methods:**
    *   `send(self, request: PreparedRequest, **kwargs) -> Response`: Must be implemented by subclasses to handle the actual network I/O.
    *   `close(self)`: Cleans up adapter resources.

### `http_client.sessions.Session`
Implement a class that manages state and executes requests. Must support use as a context manager (`with Session() as session:`).
*   **Attributes:**
    *   `headers` (dict-like): Global headers applied to all requests made by this session.
*   **Methods:**
    *   `get(url, **kwargs)`: Shortcut for `request("GET", url, **kwargs)`.
    *   `post(url, **kwargs)`: Shortcut for `request("POST", url, **kwargs)`.
    *   `request(method: str, url: str, **kwargs) -> Response`: The primary routing method. Must dynamically execute the HTTP verb provided in the `method` string (e.g., "PATCH", "OPTIONS").
    *   `prepare_request(request: Request) -> PreparedRequest`: Convert a `Request` object into a `PreparedRequest`, retaining the method, url, and headers.
    *   `mount(prefix: str, adapter: BaseAdapter)`: Register a transport adapter to a specific URL prefix (e.g., `"http://"`).

## 5. Strict Logical Rules & Behaviors

### URL & Query Parameter Handling
*   **Missing Schema:** If a URL string lacks an HTTP/HTTPS scheme (e.g., `"example.com/path"`), raise `http_client.exceptions.MissingSchema`.
*   **Malformed URL:** If a URL string is completely invalid (e.g., `"not a url"`), raise `http_client.exceptions.RequestException`.
*   **Query Parameters (`params` argument):** When a dictionary is passed to the `params` argument:
    *   Serialize the dictionary into a URL-encoded query string and append it to the URL with a `?`.
    *   Encode spaces as `+` and special characters as their `%XX` hex equivalents (e.g., `&` becomes `%26`, `@` becomes `%40`).
    *   *Rule:* If a key in the `params` dictionary has a value of `None`, completely omit that key from the resulting URL query string.
    *   *Rule:* If a key has an empty string `""`, include the key with an empty value (e.g., `key=`).

### Request Body & Serialization
*   **Form Data (`data` argument):** When a dictionary is passed to the `data` argument:
    *   Serialize the dictionary into a URL-encoded string (spaces to `+`, etc.).
    *   Set the `PreparedRequest.body` to this string.
    *   Automatically set the `Content-Type` header to `application/x-www-form-urlencoded`.
*   **JSON Data (`json` argument):** When a dictionary is passed to the `json` argument:
    *   Serialize the dictionary into a valid JSON byte string.
    *   Set the `PreparedRequest.body` to these bytes.
    *   Automatically set the `Content-Type` header to `application/json`.
*   **Priority Rule:** If *both* `data` and `json` arguments are provided in the same request, prioritize `data`. Completely ignore the `json` argument, format the body as form-urlencoded, and set the `Content-Type` to `application/x-www-form-urlencoded`.

### Headers & State Persistence
*   **Session Headers:** Headers added to `Session.headers` must be automatically included in every request made by that session.
*   **Header Overrides:** If a `headers` dictionary is passed to a specific request method (e.g., `session.get(url, headers={...})`), these headers must override any conflicting keys in `Session.headers` for that specific request only.
*   **Cookie Persistence:** If a server responds with a `Set-Cookie` header, the `Session` must parse and store that cookie. On all subsequent requests to the same domain, the `Session` must automatically construct and send a `Cookie` header containing the stored cookies.

### Authentication
*   **Basic Auth (`auth` argument):** When a tuple of `(username, password)` is passed to the `auth` argument, the library must automatically construct an `Authorization` header. The value must be `Basic ` followed by the Base64-encoded string of `username:password`.

### Timeouts & Connections
*   **Timeout Argument:** The `timeout` argument must accept either a single `float` (total timeout in seconds) or a `tuple` of two floats `(connection_timeout, read_timeout)`.
*   **Timeout Exception:** If the server fails to respond within the specified timeout duration, raise `http_client.exceptions.Timeout`.
*   **Connection Error:** If the destination domain is unresolvable or the target port is closed, raise `http_client.exceptions.ConnectionError`.

### Redirects
*   **Automatic Following:** By default, the library must automatically follow HTTP redirects (e.g., 301, 302).
*   **Redirect Attributes:** When a redirect is followed, the final `Response` object must reflect the final destination's `status_code`, `url`, and `headers`.
*   **Maximum Redirect Limit:** The library must enforce a strict maximum limit of exactly **30** redirects per request.
*   **TooManyRedirects Exception:** If a 31st redirect is encountered (either via an infinite loop to the same URL or a long chain of different URLs), the library must abort the request and raise `http_client.exceptions.TooManyRedirects`. The exception message must contain the exact phrase `"Exceeded 30 redirects"`.

### Streaming
*   **Stream Argument:** When `stream=True` is passed to a request, the library must *not* immediately download the response body. It must only read the headers. The user will then use `Response.iter_content(chunk_size)` to download the body iteratively.