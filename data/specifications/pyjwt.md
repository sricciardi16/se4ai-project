Project: `secure_signet`


## 1. High-Level Goal
Implement a Python library named `secure_signet` that encodes, decodes, and verifies secure, signed JSON tokens. The library must support symmetric (HMAC) and asymmetric (RSA) cryptographic signatures, handle standard token claims (like expiration and audience), and provide a client for fetching public keys from a JSON Web Key Set (JWKS) endpoint.

## 2. Module Structure
You must create a root module named `secure_signet` and a submodule for exceptions.
* `secure_signet/__init__.py` (Exposes the main API)
* `secure_signet/exceptions.py` (Contains all custom exceptions)

### 2.1. Exceptions
Implement the following custom exception classes in `secure_signet.exceptions`. They can inherit from standard Python `Exception`:
* `DecodeError`
* `ExpiredSignatureError`
* `ImmatureSignatureError`
* `InvalidAlgorithmError`
* `InvalidAudienceError`
* `InvalidIssuerError`
* `InvalidSignatureError`
* `MissingRequiredClaimError`

## 3. Core Functions

### 3.1. `encode(payload, key, algorithm, headers=None)`
Implement a function that serializes and signs a payload into a token string.

**Signatures & Types:**
* `payload`: `dict`
* `key`: `str` or `bytes`
* `algorithm`: `str`
* `headers`: `dict` (optional, default `None`)
* **Returns:** `str`

**Strict Behaviors & Rules:**
1. **Header Construction:** Create a header dictionary. Merge any custom headers provided in the `headers` argument. You MUST automatically include `"alg": algorithm` and `"typ": "JWT"` in the header.
2. **Datetime Conversion:** Scan the `payload` dictionary. If any value (specifically for claims like `exp` or `nbf`) is a timezone-aware `datetime.datetime` object, convert it to an integer Unix timestamp (seconds since epoch) before serialization.
3. **Serialization:** Serialize both the header and the payload to JSON strings. The JSON serialization must preserve Unicode characters (e.g., UTF-8 encoding).
4. **Type Validation:** If the payload contains unserializable objects (like `set` or `object()`), raise a standard Python `TypeError`.
5. **Base64url Encoding:** Encode the JSON header and JSON payload using Base64url encoding **without padding** (strip any trailing `=` characters).
6. **Algorithm Support:** Support at least `HS256`, `HS512`, and `RS256`. If the requested `algorithm` is not supported, raise a `NotImplementedError`.
7. **Signing:** Create a signature over the string `<base64url_header>.<base64url_payload>` using the specified `algorithm` and `key`. Base64url-encode the resulting signature (without padding).
8. **Output:** Return the final token as a string in the format: `<base64url_header>.<base64url_payload>.<base64url_signature>`.

### 3.2. `decode(token, key, algorithms, issuer=None, audience=None, leeway=0, options=None)`
Implement a function that verifies and decodes a token string back into its payload dictionary.

**Signatures & Types:**
* `token`: `str` or `bytes`
* `key`: `str` or `bytes`
* `algorithms`: `list` of `str`
* `issuer`: `str` (optional)
* `audience`: `str` (optional)
* `leeway`: `int` (optional, default `0`)
* `options`: `dict` (optional, default `None`)
* **Returns:** `dict`

**Strict Behaviors & Rules:**
1. **Input Validation:** If `token` is `None` or not a string/bytes, raise `DecodeError`.
2. **Structural Validation:** Split the token by the `.` character. If there are not exactly 3 segments, or if the token is an empty string, raise `DecodeError`.
3. **Decoding:** Base64url-decode the header and payload. If the base64 string contains invalid characters or cannot be decoded, raise `DecodeError`. Parse the decoded strings as JSON.
4. **Algorithm Validation:** Extract the `alg` from the header. If this algorithm is NOT present in the provided `algorithms` list, raise `InvalidAlgorithmError`. (Crucial security rule: If the header specifies `"alg": "none"`, you must raise `InvalidAlgorithmError` unless `"none"` is explicitly in the `algorithms` list).
5. **Signature Verification:** Recompute the signature of the `<base64url_header>.<base64url_payload>` using the provided `key` and the algorithm specified in the header. If the signature does not match the third segment of the token, raise `InvalidSignatureError`.
6. **Expiration (`exp`) Validation:** If the payload contains an `exp` claim, compare it to the current Unix time. Raise `ExpiredSignatureError` if `current_time >= exp + leeway`.
7. **Not Before (`nbf`) Validation:** If the payload contains an `nbf` claim, compare it to the current Unix time. Raise `ImmatureSignatureError` if `current_time < nbf - leeway`.
8. **Issuer (`iss`) Validation:** If the `issuer` argument is provided, verify it matches the `iss` claim in the payload. If it does not match, raise `InvalidIssuerError`.
9. **Audience (`aud`) Validation:** If the `audience` argument is provided, verify it matches the `aud` claim in the payload. The payload's `aud` claim might be a single string or a list of strings. If the provided `audience` is not equal to the string (or not contained in the list), raise `InvalidAudienceError`.
10. **Required Claims Validation:** If the `options` dictionary is provided and contains a `"require"` key (which maps to a list of claim names), verify that every claim in that list exists in the payload. If any are missing, raise `MissingRequiredClaimError`.
11. **Output:** Return the decoded payload dictionary. Ensure integer claims (like `iat`) remain integers.

### 3.3. `get_unverified_header(token)`
Implement a function that extracts the header from a token without verifying the signature.

**Signatures & Types:**
* `token`: `str`
* **Returns:** `dict`

**Strict Behaviors & Rules:**
1. Split the token by `.`. If it does not have 3 parts or contains invalid base64 characters, raise `DecodeError`.
2. Base64url-decode the first segment and parse it as JSON.
3. Return the resulting dictionary. Do **not** perform any signature validation.

## 4. Classes

### 4.1. `PyJWKClient`
Implement a client class that fetches and parses JSON Web Key Sets (JWKS) from a URL to retrieve RSA public keys.

**Constructor:** `__init__(self, uri: str, cache_keys: bool = False)`
* `uri`: The URL of the JWKS endpoint.
* `cache_keys`: A boolean indicating whether to cache HTTP responses.

**Method:** `get_signing_key_from_jwt(self, token: str)`
* **Returns:** An object (you may create a helper class for this) that has exactly two attributes:
  1. `key_id`: A string representing the Key ID (`kid`).
  2. `key`: An RSA public key object (specifically, an instance of `cryptography.hazmat.primitives.asymmetric.rsa.RSAPublicKey`).

**Strict Behaviors & Rules:**
1. **Header Extraction:** Use `get_unverified_header` on the provided `token` to extract the `kid` (Key ID).
2. **Network Request:** Use the standard library `urllib.request.urlopen` to fetch the JSON payload from the `uri`.
3. **Caching:** If `cache_keys` was set to `True` during initialization, you must cache the fetched keys. Subsequent calls to `get_signing_key_from_jwt` for a `kid` that is already cached MUST NOT trigger another `urlopen` network request.
4. **Key Matching:** Parse the fetched JSON (which will have a `"keys"` array). Find the dictionary in that array where the `"kid"` matches the token's `kid`.
5. **RSA Key Construction:** The matched JWK dictionary will contain `"n"` (modulus) and `"e"` (exponent) values, which are Base64url-encoded integers. Decode these values into Python integers and use them to construct an RSA public key using the `cryptography` library (`rsa.RSAPublicNumbers(e, n).public_key(default_backend())`).
6. **Output:** Return the object containing the `key_id` and the constructed `key`.